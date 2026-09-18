#!/usr/bin/env python3
"""Remplit le 2042-C-PRO officiel, à la case près.

    python3 outils/remplir-2042.py 5KP 209053

Le formulaire des impôts n'est pas remplissable : c'est un PDF plat d'un
mégaoctet, sans un seul champ nommé — vérifié, il n'a pas d'AcroForm. On
ne peut donc pas « remplir les champs ». On fait autrement : on repère la
case par son code imprimé (5KO, 5KP, 5HQ…), on relève les deux montants
verticaux du cadre juste à sa droite, et on écrit dedans. Comme au stylo,
mais au bon endroit et à la bonne taille.

Les cadres ne sont pas toujours fermés en haut : on se fie aux montants
verticaux, qui donnent à la fois la largeur et la hauteur. Se fier aux
traits horizontaux faisait échouer quatre cases sur six.

Les cases, telles qu'impots.gouv.fr les nomme :
    sans versement libératoire   5KO vente · 5KP services · 5HQ libéral
    avec versement libératoire   5TA vente · 5TB services · 5TE libéral

On déclare le chiffre d'affaires encaissé brut, sans rien déduire :
l'abattement est appliqué par l'administration.

Pourquoi ceci n'est pas dans l'application : Plenitu est un fichier unique
qui s'interdit toute connexion sortante. Embarquer le formulaire
multiplierait sa taille par cinq, et il faudrait le remplacer chaque
printemps. Cet outil-ci se relance en une commande.
"""
FORMULAIRE = "https://www.impots.gouv.fr/sites/default/files/formulaires/2042/2026/2042_5474.pdf"
import io, sys, warnings
warnings.filterwarnings("ignore")
import pdfplumber
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

def trouver_case(chemin, code):
    """Rend (page, x_gauche, x_droite, haut, bas) du cadre de saisie du code.

    Le cadre n'est pas toujours fermé en haut : on se fie donc aux deux
    montants verticaux, qui donnent à la fois la largeur et la hauteur.
    """
    with pdfplumber.open(chemin) as pdf:
        for i, page in enumerate(pdf.pages):
            for m in page.extract_words():
                if m["text"].strip().strip(".:,") != code:
                    continue
                y = (m["top"] + m["bottom"]) / 2
                montants = [e for e in page.edges
                            if e["orientation"] == "v"
                            and e["top"] <= y <= e["bottom"]
                            and e["x0"] > m["x1"]
                            and e["bottom"] - e["top"] > 4]      # un vrai montant, pas un angle
                if len(montants) < 2:
                    continue
                montants.sort(key=lambda e: e["x0"])
                g, d = montants[0], montants[1]
                return i, g["x0"], d["x0"], min(g["top"], d["top"]), max(g["bottom"], d["bottom"])
    return None

def remplir(entree, sortie, valeurs):
    """valeurs : {"5KP": "40 000", …}"""
    src = PdfReader(entree)
    par_page = {}
    for code, montant in valeurs.items():
        c = trouver_case(entree, code)
        if not c:
            print("case introuvable :", code); continue
        par_page.setdefault(c[0], []).append((c, montant))

    w = PdfWriter()
    for i, page in enumerate(src.pages):
        if i in par_page:
            L, H = float(page.mediabox.width), float(page.mediabox.height)
            t = io.BytesIO(); c = canvas.Canvas(t, pagesize=(L, H))
            c.setFillColorRGB(0.04, 0.09, 0.42)
            for (pg, x0, x1, haut, bas), montant in par_page[i]:
                large = x1 - x0 - 6
                taille = 10.0
                while taille > 5 and stringWidth(montant, "Helvetica-Bold", taille) > large:
                    taille -= 0.25
                c.setFont("Helvetica-Bold", taille)
                # le PDF compte depuis le bas ; pdfplumber depuis le haut
                base = H - bas + (bas - haut - taille) / 2 + 1.5
                c.drawRightString(x1 - 3, base, montant)
            c.save(); t.seek(0)
            page.merge_page(PdfReader(t).pages[0])
        w.add_page(page)
    with open(sortie, "wb") as f:
        w.write(f)

def espacer(n):
    """209053 devient « 209 053 », comme l'écrit le formulaire."""
    return "{:,}".format(int(n)).replace(",", "\u202f")

if __name__ == "__main__":
    import os.path, urllib.request
    ici = os.path.dirname(os.path.abspath(__file__))
    vierge = os.path.join(ici, "2042-c-pro.pdf")
    if not os.path.exists(vierge):
        print("téléchargement du formulaire officiel…")
        urllib.request.urlretrieve(FORMULAIRE, vierge)
    if len(sys.argv) < 3:
        sys.exit("usage : python3 outils/remplir-2042.py <CASE> <MONTANT>\n"
                 "exemple : python3 outils/remplir-2042.py 5KP 209053")
    code, montant = sys.argv[1].upper(), espacer(sys.argv[2].replace(" ", ""))
    sortie = os.path.join(ici, "..", "declaration-remplie.pdf")
    remplir(vierge, sortie, {code: montant})
    print("case %s remplie avec %s → %s" % (code, montant, os.path.normpath(sortie)))
