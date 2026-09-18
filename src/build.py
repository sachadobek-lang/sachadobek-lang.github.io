#!/usr/bin/env python3
"""Injecte les données d'exemple dans le gabarit, après contrôle de syntaxe.

    python3 src/build.py      # écrit index.html à la racine

La page n'est remplacée qu'une fois les contrôles passés. L'ancienne version
reste disponible dans index.precedent.html tant que la suivante n'a pas été
écrite : si quelque chose casse, le retour en arrière est immédiat.
"""
import io, json, os, shutil, subprocess, sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)

gabarit = io.open(os.path.join(ICI, "page.html"), encoding="utf-8").read()
exemple = json.load(open(os.path.join(ICI, "seed.json"), encoding="utf-8"))

if "__SEED__" not in gabarit:
    sys.exit("page.html ne contient pas le marqueur __SEED__")

sortie = os.path.join(RACINE, "index.html")
brouillon = os.path.join(RACINE, ".index-brouillon.html")

io.open(brouillon, "w", encoding="utf-8").write(
    gabarit.replace("__SEED__", json.dumps(exemple, ensure_ascii=False, separators=(",", ":")))
)

def renoncer(motif):
    """Rien n'a été touché : index.html est resté celui qui fonctionnait."""
    if os.path.exists(brouillon):
        os.remove(brouillon)
    sys.exit("Publication annulée : %s\nindex.html n'a pas été modifié." % motif)

for script, motif in (("verif.py", "le script contient une erreur de syntaxe"),
                      ("controles.py", "un contrôle de la page a échoué")):
    chemin = os.path.join(ICI, script)
    if not os.path.exists(chemin):
        continue
    if subprocess.run([sys.executable, chemin, brouillon], cwd=RACINE).returncode:
        renoncer(motif)

if os.path.exists(sortie):
    shutil.copy2(sortie, os.path.join(RACINE, "index.precedent.html"))
os.replace(brouillon, sortie)

total = sum(len(v) for v in exemple.values())
print("index.html écrit · %d octets · %d fiches d'exemple" % (os.path.getsize(sortie), total))
