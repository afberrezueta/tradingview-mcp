/**
 * Local historical OHLCV data — 10-year daily CSVs (source: Financial Modeling
 * Prep), independent of the live CDP/TradingView connection. Lets tools work
 * with long price history (backtesting, longer-range stats) beyond the ~500-bar
 * cap the live chart tools carry.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.resolve(__dirname, '../../data/historical_10y');
const FILE_SUFFIX = '_10y_daily.csv';

const cache = new Map(); // symbol -> parsed rows (ascending by date)
let symbolListCache = null;

function symbolFile(symbol) {
  return path.join(DATA_DIR, `${symbol}${FILE_SUFFIX}`);
}

function availableSymbols() {
  if (symbolListCache) return symbolListCache;
  if (!fs.existsSync(DATA_DIR)) return (symbolListCache = []);
  symbolListCache = fs.readdirSync(DATA_DIR)
    .filter((f) => f.endsWith(FILE_SUFFIX))
    .map((f) => f.slice(0, -FILE_SUFFIX.length))
    .sort();
  return symbolListCache;
}

function parseCsv(text) {
  const lines = text.split('\n').filter((l) => l.trim().length > 0);
  const header = lines[0].split(',');
  const idx = Object.fromEntries(header.map((h, i) => [h.trim(), i]));
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(',');
    rows.push({
      date: cols[idx.date],
      open: Number(cols[idx.open]),
      high: Number(cols[idx.high]),
      low: Number(cols[idx.low]),
      close: Number(cols[idx.close]),
      volume: Number(cols[idx.volume]),
      vwap: idx.vwap != null ? Number(cols[idx.vwap]) : undefined,
      change: idx.change != null ? Number(cols[idx.change]) : undefined,
      changePercent: idx.changePercent != null ? Number(cols[idx.changePercent]) : undefined,
    });
  }
  // Files are already ascending by date, but don't trust that blindly.
  rows.sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));
  return rows;
}

function loadSymbol(symbolRaw) {
  const requested = String(symbolRaw || '').toUpperCase().trim();
  if (cache.has(requested)) return cache.get(requested);

  // Resolve against the directory's own allowlist rather than joining raw
  // input into a path — avoids path traversal via a crafted `symbol` arg.
  const available = availableSymbols();
  const symbol = available.find((s) => s === requested);
  if (!symbol) {
    throw new Error(
      `No local historical data for "${requested}". Available symbols: ${available.join(', ') || '(none found — data/historical_10y is empty)'}`
    );
  }
  const rows = parseCsv(fs.readFileSync(symbolFile(symbol), 'utf8'));
  cache.set(symbol, rows);
  return rows;
}

export async function listHistoricalSymbols() {
  const symbols = availableSymbols();
  const result = symbols.map((symbol) => {
    const rows = loadSymbol(symbol);
    const first = rows[0];
    const last = rows[rows.length - 1];
    return {
      symbol,
      rows: rows.length,
      start_date: first?.date ?? null,
      end_date: last?.date ?? null,
    };
  });
  return { success: true, count: result.length, symbols: result, source: 'local_csv (Financial Modeling Prep, EOD daily)' };
}

export async function getHistoricalOhlcv({ symbol, count, start_date, end_date, summary } = {}) {
  if (!symbol) throw new Error('symbol is required (e.g. "NVDA", "SPY", "ETHUSD"). Call historical_list_symbols to see what is available.');
  const rows = loadSymbol(symbol);

  let filtered = rows;
  if (start_date || end_date) {
    filtered = rows.filter((r) => (!start_date || r.date >= start_date) && (!end_date || r.date <= end_date));
  } else {
    const limit = Math.min(count || 100, rows.length);
    filtered = rows.slice(-limit);
  }

  if (filtered.length === 0) {
    throw new Error(`No rows in range for ${symbol.toUpperCase()}. Data spans ${rows[0]?.date} to ${rows[rows.length - 1]?.date}.`);
  }

  if (summary) {
    const highs = filtered.map((b) => b.high);
    const lows = filtered.map((b) => b.low);
    const volumes = filtered.map((b) => b.volume);
    const first = filtered[0];
    const last = filtered[filtered.length - 1];
    return {
      success: true,
      symbol: symbol.toUpperCase(),
      bar_count: filtered.length,
      period: { from: first.date, to: last.date },
      open: first.open,
      close: last.close,
      high: Math.max(...highs),
      low: Math.min(...lows),
      change: Math.round((last.close - first.open) * 1e8) / 1e8,
      change_pct: Math.round(((last.close - first.open) / first.open) * 10000) / 100 + '%',
      avg_volume: Math.round(volumes.reduce((a, b) => a + b, 0) / volumes.length),
      last_5_bars: filtered.slice(-5),
    };
  }

  return {
    success: true,
    symbol: symbol.toUpperCase(),
    bar_count: filtered.length,
    total_available: rows.length,
    source: 'local_csv',
    bars: filtered,
  };
}
