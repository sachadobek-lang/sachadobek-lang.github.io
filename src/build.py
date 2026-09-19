#!/usr/bin/env python3
"""Injecte les données d'exemple dans le gabarit, après contrôle de syntaxe.

    python3 src/build.py      # écrit index.html à la racine

La page n'est remplacée qu'une fois les contrôles passés. L'ancienne version
reste disponible dans index.precedent.html tant que la suivante n'a pas été
écrite : si quelque chose casse, le retour en arrière est immédiat.
"""
import hashlib, io, json, os, shutil, subprocess, sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)

gabarit = io.open(os.path.join(ICI, "page.html"), encoding="utf-8").read()
exemple = json.load(open(os.path.join(ICI, "seed.json"), encoding="utf-8"))

# L'adresse du serveur et sa clé publique. Tant qu'elles sont vides,
# l'application fonctionne exactement comme avant : tout reste sur
# l'appareil, et le bouton de connexion reste éteint.
chemin_serveur = os.path.join(ICI, "serveur.json")
serveur = {"url": "", "cle": ""}
if os.path.exists(chemin_serveur):
    brut = json.load(open(chemin_serveur, encoding="utf-8"))
    serveur = {"url": brut.get("url", ""), "cle": brut.get("cle", "")}

if "__SEED__" not in gabarit:
    sys.exit("page.html ne contient pas le marqueur __SEED__")

# Le formulaire 2042-C-PRO, réduit à ses trois pages utiles, et les
# coordonnées de ses six cases. Injectés ici plutôt qu'écrits dans le
# gabarit : un million de caractères en base64 rendrait page.html
# illisible et impossible à relire pour les autres agents.
# Il faudra les regénérer chaque printemps, quand les impôts publient la
# nouvelle version — voir outils/remplir-2042.py.
# Les coordonnées des six cases : quelques centaines d'octets, injectés.
for marque, fichier in (("__CASES2042__", "cases-2042.json"),):
    chemin = os.path.join(ICI, fichier)
    contenu = io.open(chemin, encoding="utf-8").read().strip() if os.path.exists(chemin) else "{}"
    if marque in gabarit:
        gabarit = gabarit.replace(marque, contenu)

# Le formulaire lui-même est posé à côté de la page, pas dedans. Embarqué,
# il pesait 85 % du fichier et repartait avec chaque publication — huit
# aujourd'hui — alors qu'il ne change qu'au printemps. À part, il n'est
# téléchargé que par qui s'en sert, et une seule fois.
forme = os.path.join(ICI, "formulaire.pdf")
if os.path.exists(forme):
    shutil.copyfile(forme, os.path.join(RACINE, "formulaire-2042.pdf"))

sortie = os.path.join(RACINE, "index.html")
brouillon = os.path.join(RACINE, ".index-brouillon.html")

io.open(brouillon, "w", encoding="utf-8").write(
    gabarit.replace("__SEED__", json.dumps(exemple, ensure_ascii=False, separators=(",", ":")))
           .replace("__SERVEUR__", json.dumps(serveur, ensure_ascii=False, separators=(",", ":")))
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

# Le service worker porte l'empreinte de la page : une page nouvelle, une
# boîte nouvelle, et les copies de l'ancienne version sont mises au rebut.
modele = os.path.join(ICI, "sw.js")
if os.path.exists(modele):
    empreinte = hashlib.sha256(io.open(sortie, encoding="utf-8").read().encode("utf-8")).hexdigest()[:12]
    io.open(os.path.join(RACINE, "sw.js"), "w", encoding="utf-8").write(
        io.open(modele, encoding="utf-8").read().replace("__VERSION__", empreinte))
    print("sw.js écrit · version %s" % empreinte)

total = sum(len(v) for v in exemple.values())
print("index.html écrit · %d octets · %d fiches d'exemple" % (os.path.getsize(sortie), total))
