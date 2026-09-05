// Lógica pura del mi-trader-bot MCP: indicadores, zonas ETH, señales y backtest.
// Sin dependencias de red ni de MCP — todo opera sobre los CSVs locales y los
// archivos de config/estado del bot, para que sea testeable con `node --test`.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '..', '..');

export function botDir() {
  return process.env.MI_TRADER_BOT_DIR || path.join(os.homedir(), 'Documents', 'mi_trader_bot');
}

export function dataDir() {
  const candidates = [
    process.env.MI_TRADER_DATA_DIR,
    path.join(REPO_ROOT, 'data', 'historical_10y'),
    path.join(botDir(), 'data', 'historical_10y'),
  ].filter(Boolean);
  for (const dir of candidates) if (fs.existsSync(dir)) return dir;
  throw new Error(`No encuentro el directorio de CSVs históricos. Probé: ${candidates.join(', ')}. Define MI_TRADER_DATA_DIR.`);
}

export function listSymbols() {
  return fs.readdirSync(dataDir())
    .filter((f) => f.endsWith('_10y_daily.csv'))
    .map((f) => f.replace('_10y_daily.csv', ''))
    .sort();
}

export function loadCsv(symbol) {
  const file = path.join(dataDir(), `${symbol}_10y_daily.csv`);
  if (!fs.existsSync(file)) {
    throw new Error(`Sin datos para ${symbol}. Disponibles: ${listSymbols().join(', ')}`);
  }
  const rows = fs.readFileSync(file, 'utf8').trim().split('\n').slice(1).map((l) => {
    const [date, open, high, low, close, volume] = l.split(',');
    return { date, open: +open, high: +high, low: +low, close: +close, volume: +volume };
  }).filter((r) => r.open > 0 && r.high > 0);
  if (!rows.length) throw new Error(`CSV vacío para ${symbol}`);
  return rows;
}

export function atrSeries(rows, len = 14) {
  const atr = new Array(rows.length).fill(NaN);
  let prev = null, sum = 0;
  for (let i = 0; i < rows.length; i++) {
    const r = rows[i];
    const tr = prev ? Math.max(r.high - r.low, Math.abs(r.high - prev.close), Math.abs(r.low - prev.close)) : r.high - r.low;
    if (i < len) { sum += tr; if (i === len - 1) atr[i] = sum / len; }
    else atr[i] = (atr[i - 1] * (len - 1) + tr) / len;
    prev = r;
  }
  return atr;
}

export function smaSeries(vals, len) {
  const out = new Array(vals.length).fill(NaN);
  let sum = 0;
  for (let i = 0; i < vals.length; i++) {
    sum += vals[i];
    if (i >= len) sum -= vals[i - len];
    if (i >= len - 1) out[i] = sum / len;
  }
  return out;
}

// Canal Donchian sobre las N barras ANTERIORES al índice i (sin incluir i).
export function donchianAt(rows, i, len = 20) {
  if (i < len) return null;
  let hi = -Infinity, lo = Infinity;
  for (let j = i - len; j < i; j++) { hi = Math.max(hi, rows[j].high); lo = Math.min(lo, rows[j].low); }
  return { upper: hi, lower: lo };
}

function channelPosition(rows, i, len = 20) {
  const d = donchianAt(rows, i, len);
  if (!d || d.upper === d.lower) return null;
  return (rows[i].close - d.lower) / (d.upper - d.lower);
}

// SMA20 de cierres de semanas ISO COMPLETADAS, evaluada por día.
export function weeklyTrendOkSeries(rows) {
  const weekKey = (d) => {
    const dt = new Date(d + 'T00:00:00Z');
    const day = (dt.getUTCDay() + 6) % 7;
    dt.setUTCDate(dt.getUTCDate() - day + 3);
    const jan4 = new Date(Date.UTC(dt.getUTCFullYear(), 0, 4));
    const week = 1 + Math.round(((dt - jan4) / 86400000 - 3 + ((jan4.getUTCDay() + 6) % 7)) / 7);
    return `${dt.getUTCFullYear()}-${week}`;
  };
  const weeks = [];
  let curKey = null;
  const ok = new Array(rows.length).fill(false);
  const doneAt = new Array(rows.length);
  for (let i = 0; i < rows.length; i++) {
    const k = weekKey(rows[i].date);
    if (k !== curKey) { curKey = k; weeks.push(rows[i].close); }
    else weeks[weeks.length - 1] = rows[i].close;
    doneAt[i] = weeks.length - 1;
  }
  for (let i = 0; i < rows.length; i++) {
    const done = doneAt[i];
    if (done >= 20) {
      let s = 0;
      for (let j = done - 20; j < done; j++) s += weeks[j];
      ok[i] = weeks[done - 1] > s / 20;
    }
  }
  return ok;
}

