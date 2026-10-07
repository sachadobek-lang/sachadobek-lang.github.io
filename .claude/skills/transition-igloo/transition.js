// Transition « igloo » — module prêt à brancher (three.js 0.165 + postprocessing 6.36).
// Formules étudiées sur igloo.inc puis réécrites à la main. Aucun fichier, texture ou code d'igloo
// n'est repris : la texture de transition et le bruit sont générés ici.
//
// Usage minimal :
//   const fx = new IglooTransitionEffect();             // à mettre SEUL dans son EffectPass
//   composer.addPass(new EffectPass(camera, fx));        // après les autres passes (flou, etc.)
//   fx.setNextScene(rtB.texture);                        // image de la scène qui arrive
//   const scroll = new IglooScroll({ end: 1.69 });       // 0 = repos, end = arrivée
//   scroll.attach(window);
//   // à chaque image :
//   scroll.update(dtMs); fx.setProgress(scroll.transition()); fx.setAspect(innerWidth / innerHeight); fx.tick();

import * as THREE from 'three';
import { Effect } from 'postprocessing';

/* ---------- 1. La texture de transition : R glace, G rectangles « tech », B bruit flou ---------- */
export function makeScrollTexture(N = 512, seed = 1) {
  let s = seed >>> 0;
  const rnd = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
  const ph = (x, y, P, sd) => { const xi = ((x % P) + P) % P, yi = ((y % P) + P) % P; const v = Math.sin(xi * 127.1 + yi * 311.7 + sd * 74.7) * 43758.5453; return v - Math.floor(v); };
  const pn = (u, v, P, sd) => {
    const x = u * P, y = v * P, xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
    const a = xf * xf * (3 - 2 * xf), b = yf * yf * (3 - 2 * yf);
    return (ph(xi, yi, P, sd) * (1 - a) + ph(xi + 1, yi, P, sd) * a) * (1 - b) + (ph(xi, yi + 1, P, sd) * (1 - a) + ph(xi + 1, yi + 1, P, sd) * a) * b;
  };
  const fb = (u, v, P, sd, o) => { let r = 0, w = 0.5, t = 0; for (let i = 0; i < o; i++) { r += w * pn(u, v, P << i, sd + i); t += w; w *= 0.5; } return r / t; };
  const c = document.createElement('canvas'); c.width = c.height = N; const x = c.getContext('2d');
  // G : rectangles gris superposés, raccordés sur les bords (la texture se répète sans couture)
  x.fillStyle = '#000'; x.fillRect(0, 0, N, N);
  for (let i = 0; i < 1400; i++) {
    const w = 2 + Math.pow(rnd(), 2.2) * 70, h = 2 + Math.pow(rnd(), 2.2) * 60, px = rnd() * N, py = rnd() * N;
    const g = rnd() < 0.12 ? 255 : (rnd() * 230) | 0;
    x.fillStyle = `rgb(${g},${g},${g})`;
    for (const ox of [-N, 0, N]) for (const oy of [-N, 0, N]) x.fillRect(px + ox, py + oy, w, h);
  }
  const G = x.getImageData(0, 0, N, N).data, im = x.createImageData(N, N);
  for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) {
    const u = i / N, v = j / N, o = (j * N + i) * 4;
    let r = 0.55 * fb(u, v, 6, 1, 5) + 0.25 * fb(u, v * 0.25 + u * 0.02, 32, 7, 3) + 0.2 * fb(u, v, 48, 13, 2);   // glace : grain + rayures
    r = Math.min(1, Math.max(0, (r - 0.5) * 2.2 + 0.5));
    im.data[o] = r * 255; im.data[o + 1] = G[o]; im.data[o + 2] = fb(u, v, 4, 21, 2) * 255; im.data[o + 3] = 255;
  }
  x.putImageData(im, 0, 0);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.NoColorSpace; t.generateMipmaps = false; t.minFilter = THREE.LinearFilter;
  return t;
}

