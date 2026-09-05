#!/usr/bin/env node
// mi-trader-bot MCP — expone los motores de mi_trader_bot como herramientas MCP:
// zonas de acumulación ETH, señales Donchian (Agentic) y TJL, backtests sobre los
// CSVs de 10 años, estado del bot y envío a Telegram.
//
// Registro (scope user, para usarlo desde cualquier sesión de Claude):
//   claude mcp add mi-trader-bot --scope user -- node /ruta/al/repo/mi_trader_bot/mcp/server.js
//
// Rutas configurables por entorno:
//   MI_TRADER_BOT_DIR   (default ~/Documents/mi_trader_bot — config, .env, out/)
//   MI_TRADER_DATA_DIR  (default <repo>/data/historical_10y — CSVs diarios)
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import * as lib from './lib.js';

const server = new McpServer(
  { name: 'mi-trader-bot', version: '1.0.0', description: 'Motores de trading de mi_trader_bot: zonas ETH, señales Donchian/TJL, backtests, estado y Telegram' },
  {
    instructions: `mi-trader-bot MCP — herramientas de análisis del bot de trading personal.

- bot_eth_zones → escalera de tramos de acumulación de ETH (swing high 90d, drawdown, tramo activo). Pasa current_price con el precio vivo de Robinhood/Coinbase para precisión; sin él usa el último cierre del CSV.
- bot_donchian_signal → señal del motor Agentic para un símbolo (ruptura Donchian20, ATR, stop, régimen TQQQ/SOXL, sizing opcional).
- bot_tjl_signal → señal TJL v2 aproximada a diario (ruptura, SMA200, semanal, volumen) con cada filtro desglosado.
- bot_backtest → backtest de cartera de un motor ('agentic' o 'tjl') sobre los CSVs de 10 años; parámetros opcionales de universo y riesgo.
- bot_scan_status → últimos reportes de agentic_scan/eth_scan y estado de tramos ejecutados.
- bot_list_symbols → símbolos con datos históricos disponibles.
- bot_telegram_send → envía un mensaje al Telegram del bot (misma credencial que los scans). ÚSALO solo cuando el usuario pida notificar.

Todo excepto bot_telegram_send es de solo lectura y opera sobre datos locales. Este servidor NO ejecuta órdenes en ningún broker.`,
  },
);

const jsonResult = (obj, isError = false) => ({
  content: [{ type: 'text', text: JSON.stringify(obj, null, 2) }],
  isError,
});
const fail = (err) => jsonResult({ success: false, error: err.message }, true);

server.tool(
  'bot_eth_zones',
  'Calcula la escalera de tramos de acumulación de ETH: swing high de 90 días, drawdown actual, precio objetivo/importe/estado de cada tramo y cuál está activo. Pasa current_price (precio vivo) para precisión; sin él usa el último cierre del CSV local.',
  { current_price: z.coerce.number().positive().optional().describe('Precio actual de ETH-USD (ej. 2452.83). Opcional.') },
  async ({ current_price }) => {
    try { return jsonResult(lib.ethZones({ currentPrice: current_price })); }
    catch (err) { return fail(err); }
  },
);

server.tool(
  'bot_donchian_signal',
  'Señal del motor Agentic para un símbolo: ruptura del canal Donchian(20) diario, posición en el canal, ATR14, stop sugerido (entrada − 1.5×ATR), filtro de régimen TQQQ/SOXL y sizing opcional por riesgo.',
  {
    symbol: z.string().min(1).describe('Ticker con CSV disponible (ej. NVDA, TQQQ). Ver bot_list_symbols.'),
    equity: z.coerce.number().positive().optional().describe('Capital para calcular tamaño de posición. Opcional.'),
    risk_pct: z.coerce.number().min(0.1).max(20).optional().describe('% de capital a arriesgar por trade (default 4).'),
  },
  async ({ symbol, equity, risk_pct }) => {
    try { return jsonResult(lib.donchianSignal(symbol.toUpperCase(), { equity, riskPct: risk_pct })); }
    catch (err) { return fail(err); }
  },
);

server.tool(
  'bot_tjl_signal',
  'Señal TJL v2 (aproximación diaria) para un símbolo, con cada filtro desglosado: ruptura del máximo previo, cierre previo > SMA200, tendencia semanal (SMA20 de cierres semanales) y volumen relativo >1.5×. Incluye stop (1.5×ATR) y objetivo (3×ATR).',
  { symbol: z.string().min(1).describe('Ticker con CSV disponible y 200+ barras (ej. NVDA, SPY).') },
  async ({ symbol }) => {
    try { return jsonResult(lib.tjlSignal(symbol.toUpperCase())); }
    catch (err) { return fail(err); }
  },
);

server.tool(
  'bot_backtest',
  'Backtest de cartera de un motor sobre los CSVs diarios de 10 años. engine="agentic" (Donchian + trailing ATR + parcial 2R, máx 2 posiciones, riesgo 4%) o "tjl" (bracket 1.5/3 ATR, riesgo 1%). Universo y riesgo personalizables. Fills idealizados — usar para comparar motores, no como expectativa.',
  {
    engine: z.enum(['agentic', 'tjl']).describe('Motor a backtestear.'),
    symbols: z.array(z.string()).min(1).optional().describe('Universo personalizado. Default: el universo propio del motor.'),
    risk_pct: z.coerce.number().min(0.1).max(20).optional().describe('% de riesgo por trade. Default: 4 (agentic) / 1 (tjl).'),
    max_positions: z.coerce.number().int().min(1).max(20).optional().describe('Máximo de posiciones simultáneas. Default: 2 (agentic) / sin límite (tjl).'),
  },
  async ({ engine, symbols, risk_pct, max_positions }) => {
    try { return jsonResult(lib.backtest({ engine, symbols: symbols?.map((s) => s.toUpperCase()), risk_pct, max_positions })); }
    catch (err) { return fail(err); }
  },
);

server.tool(
  'bot_scan_status',
  'Últimos reportes generados por los scans del bot (agentic_scan.txt, eth_scan.txt), cola de sus logs y estado de tramos ETH ejecutados (out/eth_state.json).',
  {},
  async () => {
    try { return jsonResult(lib.scanStatus()); }
    catch (err) { return fail(err); }
  },
);

server.tool(
  'bot_list_symbols',
  'Lista los símbolos con CSV histórico diario disponible para señales y backtests.',
  {},
  async () => {
    try { return jsonResult({ success: true, data_dir: lib.dataDir(), symbols: lib.listSymbols() }); }
    catch (err) { return fail(err); }
  },
);

server.tool(
  'bot_telegram_send',
  'Envía un mensaje de texto al chat de Telegram del bot (usa TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID del entorno o del .env del bot). Acción externa: usar solo cuando el usuario pida notificar algo.',
  { message: z.string().min(1).max(4096).describe('Texto del mensaje (máx 4096 caracteres).') },
  async ({ message }) => {
    try { return jsonResult(await lib.telegramSend(message)); }
    catch (err) { return fail(err); }
  },
);

const transport = new StdioServerTransport();
await server.connect(transport);
console.error('[mi-trader-bot] servidor MCP listo (stdio)');
