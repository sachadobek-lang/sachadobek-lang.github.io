/* Cura hors-ligne — version 2511de68cd24
 *
 * Ce fichier existe pour une seule raison : que l'application s'ouvre dans
 * le métro, chez un client, partout où il n'y a pas de réseau.
 *
 * La règle qui compte, et qui n'est pas négociable : LA PAGE N'EST JAMAIS
 * SERVIE DEPUIS LE CACHE TANT QU'IL Y A DU RÉSEAU. Un service worker qui
 * répond d'abord par le cache fige l'application à la version du jour où
 * il a été installé — et plus personne ne comprend pourquoi les corrections
 * n'arrivent pas. On a déjà perdu une journée entière sur exactement ça.
 * Ici, le cache ne sert que lorsque le réseau ne répond pas.
 *
 * Ce qui ne change jamais — les polices, la bibliothèque PDF, figées par
 * leur adresse — est servi depuis le cache en premier : c'est sans risque,
 * et ça évite d'attendre le réseau à chaque ouverture.
 */
/* ⚠ Ce fichier ne peut pas être vérifié sur http://localhost.
 *
 * Le navigateur de contrôle refuse d'enregistrer un service worker sur une
 * origine en http, y compris localhost. L'erreur est « An unknown error
 * occurred when fetching the script », qui ne dit rien de sa cause : deux
 * d'entre nous ont cru successivement à un en-tête « no-store », à du
 * HTTP/1.0, puis aux accents du fichier. Éprouvé avec un script de
 * quarante-huit octets en pur ASCII, sur un serveur neutre : il échoue
 * aussi. Ce n'est ni le script, ni le serveur, ni les en-têtes.
 *
 * En ligne, sur https://, tout fonctionne — mise à jour comprise, constatée
 * en voyant la boîte passer d'une version à la suivante après publication.
 * Donc : ne pas rediagnostiquer ceci depuis un port local. Le seul endroit
 * où l'observer est la page publique.
 */
const VERSION = "2511de68cd24";
const BOITE = "cura-" + VERSION;
const FIGE = "cura-fige";

/* Les polices étaient ici : elles sont désormais servies par le dépôt,
   donc figées par FIGES_ICI comme le reste de ce qui ne bouge pas. */
const DEHORS = ["https://cdnjs.cloudflare.com"];

/* Nos propres fichiers qui ne changent pas au rythme de l'application.
   Le formulaire des impôts pèse 700 kilo-octets et n'est republié qu'au
   printemps : le ranger avec la page le ferait retélécharger à chaque
   publication — soit plusieurs fois par jour — pour une déclaration qu'on
   remplit une fois par an. */
const FIGES_ICI = ["formulaire-2042.pdf",
                   "polices/nunito-var.woff2", "polices/outfit-var.woff2"];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(BOITE)
      .then(b => b.addAll(["./", "./manifest.webmanifest", "./icone.svg"]))
      .then(() => self.skipWaiting())
      .catch(() => self.skipWaiting())
  );
});

/* Ce que la boîte figée a encore le droit de garder. */
const encoreUtile = url =>
  DEHORS.some(d => url.startsWith(d)) || FIGES_ICI.some(f => url.endsWith(f));

self.addEventListener("activate", e => {
  /* Les boîtes des versions précédentes n'ont plus lieu d'être. */
  e.waitUntil(
    caches.keys()
      .then(noms => Promise.all(
        noms.filter(n => (n.startsWith("cura-") || n.startsWith("plenitu-")) && n !== BOITE && n !== FIGE)
            .map(n => caches.delete(n))))
      /* La boîte figée, elle, n'était jamais nettoyée : elle garde ce
         qu'on lui a confié jusqu'à ce qu'on l'en décharge. Les polices
         venaient de Google et sont maintenant servies par le dépôt —
         sans ceci, leurs anciennes copies resteraient indéfiniment sur
         le téléphone, une centaine de kilo-octets que plus rien ne
         demande. Vrai pour toute dépendance qu'on retirera ensuite. */
      .then(() => caches.open(FIGE))
      .then(boite => boite.keys().then(cles => Promise.all(
        cles.filter(r => !encoreUtile(r.url)).map(r => boite.delete(r)))))
      .catch(() => {})
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const requete = e.request;
  if (requete.method !== "GET") return;

  /* Ce qui ne change pas au rythme de la page : le cache d'abord, et une
     revalidation menée en silence derrière. La copie part tout de suite —
     personne n'attend le réseau pour un fichier qui n'a pas bougé — et la
     version suivante est prête pour l'ouverture d'après. Une requête
     conditionnelle ne coûte presque rien : le serveur répond « pas modifié ».
     C'est ce qui permet de garder une copie sans jamais la figer. */
  const figeDehors = DEHORS.some(d => requete.url.startsWith(d));
  const figeIci = FIGES_ICI.some(f => requete.url.endsWith(f));
  if (figeDehors || figeIci) {
    e.respondWith(
      caches.open(FIGE).then(boite =>
        boite.match(requete).then(garde => {
          const frais = fetch(requete).then(reponse => {
            if (reponse.ok || reponse.type === "opaque") boite.put(requete, reponse.clone());
            return reponse;
          }).catch(() => garde);
          if (garde) { e.waitUntil(frais.catch(() => {})); return garde; }
          return frais;
        })
      )
    );
    return;
  }

  /* Tout le reste — la page elle-même : le réseau d'abord, toujours.
     Le cache n'intervient que s'il n'y a pas de réponse. */
  e.respondWith(
    fetch(requete)
      .then(reponse => {
        if (reponse.ok) {
          const copie = reponse.clone();
          caches.open(BOITE).then(b => b.put(requete, copie)).catch(() => {});
        }
        return reponse;
      })
      .catch(() =>
        caches.match(requete).then(garde =>
          garde || caches.match("./").then(page =>
            page || new Response("Hors ligne", {status: 503, headers: {"Content-Type": "text/plain"}})
          )
        )
      )
  );
});
