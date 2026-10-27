/* ═══ La note d'interface de Cura, mesurée ═══
   Référentiel construit le 27 octobre 2026 à partir des sources suivantes,
   classées par niveau de preuve :

   · WCAG 2.2 (W3C) — norme opposable, entièrement mesurable.
     2.5.8 AA : cible d'au moins 24 × 24 px CSS. 2.5.5 AAA : 44 × 44.
     1.4.3 AA : contraste 4,5:1 pour le texte courant, 3:1 pour le grand
     texte (≥ 18,66 px, ou 14 px en gras).
   · Apple Human Interface Guidelines — la plateforme où Cura tourne :
     cible tactile de 44 × 44 pt. Plus exigeant que WCAG AA, et c'est la
     norme qui s'applique ici.
   · Nielsen Norman Group — les 10 heuristiques (1994, révisées 2020,
     établies sur 249 problèmes d'utilisabilité analysés). Qualitatives :
     elles se vérifient écran par écran, pas au pixel.
   · AppsFlyer 2025, repris par plusieurs analyses : atteindre la
     première valeur dans la première session multiplie par 2 à 3 la
     rétention à 7 jours. Médiane d'activation mesurée par Lenny
     Rachitsky sur plus de 500 produits : 36 %.

   Ce fichier ne mesure QUE ce qui est mesurable sans interprétation.
   Le reste de la grille est noté à la main, et dit qu'il l'est. */

(function(){
  "use strict";

  function aireVisible(e){
    var r = e.getBoundingClientRect();
    return {w: r.width, h: r.height, vu: r.width > 0 && r.height > 0};
  }

  /* Luminance relative, formule WCAG 2.x exactement. */
  function lum(rgb){
    var c = rgb.map(function(v){
      v = v / 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  }
  function contraste(a, b){
    var l1 = lum(a), l2 = lum(b);
    return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  }
  function rgb(s){
    var m = /rgba?\(([^)]+)\)/.exec(s || "");
    if(!m) return null;
    var p = m[1].split(",").map(function(x){ return parseFloat(x); });
    if(p.length > 3 && p[3] < 0.95) return null;   /* translucide : fond incertain */
    return [p[0], p[1], p[2]];
  }
  /* Le fond réel d'un texte : on remonte les parents jusqu'à une couleur opaque. */
  function fondDe(e){
    var n = e;
    while(n && n !== document.documentElement){
      var c = rgb(window.getComputedStyle(n).backgroundColor);
      if(c) return c;
      n = n.parentElement;
    }
    var b = rgb(window.getComputedStyle(document.body).backgroundColor);
    return b || [255, 255, 255];
  }

  function visible(e){
    var s = window.getComputedStyle(e);
    if(s.display === "none" || s.visibility === "hidden" || Number(s.opacity) < 0.1) return false;
    var a = aireVisible(e);
    return a.vu;
  }

  /* ── 1 · les cibles tactiles ───────────────────────────────────── */
  function cibles(){
    var sel = 'button, a[href], input, select, textarea, summary, [role="button"], [tabindex]:not([tabindex="-1"])';
    var tout = [].slice.call(document.querySelectorAll(sel)).filter(visible);
    var petites = [], tres = [];
    tout.forEach(function(e){
      var a = aireVisible(e);
      var cote = Math.min(a.w, a.h);
      if(cote < 24) tres.push({quoi: (e.textContent || e.name || e.id || e.tagName).trim().slice(0, 34),
                               w: Math.round(a.w), h: Math.round(a.h)});
      else if(cote < 44) petites.push({quoi: (e.textContent || e.name || e.id || e.tagName).trim().slice(0, 34),
                                       w: Math.round(a.w), h: Math.round(a.h)});
    });
    return {total: tout.length, sous_44: petites.length, sous_24: tres.length,
            exemples_sous_24: tres.slice(0, 6), exemples_sous_44: petites.slice(0, 6)};
  }

  /* ── 2 · le contraste du texte ─────────────────────────────────── */
  function contrastes(){
    var tout = [].slice.call(document.querySelectorAll("body *")).filter(function(e){
      if(!visible(e)) return false;
      var t = "";
      for(var i = 0; i < e.childNodes.length; i++)
        if(e.childNodes[i].nodeType === 3) t += e.childNodes[i].nodeValue;
      return t.trim().length > 0;
    });
    var echecs = [];
    tout.forEach(function(e){
      var s = window.getComputedStyle(e);
      var av = rgb(s.color);
      if(!av) return;
      var ap = fondDe(e);
      var px = parseFloat(s.fontSize), gras = Number(s.fontWeight) >= 700;
      var seuil = (px >= 18.66 || (px >= 14 && gras)) ? 3 : 4.5;
      var c = contraste(av, ap);
      if(c < seuil) echecs.push({texte: (e.textContent || "").trim().slice(0, 40),
                                 ratio: Math.round(c * 100) / 100, seuil: seuil, px: Math.round(px)});
    });
    return {textes: tout.length, echecs: echecs.length, liste: echecs.slice(0, 8)};
  }

  /* ── 3 · la densité de décision (Hick) ─────────────────────────── */
  function densite(){
    var vus = [].slice.call(document.querySelectorAll(
      'button, a[href], [role="button"]')).filter(function(e){
      if(!visible(e)) return false;
      var r = e.getBoundingClientRect();
      return r.top < window.innerHeight && r.bottom > 0;   /* dans le premier écran */
    });
    return {choix_premier_ecran: vus.length};
  }

  window.__NOTE__ = function(){
    return {cibles: cibles(), contraste: contrastes(), densite: densite(),
            ecran: {w: window.innerWidth, h: window.innerHeight}};
  };
})();
