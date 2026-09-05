# mi-trader-bot MCP

Servidor MCP (stdio) que expone los motores de `mi_trader_bot` como herramientas
usables desde cualquier sesión de Claude: zonas de acumulación de ETH, señales
Donchian (motor Agentic) y TJL v2, backtests sobre los CSVs de 10 años, estado
de los scans y envío a Telegram. **No ejecuta órdenes en ningún broker** — la
ejecución sigue siendo de `agentic_scan.sh` / `eth_scan.sh` en la cuenta Agentic.

## Registro (en tu Mac)

```bash
claude mcp add mi-trader-bot --scope user -- node "$(pwd)/mi_trader_bot/mcp/server.js"
```

(Ejecutar desde la raíz del repo clonado; `--scope user` para que esté
disponible en cualquier directorio.)

## Herramientas

| Tool | Qué hace |
|---|---|
| `bot_eth_zones` | Escalera de tramos ETH: swing high 90d, drawdown, precio/importe/estado por tramo. Pasa `current_price` con el precio vivo para precisión. |
| `bot_donchian_signal` | Señal del motor Agentic para un símbolo: ruptura Donchian(20), ATR14, stop, régimen TQQQ/SOXL, sizing opcional. |
| `bot_tjl_signal` | Señal TJL v2 aproximada a diario, con los 4 filtros desglosados (los filtros intradía del TJL real no se evalúan). |
| `bot_backtest` | Backtest de cartera del motor `agentic` o `tjl`; universo/riesgo configurables. Sin breakers ni slippage — para comparar motores. |
| `bot_scan_status` | Últimos reportes de `agentic_scan`/`eth_scan`, colas de logs y `eth_state.json`. |
| `bot_list_symbols` | Símbolos con CSV disponible. |
| `bot_telegram_send` | Envía un mensaje al Telegram del bot (única herramienta con efecto externo). |

## Rutas

- `MI_TRADER_BOT_DIR` — carpeta del bot (default `~/Documents/mi_trader_bot`): config, `.env`, `out/`.
- `MI_TRADER_DATA_DIR` — CSVs diarios (default `<repo>/data/historical_10y`, con fallback a `$MI_TRADER_BOT_DIR/data/historical_10y`).

## Evaluación

`evaluation.xml` contiene 10 preguntas de solo lectura con respuestas verificadas
contra los CSVs congelados (hasta 2026-08-28). Si regeneras los CSVs, las
respuestas dejan de ser válidas.
