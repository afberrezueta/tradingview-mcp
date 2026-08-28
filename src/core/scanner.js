/**
 * Trend Join Long (TJL) day-trading scanner.
 *
 * Sequentially walks a configurable watchlist (data/tjl_watchlist.json),
 * driving the live TradingView chart per ticker, and flags names that meet
 * the entry criteria right now:
 *   daily_breakout    = curr_px > prev_daily_high  AND  prev_daily_close > sma200
 *   intraday_breakout = curr_px > premarket_high   AND  curr_px > today's-high-so-far
 * A ticker PASSes only if both are true.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as health from './health.js';
import * as chart from './chart.js';
import * as data from './data.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const WATCHLIST_PATH = path.resolve(__dirname, '../../data/tjl_watchlist.json');
const OUTPUT_DIR = path.resolve(__dirname, '../../');

const NY_TZ = 'America/New_York';
const GATE_OPEN_MIN = 10 * 60;       // 10:00am
const GATE_CLOSE_MIN = 15 * 60 + 30; // 3:30pm
const PREMARKET_START_MIN = 4 * 60;  // 4:00am
const REGULAR_OPEN_MIN = 9 * 60 + 30; // 9:30am
const SMA_LOOKBACK = 200;

function nyParts(epochMs) {
  const fmt = new Intl.DateTimeFormat('en-US', {
    timeZone: NY_TZ, hour12: false,
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', weekday: 'short',
  });
  const parts = Object.fromEntries(fmt.formatToParts(new Date(epochMs)).map((p) => [p.type, p.value]));
  const hour = parts.hour === '24' ? 0 : Number(parts.hour); // Intl can emit "24" for midnight
  return {
    dateStr: `${parts.year}-${parts.month}-${parts.day}`,
    minuteOfDay: hour * 60 + Number(parts.minute),
    weekday: parts.weekday, // "Mon".."Sun"
  };
}

function readWatchlist() {
  if (!fs.existsSync(WATCHLIST_PATH)) {
    throw new Error(`Watchlist not found at ${WATCHLIST_PATH}. Create it with a "tickers": [{ "symbol": "...", "enabled": true }] array.`);
  }
  const json = JSON.parse(fs.readFileSync(WATCHLIST_PATH, 'utf8'));
  return (json.tickers || []).filter((t) => t.enabled).map((t) => t.symbol.toUpperCase());
}

function checkTimeGate(nowMs) {
  const { minuteOfDay, weekday, dateStr } = nyParts(nowMs);
  const isWeekday = !['Sat', 'Sun'].includes(weekday);
  const inWindow = minuteOfDay >= GATE_OPEN_MIN && minuteOfDay <= GATE_CLOSE_MIN;
  return { pass: isWeekday && inWindow, isWeekday, inWindow, ny_time: `${dateStr} ${String(Math.floor(minuteOfDay / 60)).padStart(2, '0')}:${String(minuteOfDay % 60).padStart(2, '0')} ${weekday}` };
}

function outputFilename(nowMs) {
  const { dateStr, minuteOfDay } = nyParts(nowMs);
  const hh = String(Math.floor(minuteOfDay / 60)).padStart(2, '0');
  const mm = String(minuteOfDay % 60).padStart(2, '0');
  return path.join(OUTPUT_DIR, `tjl_watchlist_${dateStr}_${hh}${mm}ET.json`);
}

function writeJson(filePath, obj) {
  fs.writeFileSync(filePath, JSON.stringify(obj, null, 2) + '\n', 'utf8');
  return filePath;
}

/** Splits daily bars into the still-forming "today" bar (if present) and completed history. */
function splitDaily(bars, todayDateStr) {
  if (bars.length === 0) return { completed: [], forming: null };
  const last = bars[bars.length - 1];
  const lastDate = nyParts(last.time * 1000).dateStr;
  if (lastDate === todayDateStr) return { completed: bars.slice(0, -1), forming: last };
  return { completed: bars, forming: null };
}

