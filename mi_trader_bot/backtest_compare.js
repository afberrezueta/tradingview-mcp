#!/usr/bin/env node
// Backtest comparativo: motor "Agentic" (Donchian 20 + trailing ATR + parcial 2R)
// vs motor "TJL v2" aproximado a datos diarios (breakout prev-high + SMA200 +
// SMA20 semanal + volumen relativo, bracket 1.5/3.0 ATR).
//
// LIMITACIONES (leer antes de sacar conclusiones):
//  - Datos diarios: los filtros intradía de TJL (premarket high, HOD, ventana
//    10:00-15:30 NY) NO son reproducibles aquí. TJL sale aproximado.
//  - Sin slippage ni coste de spread; fills idealizados (stop y target al precio
//    exacto salvo gap, en cuyo caso al open). Si stop y target caben el mismo
//    día se asume stop primero (conservador).
//  - El universo fue elegido conociendo el pasado (sesgo de selección): los
//    números absolutos están inflados para ambos motores; solo la COMPARACIÓN
//    relativa entre ellos es medianamente informativa.
//
// Uso: node backtest_compare.js <dir_csvs>
import fs from 'node:fs';
import path from 'node:path';

const DATA_DIR = process.argv[2] || 'data/historical_10y';
const AGENTIC_UNIVERSE = ['CRCL', 'COIN', 'MSTR', 'PLTR', 'NVDA', 'TQQQ', 'SOXL', 'SPCX'];
const TJL_WATCHLIST = ['NVDA', 'MSTR', 'COIN', 'CRCL', 'TSLA', 'QQQ', 'SPY', 'SOXX', 'TQQQ', 'SOXL', 'SPXL', 'NVDL', 'TSLL'];

function loadCsv(sym) {
  const file = path.join(DATA_DIR, `${sym}_10y_daily.csv`);
  if (!fs.existsSync(file)) return null;
  const rows = fs.readFileSync(file, 'utf8').trim().split('\n').slice(1).map((l) => {
    const [date, open, high, low, close, volume] = l.split(',');
    return { date, open: +open, high: +high, low: +low, close: +close, volume: +volume };
  }).filter((r) => r.open > 0 && r.high > 0);
  return rows.length ? rows : null;
}

