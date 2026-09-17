# Plenitu

Une application pour piloter une très petite entreprise : sa journée, ses clients,
son argent. Pas de compte à créer, pas de configuration, pas de serveur — un seul
fichier HTML qui s'ouvre dans un navigateur.

Elle s'est appelée Cadence, puis Simpli, avant de devenir Plenitu le
17 septembre 2026. Les copies de sauvegarde enregistrées sous l'un ou l'autre
de ces noms se restaurent toujours.

## Les trois onglets

| Onglet | Ce qu'on y fait |
|---|---|
| **Agenda** | La journée en ruban, les créneaux libres, le temps de route entre deux rendez-vous qui s'enchaînent, et le tableau des notes en dessous |
| **Clients** | Le carnet, rangé par mois de signature, et sur chaque fiche de quoi appeler, écrire ou s'y rendre. Au-dessus, une ligne dit combien de personnes attendent un appel — impayé, devis qui dort, client content, client oublié — et mène à l'écran qui les propose une à la fois |
| **Comptabilité** | *Calculs* : ce qu'il vous restera une fois cotisations et impôt payés. *Factures* : les totaux de l'année, la liste, le PDF. *Mon argent* : ce qui est vraiment à vous |

## Principes de conception

- **Trois options au maximum** par écran. Chaque ajout doit en retirer un autre.
- **Une seule question par écran**, une seule réponse.
- **Un seul dégradé**, du graphite au presque noir, à peine bleuté, pour toute
  l'identité visuelle.
- **Aucun rouge.** L'ambre signale ce qui est en retard, et c'est tout. Chaque
  rouge inutile est une injection d'anxiété dans une application qui parle d'argent.
- **Des mots que tout le monde comprend** : « À encaisser » plutôt qu'« impayés ».
- **Les couleurs qui informent ne décorent pas.** Le vert de l'encaissé et l'ambre
  du retard ne suivent pas la signature : ils veulent dire quelque chose.
- **Une couleur de graphique n'emprunte jamais une couleur de texte.** Sinon un
  réglage de lisibilité déplace un aplat sans que personne ne le voie.

## L'argent n'a qu'une seule source

Les factures. « Mon argent » et « Calculs » en dérivent, facturer quelqu'un
l'inscrit au carnet des clients. Aucun total n'est stocké : tout se recalcule.
Deux listes parallèles, et les écrans finissent par se contredire — c'est
l'erreur qui a coûté le plus cher sur ce projet.

**Un total sans son périmètre n'est pas une mesure.** Les écrans filtrent sur
l'année en cours : annoncer un chiffre sans dire « 2026, hors brouillons » est
une source de désaccord, pas une information.

## Les données

Tout est enregistré dans le `localStorage` du navigateur, sur l'appareil du
visiteur uniquement. Rien n'est envoyé nulle part, il n'y a pas de serveur. Au
premier lancement, l'application écrit un jeu de fiches d'exemple — de vraies
fiches, qu'on peut modifier et supprimer, et qu'un bouton efface d'un coup.

Le dossier `supabase/` contient les migrations d'un socle de données en ligne :
schéma, sécurité au niveau des lignes, back-office en lecture seule. **Il n'est
branché à rien.** Le jour où il le sera, la phrase ci-dessus devra être réécrite
dans le même commit — jamais avant, jamais après.

## Développement

Le fichier livré, `index.html`, est **généré** : ne le modifiez pas à la main.

```bash
python3 src/build.py
```

- `src/page.html` — le gabarit, avec le marqueur `__SEED__` à la place des données
- `src/verif.py` — contrôle du script : chaînes fermées, blocs équilibrés,
  fonctions appelées qui existent. `build.py` l'exécute et refuse d'écrire si
  quelque chose cloche. Ce garde-fou existe parce que des guillemets mal appariés
  ont blanchi la page plusieurs fois
- `outils/serveur-partage.py` — l'adresse commune sur le port 4173, qui sert ce
  dépôt en interdisant toute mise en cache

## Plusieurs agents sur le même projet

Trois agents travaillent en parallèle, chacun sur un onglet, chacun dans sa copie
isolée du dépôt. Les règles qui font que ça tient :

1. **Vérifié, fusionné, visible.** Le 4173 sert `main` : un travail non fusionné
   est invisible pour tout le monde.
2. **Régénérer après avoir fusionné.** Le 4173 sert `index.html`, qui est généré.
   Fusionner sans relancer `build.py` ne change rien à l'écran.
3. **Une seule adresse pour montrer quelque chose** : le 4173. Les ports
   personnels ne servent qu'à se vérifier soi-même avant de fusionner.
4. **Un agent ne modifie pas les instructions d'un autre**, même quand il les a
   écrites. On se transmet l'état du code, pas des consignes.
