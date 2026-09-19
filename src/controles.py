#!/usr/bin/env python3
"""Ce qu'on vérifie sur la page avant de la publier.

    python3 src/controles.py [fichier]      # index.html par défaut

Chaque contrôle correspond à quelque chose qui a déjà cassé une fois. On
n'en ajoute pas par principe : on en ajoute quand on s'est fait avoir.
"""
import io, json, os, re, sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
cible = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RACINE, "index.html")
page = io.open(cible, encoding="utf-8").read()

fautes = []
def exiger(condition, message):
    if not condition:
        fautes.append(message)

# ── Les données d'exemple ont bien été injectées ─────────────────────
exiger("__SEED__" not in page,
       "le marqueur __SEED__ est resté dans la page : le gabarit n'a pas été traité")

# ── L'application s'ouvre vide : c'est la sienne, pas une démonstration ──
seed = json.load(open(os.path.join(ICI, "seed.json"), encoding="utf-8"))
fiches = sum(len(v) for v in seed.values())
exiger(fiches == 0,
       "seed.json contient %d fiches d'exemple : l'application ne s'ouvrirait pas vide" % fiches)

# ── Un seul nom. Deux noms lui ont déjà coûté une journée ────────────
for motif, ou in ((r"<title>([^<]*)</title>", "le titre de l'onglet"),
                  (r'name="apple-mobile-web-app-title"\s+content="([^"]*)"', "le nom sur l'écran d'accueil"),
                  (r'name="application-name"\s+content="([^"]*)"', "le nom de l'application")):
    trouve = re.search(motif, page)
    exiger(trouve and trouve.group(1).strip() == "Cura",
           "%s n'est pas « Cura » (%s)" % (ou, trouve.group(1) if trouve else "absent"))

# ── Le thème sombre ne doit pas repeindre les boutons en blanc ───────
exiger('name="color-scheme"' in page,
       "meta color-scheme absent : le mode sombre du navigateur blanchit les contrôles")

# ── Sans viewport-fit, les marges de la barre d'accueil ne s'appliquent pas ──
exiger("viewport-fit=cover" in page,
       "viewport-fit=cover absent : env(safe-area-inset-*) vaudra zéro sur iPhone")

# ── Rien de ce qu'il saisit ne doit pouvoir sortir de l'appareil ─────
csp = re.search(r'http-equiv="Content-Security-Policy"\s+content="([^"]*)"', page)
exiger(csp, "aucune politique de sécurité : un script tiers pourrait envoyer ses chiffres ailleurs")
if csp:
    regles = csp.group(1)
    connexions = re.search(r"connect-src ([^;]*)", regles)
    exiger(connexions, "la politique de sécurité ne dit rien de connect-src")
    if connexions:
        # Ce contrôle a longtemps exigé qu'AUCUN serveur extérieur ne figure
        # ici : la promesse était que rien ne pouvait sortir de l'appareil.
        # Depuis que Cura sait garder une copie en ligne, cette promesse
        # devient : rien ne sort vers personne d'autre que notre serveur, et
        # rien ne part tant qu'on ne s'est pas connecté. La liste ci-dessous
        # est donc la liste complète des destinations permises — tout ajout
        # est une décision, pas un détail.
        PERMIS = {"https://*.supabase.co", "wss://*.supabase.co"}
        dehors = [m for m in connexions.group(1).split()
                  if (m.startswith("http") or m.startswith("//") or m == "*")
                  and m not in PERMIS]
        exiger(not dehors,
               "connect-src autorise une destination non prévue : %s" % " ".join(dehors))
        exiger("*" not in connexions.group(1).split(),
               "connect-src autorise n'importe quelle destination")
    exiger("object-src 'none'" in regles, "object-src n'est pas fermé")
    exiger("form-action 'none'" in regles, "form-action n'est pas fermé")
    exiger("worker-src 'self'" in regles,
           "worker-src manquant : le service worker sera refusé et l'application ne s'ouvrira pas sans réseau")
    exiger("manifest-src 'self'" in regles, "manifest-src manquant : le manifeste sera refusé")

# ── Un script qu'on ne fabrique pas doit être celui qu'on croit ──────
for balise in re.findall(r"<script\b[^>]*\bsrc=[^>]*>", page):
    source = re.search(r'src="([^"]+)"', balise)
    adresse = source.group(1) if source else balise
    if adresse.startswith("http"):
        exiger("integrity=" in balise,
               "le script %s n'a pas d'empreinte : un serveur compromis pourrait le remplacer" % adresse)

# ── Aucune adresse en clair, et aucun domaine inattendu ──────────────
exiger("http://" not in page.replace("http://www.w3.org", ""),
       "une adresse en http:// sans chiffrement figure dans la page")
autorises = {"fonts.googleapis.com", "fonts.gstatic.com", "cdnjs.cloudflare.com",
             "maps.apple.com", "www.google.com", "waze.com", "www.w3.org"}
charges = set(re.findall(r'(?:src|href)="https://([^/"]+)', page))
inconnus = sorted(charges - autorises)
exiger(not inconnus,
       "la page charge un domaine non prévu : %s" % " ".join(inconnus))

# ── S'installer sur le téléphone, et s'ouvrir sans réseau ────────────
exiger('rel="manifest"' in page, "le manifeste n'est pas déclaré : l'installation sera bancale")
exiger('navigator.serviceWorker.register' in page,
       "le service worker n'est pas enregistré : l'application ne s'ouvrira pas sans réseau")
for fichier, role in (("manifest.webmanifest", "le manifeste"),
                      ("icone.svg", "l'icône"),
                      ("sw.js", "le service worker"),
                      ("404.html", "la page d'adresse inconnue"),
                      ("robots.txt", "le fichier robots")):
    exiger(os.path.exists(os.path.join(RACINE, fichier)), "%s (%s) est absent" % (role, fichier))

# ── Le service worker ne doit JAMAIS servir la page depuis le cache
#    tant qu'il y a du réseau. C'est ce qui fige une application et fait
#    croire que les corrections ne sont pas arrivées. Ça a déjà coûté
#    une journée entière. ─────────────────────────────────────────────
chemin_sw = os.path.join(RACINE, "sw.js")
if os.path.exists(chemin_sw):
    sw = io.open(chemin_sw, encoding="utf-8").read()
    exiger("__VERSION__" not in sw, "sw.js n'a pas été versionné : le ménage des vieilles copies ne se fera pas")
    exiger(re.search(r"e\.respondWith\(\s*fetch\(requete\)", sw),
           "sw.js ne demande pas le réseau en premier : il figerait l'application sur une vieille version")

# ── Une page trop lourde s'ouvre mal en 4G ───────────────────────────
poids = len(page.encode("utf-8"))
exiger(poids < 2_000_000,
       "la page pèse %.1f Mo : trop lourde pour une ouverture confortable au téléphone" % (poids / 1e6))

if fautes:
    print("CONTRÔLES ÉCHOUÉS")
    for f in fautes:
        print("  " + f)
    sys.exit(1)
print("contrôles passés · %d · page de %.0f Ko" % (10 + len(charges), poids / 1024))