async function analyzeTicker(symbol, nowMs, todayDateStr) {
  await chart.setSymbol({ symbol });
  await chart.setTimeframe({ timeframe: 'D' });
  const dailyRaw = await data.getOhlcv({ count: 210 });
  const { completed: dailyCompleted } = splitDaily(dailyRaw.bars, todayDateStr);

  if (dailyCompleted.length < SMA_LOOKBACK) {
    return { symbol, error: `Only ${dailyCompleted.length} completed daily bars available (need ${SMA_LOOKBACK} for SMA200). Skipping — likely too-recent a listing.` };
  }

  const prevBar = dailyCompleted[dailyCompleted.length - 1];
  const prev_daily_high = prevBar.high;
  const prev_daily_close = prevBar.close;
  const sma200 = dailyCompleted.slice(-SMA_LOOKBACK).reduce((sum, b) => sum + b.close, 0) / SMA_LOOKBACK;

  const quote = await data.getQuote({ symbol });
  const curr_px = quote.last ?? quote.close;

  await chart.setTimeframe({ timeframe: '1' });
  // 500 is the live-chart hard cap (MAX_OHLCV_BARS in core/data.js) — as many 1-min bars as the
  // API will give us in one call, ~8h20m of coverage. That reaches back to 4:00am premarket only
  // for scans run before ~12:20pm NY; later in the gate window the premarket edge gets clipped
  // (flagged via data_gap below rather than silently returning a wrong/null pmh).
  const intradayRaw = await data.getOhlcv({ count: 500 });
  const minuteBars = intradayRaw.bars.filter((b) => nyParts(b.time * 1000).dateStr === todayDateStr);
  const forming1m = minuteBars.length ? minuteBars[minuteBars.length - 1] : null;
  const settled1m = forming1m ? minuteBars.slice(0, -1) : minuteBars;

  const premarketBars = settled1m.filter((b) => {
    const m = nyParts(b.time * 1000).minuteOfDay;
    return m >= PREMARKET_START_MIN && m < REGULAR_OPEN_MIN;
  });
  const regularBars = settled1m.filter((b) => nyParts(b.time * 1000).minuteOfDay >= REGULAR_OPEN_MIN);

  const earliestMinute = settled1m.length ? nyParts(settled1m[0].time * 1000).minuteOfDay : null;
  const data_gap = earliestMinute != null && earliestMinute > PREMARKET_START_MIN
    ? `1-min history only reaches back to ${String(Math.floor(earliestMinute / 60)).padStart(2, '0')}:${String(earliestMinute % 60).padStart(2, '0')} ET today (500-bar cap) — premarket window (04:00-09:30) may be partially or fully missed.`
    : null;

  const pmh = premarketBars.length ? Math.max(...premarketBars.map((b) => b.high)) : null;
  const today_hod = regularBars.length ? Math.max(...regularBars.map((b) => b.high)) : null;

  const daily_breakout = curr_px > prev_daily_high && prev_daily_close > sma200;
  const intraday_breakout = pmh != null && today_hod != null && curr_px > pmh && curr_px > today_hod;

  let result, reason;
  if (!daily_breakout) {
    result = 'fail_daily';
    reason = curr_px <= prev_daily_high
      ? `price ${curr_px} has not broken prior daily high ${prev_daily_high}`
      : `prior close ${prev_daily_close} is below SMA200 ${sma200.toFixed(2)} (not in an uptrend)`;
  } else if (!intraday_breakout) {
    result = 'fail_intraday';
    reason = pmh == null || today_hod == null
      ? 'no premarket or regular-session 1-min bars found for today yet'
      : curr_px <= pmh
        ? `price ${curr_px} has not broken premarket high ${pmh}`
        : `price ${curr_px} has not broken today's high-so-far ${today_hod}`;
  } else {
    result = 'PASS';
    reason = `broke prior daily high (${prev_daily_high}) with close above SMA200, and broke both premarket high (${pmh}) and today's high (${today_hod})`;
  }

  return {
    symbol, curr_px, prev_daily_high, prev_daily_close, sma200: Math.round(sma200 * 100) / 100,
    pmh, today_hod, daily_breakout, intraday_breakout, result, reason,
    ...(data_gap && { data_gap }),
  };
}

export async function runTrendJoinLong({ override_time_gate = false, symbols: symbolsOverride } = {}) {
  const nowMs = Date.now();

  // PREREQ — do not proceed on a dead CDP connection.
  let health_check;
  try {
    health_check = await health.healthCheck();
  } catch (err) {
    return {
      success: false, stage: 'prereq',
      error: `TradingView CDP connection not available: ${err.message}`,
      hint: 'Launch TradingView with: open -a TradingView --args --remote-debugging-port=9222 — then confirm before I proceed.',
    };
  }
  if (!health_check.cdp_connected || !health_check.api_available) {
    return {
      success: false, stage: 'prereq',
      error: 'TradingView is running but the chart API is not available yet.',
      hint: 'Launch TradingView with: open -a TradingView --args --remote-debugging-port=9222 — then confirm before I proceed.',
      health_check,
    };
  }

  // TIME GATE — save an error JSON and exit cleanly rather than scanning outside the window.
  const gate = checkTimeGate(nowMs);
  if (!gate.pass && !override_time_gate) {
    const outPath = outputFilename(nowMs);
    const errorDoc = {
      scanned_at: new Date(nowMs).toISOString(),
      success: false,
      error: 'time_gate_closed',
      message: `Trend Join Long only runs 10:00am–03:30pm New York time, Mon–Fri. Current NY time: ${gate.ny_time}.`,
      candidates_checked: 0, hits: [], all_results: [],
    };
    writeJson(outPath, errorDoc);
    return { success: false, stage: 'time_gate', ...errorDoc, saved_to: outPath };
  }

  const symbols = symbolsOverride?.length ? symbolsOverride.map((s) => s.toUpperCase()) : readWatchlist();
  if (symbols.length === 0) {
    return { success: false, stage: 'watchlist', error: 'No enabled tickers in data/tjl_watchlist.json.' };
  }

  const { dateStr: todayDateStr } = nyParts(nowMs);
  const all_results = [];
  const hits = [];
  const details = [];

  // Sequential by design — one ticker's chart state must settle before the next.
  for (const symbol of symbols) {
    try {
      const r = await analyzeTicker(symbol, nowMs, todayDateStr);
      if (r.error) {
        all_results.push({ symbol, result: 'error' });
        details.push(r);
        continue;
      }
      all_results.push({ symbol: r.symbol, result: r.result });
      details.push(r);
      if (r.result === 'PASS') {
        hits.push({
          symbol: r.symbol, curr_price: r.curr_px, prev_daily_high: r.prev_daily_high,
          sma200: r.sma200, pmh: r.pmh, today_hod: r.today_hod,
        });
      }
    } catch (err) {
      all_results.push({ symbol, result: 'error' });
      details.push({ symbol, error: err.message });
    }
  }

  const outDoc = {
    scanned_at: new Date(nowMs).toISOString(),
    candidates_checked: symbols.length,
    hits,
    all_results,
  };
  const outPath = outputFilename(nowMs);
  writeJson(outPath, outDoc);

  return { success: true, ...outDoc, details, saved_to: outPath, gate_override_used: gate.pass ? false : override_time_gate };
}
