/* Plenitu hors-ligne — version b6d70952f05e
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
const VERSION = "b6d70952f05e";
const BOITE = "plenitu-" + VERSION;
const FIGE = "plenitu-fige";

const DEHORS = ["https://fonts.googleapis.com", "https://fonts.gstatic.com",
                "https://cdnjs.cloudflare.com"];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(BOITE)
      .then(b => b.addAll(["./", "./manifest.webmanifest", "./icone.svg"]))
      .then(() => self.skipWaiting())
      .catch(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  /* Les boîtes des versions précédentes n'ont plus lieu d'être. */
  e.waitUntil(
    caches.keys()
      .then(noms => Promise.all(
        noms.filter(n => n.startsWith("plenitu-") && n !== BOITE && n !== FIGE)
            .map(n => caches.delete(n))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const requete = e.request;
  if (requete.method !== "GET") return;

  /* Ce qui vient d'ailleurs et ne change jamais : le cache d'abord. */
  if (DEHORS.some(d => requete.url.startsWith(d))) {
    e.respondWith(
      caches.open(FIGE).then(boite =>
        boite.match(requete).then(garde =>
          garde || fetch(requete).then(reponse => {
            if (reponse.ok || reponse.type === "opaque") boite.put(requete, reponse.clone());
            return reponse;
          })
        )
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
