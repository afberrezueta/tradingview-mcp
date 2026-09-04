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
if [ ! -f "$MODELOS/ggml-base.bin" ]; then
  curl -L --fail -o "$MODELOS/ggml-base.bin" "$MODELO_URL"
else
  echo "   Ya estaba descargado."
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
