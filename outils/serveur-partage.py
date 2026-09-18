#!/usr/bin/env python3
"""L'adresse commune : http://localhost:4173

Sert le dépôt principal — donc main, donc le travail fusionné de tous les
agents — en interdisant au navigateur de garder quoi que ce soit en cache.

Pourquoi : un serveur de fichiers ordinaire laisse le navigateur réutiliser
la page qu'il a déjà. Quatre conversations ouvertes sur la même adresse
finissent alors par montrer quatre versions différentes, chacune figée au
moment où elle a été chargée pour la première fois. C'est exactement ce qui
s'est produit, et personne ne s'en apercevait : le serveur était à jour,
les écrans ne l'étaient pas.

Ici chaque rechargement redemande le fichier, sans exception. Un F5 suffit
à voir la dernière fusion.
"""
import http.server, os, socketserver

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Le 4173 est l'adresse commune : elle sert main, et elle seule.
# Un port passé en argument sert à se vérifier soi-même avant de fusionner :
#     python3 outils/serveur-partage.py 4199
# Le faire avec ce script plutôt qu'avec « python3 -m http.server » n'est pas
# un détail — celui-ci répond 304 et laisse le navigateur garder l'ancienne
# page. On se relit alors sans voir ses propres corrections.
#     python3 outils/serveur-partage.py libre
# choisit un port libre et l'annonce — à préférer, car un port personnel fixe
# écrit dans un conseil devient vite le port personnel de tout le monde.
import hashlib, socket, sys

def occupe(port):
    """Quelqu'un écoute-t-il déjà ici ?"""
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex(("127.0.0.1", port)) == 0

def premier_libre(depart=4200):
    for p in range(depart, depart + 60):
        if not occupe(p):
            return p
    return 0   # que le système en choisisse un

def empreinte_locale():
    chemin = os.path.join(RACINE, "index.html")
    if not os.path.exists(chemin):
        return "(pas de index.html)"
    return hashlib.sha256(open(chemin, "rb").read()).hexdigest()[:12]

argument = sys.argv[1] if len(sys.argv) > 1 else None
if argument in ("libre", "--libre"):
    PORT = premier_libre()
else:
    PORT = int(argument) if argument else 4173

class SansCache(http.server.SimpleHTTPRequestHandler):
    # http.server répond en HTTP/1.0 par défaut et ferme la connexion après
    # chaque réponse. HTTP/1.1 les garde ouvertes : une page de 370 Ko et ses
    # quelques fichiers se chargent en une conversation au lieu de dix.
    # Content-Length est déjà fourni par la classe mère, c'est tout ce qu'il
    # fallait pour y passer.
    protocol_version = "HTTP/1.1"

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=RACINE, **kw)

    def end_headers(self):
        """Interdire le cache — sauf pour le service worker.

        « no-store » dit au navigateur de ne rien conserver. Le service worker
        a besoin de garder une copie du script pour la comparer à la suivante
        et décider s'il y a une version à installer : lui interdire de stocker
        peut l'empêcher de se mettre à jour, et un service worker qui ne se met
        pas à jour fige l'application — le défaut même que tout ceci cherche à
        éviter. En ligne, GitHub Pages n'envoie pas no-store ; le servir ainsi
        ici ferait vérifier autre chose que ce qui sera publié.

        Pour lui : revalidation à chaque fois, mais stockage autorisé.
        """
        if self.path.endswith("sw.js"):
            self.send_header("Cache-Control", "no-cache, max-age=0, must-revalidate")
        else:
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

    def send_head(self):
        """Ne jamais répondre « pas modifié » : le navigateur garderait sa copie.

        On efface les en-têtes conditionnels de la requête avant que la
        classe mère ne les lise. HTTPMessage se comporte comme un
        dictionnaire de courrier, pas comme un dict : il faut del, et il
        n'a pas de pop.
        """
        for entete in ("If-Modified-Since", "If-None-Match"):
            while entete in self.headers:
                del self.headers[entete]
        return super().send_head()

class Reutilisable(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    # Refuser bruyamment plutôt que de laisser croire qu'on sert.
    #
    # Un agent a lancé ce script sur un port déjà pris par le worktree d'un
    # autre. Le démarrage a échoué là où personne ne le lisait, curl a répondu
    # 200 — depuis l'autre serveur — et il a passé trois mesures à conclure que
    # son propre travail « n'existait pas ». Un outil qui échoue en silence
    # pendant qu'une réponse arrive quand même est pire qu'un outil absent.
    if PORT and occupe(PORT):
        libre = premier_libre()
        print("Le port %d est déjà pris par quelqu'un d'autre." % PORT, file=sys.stderr)
        print("", file=sys.stderr)
        if PORT == 4173:
            print("  C'est l'adresse commune. Si ce n'est pas toi qui la sers,", file=sys.stderr)
            print("  ne conclus rien de ce que tu y vois avant d'avoir comparé :", file=sys.stderr)
            print("      python3 outils/surfaces.py", file=sys.stderr)
        else:
            print("  Tu regarderais la page de quelqu'un d'autre en croyant", file=sys.stderr)
            print("  regarder la tienne. C'est exactement comme ça qu'on passe", file=sys.stderr)
            print("  une heure à chercher un travail qui est pourtant bien là.", file=sys.stderr)
        print("", file=sys.stderr)
        print("  Port libre : %d   ·   ou « libre » pour ne plus y penser :" % libre, file=sys.stderr)
        print("      python3 outils/serveur-partage.py libre", file=sys.stderr)
        sys.exit(1)

    with Reutilisable(("127.0.0.1", PORT), SansCache) as httpd:
        port_reel = httpd.server_address[1]
        role = "adresse commune" if port_reel == 4173 else "port de vérification"
        print("%s sur http://localhost:%d" % (role, port_reel))
        print("  sert    %s" % RACINE)
        # L'empreinte au démarrage : elle se compare d'un coup d'œil avec
        # celle des autres surfaces, sans avoir à choisir un algorithme.
        print("  page    %s" % empreinte_locale())
        sys.stdout.flush()
        httpd.serve_forever()