function readJson(file, fallback = null) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); }
  catch { return fallback; }
}

export function loadEthConfig() {
  const candidates = [
    path.join(botDir(), 'eth_accumulation_config.json'),
    path.join(REPO_ROOT, 'mi_trader_bot', 'eth_accumulation_config.json'),
  ];
  for (const f of candidates) {
    const cfg = readJson(f);
    if (cfg) return { config: cfg, source: f };
  }
  throw new Error(`No encuentro eth_accumulation_config.json (probé ${candidates.join(', ')})`);
}

// Zonas de acumulación ETH: escalera de tramos por drawdown desde el swing high.
export function ethZones({ currentPrice } = {}) {
  const { config, source } = loadEthConfig();
  const rows = loadCsv(config.asset || 'ETHUSD');
  const lookback = config.swing_lookback_days || 90;
  const recent = rows.slice(-lookback);
  let swingHigh = Math.max(...recent.map((r) => r.close));
  const lastClose = rows[rows.length - 1].close;
  const price = currentPrice ?? lastClose;
  if (price > swingHigh) swingHigh = price;

  const state = readJson(path.join(botDir(), config.execution?.state_file || 'out/eth_state.json'), { executed_tranches: [] });
  const executed = new Set(state.executed_tranches || []);
  const band = (config.zone_band_pct ?? 1.5) / 100;
  const levels = config.tranche_drawdown_levels_pct || [-30, -40, -50, -60];
  const pcts = config.tranche_pcts || [20, 25, 30, 25];
  const capital = config.capital_usd;

  const drawdownPct = (price / swingHigh - 1) * 100;
  const tranches = levels.map((lvl, i) => {
    const target = swingHigh * (1 + lvl / 100);
    const inBand = price <= target * (1 + band); // el precio alcanzó (o perforó) la banda del tramo
    return {
      tranche: i + 1,
      drawdown_level_pct: lvl,
      target_price: +target.toFixed(2),
      amount_usd: capital ? +(capital * pcts[i] / 100).toFixed(2) : null,
      executed: executed.has(i + 1),
      active_now: inBand && !executed.has(i + 1),
      distance_pct: +((target / price - 1) * 100).toFixed(2),
    };
  });
  const next = tranches.find((t) => !t.executed && !t.active_now);
  return {
    success: true,
    config_source: source,
    price_used: +price.toFixed(2),
    price_source: currentPrice ? 'caller' : `último cierre CSV (${rows[rows.length - 1].date})`,
    swing_high_90d: +swingHigh.toFixed(2),
    drawdown_from_swing_pct: +drawdownPct.toFixed(2),
    capital_usd: capital,
    tranches,
    next_pending_tranche: next ? next.tranche : null,
    note: 'active_now indica que el precio está en o bajo la banda del tramo y no se ha ejecutado. La ejecución real la hace eth_scan.sh en la cuenta Agentic; esta herramienta solo calcula.',
  };
}

