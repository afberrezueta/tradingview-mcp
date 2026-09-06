/**
 * Cotización de ETH en vivo para la web pública.
 *
 * Nunca expone una clave al navegador: la clave de Financial Modeling Prep vive
 * en la variable de entorno FMP_API_KEY del proyecto de Vercel. Si no está
 * configurada, la función cae a fuentes públicas sin clave (Coinbase y Binance),
 * de modo que la página sirve datos reales desde el primer despliegue.
 *
 * Respuesta: { precio, cambio_pct, min_dia, max_dia, hora_utc, fuente, en_vivo }
 * en_vivo=false significa que ninguna fuente respondió y el cliente debe usar
 * la instantánea estática de web/datos/publico.json.
 */

const TIEMPO_LIMITE_MS = 4000;

async function traer(url, opciones = {}) {
  const control = new AbortController();
  const alarma = setTimeout(() => control.abort(), TIEMPO_LIMITE_MS);
  try {
    const r = await fetch(url, { ...opciones, signal: control.signal });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.json();
  } finally {
    clearTimeout(alarma);
  }
}

const numero = (v) => {
  const n = typeof v === 'string' ? Number.parseFloat(v) : v;
  return Number.isFinite(n) ? n : null;
};

/**
 * Financial Modeling Prep: la fuente que ya usa el motor, para que web y motor coincidan.
 * Se prueban las dos rutas que FMP ha servido (la nueva "stable" y la clásica v3) porque
 * la cuenta puede estar en cualquiera de las dos, y los nombres de campo difieren entre ellas.
 */
async function desdeFmp(clave) {
  const rutas = [
    `https://financialmodelingprep.com/stable/quote?symbol=ETHUSD&apikey=${encodeURIComponent(clave)}`,
    `https://financialmodelingprep.com/api/v3/quote/ETHUSD?apikey=${encodeURIComponent(clave)}`,
  ];
  let ultimo = null;
  for (const url of rutas) {
    try {
      const datos = await traer(url);
      const q = Array.isArray(datos) ? datos[0] : datos;
      const precio = numero(q?.price);
      if (precio === null) throw new Error('respuesta sin precio');
      return {
        precio,
        // "changePercentage" en stable, "changesPercentage" en v3
        cambio_pct: numero(q?.changePercentage ?? q?.changesPercentage),
        min_dia: numero(q?.dayLow),
        max_dia: numero(q?.dayHigh),
        hora_utc: q?.timestamp
          ? new Date(q.timestamp * 1000).toISOString().slice(0, 16).replace('T', ' ')
          : null,
        fuente: 'Financial Modeling Prep',
      };
    } catch (e) {
      ultimo = e;
    }
  }
  throw new Error(`FMP falló: ${ultimo instanceof Error ? ultimo.message : 'sin detalle'}`);
}

/** Binance público: da precio y rango del día en una sola llamada, sin clave. */
async function desdeBinance() {
  const datos = await traer('https://api.binance.com/api/v3/ticker/24hr?symbol=ETHUSDT');
  const precio = numero(datos?.lastPrice);
  if (precio === null) throw new Error('Binance no devolvió precio');
  return {
    precio,
    cambio_pct: numero(datos?.priceChangePercent),
    min_dia: numero(datos?.lowPrice),
    max_dia: numero(datos?.highPrice),
    hora_utc: new Date(numero(datos?.closeTime) ?? Date.now()).toISOString().slice(0, 16).replace('T', ' '),
    fuente: 'Binance (ETHUSDT, público)',
  };
}

/** Coinbase público: último recurso, solo precio al contado. */
async function desdeCoinbase() {
  const datos = await traer('https://api.coinbase.com/v2/prices/ETH-USD/spot');
  const precio = numero(datos?.data?.amount);
  if (precio === null) throw new Error('Coinbase no devolvió precio');
  return {
    precio,
    cambio_pct: null,
    min_dia: null,
    max_dia: null,
    hora_utc: new Date().toISOString().slice(0, 16).replace('T', ' '),
    fuente: 'Coinbase (ETH-USD al contado, público)',
  };
}

export default async function handler(req, res) {
  const clave = process.env.FMP_API_KEY;
  const intentos = [];
  if (clave) intentos.push(desdeFmp.bind(null, clave));
  intentos.push(desdeBinance, desdeCoinbase);

  const fallos = [];
  for (const intento of intentos) {
    try {
      const cotizacion = await intento();
      // 20 s de caché en el borde: el precio es fresco sin castigar el límite de peticiones.
      res.setHeader('Cache-Control', 'public, s-maxage=20, stale-while-revalidate=120');
      res.setHeader('Content-Type', 'application/json; charset=utf-8');
      return res.status(200).json({ ...cotizacion, en_vivo: true, consultado: new Date().toISOString() });
    } catch (e) {
      fallos.push(e instanceof Error ? e.message : String(e));
    }
  }

  // Ninguna fuente respondió: se dice, no se inventa un número.
  res.setHeader('Cache-Control', 'public, s-maxage=10');
  return res.status(503).json({
    en_vivo: false,
    error: 'ninguna fuente de precio respondió',
    detalle: fallos,
  });
}
