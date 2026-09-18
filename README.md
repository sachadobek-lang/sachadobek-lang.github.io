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

Les fichiers livrés, `index.html` et `sw.js`, sont **générés** : ne les modifiez
pas à la main, et **ne les fusionnez jamais ligne à ligne**. `sw.js` porte
l'empreinte de la page ; une fusion produit un fichier qui ne correspond à
aucune version, donc un cache qui ne sera jamais mis au rebut. En cas de
conflit sur l'un ou l'autre : prendre n'importe quelle version, puis
régénérer.

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

## Ce qui a été tranché

Une session qui démarre reçoit ce fichier, pas ce que les autres se sont dit.
Sans cette liste, les mêmes questions reviennent — l'une d'elles est remontée
quatre fois à Sacha en deux jours, chaque fois présentée comme neuve. **Avant de
lui proposer quelque chose, vérifier ici.**

- **L'application s'ouvre vide.** Demandé deux fois, explicitement. Ne pas
  proposer de bouton « voir un exemple » : la note « *le jour où* Plenitu
  cherchera des utilisateurs » écrite dans le commit 338ab86 est une condition
  qui n'est pas remplie, et le `robots.txt` en `Disallow` retire ce qu'il restait
  de l'argument. `fichesExemple()` reste dans le code comme **jeu de
  vérification**, injecté en mémoire et jamais enregistré — pas comme une
  fonctionnalité en attente.
- **Le carnet des clients ne filtre pas sur l'année, la comptabilité si.** Ce
  n'est pas une incohérence : « qui sont mes clients » et « combien ai-je gagné
  cette année » sont deux questions différentes. C'est ce qui explique l'écart
  de 9 600 € qui a occupé une heure. Tant que chaque chiffre est annoncé avec
  son périmètre, il n'y a rien à corriger.
- **Le thème clair est forcé.** La palette sombre existe mais reste
  inatteignable : c'est sa décision, prise en connaissance de cause.
- **`supabase/` n'est branché à rien**, et ce n'est pas un oubli.
- **Le bouton « Nouveau client » est volontairement plus léger que « Faire une
  facture ».** Même geste, rang différent : dans Factures, facturer est l'action
  principale de l'écran ; dans le carnet, l'action principale est de lire ses
  clients. Sacha a demandé « affiche-moi directement tous les clients », et une
  heure plus tôt « plus petit, pas dans une case, en blanc, que ce soit pas
  énorme ». Deux boutons du même geste avec deux poids différents donnent envie
  de les uniformiser : ne pas le faire.
- **Le ruban de l'Agenda a été essayé puis retiré.** Il montrait les
  rendez-vous, mais pas la journée : ni les trous, ni l'heure qu'il est par
  rapport au reste. Un agenda qui ne montre que ce qui est pris ne sert pas à
  décider.
- **Les boutons de zoom ont été supprimés** au profit du geste seul, avec le
  double-clic comme porte d'entrée pour qui ne pince pas. C'est ce retrait qui a
  rendu possible l'ajout de la vue Mois : trois options par écran, un ajout pour
  un retrait.

**Une note conditionnelle dans un message de commit finit par être lue comme une
tâche** : la condition est la première chose qui saute quand quelqu'un relaie la
phrase, et l'attribution la deuxième. Ne pas en écrire ; l'écrire ici à la place.

## Ce qui ne se vérifie pas en local

**Le fonctionnement hors-ligne ne s'observe que sur la page publique.** Le
navigateur de contrôle refuse d'enregistrer un service worker sur une origine
en `http://`, localhost compris, avec un message qui ne dit pas sa cause :
« An unknown error occurred when fetching the script ». Deux agents ont cru
successivement à un en-tête, à la version du protocole, puis aux accents du
fichier — éprouvé avec un script de quarante-huit octets en pur ASCII sur un
serveur neutre, il échoue aussi.

Tout fonctionne en ligne, mise à jour comprise. **Ne pas rediagnostiquer ceci
depuis un port local** : y observer une anomalie ne prouve rien.

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
5. **Avant tout diagnostic, mesurer ce qu'on regarde vraiment.**

```bash
python3 outils/surfaces.py
```

Il compare les quatre surfaces — copie de travail, `main`, le 4173, la page
publique — et dit laquelle diverge. La cause la plus fréquente d'un « ce n'est
pas à jour » n'est pas le code : c'est qu'on ne regarde pas la surface qu'on
vérifie. Le 4173 a déjà servi la copie isolée d'un agent pendant qu'un autre en
tirait des conclusions sur `main`.

**Le script existe pour une raison précise** : deux agents ont comparé le même
fichier, l'un avec `shasum`, l'autre avec `shasum -a 256`, obtenu deux valeurs
différentes et failli conclure qu'ils regardaient des pages différentes. Une
règle qui dépend de l'outil que chacun choisit n'est pas une règle — d'où un
seul script, un seul algorithme, pour tout le monde.
