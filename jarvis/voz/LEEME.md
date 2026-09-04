# Voz local

Todo corre en el Mac mini. **El audio nunca sale de la máquina**: sin API, sin
costo por uso, sin latencia de red.

| Pieza | Qué usa |
|---|---|
| STT (te escucha) | `whisper.cpp`, modelo `ggml-base` (multilingüe, ~148 MB) |
| Grabación | `sox` |
| TTS (te responde) | `say` — voz del sistema de macOS, ya viene instalada |

## Instalar

```bash
cd voz && ./instalar.sh
```

Toma unos 5 minutos: instala `whisper-cpp` y `sox` por Homebrew y baja el modelo.

Después, **dale permiso de micrófono a la Terminal**: Ajustes del Sistema →
Privacidad y seguridad → Micrófono → activa Terminal (o iTerm). Sin esto la
grabación sale vacía y no hay mensaje de error obvio.

## Usar

```bash
./hablar.sh "Sistema en línea"    # prueba el TTS
./escuchar.sh                     # graba, transcribe, guarda en boveda/raw/
./jarvis.sh                       # el bucle completo: hablas → Claude responde en voz
```

En `escuchar.sh` y `jarvis.sh`: Enter empieza a grabar, Enter termina.

## Ajustes

```bash
export JARVIS_VOZ="Paulina"      # ver opciones con:  say -v '?'
# En macOS moderno los nombres llevan espacios: usa comillas y el nombre
# completo tal como aparece en la lista, p. ej. JARVIS_VOZ="Mónica (Enhanced)".
export JARVIS_VELOCIDAD=185      # palabras por minuto
export JARVIS_IDIOMA=es          # o 'en'
```

Ponlos en tu `~/.zshrc` para que queden fijos.

## Si algo no funciona

**"No se grabó audio"** — falta el permiso de micrófono a la Terminal (arriba).

**"whisper falló: …"** — el script muestra las últimas líneas del error real.
Lo más común es un modelo a medio bajar: `./instalar.sh` lo detecta por tamaño
y lo vuelve a descargar.

**`jarvis.sh` responde pero no escribe en la bóveda** — el bucle pasa
`--permission-mode acceptEdits` a `claude -p`; sin eso, en modo no interactivo
toda escritura se deniega. Los errores quedan en `voz/jarvis.log`.

**Transcripción mala en español** — cambia el modelo a `small`. Es ~3× más
lento pero bastante mejor:

```bash
curl -L -o voz/modelos/ggml-small.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin
# luego edita MODELO en escuchar.sh
```

**No hay voces en español** — Ajustes → Accesibilidad → Contenido hablado →
Voz del sistema → Administrar voces → descarga una en español. Las "Premium"
suenan claramente mejor que las básicas.

**`whisper-cli: command not found`** — Homebrew cambió el nombre del binario
entre versiones. Los scripts prueban `whisper-cli` y luego `whisper-cpp`; si
tienes otro nombre, revisa `brew info whisper-cpp` y ajústalo en `escuchar.sh`.

## Nota honesta

El "push-to-talk" real (mantener una tecla) necesita un listener de teclado a
nivel de sistema, que en macOS pide permisos de accesibilidad y complica el
setup. Enter-para-empezar / Enter-para-parar hace el mismo trabajo y se instala
en cinco minutos. Si después quieres el hold-to-talk de verdad, se agrega con
una app pequeña en Swift o con Hammerspoon.
