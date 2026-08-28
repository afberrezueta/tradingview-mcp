import { z } from 'zod';
import { jsonResult } from './_format.js';
import * as core from '../core/historical.js';

export function registerHistoricalTools(server) {
  server.tool('historical_list_symbols', 'List symbols available in the local 10-year daily historical dataset (CSV files, independent of the live TradingView connection — works even if TradingView/CDP is not running). Returns each symbol\'s row count and date coverage. Call this first.', {}, async () => {
    try { return jsonResult(await core.listHistoricalSymbols()); }
    catch (err) { return jsonResult({ success: false, error: err.message }, true); }
  });

  server.tool('historical_get_ohlcv', 'Get daily OHLCV bars from the local 10-year historical dataset (not the live chart — works without a TradingView/CDP connection). Use for backtesting or longer-range stats beyond the ~500-bar live cap. ALWAYS pass summary=true unless you need individual bars.', {
    symbol: z.string().describe('Symbol, e.g. "NVDA", "SPY", "ETHUSD". Call historical_list_symbols for the full list.'),
    count: z.coerce.number().optional().describe('Number of most recent daily bars to return (default 100). Ignored if start_date/end_date given.'),
    start_date: z.string().optional().describe('ISO date (YYYY-MM-DD), inclusive. If set (with or without end_date), overrides count.'),
    end_date: z.string().optional().describe('ISO date (YYYY-MM-DD), inclusive. Defaults to the latest available date.'),
    summary: z.coerce.boolean().optional().describe('Return summary stats (high, low, open, close, change%, avg volume, last 5 bars) instead of all bars — much smaller output'),
  }, async ({ symbol, count, start_date, end_date, summary }) => {
    try { return jsonResult(await core.getHistoricalOhlcv({ symbol, count, start_date, end_date, summary })); }
    catch (err) { return jsonResult({ success: false, error: err.message }, true); }
  });
}
