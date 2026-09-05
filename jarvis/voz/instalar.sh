#!/usr/bin/env bash
# Instala la voz local de JARVIS en el Mac mini.
# Todo corre offline. El audio nunca sale de la máquina.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODELOS="$DIR/modelos"

echo "→ Verificando Homebrew…"
if ! command -v brew >/dev/null 2>&1; then
  echo "   Homebrew no está instalado. Instálalo primero:"
  echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
  exit 1
fi

echo "→ Instalando whisper-cpp (transcripción local) y sox (grabación)…"
brew list whisper-cpp >/dev/null 2>&1 || brew install whisper-cpp
brew list sox         >/dev/null 2>&1 || brew install sox

echo "→ Descargando el modelo de whisper…"
mkdir -p "$MODELOS"
# base = rápido y suficiente para español. Si quieres más precisión a costa de
# velocidad, cambia base por small y actualiza MODELO en escuchar.sh.
MODELO_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin"
DEST="$MODELOS/ggml-base.bin"
MIN=100000000   # ~148 MB reales; menos que esto es una descarga a medias
if [ -f "$DEST" ] && [ "$(wc -c < "$DEST" | tr -d ' ')" -ge "$MIN" ]; then
  echo "   Ya estaba descargado."
else
  # Se baja a .part y se renombra al final: un Ctrl-C no deja un modelo roto
  # que luego pase por "ya descargado".
  rm -f "$DEST"
  curl -L --fail -o "$DEST.part" "$MODELO_URL"
  if [ "$(wc -c < "$DEST.part" | tr -d ' ')" -ge "$MIN" ]; then
    mv "$DEST.part" "$DEST"
  else
    echo "   Descarga incompleta ($(wc -c < "$DEST.part" | tr -d ' ') bytes). Vuelve a correr este script." >&2
    rm -f "$DEST.part"; exit 1
  fi
fi

echo "→ Verificando el binario de whisper…"
if   command -v whisper-cli >/dev/null 2>&1; then BIN=whisper-cli
elif command -v whisper-cpp >/dev/null 2>&1; then BIN=whisper-cpp
else
  echo "   No encontré whisper-cli ni whisper-cpp en el PATH."
  echo "   Revisa la salida de: brew info whisper-cpp"
  exit 1
fi
echo "   Usando: $BIN"

echo "→ Voces de TTS en español disponibles:"
say -v '?' 2>/dev/null | grep -iE 'es_(MX|ES|AR|US)' || \
  echo "   Ninguna instalada. Ajustes → Accesibilidad → Contenido hablado → Voz del sistema → Administrar voces."

chmod +x "$DIR"/*.sh

echo
echo "Listo. Prueba:"
echo "  $DIR/hablar.sh 'Sistema en línea'"
echo "  $DIR/escuchar.sh"
