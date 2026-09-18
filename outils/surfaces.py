#!/usr/bin/env python3
"""Les quatre surfaces regardent-elles la même page ?

    python3 outils/surfaces.py

La cause la plus fréquente d'un « ce n'est pas à jour » n'est pas le code :
c'est qu'on ne regarde pas la surface qu'on vérifie. Ce script compare les
quatre, avec le même algorithme pour toutes — ce détail compte : deux agents
ont comparé le même fichier avec sha1 et sha256, obtenu deux valeurs
différentes, et failli conclure qu'ils regardaient des pages différentes.
Une règle qui dépend de l'outil que chacun choisit n'est pas une règle.
"""
import hashlib, os, subprocess, sys, urllib.request

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADRESSE_COMMUNE = "http://localhost:4173/"
ADRESSE_PUBLIQUE = "https://sachadobek-lang.github.io/"

def empreinte(octets):
    return hashlib.sha256(octets).hexdigest()[:12]

def lire_fichier(chemin):
    return open(chemin, "rb").read()

def lire_git(ref):
    r = subprocess.run(["git", "show", ref], cwd=RACINE, capture_output=True)
    if r.returncode:
        raise RuntimeError("référence absente")
    return r.stdout

def lire_web(adresse, secondes=6):
    with urllib.request.urlopen(adresse, timeout=secondes) as r:
        return r.read()

surfaces = [
    ("ma copie de travail", lambda: lire_fichier(os.path.join(RACINE, "index.html"))),
    ("main (origin)",       lambda: lire_git("origin/main:index.html")),
    ("l'adresse commune",   lambda: lire_web(ADRESSE_COMMUNE)),
    ("la page publique",    lambda: lire_web(ADRESSE_PUBLIQUE)),
]

resultats, absentes = [], []
for nom, lire in surfaces:
    try:
        resultats.append((nom, empreinte(lire())))
    except Exception as e:
        absentes.append((nom, str(e).split("\n")[0][:48]))

for nom, e in resultats:
    print("  %-22s %s" % (nom, e))
for nom, motif in absentes:
    print("  %-22s — %s" % (nom, motif))

valeurs = {e for _, e in resultats}
print()
if len(valeurs) <= 1 and len(resultats) > 1:
    print("Les %d surfaces joignables montrent la même page." % len(resultats))
    sys.exit(0)
if len(resultats) < 2:
    print("Pas assez de surfaces joignables pour comparer.")
    sys.exit(0)

print("CES SURFACES NE MONTRENT PAS LA MÊME PAGE.")
reference = dict(resultats).get("main (origin)")
for nom, e in resultats:
    if reference and e != reference:
        if nom == "ma copie de travail":
            print("  · ta copie diffère de main : fusionner, ou « python3 src/build.py »")
        elif nom == "l'adresse commune":
            print("  · le 4173 ne sert pas main : quelqu'un l'a pris avec sa propre copie.")
            print("    Ne conclus rien de ce que tu y vois ; vérifie-toi sur ton port :")
            print("    python3 outils/serveur-partage.py 4199")
        elif nom == "la page publique":
            print("  · la page en ligne est en retard : republier, ou attendre")
            print("    les 10 minutes de cache de GitHub Pages")
sys.exit(1)
