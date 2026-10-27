# Le référentiel d'interface de Cura

Construit le 27 octobre 2026. Il ne retient que ce qui est **mesurable** ou
**sourcé sur des observations**, et il dit à chaque fois lequel des deux.

## Les sources, et ce qu'elles valent

| Source | Apport | Solidité |
|---|---|---|
| **Steven Hoober, UXmatters 2013 puis 2017** | 1 333 personnes observées en vrai (rue, gares, cafés). Prises en main : 49 % une main, 36 % en berceau, 15 % deux mains. **2017 : 7 mm au centre, 12 mm dans les coins** pour couvrir 95 % des appuis. | Observation directe. La meilleure source trouvée. |
| **WCAG 2.2 (W3C)** | 2.5.8 AA : cible ≥ 24 px CSS. 2.5.5 AAA : 44. 1.4.3 AA : contraste 4,5:1 (3:1 pour le grand texte). | Norme opposable, entièrement mesurable. |
| **Apple HIG** | 44 × 44 pt. | Norme de la plateforme. Équivaut aux 7 mm de Hoober — donc c'est la règle du **centre**, pas des coins. |
| **Luke Wroblewski, lukew.com, oct. 2009** | 11 champs → 4 champs : **+120 % de conversion**, sans perte de qualité des contacts. | Cas réel chiffré, source primaire. |
| **Nielsen Norman Group** | Les 10 heuristiques (1994, révisées 2020, établies sur 249 problèmes). | Fondateur, mais **qualitatif** : NN/g écrit lui-même qu'une évaluation heuristique ne donne aucun chiffre. |
| **AppsFlyer 2025 ; Lenny Rachitsky (500+ produits)** | Atteindre la première valeur dès la 1ʳᵉ session : rétention J7 ×2 à ×3. Activation médiane : 36 %. | Chiffré, traçable. Inapplicable ici : Cura n'a aucun utilisateur. |

### Ce qui a été écarté, et pourquoi
- **Seuil de Doherty (400 ms)** : les sources se contredisent sur l'effet
  (×2, +25-30 %, +10-15 %) et renvoient toutes au même papier IBM de 1982
  sans le citer. Non retenu comme règle.
- **La « zone du pouce »** : le graphique le plus repris du métier. **Hoober,
  son auteur, le qualifie de faux** et demande qu'on cesse de s'en servir.
- **Les listicles de design** (« 15 meilleures sources 2026 ») : aucune donnée.

## La règle qui en sort, et que presque personne n'applique

> **La taille d'une cible dépend de sa position.**
> 45 pt au centre — c'est la règle Apple, que tout le monde applique partout.
> **77 pt dans un coin**, que personne n'applique.
> Et : contenu principal au centre, actions secondaires le long des bords
> haut et bas, fonctions tertiaires dans les coins.

## La note de Cura, sur 100

Mesurée le 27 octobre, avant puis après correction.

| | Poids | Avant | Après | Mesure |
|---|---|---|---|---|
| Cibles tactiles (position comprise) | 15 | 11 | **15** | 19/103 hors norme → 1 seul vrai défaut, corrigé |
| Contraste WCAG AA | 15 | 15 | **15** | 0 échec sur 329 textes |
| Gestes pour la tâche principale | 15 | 8 | **15** | devis 3 touches ; facture 5 champs tapés → **2 touches** |
| Fluidité, poids, hors-ligne | 15 | 13 | **13** | 61 images/s, 16,7 ms, 667 Ko |
| Les 10 heuristiques NN/g | 30 | 22 | **26** | cohérence devis/facture réparée |
| **Preuve d'usage réelle** | 10 | 0 | **0** | **aucun utilisateur hors Sacha** |
| **Total** | **100** | **69** | **84** | |

**Le plafond est à 90 tant qu'il n'y a pas d'utilisateurs.** Les 10 points
restants ne s'achètent pas en dessinant : ils se mesurent sur des gens.

## Ce qu'il reste à prendre (6 points)
- Aide et documentation : il n'y en a aucune (−2).
- Annulation après coup : on prévient avant de supprimer, on ne revient pas en arrière après (−1).
- Messages d'erreur : jamais vérifiés un par un (−1).
- Poids de la page : 667 Ko pour un fichier unique (−2).
