# Script parfait — la transition d'igloo.inc (igloo → scène suivante)

Lu dans leur code (App3D.js, shader de composition et timeline de caméra). Les formules
sont réécrites à la main ; aucun fichier ni aucune texture d'igloo n'est réutilisé.

## 1. Le défilement (ce qui pilote tout)

- Pas de vraie page qui défile : une valeur `y` en « écrans ».
- Entrées : molette × 0,00075 écran ; flèches ± 0,1125 ; glisser × 1,25.
- Double lissage, à chaque image :
  1. `y1 = lerpFPS(y1, cible, 0,075)`, pas plus de 0,075 écran par image ;
  2. `y  = lerpFPS(y, y1, 0,15)` ;
  3. la cible ne peut pas avoir plus de 0,5625 écran d'avance sur `y`.
- Scène igloo : 2,35 écrans de haut. Progression de la scène = `(y + 1) / 3,35`.
  Au repos `y = 0,66` → progression 0,4955.
- La transition commence à `y = 1,35` et finit à `y = 2,35` :
  `p = y − 1,35`, borné entre 0 et 1. Elle suit donc le doigt : on peut s'arrêter au milieu.
- Aimant : 1,4 s sans geste → retour en douceur au point de repos le plus proche
  (courbe inOut3). **Dans notre site** : remplacé par « un geste suffit », car l'aimant
  donnait l'impression de bug sur pavé tactile.

## 2. La caméra de l'igloo pendant qu'on défile

Timeline de 21 s, lue à `temps = 21 × progression` :

| De | À | Quoi | Courbe |
|---|---|---|---|
| 0 s | 14 s | hauteur de la caméra : 2,5 + 9 → 2,5 | power2.out (cubique) |
| 0 s | 14 s | hauteur du regard : 1 + 14 → 1 | power2.out |
| 7 s | 21 s | caméra : x −13,25 → −15,25 ; z 13,25 → 23,25 | power1.inOut (quadratique) |

Vérification : à 10,4 s (repos), on retombe sur (−13,49 ; 2,65 ; 14,43). Pendant la
transition, la caméra **recule** et s'éloigne de l'igloo.

## 3. L'image : deux scènes mélangées en plein écran

Chaque scène est dessinée dans sa propre image. Un triangle plein écran les mélange :

1. **Texture de transition** (3 canaux, répétée, corrigée du ratio de l'écran) :
   - R : glace, un grain sale et rayé ;
   - G : des rectangles gris de toutes tailles, façon « tech » ;
   - B : un bruit très flou.
2. **Diagonale** : pente −0,2 × ratio de l'écran. Le bord est ondulé par le canal B (± 0,4).
   `g = uv.y + (uv.x + ondulation) × 0,2 × ratio`
   `pi = p × (1 + 0,2 × ratio)`
3. **Fondu de leur code** : `falloff(x, marge, u)` vaut 1 quand `x ≤ q`, 0 quand
   `x ≥ q + marge`, avec `q = mix(−marge, 1, u)`.
   (Ma version d'avant était décalée d'une marge : c'était une erreur.)
4. Quatre masques, tous calculés sur `g` :
   - flou (aberration) : `falloff(g, 2,0, pi)` ;
   - décalage tech : `falloff(G, 1,0, falloff(g, 0,9, pi))` ;
   - **coupe** : `falloff(R, 2,0, falloff(g, 0,2, pi))`. La glace « ronge » le bord, et le
     bas de l'écran passe en premier.
5. **Parallaxe** :
   - l'igloo monte de `0,4 × p³` ;
   - la scène suivante arrive par le bas, avec `0,4 × (1 − p)³` ;
   - plus un petit décalage de 0,025 tiré du canal G.
6. **Aberration chromatique** : 5 échantillons en arc-en-ciel, déformation en barillet.
   - Force : `12 × (lissé vers 0 près des bords)` × masque de flou × bruit bleu.
   - Le bruit bleu change de place à chaque image, pour cacher les marches.
7. `couleur = mix(igloo, suivante, coupe)`, puis bornée entre 0 et 1.

Ce qu'il n'y a **pas** : pas de trait lumineux sur le bord, pas de flash, pas de vague de
blocs. La transition est sobre : une glace qui ronge l'image, du décalage et de l'arc-en-ciel.

## 4. Ce que notre site fait de différent (honnête)

- La texture de transition et le bruit bleu sont **les nôtres** (générés en code). Leur
  dessin est proche, mais pas identique au pixel.
- La scène suivante est notre page pelle, pas leurs cubes.
- Un seul geste lance le défilement jusqu'au bout. Ensuite, le mouvement suit exactement
  leur double lissage.
