/**
 * Read-only mode for the MCP server.
 *
 * When TV_MCP_READONLY is set (1/true/yes/on), tools that persist changes,
 * place replay trades, or drive arbitrary UI/JS are NOT registered, so the
 * connected agent cannot call them at all. Chart navigation (symbol, timeframe,
 * indicators, replay stepping, screenshots) stays available because it only
 * changes the view, not the account or TradingView cloud state.
 */

export const WRITE_TOOLS = Object.freeze([
  // Persist to TradingView cloud / layout
  'alert_create', 'alert_delete',
  'draw_shape', 'draw_clear', 'draw_remove_one',
  'layout_new',
  'pine_save', 'pine_new',
  'watchlist_add', 'watchlist_add_bulk', 'watchlist_remove',
  // Trading semantics (even in replay)
  'replay_trade',
  // Arbitrary UI / JS execution
  'ui_evaluate', 'ui_click', 'ui_mouse_click', 'ui_keyboard', 'ui_type_text',
  // Self-modification
  'tv_update',
]);

const WRITE_SET = new Set(WRITE_TOOLS);
const TRUTHY = new Set(['1', 'true', 'yes', 'on']);

export function isReadOnly(env = process.env) {
  const raw = env.TV_MCP_READONLY;
  return typeof raw === 'string' && TRUTHY.has(raw.trim().toLowerCase());
}

export function isWriteTool(name) {
  return WRITE_SET.has(name);
}

/**
 * Wrap server.tool so write tools are skipped instead of registered.
 * Returns the list of tool names that were skipped.
 */
export function installReadOnlyGuard(server) {
  const skipped = [];
  const originalTool = server.tool.bind(server);
  server.tool = (name, ...rest) => {
    if (isWriteTool(name)) {
      skipped.push(name);
      return undefined;
    }
    return originalTool(name, ...rest);
  };
  return skipped;
}
