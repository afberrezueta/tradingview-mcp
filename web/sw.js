/*
 * Trabajador de servicio: hace que la página se instale en el teléfono y siga
 * abriendo sin conexión, mostrando el último dato conocido.
 *
 * Tres reglas distintas a propósito:
 *   /api/*    nunca se cachea. Es el precio en vivo; un precio viejo servido
 *             como fresco sería mentir. Si falla, la página ya sabe caer al
 *             respaldo por su cuenta.
 *   /datos/*  red primero, caché como red de seguridad. Sin conexión se ve el
 *             último cálculo, y la página dice que está desconectada.
 *   el resto  caché primero. Es el armazón: no cambia entre despliegues salvo
 *             que cambie la versión de abajo.
 */
const VERSION = 'v1';
const ARMAZON = `armazon-${VERSION}`;
const DATOS = `datos-${VERSION}`;
const PRECARGA = ['/', '/manifest.webmanifest', '/icono-192.png', '/icono-512.png', '/apple-touch-icon.png'];

self.addEventListener('install', (evento) => {
  evento.waitUntil(
    caches.open(ARMAZON)
      .then((c) => c.addAll(PRECARGA))
      .then(() => self.skipWaiting())
      .catch(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (evento) => {
  evento.waitUntil(
    caches.keys()
      .then((claves) => Promise.all(
        claves.filter((k) => k !== ARMAZON && k !== DATOS).map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (evento) => {
  const pedido = evento.request;
  if (pedido.method !== 'GET') return;

  const url = new URL(pedido.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.startsWith('/api/')) return; // en vivo o nada

  if (url.pathname.startsWith('/datos/')) {
    evento.respondWith(
      fetch(pedido)
        .then((r) => {
          if (r && r.ok) {
            const copia = r.clone();
            caches.open(DATOS).then((c) => c.put(pedido, copia));
          }
          return r;
        })
        .catch(() => caches.match(pedido))
    );
    return;
  }

  evento.respondWith(
    caches.match(pedido).then((guardado) => guardado || fetch(pedido).then((r) => {
      if (r && r.ok && r.type === 'basic') {
        const copia = r.clone();
        caches.open(ARMAZON).then((c) => c.put(pedido, copia));
      }
      return r;
    }))
  );
});