// Señal Donchian (motor Agentic) para un símbolo, con sizing opcional.
export function donchianSignal(symbol, { equity, riskPct = 4 } = {}) {
  const rows = loadCsv(symbol);
  const i = rows.length - 1;
  const d = donchianAt(rows, i, 20);
  const atr = atrSeries(rows)[i];
  if (!d || isNaN(atr)) throw new Error(`Historia insuficiente para ${symbol} (se necesitan 20+ barras)`);
  const close = rows[i].close;
  const breakout = close > d.upper;
  const stop = close - 1.5 * atr;

  let regime = null;
  try {
    const tq = loadCsv('TQQQ'), sx = loadCsv('SOXL');
    const pt = channelPosition(tq, tq.length - 1), ps = channelPosition(sx, sx.length - 1);
    regime = {
      tqqq_channel_pos_pct: pt === null ? null : +(pt * 100).toFixed(1),
      soxl_channel_pos_pct: ps === null ? null : +(ps * 100).toFixed(1),
      risk_off: pt !== null && ps !== null && pt <= 0.25 && ps <= 0.25,
    };
  } catch { /* sin datos de régimen */ }

  const out = {
    success: true,
    symbol,
    as_of: rows[i].date,
    close: +close.toFixed(2),
    donchian20_upper: +d.upper.toFixed(2),
    donchian20_lower: +d.lower.toFixed(2),
    channel_position_pct: +((channelPosition(rows, i) ?? 0) * 100).toFixed(1),
    atr14: +atr.toFixed(2),
    breakout_signal: breakout,
    distance_to_breakout_pct: +((d.upper / close - 1) * 100).toFixed(2),
    stop_if_entered: +stop.toFixed(2),
    regime,
  };
  if (equity) {
    const riskDollars = equity * riskPct / 100;
    const riskPerShare = close - stop;
    out.sizing = {
      equity, risk_pct: riskPct, risk_usd: +riskDollars.toFixed(2),
      shares: +(riskDollars / riskPerShare).toFixed(4),
      position_usd: +((riskDollars / riskPerShare) * close).toFixed(2),
    };
  }
  return out;
}

// Señal TJL v2 (aproximación diaria) para un símbolo.
export function tjlSignal(symbol) {
  const rows = loadCsv(symbol);
  const i = rows.length - 1;
  if (i < 200) throw new Error(`Historia insuficiente para TJL en ${symbol} (SMA200 necesita 200+ barras, hay ${i + 1})`);
  const sma200 = smaSeries(rows.map((r) => r.close), 200);
  const volSma20 = smaSeries(rows.map((r) => r.volume), 20);
  const weeklyOk = weeklyTrendOkSeries(rows);
  const atr = atrSeries(rows)[i];
  const r = rows[i], prev = rows[i - 1];
  const checks = {
    daily_breakout: { pass: r.close > prev.high, close: +r.close.toFixed(2), prev_high: +prev.high.toFixed(2) },
    above_sma200: { pass: prev.close > sma200[i - 1], prev_close: +prev.close.toFixed(2), sma200: +sma200[i - 1].toFixed(2) },
    weekly_trend_up: { pass: weeklyOk[i] },
    relative_volume: { pass: r.volume > volSma20[i - 1] * 1.5, volume: r.volume, avg20_x1_5: Math.round(volSma20[i - 1] * 1.5) },
  };
  const signal = Object.values(checks).every((c) => c.pass);
  return {
    success: true,
    symbol,
    as_of: r.date,
    signal,
    checks,
    atr14: +atr.toFixed(2),
    stop_if_entered: +(r.close - 1.5 * atr).toFixed(2),
    target_if_entered: +(r.close + 3.0 * atr).toFixed(2),
    note: 'Aproximación con datos diarios: los filtros intradía del TJL real (premarket high / HOD) no se evalúan aquí.',
  };
}

// ---- Backtest (mismas mecánicas que backtest_compare.js) ----
function prepare(symbol) {
  const rows = loadCsv(symbol);
  return {
    sym: symbol, rows,
    atr: atrSeries(rows),
    sma200: smaSeries(rows.map((r) => r.close), 200),
    volSma20: smaSeries(rows.map((r) => r.volume), 20),
    weeklyOk: weeklyTrendOkSeries(rows),
    idxByDate: new Map(rows.map((r, i) => [r.date, i])),
  };
}

function agenticEntry(d, i) {
  const don = donchianAt(d.rows, i, 20);
  return don && !isNaN(d.atr[i]) && d.rows[i].close > don.upper;
}

