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

  # --continue mantiene el hilo entre turnos. En modo -p no hay quien apruebe
  # permisos: sin --permission-mode, toda escritura en la bóveda se deniega y
  # las skills solo podrían leer. acceptEdits permite editar archivos del
  # proyecto; los comandos de lectura que usan las skills van en allowedTools.
  # El candado de órdenes de Robinhood (.claude/settings.json) sigue aplicando.
  # Errores a voz/jarvis.log en vez de /dev/null, para poder diagnosticar.
  OPCIONES=(--permission-mode acceptEdits
            --allowedTools "Bash(date:*),Bash(ls:*),Bash(grep:*),Bash(find:*),Bash(cat:*),Bash(head:*),Bash(tail:*)")
  RESPUESTA="$(claude -p "$PREGUNTA" --continue "${OPCIONES[@]}" 2>>"$DIR/jarvis.log" \
            || claude -p "$PREGUNTA" "${OPCIONES[@]}" 2>>"$DIR/jarvis.log" || true)"

  printf '%s\n' "$RESPUESTA"

  # Lee en voz alta solo los primeros ~600 caracteres; el resto queda en pantalla.
  # Corte por caracteres con expansión de bash (respeta UTF-8), no por bytes:
  # 'head -c' podía partir una tilde y, con pipefail, tumbar el bucle.
  # '|| true': que un fallo de la voz no termine la sesión.
  if [ -n "${RESPUESTA// /}" ]; then
    "$DIR/hablar.sh" "${RESPUESTA:0:600}" || true
  fi
done
