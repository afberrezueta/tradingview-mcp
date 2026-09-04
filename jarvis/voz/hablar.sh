#!/usr/bin/env bash
# TTS local con la voz del sistema de macOS. Sin API, sin red.
#
#   ./hablar.sh "texto"
#   echo "texto" | ./hablar.sh
#
# Voz configurable:  export JARVIS_VOZ="Paulina"
# Velocidad:         export JARVIS_VELOCIDAD=190
set -euo pipefail

VELOCIDAD="${JARVIS_VELOCIDAD:-185}"

# Elige la primera voz en español disponible si no hay una configurada.
if [ -n "${JARVIS_VOZ:-}" ]; then
  VOZ="$JARVIS_VOZ"
else
  VOZ="$(say -v '?' 2>/dev/null | grep -iE 'es_(MX|ES|AR|US)' | head -1 | awk '{print $1}')"
fi

TEXTO="${*:-}"
[ -z "$TEXTO" ] && TEXTO="$(cat)"

# Limpia markdown para que no lea asteriscos, backticks ni URLs completas.
TEXTO="$(printf '%s' "$TEXTO" \
  | sed -E 's/https?:\/\/[^ ]*/enlace/g' \
  | sed -E 's/`([^`]*)`/\1/g' \
  | sed -E 's/\*\*([^*]*)\*\*/\1/g' \
  | sed -E 's/^#+ //g' \
  | sed -E 's/^[-*] /, /g' \
  | tr '\n' ' ')"

if [ -n "$VOZ" ]; then
  say -v "$VOZ" -r "$VELOCIDAD" "$TEXTO"
else
  say -r "$VELOCIDAD" "$TEXTO"
fi
