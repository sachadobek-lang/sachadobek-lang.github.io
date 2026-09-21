#!/usr/bin/env python3
"""Les surfaces regardent-elles la même page ?

    python3 outils/surfaces.py

La cause la plus fréquente d'un « ce n'est pas à jour » n'est pas le code :
c'est qu'on ne regarde pas la surface qu'on vérifie. Ce script les compare
toutes, avec le même algorithme pour chacune — ce détail compte : deux agents
ont comparé le même fichier avec sha1 et sha256, obtenu deux valeurs
différentes, et failli conclure qu'ils regardaient des pages différentes.
Une règle qui dépend de l'outil que chacun choisit n'est pas une règle.

La référence est **main local**, pas le dépôt distant. Du travail fusionné et
pas encore publié est un état normal, pas une anomalie : la première version
de ce script prenait origin pour référence et annonçait une divergence à
chaque fusion en attente, en envoyant chercher un problème qui n'existait pas.
Un outil qui affirme une chose fausse coûte plus cher qu'un outil absent.
"""
import hashlib, os, subprocess, sys, urllib.request

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADRESSE_COMMUNE = "http://localhost:4173/"
ADRESSE_PUBLIQUE = "https://sachadobek-lang.github.io/"

def empreinte(octets):
    return hashlib.sha256(octets).hexdigest()[:12]

def fichier(chemin):
    return open(chemin, "rb").read()

def git(ref):
    r = subprocess.run(["git", "show", ref], cwd=RACINE, capture_output=True)
    if r.returncode:
        raise RuntimeError("référence absente")
    return r.stdout

def web(adresse, secondes=6):
    with urllib.request.urlopen(adresse, timeout=secondes) as r:
        return r.read()

def en_attente():
    """Les fichiers modifiés mais pas encore commités, s'il y en a."""
    r = subprocess.run(["git", "status", "--porcelain", "--", "index.html", "src/page.html", "sw.js"],
                       cwd=RACINE, capture_output=True, text=True)
    return [l[3:].strip() for l in r.stdout.splitlines() if l.strip()]

SURFACES = [
    ("ma copie de travail", lambda: fichier(os.path.join(RACINE, "index.html"))),
    ("main (local)",        lambda: git("main:index.html")),
    ("main (origin)",       lambda: git("origin/main:index.html")),
    ("l'adresse commune",   lambda: web(ADRESSE_COMMUNE)),
    ("la page publique",    lambda: web(ADRESSE_PUBLIQUE)),
]

vu = {}
for nom, lire in SURFACES:
    try:
        vu[nom] = empreinte(lire())
        print("  %-22s %s" % (nom, vu[nom]))
    except Exception as e:
        print("  %-22s — %s" % (nom, str(e).split("\n")[0][:46]))

reference = vu.get("main (local)") or vu.get("ma copie de travail")
graves, normaux = [], []

# Une copie de travail qui s'écarte de main a deux causes opposées, et le
# même mot les confondait. Si des fichiers attendent d'être commités, elle
# est EN AVANCE : « fusionner ou régénérer » est alors un mauvais conseil,
# il n'y a rien à rattraper, seulement à commiter. Ce faux signal a coûté
# une enquête à deux agents le même jour — l'un a conclu « anomalie de
# publication » sur une page qui était simplement plus récente.
if "ma copie de travail" in vu and vu["ma copie de travail"] != reference:
    attente = en_attente()
    if attente:
        normaux.append("ta copie de travail est EN AVANCE sur main : "
                       + ", ".join(attente) + "\n"
                       "    attend" + ("ent" if len(attente) > 1 else "")
                       + " d'être commité" + ("s" if len(attente) > 1 else "") + ".\n"
                       "    Rien à rattraper. Et tout ce qui est servi depuis le disque —\n"
                       "    le 4173 — montre déjà cette version, pas celle qui est poussée.")
    else:
        graves.append("ta copie de travail s'écarte de main local sans rien en attente.\n"
                      "    Un fichier généré n'a pas suivi sa source : python3 src/build.py")

# Le 4173 sert le dépôt principal : il doit donc refléter la copie de travail,
# pas main local. Les comparer à main local accusait un serveur qui servait
# pourtant exactement la bonne chose.
servie = vu.get("ma copie de travail", reference)
if "l'adresse commune" in vu and vu["l'adresse commune"] != servie:
    graves.append("le 4173 ne sert pas ta version : quelqu'un l'a pris avec sa\n"
                  "    propre copie. Ne conclus rien de ce que tu y vois ; vérifie-toi\n"
                  "    sur un port à toi : python3 outils/serveur-partage.py libre")

if "main (origin)" in vu and vu["main (origin)"] != reference:
    normaux.append("du travail est fusionné mais pas encore publié.\n"
                   "    C'est normal avant « git push origin main ».")
elif "la page publique" in vu and vu["la page publique"] != vu.get("main (origin)"):
    normaux.append("la page publique est en retard sur ce qui est poussé.\n"
                   "    GitHub Pages met quelques minutes, puis garde 10 minutes en cache.")

print()
if not graves and not normaux:
    print("Toutes les surfaces joignables montrent la même page.")
    sys.exit(0)

if graves:
    print("CES SURFACES NE MONTRENT PAS LA MÊME PAGE.")
    for g in graves:
        print("  · " + g)
if normaux:
    if graves:
        print()
    print("Et ceci, qui n'est pas une anomalie :")
    for n in normaux:
        print("  · " + n)

sys.exit(1 if graves else 0)
