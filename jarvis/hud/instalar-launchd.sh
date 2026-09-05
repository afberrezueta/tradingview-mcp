#!/usr/bin/env bash
# Instala un agente de launchd que regenera el HUD cada 10 minutos y al iniciar
# sesión, sin cron ni permisos especiales. El HUD abierto se recarga solo, así
# que la pantalla queda viva. Para quitarlo:
#   launchctl unload ~/Library/LaunchAgents/com.jarvis.hud.plist && rm ~/Library/LaunchAgents/com.jarvis.hud.plist
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
RAIZ="$(cd "$DIR/.." && pwd)"
PY="$(command -v python3)"
PLIST="$HOME/Library/LaunchAgents/com.jarvis.hud.plist"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.jarvis.hud</string>
  <key>ProgramArguments</key>
  <array><string>$PY</string><string>$RAIZ/hud/generar.py</string></array>
  <key>WorkingDirectory</key><string>$RAIZ</string>
  <key>RunAtLoad</key><true/>
  <key>StartInterval</key><integer>600</integer>
  <key>StandardOutPath</key><string>$RAIZ/hud/generar.log</string>
  <key>StandardErrorPath</key><string>$RAIZ/hud/generar.log</string>
</dict>
</plist>
PLIST
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "Instalado: $PLIST"
echo "El HUD se regenera ahora, cada 10 minutos y al iniciar sesión. Log: $RAIZ/hud/generar.log"
