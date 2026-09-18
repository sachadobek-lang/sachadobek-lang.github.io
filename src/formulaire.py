#!/usr/bin/env python3
"""L'administration a-t-elle republié le formulaire des impôts ?

    python3 src/formulaire.py

Le 2042-C-PRO est republié chaque printemps. L'application continuerait à
remplir l'ancien sans que rien ne le signale : les cases sont aux mêmes
endroits, les chiffres sont bons, la déclaration part — et elle est faite sur
un formulaire de l'an dernier. **Une erreur qui ne se voit pas est celle qu'on
découvre en avril, trop tard.**

Si l'empreinte a changé, relancer outils/remplir-2042.py : il retélécharge,
relit les coordonnées des cases et régénère ce dont la page a besoin.
"""
import hashlib, io, json, os, sys, urllib.request

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fiche = os.path.join(RACINE, "src", "formulaire-officiel.json")
if not os.path.exists(fiche):
    print("src/formulaire-officiel.json est absent : rien à comparer")
    sys.exit(0)

connu = json.load(open(fiche, encoding="utf-8"))
adresse = connu["adresse"]
print("  adresse   %s" % adresse)

try:
    requete = urllib.request.Request(adresse, headers={"User-Agent": "Plenitu/veille"})
    with urllib.request.urlopen(requete, timeout=40) as r:
        octets = r.read()
except Exception as e:
    # Le site des impôts peut être indisponible : ce n'est pas notre affaire.
    print("  injoignable — %s" % str(e).split("\n")[0][:60])
    print("\nRien à conclure aujourd'hui.")
    sys.exit(0)

reelle = hashlib.sha256(octets).hexdigest()
print("  attendue  %s · %d octets" % (connu["empreinte"][:16], connu["octets"]))
print("  servie    %s · %d octets" % (reelle[:16], len(octets)))
print()

if reelle == connu["empreinte"]:
    print("Le formulaire officiel n'a pas changé depuis le %s." % connu["releve_le"])
    sys.exit(0)

print("LE FORMULAIRE OFFICIEL A CHANGÉ.")
print("  L'application remplit encore celui de l'an dernier, avec les bons")
print("  chiffres et dans les bonnes cases — donc sans que rien ne le signale.")
print()
print("  À faire :  python3 outils/remplir-2042.py")
print("  puis relever la nouvelle empreinte dans src/formulaire-officiel.json")
sys.exit(1)