/* ---------- 2. L'effet : diagonale rongée par la glace, parallaxe, aberration chromatique ---------- */
const FRAG = /* glsl */`
  uniform sampler2D tB; uniform sampler2D tScroll;
  uniform float uProgress; uniform float uAspect; uniform vec2 uNoiseOffset;
  // fondu : 1 quand x <= q, 0 quand x >= q + marge, avec q = mix(-marge, 1, u)
  float fo(float x, float m, float u){ float q = mix(-m, 1.0, u); return clamp((q + m - x) / m, 0.0, 1.0); }
  vec2 barrel(vec2 c, float a){ vec2 d = c - 0.5; return c + d * dot(d, d) * a; }
  vec4 spec(float t){
    float lo = step(t, 0.5), hi = 1.0 - lo;
    float w = clamp(1.0 - abs(2.0 * clamp((t - 1.0 / 6.0) / (4.0 / 6.0), 0.0, 1.0) - 1.0), 0.0, 1.0);
    return pow(vec4(lo, 1.0, hi, 1.0) * vec4(1.0 - w, w, 1.0 - w, 1.0), vec4(1.0 / 2.2));
  }
  vec3 ca(sampler2D tx, vec2 uv, float k){
    vec4 s = vec4(0.0), sw = vec4(0.0);
    for (int i = 0; i < 5; i++){ float t = float(i) / 5.0; vec4 w = spec(t); sw += w; s += w * texture2D(tx, barrel(uv, k * t)); }
    return (s / sw).rgb;
  }
  void mainImage(const in vec4 inputColor, const in vec2 uv, out vec4 outputColor){
    float p = uProgress;
    if (p <= 0.0) { outputColor = inputColor; return; }
    if (p >= 1.0) { outputColor = vec4(texture2D(tB, uv).rgb, 1.0); return; }
    vec2 ut = uv - 0.5; ut.x *= uAspect; ut += 0.5;
    vec3 st = texture2D(tScroll, ut).rgb;                                  // R glace, G rectangles, B flou
    float slope = 0.2 * uAspect;
    float g = uv.y + (uv.x + (st.b * 2.0 - 1.0) * 0.4) * slope;             // diagonale ondulée
    float pi = p * (1.0 + slope);
    float blurK = fo(g, 2.0, pi);
    float cutDisp = fo(st.g, 1.0, fo(g, 0.9, pi));
    float cut = fo(st.r, 2.0, fo(g, 0.2, pi));                             // la glace ronge le bord
    vec2 fc = gl_FragCoord.xy + uNoiseOffset * 128.0;                      // bruit régulier (proche d'un bruit bleu)
    vec2 nz = vec2(fract(52.9829189 * fract(dot(fc, vec2(0.06711056, 0.00583715)))),
                   fract(52.9829189 * fract(dot(fc + 37.0, vec2(0.06711056, 0.00583715)))));
    float modu = 12.0 * smoothstep(1.0, 0.7, abs(uv.x * 2.0 - 1.0)) * smoothstep(1.0, 0.7, abs(uv.y * 2.0 - 1.0));
    vec3 s1 = vec3(0.0), s2 = vec3(0.0);
    if (cut < 1.0) s1 = ca(inputBuffer, uv - vec2(0.0, 0.4 * p * p * p + 0.025 * cutDisp), modu * blurK * nz.x);
    if (cut > 0.0) s2 = ca(tB, uv + vec2(0.0, 0.4 * pow(1.0 - p, 3.0) + 0.025 * (1.0 - cutDisp)), modu * (1.0 - blurK) * nz.y);
    outputColor = vec4(max(mix(s1, s2, cut), vec3(0.0)), 1.0);
  }`;

