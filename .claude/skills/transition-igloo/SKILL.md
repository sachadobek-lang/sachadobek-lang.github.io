---
name: transition-igloo
description: Recrée la transition de scroll d'igloo.inc entre deux scènes 3D (three.js + postprocessing). La scène suivante monte par le bas en diagonale, rongée par une texture de glace, avec parallaxe et aberration chromatique arc-en-ciel. Le tout suit le scroll, avec le double lissage d'igloo. À utiliser quand Sacha demande « la transition igloo », une transition « comme igloo.inc », ou un passage d'une scène 3D à une autre piloté par le défilement.
---

# Transition igloo

Transition de scroll entre deux scènes 3D, fidèle à igloo.inc. Les formules ont été lues
dans leur code, puis **réécrites à la main**. Ne jamais copier les fichiers, textures, sons
ou code d'igloo.inc dans un site de Sacha : ce sont leurs créations.

- Valeurs exactes et explication : [reference.md](reference.md).
- Module prêt à brancher : [transition.js](transition.js), à copier dans le site.

## Ce que voit l'utilisateur

1. Il défile. L'image suit son doigt et peut s'arrêter au milieu.
2. La scène suivante monte par le bas en diagonale. Son bord est rongé par de la glace.
3. L'ancienne scène glisse vers le haut, la nouvelle arrive de dessous (parallaxe en cube).
4. Un flou en éventail avec des franges arc-en-ciel accompagne le passage.
5. Rien d'autre : pas de trait lumineux, pas de flash.

## Brancher la transition

1. **Deux images.**
   - La scène actuelle passe par l'`EffectComposer`.
   - La scène suivante est dessinée dans un `WebGLRenderTarget` HalfFloat (`rtB`), à la taille
     du tampon de dessin.
   - **Toujours appeler `renderer.clear()`** juste après `setRenderTarget(rtB)`. Le composeur
     coupe l'effacement automatique : sans ça, l'image d'avant reste en taches.
2. **Une passe à part.**
   - `IglooTransitionEffect` lit `inputBuffer`. Il doit donc être **seul dans son
     `EffectPass`**, placé après les passes de flou ou de profondeur de champ.
   - S'il est fusionné avec un autre effet, il lit l'image d'avant ces effets.
3. **À chaque image :**
   ```js
   const y = scroll.update(dtMs);
   fx.setProgress(scroll.transition());
   fx.setAspect(innerWidth / innerHeight);
   fx.tick();
   if (scroll.transition() > 0.001) {
     renderer.setRenderTarget(rtB); renderer.clear(); renderer.render(nextScene, nextCam);
     renderer.setRenderTarget(null);
   }
   fx.setNextScene(rtB.texture);
   composer.render();
   ```
4. **Économie.**
   - Ne dessiner la scène suivante que pendant et après la transition.
   - Quand la transition est finie, cacher la scène de départ avec `scene.visible = false`.
   - **Ne pas couper la `RenderPass`** : coupée, son tampon casse quand la résolution change.
5. **La caméra de la scène de départ (option).** `iglooCamera(progression)` reproduit leur
   recul pendant la sortie. Ces chiffres valent pour un objet au centre, vu à environ 20 unités.

## Réglages

| Valeur | Chez igloo | Effet |
|---|---|---|
| Pente de la diagonale | 0,2 × ratio de l'écran | inclinaison du bord |
| Ondulation du bord | ± 0,4 (canal B) | bord vivant |
| Marges de fondu | 2,0 / 0,9 / 0,2 | flou / décalage / coupe |
| Parallaxe | 0,4 × p³ | glissement des deux scènes |
| Décalage tech | 0,025 | petits sauts « rectangles » |
| Aberration | 12, nulle aux bords | arc-en-ciel |
| Molette | 0,00075 écran par unité | sensibilité |
| Lissage | 0,075 puis 0,15 | sensation de glisse |

## Pièges déjà rencontrés

- **Étalonnage sombre** : si le site utilise une courbe façon igloo (0,47 → noir), les couleurs
  foncées tournent au noir. Éclaircir la texture du produit, ou compenser l'étalonnage sur
  une photo de fond.
- **Même ambiance des deux côtés** : les deux scènes doivent passer par le même étalonnage
  (brume, grain, gris-bleu). Sinon la transition « change de film ».
- **Pas d'aimant** : chez igloo, le scroll revient tout seul au repos après 1,4 s. Sacha l'a
  ressenti comme un bug sur pavé tactile. Ne pas l'ajouter sans le lui demander.
- **Texture faite maison** : la texture de transition et le bruit sont générés par le code.
  Le rendu est proche d'igloo, mais pas identique au pixel. Le dire honnêtement.

## Vérifier avant de publier

- Capturer la transition à 15 %, 30 %, 60 % et 85 % : la nouvelle scène doit monter par le
  bas, rongée par la glace, avec les franges.
- Tester avec des événements `wheel` espacés : s'arrêter au milieu (l'image reste), continuer,
  puis remonter.
- Dans Chromium sans carte graphique (SwiftShader), le lissage paraît lent : c'est normal, il
  ne fait qu'environ 1 image par seconde.
