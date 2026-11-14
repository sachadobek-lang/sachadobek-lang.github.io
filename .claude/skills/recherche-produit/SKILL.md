---
name: recherche-produit
description: Vérifie et note un produit (ou un fournisseur) avant de le mettre dans une boutique de cadeaux. À utiliser quand Sacha demande une « recherche produit », veut savoir si un produit est bon, rentable ou fiable, compare des fournisseurs, ou choisit les produits d'une catégorie. Ne pas utiliser pour écrire les textes des fiches ni pour créer la boutique.
---

# Recherche produit

But : ne garder que des produits **européens, bien notés, de bonne qualité, rentables**,
et sans aucun risque légal. On applique les étapes dans l'ordre. Un produit qui échoue
une étape « bloquante » est rejeté, même s'il est bon ailleurs.

## Règle de base

Chaque information reçoit une étiquette :
- **Certain** : vérifié (page fournisseur lue, commande test, document fourni).
- **Déduction** : découle d'un fait certain.
- **Supposition** : non vérifié. On le dit, et on propose comment le vérifier.
- **Inconnu** : on écrit « je ne sais pas ».

Ne jamais inventer un délai, une note, un avis, un prix ou une licence.

## Étape 1 : Bloquants (un seul échec = rejet)

1. **Entrepôt en Europe.** Le fournisseur indique le pays de départ. Sans cette
   information écrite, c'est inconnu, donc bloquant.
2. **Délai annoncé par le fournisseur**, recopié tel quel avec sa source. Pas de délai
   estimé par nous.
3. **Avis vérifiables.** Une note et un nombre d'avis, avec la source (Trustpilot, avis
   de la page produit, avis Shopify). Seuils à fixer avec Sacha. Signaux d'alerte :
   avis tous très récents, avis tous identiques, aucun avis négatif du tout.
4. **Pas de contrefaçon.** Pour figurines, manga, jeux ou marques connues : preuve de
   licence ou de fabricant officiel. Sans preuve, rejet.
5. **Pas de contenu médical ou de promesse de santé.** Aucune allégation thérapeutique.
6. **Cosmétiques (si le produit en est un)** : dans l'UE, ils suivent le règlement
   (CE) n° 1223/2009. Il faut un responsable identifié dans l'UE et des informations
   produit (ingrédients, mode d'emploi, mention de lot). Je n'ai pas vérifié le texte
   aujourd'hui : c'est une règle connue, à confirmer sur EUR-Lex avant d'en faire une
   règle de validation.
7. **Sécurité des jouets et figurines pour enfants** : marquage CE et documents de
   conformité demandés au fournisseur. Règle connue, à vérifier pour chaque catégorie.
8. **Politique de retour écrite** par le fournisseur.

## Étape 2 : Qualité (notée de 0 à 2 chacun)

- **Finition** : photos de clients réels ou échantillon reçu. Le catalogue ne suffit pas.
- **Matière** : ce qui est écrit, et ce qui est vérifié à la réception.
- **Modernité** : le design correspond-il à ce qu'achète la cible ?
- **Avis négatifs** : relever les 3 plaintes les plus fréquentes. Si elles portent sur
  la casse, la taille ou le délai, la note baisse.

## Étape 3 : Rentabilité

Calcul par vente :

```
Marge = prix de vente TTC
      - prix fournisseur
      - frais de livraison
      - frais de paiement
      - coût publicitaire par vente
      - TVA et frais de plateforme (à confirmer avec un comptable)
```

- Le prix de vente cible vient de l'angle choisi (fourchette de budget).
- La marge minimale et le coût publicitaire maximal sont **fixés avec Sacha**. Je ne
  les choisis pas à sa place.
- Si une valeur manque, la marge est **inconnue**, pas positive.

## Étape 4 : Décision

- **Garder** : toutes les étapes 1 à 3 validées, qualité au seuil, marge au seuil.
- **À tester** : étape 1 validée, mais qualité ou marge incertaine. On commande un
  échantillon avant de décider.
- **Rejeter** : une étape 1 échoue, ou marge négative, ou qualité sous le seuil.

## Fiche produit (format de sortie)

```
Produit :
Fournisseur :
Pays de départ : [certain / inconnu, source]
Délai annoncé : [texte exact, source]
Note et nombre d'avis : [source, date]
Licence ou fabricant officiel : [oui / non / inconnu]
Cosmétique : [non / oui, documents]
Politique de retour : [texte exact]
Qualité (0-2 x 4) : [total, justification]
Marge estimée : [calcul, valeurs manquantes indiquées]
Décision : garder / à tester / rejeter
Ce qui n'est pas vérifié :
```

## Ce qu'on ne fait jamais

- Inventer un délai, une note, un avis, un prix ou une licence.
- Écrire un faux avis ou une fausse note sur le site.
- Recommander un produit contrefait ou sans licence.
- Présenter une supposition comme un fait.

## Infos à demander à Sacha avant la première recherche

1. Les catégories à chercher (les 8 onglets retenus).
2. Le prix de vente visé (fourchette).
3. La note minimale et le nombre d'avis minimal.
4. La marge minimale par vente.
5. Le coût publicitaire maximal par vente.
6. Si les **cosmétiques** sont voulus ou non. Le mot « cosmétiques » est dans la demande, mais ce n'est pas tranché.