function tjlEntry(d, i) {
  if (i < 200 || isNaN(d.sma200[i - 1]) || isNaN(d.volSma20[i - 1]) || isNaN(d.atr[i])) return false;
  const r = d.rows[i], prev = d.rows[i - 1];
  return r.close > prev.high && prev.close > d.sma200[i - 1] && d.weeklyOk[i] && r.volume > d.volSma20[i - 1] * 1.5;
}

export function backtest({ engine = 'agentic', symbols, risk_pct, max_positions } = {}) {
  const isAgentic = engine === 'agentic';
  const universe = symbols?.length ? symbols : (isAgentic
    ? ['CRCL', 'COIN', 'MSTR', 'PLTR', 'NVDA', 'TQQQ', 'SOXL', 'SPCX']
    : ['NVDA', 'MSTR', 'COIN', 'CRCL', 'TSLA', 'QQQ', 'SPY', 'SOXX', 'TQQQ', 'SOXL', 'SPXL', 'NVDL', 'TSLL']);
  const riskPct = (risk_pct ?? (isAgentic ? 4 : 1)) / 100;
  const maxPositions = max_positions ?? (isAgentic ? 2 : Infinity);
  const signalFn = isAgentic ? agenticEntry : tjlEntry;

  const data = new Map();
  const missing = [];
  for (const s of universe) {
    try { data.set(s, prepare(s)); } catch { missing.push(s); }
  }
  if (!data.size) throw new Error(`Ningún símbolo del universo tiene datos: ${universe.join(', ')}`);

  const dates = [...new Set([...data.values()].flatMap((d) => d.rows.map((r) => r.date)))].sort();
  let cash = 100, peak = 100, maxDD = 0;
  const positions = new Map();
  const closed = [];

  const mark = (date) => {
    let eq = cash;
    for (const [sym, p] of positions) {
      const d = data.get(sym), i = d.idxByDate.get(date);
      eq += p.qty * (i !== undefined ? d.rows[i].close : d.rows[d.rows.length - 1].close);
    }
    return eq;
  };

  for (const date of dates) {
    for (const [sym, p] of [...positions]) {
      const d = data.get(sym), i = d.idxByDate.get(date);
      if (i === undefined) continue;
      const b = d.rows[i];
      if (b.low <= p.stop) {
        const fill = b.open < p.stop ? b.open : p.stop;
        cash += p.qty * fill;
        closed.push((p.partialPnl + p.qty * (fill - p.entry)) / p.riskDollars);
        positions.delete(sym);
        continue;
      }
      if (!isAgentic && b.high >= p.target) {
        const fill = b.open > p.target ? b.open : p.target;
        cash += p.qty * fill;
        closed.push(p.qty * (fill - p.entry) / p.riskDollars);
        positions.delete(sym);
        continue;
      }
      if (isAgentic) {
        const twoR = p.entry + 2 * p.riskPerShare;
        if (!p.tookPartial && b.high >= twoR) {
          const fill = b.open > twoR ? b.open : twoR;
          const half = p.qty / 2;
          cash += half * fill;
          p.partialPnl += half * (fill - p.entry);
          p.qty = half;
          p.tookPartial = true;
        }
        if (b.close >= p.entry + p.riskPerShare) p.stop = Math.max(p.stop, b.close - 1.5 * d.atr[i]);
      }
    }

    const eqNow = mark(date);
    let buys = 0;
    for (const sym of universe) {
      if (positions.size >= maxPositions || (isAgentic && buys >= 1)) break;
      if (positions.has(sym) || !data.has(sym)) continue;
      const d = data.get(sym), i = d.idxByDate.get(date);
      if (i === undefined || i === 0 || !signalFn(d, i - 1)) continue;
      if (isAgentic && data.has('TQQQ') && data.has('SOXL')) {
        const prevDate = d.rows[i - 1].date;
        const tq = data.get('TQQQ'), sx = data.get('SOXL');
        const ti = tq.idxByDate.get(prevDate), si = sx.idxByDate.get(prevDate);
        if (ti !== undefined && si !== undefined) {
          const pt = channelPosition(tq.rows, ti), ps = channelPosition(sx.rows, si);
          if (pt !== null && ps !== null && pt <= 0.25 && ps <= 0.25) continue;
        }
      }
      const entry = d.rows[i].open;
      const atr0 = d.atr[i - 1];
      const stop = entry - 1.5 * atr0;
      if (!(stop > 0)) continue;
      const riskPerShare = entry - stop;
      let qty = (eqNow * riskPct) / riskPerShare;
      if (isAgentic) qty = Math.min(qty, (eqNow * 0.45) / entry, Math.max(0, cash - eqNow * 0.20) / entry);
      else qty = Math.min(qty, cash / entry);
      if (qty * entry < eqNow * 0.001) continue;
      cash -= qty * entry;
      positions.set(sym, {
        qty, entry, stop, riskPerShare,
        riskDollars: qty * riskPerShare, partialPnl: 0, tookPartial: false,
        target: entry + 3.0 * atr0,
      });
      buys++;
    }

    const eq = mark(date);
    peak = Math.max(peak, eq);
    maxDD = Math.max(maxDD, (peak - eq) / peak);
  }

  const finalEq = mark(dates[dates.length - 1]);
  const years = (new Date(dates[dates.length - 1]) - new Date(dates[0])) / 86400000 / 365.25;
  const wins = closed.filter((r) => r > 0);
  return {
    success: true,
    engine, universe: [...data.keys()], symbols_without_data: missing,
    period: { from: dates[0], to: dates[dates.length - 1], years: +years.toFixed(1) },
    risk_pct_per_trade: riskPct * 100,
    final_multiple: +(finalEq / 100).toFixed(2),
    cagr_pct: +((Math.pow(finalEq / 100, 1 / years) - 1) * 100).toFixed(1),
    max_drawdown_pct: +(maxDD * 100).toFixed(1),
    closed_trades: closed.length,
    win_rate_pct: closed.length ? +((wins.length / closed.length) * 100).toFixed(1) : null,
    avg_r: closed.length ? +(closed.reduce((s, r) => s + r, 0) / closed.length).toFixed(2) : null,
    caveats: 'Fills idealizados, sin slippage, sin circuit breakers ni kill switch (a diferencia de backtest_compare.js), universo elegido con retrospectiva. Comparar motores entre sí, no tomar los números absolutos como expectativa.',
  };
}

