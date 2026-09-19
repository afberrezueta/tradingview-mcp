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

# Elige una voz en español si no hay una configurada. Cada pipeline lleva
# '|| true': con 'set -e', un grep sin coincidencias mataría el script antes
# de hablar y el fallback de abajo sería código muerto.
# El nombre se toma completo hasta la columna del idioma ("Mónica (Enhanced)"),
# no solo la primera palabra: en macOS moderno los nombres llevan espacios.
if [ -n "${JARVIS_VOZ:-}" ]; then
  VOZ="$JARVIS_VOZ"
else
  LISTA="$(say -v '?' 2>/dev/null | grep -E '[[:space:]]es_(MX|ES|AR|US|CL|CO)[[:space:]]' || true)"
  # Primero las voces clásicas; si no hay, la primera en español que exista.
  VOZ="$(printf '%s\n' "$LISTA" | grep -E '^(Paulina|Mónica|Monica|Jorge|Juan|Diego|Angélica|Angelica|Carlos|Soledad|Francisca|Isabela)' | head -1 | sed -E 's/[[:space:]]+es_[A-Z]{2}[[:space:]].*$//' || true)"
  [ -n "$VOZ" ] || VOZ="$(printf '%s\n' "$LISTA" | head -1 | sed -E 's/[[:space:]]+es_[A-Z]{2}[[:space:]].*$//' || true)"
fi

TEXTO="${*:-}"
# Solo lee stdin si de verdad viene por tubería; con un argumento vacío y una
# terminal como stdin, 'cat' se quedaría esperando para siempre.
if [ -z "$TEXTO" ] && [ ! -t 0 ]; then
  TEXTO="$(cat || true)"
fi
[ -n "${TEXTO// /}" ] || exit 0

# Limpia markdown para que no lea asteriscos, backticks ni URLs completas.
TEXTO="$(printf '%s' "$TEXTO" \
  | sed -E 's/https?:\/\/[^ ]*/enlace/g' \
  | sed -E 's/`([^`]*)`/\1/g' \
  | sed -E 's/\*\*([^*]*)\*\*/\1/g' \
  | sed -E 's/^#+ //g' \
  | sed -E 's/^[-*] /, /g' \
  | tr '\n' ' ')"

# Si la voz configurada no existe ("Voice not found"), habla con la del sistema.
if [ -n "$VOZ" ]; then
  say -v "$VOZ" -r "$VELOCIDAD" "$TEXTO" 2>/dev/null || say -r "$VELOCIDAD" "$TEXTO"
else
  say -r "$VELOCIDAD" "$TEXTO"
fi
