#!/bin/bash
# Escaneo diario Robinhood Agentic → Telegram (MODO AUTÓNOMO)
# Uso: crontab -e  →  45 9 * * 1-5 /Users/TU_USUARIO/Documents/mi_trader_bot/agentic_scan.sh
set -e
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

BOT_DIR="$HOME/Documents/mi_trader_bot"
mkdir -p "$BOT_DIR/out"

# Carga TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID desde el .env del proyecto mi_trader_bot
ENV_FILE="$BOT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi
if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
  echo "ERROR: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID no definidas (esperadas en $ENV_FILE)" >&2
  exit 1
fi

# Ejecuta Claude Code en modo headless con el MCP de Robinhood ya registrado
claude -p "$(cat "$BOT_DIR/agentic_scan_prompt.md")" \
  --allowedTools "mcp__robinhood-trading__*" \
  --max-turns 40 --dangerously-skip-permissions \
  > "$BOT_DIR/out/agentic_scan.log" 2>&1

# Envía el resultado por Telegram (usa las mismas vars que mi_trader_bot)
MSG=$(cat "$BOT_DIR/out/agentic_scan.txt")
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d chat_id="${TELEGRAM_CHAT_ID}" \
  --data-urlencode text="$MSG" > /dev/null