// Estado del bot: últimos reportes y estado de tramos.
export function scanStatus() {
  const dir = path.join(botDir(), 'out');
  const readText = (f) => {
    try { return fs.readFileSync(path.join(dir, f), 'utf8').trim(); } catch { return null; }
  };
  const tailLog = (f, lines = 15) => {
    const t = readText(f);
    return t ? t.split('\n').slice(-lines).join('\n') : null;
  };
  return {
    success: true,
    bot_dir: botDir(),
    agentic_scan: { last_report: readText('agentic_scan.txt'), log_tail: tailLog('agentic_scan.log') },
    eth_scan: { last_report: readText('eth_scan.txt'), log_tail: tailLog('eth_scan.log') },
    eth_state: readJson(path.join(dir, 'eth_state.json')),
  };
}

// Envío a Telegram usando las mismas credenciales del bot (.env del BOT_DIR).
export async function telegramSend(message) {
  const envFile = path.join(botDir(), '.env');
  let token = process.env.TELEGRAM_BOT_TOKEN, chatId = process.env.TELEGRAM_CHAT_ID;
  if ((!token || !chatId) && fs.existsSync(envFile)) {
    for (const line of fs.readFileSync(envFile, 'utf8').split('\n')) {
      const m = line.match(/^(?:export\s+)?(TELEGRAM_BOT_TOKEN|TELEGRAM_CHAT_ID)=["']?([^"'\n]+)["']?/);
      if (m) { if (m[1] === 'TELEGRAM_BOT_TOKEN') token = m[2]; else chatId = m[2]; }
    }
  }
  if (!token || !chatId) throw new Error(`TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID no disponibles (ni en el entorno ni en ${envFile})`);
  const res = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ chat_id: chatId, text: message }),
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok || body.ok === false) throw new Error(`Telegram respondió ${res.status}: ${body.description || 'error desconocido'}`);
  return { success: true, message_id: body.result?.message_id ?? null };
}
