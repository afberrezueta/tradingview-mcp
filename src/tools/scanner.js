import { z } from 'zod';
import { jsonResult } from './_format.js';
import * as core from '../core/scanner.js';

export function registerScannerTools(server) {
  server.tool(
    'scanner_run_tjl',
    'Run the Trend Join Long day-trading scanner over the watchlist in data/tjl_watchlist.json (edit that file to enable/disable/add tickers — no restart needed). Sequentially drives the live chart per ticker (chart_set_symbol → daily OHLCV → quote → 1-min OHLCV) to test: daily_breakout (price > prior daily high AND prior close > SMA200) AND intraday_breakout (price > premarket high AND price > today\'s high-so-far). Requires TradingView running with CDP, and only runs 10:00am-3:30pm New York time (otherwise saves an error JSON and exits). Saves results to ./tjl_watchlist_YYYY-MM-DD_HHMMET.json. The result includes a `notify` object ({should_notify, notify_reason, new_hit_symbols}) for callers running this on a schedule: should_notify is true only on the first run of the calendar day, a genuinely new PASS vs. the last run, or the first CDP/prereq failure of the day — everything else (repeat non-hits, repeat known hits, repeat failures same day) is should_notify:false. When should_notify is true, use the PushNotification tool to alert the user; otherwise stay silent.',
    {
      symbols: z.array(z.string()).optional().describe('Override the watchlist file with an explicit ticker list for this run only (e.g. for a quick ad-hoc test). Omit to use the enabled tickers in data/tjl_watchlist.json.'),
      override_time_gate: z.coerce.boolean().optional().describe('Bypass the 10am-3:30pm NY time gate — for testing/demo only, never for real entries outside market hours.'),
    },
    async ({ symbols, override_time_gate }) => {
      try { return jsonResult(await core.runTrendJoinLong({ symbols, override_time_gate })); }
      catch (err) { return jsonResult({ success: false, error: err.message }, true); }
    }
  );
}
