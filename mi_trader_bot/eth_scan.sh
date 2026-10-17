#!/bin/bash
# Acumulación diaria de ETH (cuenta Agentic) → Telegram
# Crontab sugerido (tras probarlo a mano):  50 9 * * 1-5 $HOME/Documents/mi_trader_bot/eth_scan.sh
set -e
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

BOT_DIR="$HOME/Documents/mi_trader_bot"
mkdir -p "$BOT_DIR/out"

# Carga TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID (mismo .env que agentic_scan.sh)
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

# Necesita el MCP robinhood-trading (scope user) y acceso de lectura al CSV/config/estado
claude -p "$(cat "$BOT_DIR/eth_scan_prompt.md")" \
  --allowedTools "mcp__robinhood-trading__*,Read,Write" \
  --max-turns 30 --dangerously-skip-permissions \
  > "$BOT_DIR/out/eth_scan.log" 2>&1

MSG=$(cat "$BOT_DIR/out/eth_scan.txt")
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d chat_id="${TELEGRAM_CHAT_ID}" \
  --data-urlencode text="$MSG" > /dev/null
