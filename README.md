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
visiteur uniquement. Rien n'est envoyé nulle part, il n'y a pas de serveur.
**L'application s'ouvre vide** : c'est la sienne, pas une démonstration. Un
contrôle refuse la publication si des fiches d'exemple réapparaissent.

Cette promesse est désormais tenue par le navigateur lui-même : une politique
de sécurité déclarée dans la page n'autorise aucune connexion sortante. Même
si un script tiers était un jour compromis, il ne pourrait rien envoyer.

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
  fonctions appelées qui existent. Ce garde-fou existe parce que des guillemets
  mal appariés ont blanchi la page plusieurs fois
- `src/controles.py` — ce qu'on vérifie sur la page avant de publier : un seul
  nom, l'application qui s'ouvre vide, la politique de sécurité, aucun script
  tiers sans empreinte, aucun domaine non prévu. **Chaque contrôle correspond à
  quelque chose qui a déjà cassé** — on n'en ajoute pas par principe
- `src/tiers.py` — l'empreinte annoncée pour le script extérieur est-elle celle
  du fichier réellement servi
- `src/sw.js` — la copie locale qui permet d'ouvrir l'application sans réseau
- `outils/serveur-partage.py` — l'adresse commune sur le port 4173, qui sert ce
  dépôt en interdisant toute mise en cache
- `outils/hooks/pre-push` — le dernier verrou avant l'envoi

**`build.py` écrit d'abord un brouillon, le contrôle, et ne remplace `index.html`
qu'une fois les contrôles passés.** Il l'a longtemps fait dans l'autre sens : une
erreur de syntaxe était déjà publiée quand le message « Publication annulée »
s'affichait. L'ancienne page reste dans `index.precedent.html`, le temps d'un
retour en arrière.

## Ce qui protège la publication

Quatre verrous, du plus proche au plus lointain :

1. **`build.py`** ne remplace la page qu'une fois les contrôles passés.
2. **`outils/hooks/pre-push`** refuse d'envoyer une page qui ne les passe pas.
   Le commit local, lui, se fait toujours : le travail en cours n'est jamais
   perdu, et la page en ligne reste la dernière qui fonctionnait.
3. **`.github/workflows/verification.yml`** régénère la page et la compare à
   celle qui est publiée. Modifier le gabarit sans relancer `build.py` est
   l'oubli le plus coûteux du projet ; il ne passe plus.
4. **`.github/workflows/veille.yml`**, chaque matin : l'adresse publique répond,
   elle porte bien ses protections, et le script extérieur n'a pas changé.

## S'ouvrir sans réseau

`sw.js` garde une copie de la page. **Il ne la sert que si le réseau ne répond
pas.** Une copie servie en priorité fige l'application à la version du jour où
elle a été installée, et plus personne ne comprend pourquoi les corrections
n'arrivent pas — c'est exactement ce qui a coûté une journée entière. Un contrôle
refuse la publication si `sw.js` s'écarte de cette règle.

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
