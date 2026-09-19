// Integración con la CryptoQuant Data API (https://api.cryptoquant.com/v1/).
// Métricas on-chain para la tesis de acumulación de ETH: flujos netos de
// exchanges (acumulación vs distribución), MVRV, SOPR, NUPL, funding rates.
//
// Requiere CRYPTOQUANT_API_KEY en el entorno (plan Professional o superior —
// el plan Free NO da acceso a la Data API). Sin clave, las herramientas
// devuelven un error accionable en vez de fallar en silencio.
const BASE = 'https://api.cryptoquant.com/v1';

export function hasApiKey() {
  return Boolean(process.env.CRYPTOQUANT_API_KEY);
}

function requireKey() {
  const key = process.env.CRYPTOQUANT_API_KEY;
  if (!key) {
    throw new Error(
      'CRYPTOQUANT_API_KEY no está definida. Consíguela en cryptoquant.com (la Data API requiere plan Professional; '
      + 'el plan Free no la incluye) y expórtala en el entorno del servidor MCP, o añádela al .env del bot.',
    );
  }
  return key;
}

// Llamada genérica: cualquier endpoint documentado en cryptoquant.dev.
// path ej: 'eth/exchange-flows/netflow' — sin la barra inicial ni /v1.
export async function fetchMetric(path, params = {}) {
  const key = requireKey();
  const clean = String(path).replace(/^\/+/, '').replace(/^v1\//, '');
  const url = new URL(`${BASE}/${clean}`);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, String(v));
  }
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  const text = await res.text();
  let body;
  try { body = JSON.parse(text); } catch { body = { raw: text.slice(0, 500) }; }
  if (!res.ok) {
    const hint = res.status === 401 || res.status === 403
      ? ' Clave inválida o el plan no cubre este endpoint (la Data API es de plan Professional en adelante).'
      : res.status === 404
        ? ' Endpoint inexistente — verifica la ruta en cryptoquant.dev/resource/api.'
        : '';
    throw new Error(`CryptoQuant respondió ${res.status}: ${body?.error?.message || body?.message || text.slice(0, 200)}.${hint}`);
  }
  return body;
}

// Devuelve solo los últimos N puntos de la serie, para no inflar el contexto.
function tail(body, limit) {
  const rows = body?.result?.data ?? body?.data ?? body;
  if (!Array.isArray(rows)) return { raw: body };
  return { points: rows.slice(0, limit), returned: Math.min(limit, rows.length), total_available: rows.length };
}

// Flujo neto de exchanges: negativo = salen monedas de exchanges (acumulación
// hacia custodia propia); positivo = entran (presión vendedora potencial).
export async function exchangeNetflow({ asset = 'eth', window = 'day', exchange = 'all_exchange', limit = 14 } = {}) {
  const body = await fetchMetric(`${asset}/exchange-flows/netflow`, { window, exchange, limit });
  return {
    success: true, asset, window, exchange,
    interpretation: 'netflow negativo = retiradas netas de exchanges (sesgo acumulación); positivo = depósitos netos (sesgo distribución).',
    ...tail(body, limit),
  };
}

// MVRV: valor de mercado / valor realizado. <1 históricamente zona de suelo.
export async function mvrv({ asset = 'eth', window = 'day', limit = 14 } = {}) {
  const body = await fetchMetric(`${asset}/market-indicator/mvrv`, { window, limit });
  return {
    success: true, asset, window,
    interpretation: 'MVRV < 1 = precio bajo el coste medio de la red (zona históricamente de capitulación/suelo); MVRV alto = sobreextensión.',
    ...tail(body, limit),
  };
}

// SOPR: >1 el mercado vende en ganancia; <1 vende en pérdida (capitulación).
export async function sopr({ asset = 'eth', window = 'day', limit = 14 } = {}) {
  const body = await fetchMetric(`${asset}/network-indicator/sopr`, { window, limit });
  return {
    success: true, asset, window,
    interpretation: 'SOPR < 1 = las monedas movidas se venden con pérdida (capitulación); > 1 = toma de ganancias.',
    ...tail(body, limit),
  };
}
