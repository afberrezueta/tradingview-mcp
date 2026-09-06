#!/usr/bin/env bash
# Doble clic en Finder: regenera el HUD con la bóveda actual y lo abre.
# Si hay Google Chrome, lo abre en ventana propia (modo app, sin barra de
# direcciones), que es lo que mejor queda a pantalla completa (ctrl+cmd+F).
# Con JARVIS_HUD_APP=0 usa el navegador por defecto.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR/.."
if ! python3 hud/generar.py; then
  echo
  echo "python3 falló. Si macOS pidió instalar herramientas, corre: xcode-select --install"
  read -r -p "Enter para cerrar" _
  exit 1
fi
HUD="$DIR/hud.html"
if [ "${JARVIS_HUD_APP:-1}" = "1" ] && [ -d "/Applications/Google Chrome.app" ]; then
  open -na "Google Chrome" --args --app="file://$HUD" --window-size=1500,900
else
  open "$HUD"
fi
