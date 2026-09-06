#!/bin/bash
# Instalador del escaneo diario Agentic (ejecutar EN TU MAC, no en cloud).
# Automatiza: carpeta out/, copia de archivos, registro del MCP robinhood-trading,
# detección del .env con las vars de Telegram, prueba única y alta en crontab.
#
# Uso:  ./install_agentic_scan.sh            (instala + ejecuta una prueba + crontab)
#       ./install_agentic_scan.sh --no-run   (instala sin ejecutar el escaneo)
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
BOT_DIR="$HOME/Documents/mi_trader_bot"
CRON_LINE="45 9 * * 1-5 \$HOME/Documents/mi_trader_bot/agentic_scan.sh"

echo "==> 1/6 Creando $BOT_DIR/out"
mkdir -p "$BOT_DIR/out"

echo "==> 2/6 Copiando agentic_scan_prompt.md y agentic_scan.sh"
cp "$SRC_DIR/agentic_scan_prompt.md" "$BOT_DIR/agentic_scan_prompt.md"
cp "$SRC_DIR/agentic_scan.sh" "$BOT_DIR/agentic_scan.sh"
chmod +x "$BOT_DIR/agentic_scan.sh"

echo "==> 3/6 Buscando TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID en el proyecto"
if [ ! -f "$BOT_DIR/.env" ] || ! grep -q '^\(export \)\?TELEGRAM_BOT_TOKEN=' "$BOT_DIR/.env"; then
  FOUND="$(grep -rl --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=venv \
      --exclude-dir=.git --exclude-dir=out --include='*.env' --include='.env*' --include='*.sh' \
      'TELEGRAM_BOT_TOKEN=' "$BOT_DIR" 2>/dev/null | head -1 || true)"
  if [ -n "$FOUND" ]; then
    echo "    Vars encontradas en: $FOUND → copiando a $BOT_DIR/.env"
    grep -h '^\(export \)\?TELEGRAM_\(BOT_TOKEN\|CHAT_ID\)=' "$FOUND" >> "$BOT_DIR/.env"
  else
    echo "    ERROR: no encontré TELEGRAM_BOT_TOKEN en $BOT_DIR."
    echo "    Crea $BOT_DIR/.env con TELEGRAM_BOT_TOKEN=... y TELEGRAM_CHAT_ID=... y reintenta."
    exit 1
  fi
fi
echo "    OK: $BOT_DIR/.env tiene las variables."

echo "==> 4/6 Verificando MCP robinhood-trading"
if claude mcp list 2>/dev/null | grep -q 'robinhood-trading'; then
  echo "    Ya registrado."
else
  echo "    Registrando (scope user, para que funcione desde cron en cualquier directorio)..."
  claude mcp add robinhood-trading --scope user --transport http https://agent.robinhood.com/mcp/trading
  echo "    IMPORTANTE: abre 'claude' una vez y autentica el servidor con /mcp antes de la prueba."
fi

if [ "${1:-}" = "--no-run" ]; then
  echo "==> 5/6 Omitida la ejecución de prueba (--no-run). No se instala el crontab."
  echo "    Cuando quieras: $BOT_DIR/agentic_scan.sh && ./install_agentic_scan.sh"
  exit 0
fi

echo "==> 5/6 Ejecutando una prueba: $BOT_DIR/agentic_scan.sh"
if "$BOT_DIR/agentic_scan.sh"; then
  echo "    --- LOG (out/agentic_scan.log) ---"
  cat "$BOT_DIR/out/agentic_scan.log"
  echo "    --- MENSAJE ENVIADO A TELEGRAM (out/agentic_scan.txt) ---"
  cat "$BOT_DIR/out/agentic_scan.txt"
else
  echo "    ERROR: la prueba falló. Revisa $BOT_DIR/out/agentic_scan.log. No se instala el crontab."
  exit 1
fi

echo "==> 6/6 Instalando crontab (L-V 9:45)"
( crontab -l 2>/dev/null | grep -v 'agentic_scan\.sh' || true; echo "$CRON_LINE" ) | crontab -
echo "    crontab actual:"
crontab -l
echo
echo "Listo. Nota macOS: si cron no puede leer ~/Documents, da 'Acceso total al disco'"
echo "a /usr/sbin/cron en Ajustes → Privacidad y seguridad → Acceso total al disco."
