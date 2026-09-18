#!/usr/bin/env python3
"""Le script qu'on ne fabrique pas est-il toujours celui qu'on croit ?

    python3 src/tiers.py [fichier]      # index.html par défaut

L'application charge jsPDF depuis un serveur qui ne nous appartient pas.
La page porte son empreinte : si le fichier servi changeait, le navigateur
refuserait de l'exécuter — et l'export PDF cesserait de fonctionner sans
que personne ne comprenne pourquoi. On préfère l'apprendre ici.
"""
import base64, hashlib, io, os, re, sys, urllib.request

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cible = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RACINE, "index.html")
page = io.open(cible, encoding="utf-8").read()

balises = re.findall(r"<script\b[^>]*\bsrc=\"(https://[^\"]+)\"[^>]*>", page)
if not balises:
    print("aucun script extérieur : rien à vérifier")
    sys.exit(0)

souci = False
for adresse in balises:
    bloc = re.search(r"<script\b[^>]*" + re.escape(adresse) + r"[^>]*>", page).group(0)
    annonce = re.search(r'integrity="(sha\d+)-([^"]+)"', bloc)
    if not annonce:
        print("SANS EMPREINTE : %s" % adresse)
        souci = True
        continue
    algo, attendue = annonce.group(1), annonce.group(2)
    with urllib.request.urlopen(adresse, timeout=30) as reponse:
        octets = reponse.read()
    reelle = base64.b64encode(hashlib.new(algo.replace("sha", "sha"), octets).digest()).decode()
    print("  %s" % adresse)
    print("    annoncée : %s" % attendue)
    print("    servie   : %s" % reelle)
    if attendue != reelle:
        print("    LE FICHIER SERVI A CHANGÉ")
        souci = True

if souci:
    print("Le script extérieur ne correspond plus à ce que la page attend.")
    sys.exit(1)
print("le script extérieur est inchangé")
