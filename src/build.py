#!/usr/bin/env python3
"""Injecte les données d'exemple dans le gabarit, après contrôle de syntaxe.

    python3 src/build.py      # écrit index.html à la racine
"""
import io, json, os, subprocess, sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)

gabarit = io.open(os.path.join(ICI, "page.html"), encoding="utf-8").read()
exemple = json.load(open(os.path.join(ICI, "seed.json"), encoding="utf-8"))

if "__SEED__" not in gabarit:
    sys.exit("page.html ne contient pas le marqueur __SEED__")

sortie = os.path.join(RACINE, "index.html")
io.open(sortie, "w", encoding="utf-8").write(
    gabarit.replace("__SEED__", json.dumps(exemple, ensure_ascii=False, separators=(",", ":")))
)

controle = subprocess.run([sys.executable, os.path.join(ICI, "verif.py")], cwd=RACINE)
if controle.returncode:
    sys.exit("Publication annulée : le script contient une erreur de syntaxe.")

total = sum(len(v) for v in exemple.values())
print("index.html écrit · %d octets · %d fiches d'exemple" % (os.path.getsize(sortie), total))
