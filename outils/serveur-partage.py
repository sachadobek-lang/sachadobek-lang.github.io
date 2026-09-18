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
import sys
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 4173

class SansCache(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=RACINE, **kw)

    def end_headers(self):
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
    with Reutilisable(("127.0.0.1", PORT), SansCache) as httpd:
        print("adresse commune sur http://localhost:%d — sert %s" % (PORT, RACINE))
        httpd.serve_forever()