function atrSeries(rows, len = 14) {
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

function smaSeries(vals, len) {
  const out = new Array(vals.length).fill(NaN);
  let sum = 0;
  for (let i = 0; i < vals.length; i++) {
    sum += vals[i];
    if (i >= len) sum -= vals[i - len];
    if (i >= len - 1) out[i] = sum / len;
  }
  return out;
}

// Semana ISO (para el filtro semanal de TJL): SMA20 de cierres de semanas COMPLETADAS.
function weeklyFilter(rows) {
  const weekKey = (d) => {
    const dt = new Date(d + 'T00:00:00Z');
    const day = (dt.getUTCDay() + 6) % 7; // lunes=0
    dt.setUTCDate(dt.getUTCDate() - day + 3); // jueves de la semana ISO
    const jan4 = new Date(Date.UTC(dt.getUTCFullYear(), 0, 4));
    const week = 1 + Math.round(((dt - jan4) / 86400000 - 3 + ((jan4.getUTCDay() + 6) % 7)) / 7);
    return `${dt.getUTCFullYear()}-${week}`;
  };
  const weeks = []; // cierres semanales en orden
  let curKey = null;
  const wIndexAt = new Array(rows.length); // nº de semanas COMPLETADAS antes del día i
  for (let i = 0; i < rows.length; i++) {
    const k = weekKey(rows[i].date);
    if (k !== curKey) { curKey = k; weeks.push(rows[i].close); }
    else weeks[weeks.length - 1] = rows[i].close;
    wIndexAt[i] = weeks.length - 1; // la semana actual (incompleta) es weeks[wIndexAt[i]]
  }
  const ok = new Array(rows.length).fill(false);
  for (let i = 0; i < rows.length; i++) {
    const done = wIndexAt[i]; // semanas completadas = índices 0..done-1
    if (done >= 20) {
      let s = 0;
      for (let j = done - 20; j < done; j++) s += weeks[j];
      ok[i] = weeks[done - 1] > s / 20;
    }
  }
  return ok;
}

function prepare(sym) {
  const rows = loadCsv(sym);
  if (!rows) return null;
  const atr = atrSeries(rows, 14);
  const sma200 = smaSeries(rows.map((r) => r.close), 200);
  const volSma20 = smaSeries(rows.map((r) => r.volume), 20);
  const weeklyOk = weeklyFilter(rows);
  const donUp = new Array(rows.length).fill(NaN);
  const donLo = new Array(rows.length).fill(NaN);
  for (let i = 20; i < rows.length; i++) {
    let hi = -Infinity, lo = Infinity;
    for (let j = i - 20; j < i; j++) { hi = Math.max(hi, rows[j].high); lo = Math.min(lo, rows[j].low); }
    donUp[i] = hi; donLo[i] = lo;
  }
  return { sym, rows, atr, sma200, volSma20, weeklyOk, donUp, donLo, idxByDate: new Map(rows.map((r, i) => [r.date, i])) };
}

// Señales al cierre del día i (se ejecutan al open del día i+1).
function agenticSignal(d, i) {
  return i >= 20 && !isNaN(d.donUp[i]) && !isNaN(d.atr[i]) && d.rows[i].close > d.donUp[i];
}
function tjlSignal(d, i) {
  if (i < 200 || isNaN(d.sma200[i - 1]) || isNaN(d.volSma20[i - 1]) || isNaN(d.atr[i])) return false;
  const r = d.rows[i], prev = d.rows[i - 1];
  return r.close > prev.high && prev.close > d.sma200[i - 1] && d.weeklyOk[i] && r.volume > d.volSma20[i - 1] * 1.5;
}
function channelPos(d, i) {
  const up = d.donUp[i], lo = d.donLo[i];
  return isNaN(up) || up === lo ? NaN : (d.rows[i].close - lo) / (up - lo);
}

// ---------- 1) Estadística por señal (todas las señales, 1R por trade) ----------
function perTradeStats(universe, dataBySym, signalFn, opts) {
  const results = [];
  for (const sym of universe) {
    const d = dataBySym.get(sym);
    if (!d) continue;
    for (let i = 0; i < d.rows.length - 1; i++) {
      if (!signalFn(d, i)) continue;
      const entry = d.rows[i + 1].open;
      const atr0 = d.atr[i];
      let stop = entry - 1.5 * atr0;
      if (stop <= 0) continue;
      const risk = entry - stop;
      const target = opts.target ? entry + 3.0 * atr0 : Infinity;
      let r = null, tookPartial = false, partialR = 0;
      for (let j = i + 1; j < d.rows.length; j++) {
        const b = d.rows[j];
        const stopped = j > i + 1 && b.low <= stop; // día de entrada: stop activo también
        const stoppedToday = j === i + 1 ? b.low <= stop : stopped;
        if (stoppedToday) { // stop primero (conservador)
          const fill = b.open < stop ? b.open : stop;
          r = partialR + (tookPartial ? 0.5 : 1) * (fill - entry) / risk;
          break;
        }
        if (opts.target && b.high >= target) {
          const fill = b.open > target ? b.open : target;
          r = (fill - entry) / risk;
          break;
        }
        if (opts.trailing) {
          if (!tookPartial && b.high >= entry + 2 * risk) {
            const fill = b.open > entry + 2 * risk ? b.open : entry + 2 * risk;
            partialR = 0.5 * (fill - entry) / risk;
            tookPartial = true;
          }
          if (b.close >= entry + risk) stop = Math.max(stop, b.close - 1.5 * d.atr[j]);
        }
      }
      if (r === null) { // aún abierta al final: valora al último cierre
        const last = d.rows[d.rows.length - 1].close;
        r = partialR + (tookPartial ? 0.5 : 1) * (last - entry) / risk;
      }
      results.push({ sym, date: d.rows[i + 1].date, r });
    }
  }
  const wins = results.filter((t) => t.r > 0);
  const losses = results.filter((t) => t.r <= 0);
  const sum = (a) => a.reduce((s, t) => s + t.r, 0);
  return {
    trades: results.length,
    winRate: results.length ? wins.length / results.length : 0,
    avgR: results.length ? sum(results) / results.length : 0,
    profitFactor: losses.length && sum(losses) !== 0 ? sum(wins) / -sum(losses) : Infinity,
    avgWinR: wins.length ? sum(wins) / wins.length : 0,
    avgLossR: losses.length ? sum(losses) / losses.length : 0,
    totalR: sum(results),
  };
}

// ---------- 2) Simulación de cartera con las reglas propias de cada motor ----------
function portfolioSim(universe, dataBySym, signalFn, cfg) {
  const dates = [...new Set(universe.flatMap((s) => dataBySym.get(s)?.rows.map((r) => r.date) ?? []))].sort();
  let cash = 100, equityPeak = 100, maxDD = 0, halted = null;
  const positions = new Map(); // sym -> {qty, entry, stop, risk, tookPartial}
  let consecLosses = 0, pauseUntil = -1, weekStartEq = 100, curWeek = null;
  const closedTrades = [];
  const equityCurve = [];

  const weekOf = (date) => {
    const dt = new Date(date + 'T00:00:00Z');
    const day = (dt.getUTCDay() + 6) % 7;
    dt.setUTCDate(dt.getUTCDate() - day);
    return dt.toISOString().slice(0, 10);
  };

  for (let t = 0; t < dates.length; t++) {
    const date = dates[t];
    const wk = weekOf(date);
    const markEquity = () => {
      let eq = cash;
      for (const [sym, p] of positions) {
        const d = dataBySym.get(sym); const i = d.idxByDate.get(date);
        const px = i !== undefined ? d.rows[i].close : d.rows[d.rows.length - 1].close;
        eq += p.qty * px;
      }
      return eq;
    };
    if (wk !== curWeek) { curWeek = wk; weekStartEq = markEquity(); }

    // --- salidas ---
    for (const [sym, p] of [...positions]) {
      const d = dataBySym.get(sym); const i = d.idxByDate.get(date);
      if (i === undefined) continue;
      const b = d.rows[i];
      if (b.low <= p.stop) {
        const fill = b.open < p.stop ? b.open : p.stop;
        cash += p.qty * fill;
        const pnlR = (p.partialPnl + p.qty * (fill - p.entry)) / p.riskDollars;
        closedTrades.push(pnlR);
        consecLosses = pnlR <= 0 ? consecLosses + 1 : 0;
        if (cfg.breakers && consecLosses >= 3) { pauseUntil = t + 3; consecLosses = 0; }
        positions.delete(sym);
        continue;
      }
      if (cfg.target && b.high >= p.target) {
        const fill = b.open > p.target ? b.open : p.target;
        cash += p.qty * fill;
        const pnlR = p.qty * (fill - p.entry) / p.riskDollars;
        closedTrades.push(pnlR);
        consecLosses = 0;
        positions.delete(sym);
        continue;
      }
      if (cfg.trailing) {
        const twoR = p.entry + 2 * p.riskPerShare;
        if (!p.tookPartial && b.high >= twoR) {
          const fill = b.open > twoR ? b.open : twoR;
          const half = p.qty / 2;
          cash += half * fill;
          p.partialPnl += half * (fill - p.entry);
          p.qty = half; p.tookPartial = true;
        }
        if (b.close >= p.entry + p.riskPerShare) p.stop = Math.max(p.stop, b.close - 1.5 * d.atr[i]);
      }
    }

    // --- entradas (señales del día anterior, ejecutadas al open de hoy) ---
    const eqNow = markEquity();
    if (cfg.killSwitch && eqNow < 78 && !halted) halted = date; // −22% desde 100
    const weekDD = weekStartEq > 0 ? (weekStartEq - eqNow) / weekStartEq : 0;
    const canEnter = !halted && t > pauseUntil && !(cfg.breakers && weekDD > 0.08);

    if (canEnter) {
      let buysToday = 0;
      for (const sym of universe) {
        if (cfg.maxPositions && positions.size >= cfg.maxPositions) break;
        if (cfg.maxBuysPerDay && buysToday >= cfg.maxBuysPerDay) break;
        if (positions.has(sym)) continue;
        const d = dataBySym.get(sym);
        if (!d) continue;
        const i = d.idxByDate.get(date);
        if (i === undefined || i === 0) continue;
        if (!signalFn(d, i - 1)) continue;
        if (cfg.regime) {
          const tq = dataBySym.get('TQQQ'), sx = dataBySym.get('SOXL');
          const ti = tq?.idxByDate.get(d.rows[i - 1].date), si = sx?.idxByDate.get(d.rows[i - 1].date);
          if (ti !== undefined && si !== undefined) {
            const pt = channelPos(tq, ti), ps = channelPos(sx, si);
            if (!isNaN(pt) && !isNaN(ps) && pt <= 0.25 && ps <= 0.25) continue;
          }
        }
        const entry = d.rows[i].open;
        const atr0 = d.atr[i - 1];
        const stop = entry - 1.5 * atr0;
        if (stop <= 0 || isNaN(stop)) continue;
        const riskPerShare = entry - stop;
        let qty = (eqNow * cfg.riskPct) / riskPerShare;
        if (cfg.maxPosPct) qty = Math.min(qty, (eqNow * cfg.maxPosPct) / entry);
        const maxCash = cfg.minCashPct ? cash - eqNow * cfg.minCashPct : cash;
        qty = Math.min(qty, Math.max(0, maxCash) / entry);
        if (qty * entry < eqNow * 0.001) continue;
        cash -= qty * entry;
        positions.set(sym, {
          qty, entry, stop, riskPerShare,
          riskDollars: qty * riskPerShare, partialPnl: 0, tookPartial: false,
          target: entry + 3.0 * atr0,
        });
        buysToday++;
      }
    }

    const eqClose = markEquity();
    equityPeak = Math.max(equityPeak, eqClose);
    maxDD = Math.max(maxDD, (equityPeak - eqClose) / equityPeak);
    equityCurve.push({ date, eq: eqClose });
  }

  const finalEq = equityCurve[equityCurve.length - 1].eq;
  const years = (new Date(dates[dates.length - 1]) - new Date(dates[0])) / 86400000 / 365.25;
  const wins = closedTrades.filter((r) => r > 0).length;
  return {
    finalMultiple: finalEq / 100,
    cagr: Math.pow(finalEq / 100, 1 / years) - 1,
    maxDD,
    closedTrades: closedTrades.length,
    winRate: closedTrades.length ? wins / closedTrades.length : 0,
    killSwitchDate: halted,
    years,
  };
}

// ---------- main ----------
const allSyms = [...new Set([...AGENTIC_UNIVERSE, ...TJL_WATCHLIST])];
const dataBySym = new Map();
for (const s of allSyms) { const d = prepare(s); if (d) dataBySym.set(s, d); else console.error(`(sin datos: ${s})`); }

const fmt = (x, pct = false) => pct ? (100 * x).toFixed(1) + '%' : x.toFixed(2);
const show = (name, s) => console.log(
  `${name.padEnd(38)} trades=${String(s.trades).padStart(4)}  winRate=${fmt(s.winRate, true).padStart(6)}  avgR=${fmt(s.avgR).padStart(6)}  PF=${s.profitFactor === Infinity ? '∞' : fmt(s.profitFactor).padStart(5)}  avgWin=${fmt(s.avgWinR)}R  avgLoss=${fmt(s.avgLossR)}R  totalR=${fmt(s.totalR)}`);

console.log('=== 1) Calidad del motor por señal (1R por trade, sin límites de cartera) ===');
show('Agentic/Donchian (universo agentic)', perTradeStats(AGENTIC_UNIVERSE, dataBySym, agenticSignal, { trailing: true }));
show('TJL v2 aprox-diario (universo agentic)', perTradeStats(AGENTIC_UNIVERSE, dataBySym, tjlSignal, { target: true }));
show('TJL v2 aprox-diario (su watchlist)', perTradeStats(TJL_WATCHLIST, dataBySym, tjlSignal, { target: true }));

console.log('\n=== 2) Simulación de cartera con las reglas propias de cada motor ===');
const showP = (name, p) => console.log(
  `${name.padEnd(38)} x${fmt(p.finalMultiple)} en ${p.years.toFixed(1)}a  CAGR=${fmt(p.cagr, true)}  maxDD=${fmt(p.maxDD, true)}  trades=${p.closedTrades}  winRate=${fmt(p.winRate, true)}${p.killSwitchDate ? `  KILL-SWITCH ${p.killSwitchDate}` : ''}`);
showP('Agentic (4% riesgo, máx2 pos, breakers)', portfolioSim(AGENTIC_UNIVERSE, dataBySym, agenticSignal, {
  riskPct: 0.04, maxPositions: 2, maxBuysPerDay: 1, maxPosPct: 0.45, minCashPct: 0.20,
  trailing: true, regime: true, breakers: true, killSwitch: true,
}));
showP('Agentic sin kill-switch', portfolioSim(AGENTIC_UNIVERSE, dataBySym, agenticSignal, {
  riskPct: 0.04, maxPositions: 2, maxBuysPerDay: 1, maxPosPct: 0.45, minCashPct: 0.20,
  trailing: true, regime: true, breakers: true, killSwitch: false,
}));
showP('TJL v2 (1% riesgo, bracket 2:1)', portfolioSim(TJL_WATCHLIST, dataBySym, tjlSignal, {
  riskPct: 0.01, target: true,
}));
showP('TJL v2 sobre universo agentic', portfolioSim(AGENTIC_UNIVERSE, dataBySym, tjlSignal, {
  riskPct: 0.01, target: true,
}));
showP('TJL v2 riesgo igualado a 4%', portfolioSim(TJL_WATCHLIST, dataBySym, tjlSignal, {
  riskPct: 0.04, target: true,
}));