export class IglooTransitionEffect extends Effect {
  constructor({ scrollTexture = makeScrollTexture() } = {}) {
    super('IglooTransitionEffect', FRAG, {
      uniforms: new Map([
        ['tB', new THREE.Uniform(null)], ['tScroll', new THREE.Uniform(scrollTexture)],
        ['uProgress', new THREE.Uniform(0)], ['uAspect', new THREE.Uniform(1)], ['uNoiseOffset', new THREE.Uniform(new THREE.Vector2())],
      ]),
    });
  }
  setNextScene(texture) { this.uniforms.get('tB').value = texture; }
  setProgress(p) { this.uniforms.get('uProgress').value = Math.min(1, Math.max(0, p)); }
  setAspect(a) { this.uniforms.get('uAspect').value = a; }
  tick() { this.uniforms.get('uNoiseOffset').value.set(Math.random() * 10, Math.random() * 12.5); }   // le bruit bouge à chaque image
}

/* ---------- 3. Le défilement piloté par le geste, avec le double lissage d'igloo ---------- */
// Unités : « écrans ». 0 = repos. La transition occupe 1 écran, et se termine à `end`.
export class IglooScroll {
  constructor({ end = 1.69, transitionStart = 0.69, min = -0.45 } = {}) {
    Object.assign(this, { end, transitionStart, min, target: 0, y1: 0, y: 0 });
  }
  scrollBy(screens) {
    this.target = Math.max(this.min, Math.min(this.end, this.target + screens));
    this.target = Math.max(this.y - 0.5625, Math.min(this.y + 0.5625, this.target));   // au plus 0,5625 écran d'avance
  }
  goTo(y) { this.target = Math.max(this.min, Math.min(this.end, y)); }
  update(dtMs) {
    const R = Math.min(5, dtMs / 16.67), lerp = (a, b, k) => a + (b - a) * (1 - Math.pow(1 - k, R));
    const d = lerp(this.y1, this.target, 0.075) - this.y1, mx = 0.075 * R;            // pas max 0,075 écran par image
    this.y1 += Math.max(-mx, Math.min(mx, d));
    this.y = lerp(this.y, this.y1, 0.15);
    return this.y;
  }
  transition() { return Math.min(1, Math.max(0, this.y - this.transitionStart)); }
  attach(el = window) {
    el.addEventListener('wheel', (e) => {
      e.preventDefault(); if (e.ctrlKey) return;                                       // pincement : pas un défilement
      const k = e.deltaMode === 1 ? 33 : e.deltaMode === 2 ? innerHeight : 1;
      this.scrollBy(Math.max(-400, Math.min(400, e.deltaY * k)) * 0.00075);            // molette : 0,00075 écran par unité
    }, { passive: false });
    el.addEventListener('keydown', (e) => {
      if (['ArrowDown', 'PageDown', ' '].includes(e.key)) this.scrollBy(0.1125);
      if (['ArrowUp', 'PageUp'].includes(e.key)) this.scrollBy(-0.1125);
    });
    let dragY = null;
    el.addEventListener('pointerdown', (e) => { if (e.pointerType !== 'mouse') dragY = e.clientY; });
    el.addEventListener('pointerup', () => { dragY = null; });
    el.addEventListener('pointercancel', () => { dragY = null; });
    el.addEventListener('pointermove', (e) => { if (dragY !== null) { this.scrollBy((dragY - e.clientY) / innerHeight * 1.25); dragY = e.clientY; } });
  }
}

/* ---------- 4. (optionnel) La caméra qui recule pendant la sortie, timeline de 21 s d'igloo ---------- */
// sceneProgress = (y + 0,66 + 1) / 3,35 avec y du défilement ci-dessus. Au repos ≈ 0,4955.
export function iglooCamera(sceneProgress, pos = new THREE.Vector3(), look = new THREE.Vector3()) {
  const t = 21 * Math.min(1, Math.max(0, sceneProgress));
  const a = Math.min(1, t / 14), out3 = 1 - Math.pow(1 - a, 3);                         // power2.out = cubique
  const b = Math.min(1, Math.max(0, (t - 7) / 14)), q = b < 0.5 ? 2 * b * b : 1 - Math.pow(-2 * b + 2, 2) / 2;   // power1.inOut
  pos.set(-13.25 - 2 * q, 2.5 + 9 * (1 - out3), 13.25 + 10 * q);
  look.set(0, 1 + 14 * (1 - out3), 0);
  return { pos, look };
}
