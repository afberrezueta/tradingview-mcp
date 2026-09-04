#!/usr/bin/env bash
# STT local: graba hasta que presiones Enter, transcribe con whisper.cpp,
# imprime el texto y lo guarda en boveda/raw/.
#
# El audio nunca sale de esta máquina. Sin API, sin latencia de red.
#
#   ./escuchar.sh              -> transcribe e imprime
#   ./escuchar.sh --sin-guardar -> no escribe en la bóveda
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAIZ="$(dirname "$DIR")"
MODELO="$DIR/modelos/ggml-base.bin"
IDIOMA="${JARVIS_IDIOMA:-es}"
GUARDAR=1
[ "${1:-}" = "--sin-guardar" ] && GUARDAR=0

if   command -v whisper-cli >/dev/null 2>&1; then WHISPER=whisper-cli
elif command -v whisper-cpp >/dev/null 2>&1; then WHISPER=whisper-cpp
else echo "whisper no instalado. Corre: $DIR/instalar.sh" >&2; exit 1; fi

[ -f "$MODELO" ] || { echo "Falta el modelo. Corre: $DIR/instalar.sh" >&2; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
WAV="$TMP/audio.wav"

echo "🎙  Grabando… presiona Enter para terminar." >&2
# 16 kHz mono es lo que whisper.cpp espera.
rec -q -r 16000 -c 1 -b 16 "$WAV" >/dev/null 2>&1 &
REC_PID=$!
read -r < /dev/tty || true
kill -INT "$REC_PID" 2>/dev/null || true   # SIGINT: sox cierra la cabecera del WAV
wait "$REC_PID" 2>/dev/null || true

[ -s "$WAV" ] || { echo "No se grabó audio. ¿Diste permiso de micrófono a la Terminal?" >&2; exit 1; }

echo "⏳ Transcribiendo…" >&2
TEXTO="$("$WHISPER" -m "$MODELO" -f "$WAV" -l "$IDIOMA" --no-timestamps --output-txt --output-file "$TMP/out" 2>/dev/null; cat "$TMP/out.txt" 2>/dev/null)"
# '|| true': con pipefail, si grep filtra todo (solo [BLANK_AUDIO]) el pipeline
# devuelve 1 y set -e mataría el script antes del mensaje de silencio.
TEXTO="$(echo "$TEXTO" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | grep -v '^\[.*\]$' | tr '\n' ' ' | sed 's/  */ /g' || true)"

[ -n "${TEXTO// /}" ] || { echo "Silencio — nada que transcribir." >&2; exit 0; }

echo "$TEXTO"

if [ "$GUARDAR" = "1" ]; then
  FECHA="$(date +%F)"
  ARCHIVO="$RAIZ/boveda/raw/${FECHA}-voz.md"
  if [ ! -f "$ARCHIVO" ]; then
    cat > "$ARCHIVO" <<EOF
---
titulo: Capturas de voz $FECHA
tipo: captura
fecha: $FECHA
tags: [voz]
---

EOF
  fi
  printf '\n## %s\n\n%s\n' "$(date +%H:%M)" "$TEXTO" >> "$ARCHIVO"
  echo "→ guardado en boveda/raw/${FECHA}-voz.md" >&2
fi
