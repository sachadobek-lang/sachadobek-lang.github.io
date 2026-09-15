# Cadence

Une application pour piloter une petite entreprise : ce qu'il y a à faire, l'argent
qui rentre, les clients, le budget. Pas de compte à créer, pas de configuration,
pas de serveur — un seul fichier HTML qui s'ouvre dans un navigateur.

## Les quatre écrans

| Écran | Ce qu'on y fait |
|---|---|
| **À faire** | L'anneau du jour, les tâches groupées *En retard · Aujourd'hui · Plus tard*, et une série de jours à ne pas casser |
| **Argent** | Ce qui a été facturé ce mois, ce qui est déjà encaissé, ce qui reste à encaisser, et la liste des factures |
| **Clients** | Une fiche par client : le chantier, le montant facturé, l'état (Prospect → En cours → Terminé) |
| **Budget** | Ce qu'il reste sur l'année : chiffre d'affaires − dépenses − investissements |

## Principes de conception

- **Trois options au maximum** partout : trois onglets de filtre, trois choix de date,
  trois groupes de tâches. Au-delà, on perd le lecteur.
- **Un seul dégradé**, vert vers bleu, pour toute l'identité visuelle.
- **Aucun rouge.** L'ambre est la seule couleur chaude, réservée à ce qui est en retard.
  Chaque rouge inutile est une injection d'anxiété dans une application qui parle d'argent.
- **Des mots que tout le monde comprend** : « À encaisser » plutôt que « impayés »,
  « Important » plutôt que « priorité haute ».

## Les données

Tout est enregistré dans le `localStorage` du navigateur, sur l'appareil du visiteur
uniquement. Rien n'est envoyé nulle part, il n'y a pas de serveur. Au premier lancement,
l'application affiche l'exemple d'un atelier de menuiserie ; un bouton *Repartir de zéro*
efface ces fiches.

## Développement

Le fichier livré, `index.html`, est **généré** : ne le modifiez pas à la main.

```bash
python3 src/build.py
```

- `src/page.html` — le gabarit, avec le marqueur `__SEED__` à la place des données
- `src/seed.json` — les fiches d'exemple
- `src/verif.py` — contrôle de syntaxe du script (chaînes fermées, blocs équilibrés) ;
  `build.py` l'exécute et refuse d'écrire si quelque chose cloche
- `index.html` — le résultat, autonome, à ouvrir ou à héberger tel quel

Pour le regarder tourner en local :

```bash
python3 -m http.server 4173
```
