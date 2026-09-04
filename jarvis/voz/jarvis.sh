#!/usr/bin/env bash
# El bucle completo: escuchas → Claude Code responde → lo dice en voz alta.
#
#   ./jarvis.sh
#
# Cada turno: Enter para grabar, Enter para parar. Ctrl-C para salir.
# Requiere el CLI de Claude Code en el PATH.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAIZ="$(dirname "$DIR")"

command -v claude >/dev/null 2>&1 || { echo "El CLI 'claude' no está en el PATH." >&2; exit 1; }

cd "$RAIZ"   # importante: Claude Code lee CLAUDE.md y las skills desde aquí

"$DIR/hablar.sh" "Sistema en línea." || true

while true; do
  printf '\n\033[2m[Enter para hablar · Ctrl-C para salir]\033[0m ' >&2
  read -r < /dev/tty || break

  PREGUNTA="$("$DIR/escuchar.sh")" || continue
  [ -n "${PREGUNTA// /}" ] || continue

  printf '\033[1m› %s\033[0m\n' "$PREGUNTA"

  # --continue mantiene el hilo entre turnos.
  RESPUESTA="$(claude -p "$PREGUNTA" --continue 2>/dev/null || claude -p "$PREGUNTA")"

  printf '%s\n' "$RESPUESTA"

  # Lee en voz alta solo los primeros ~600 caracteres; el resto queda en pantalla.
  printf '%s' "$RESPUESTA" | head -c 600 | iconv -c -f UTF-8 -t UTF-8 | "$DIR/hablar.sh"
done
