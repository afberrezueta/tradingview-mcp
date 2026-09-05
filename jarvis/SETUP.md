# Instalación — 20 minutos

Todo esto corre en tu Mac mini. No hay servidor, no hay nube, no hay costo
recurrente más allá de lo que ya pagas por Claude Code.

---

## 0. Requisitos (una vez)

- **Command Line Tools de Apple**: `xcode-select --install`. Sin esto,
  `/usr/bin/python3` es solo un lanzador del instalador y el HUD (y su cron)
  no corren. Comprueba con `python3 -V`.
- **Claude Code CLI** instalado (`claude --version`).
- **Homebrew**, solo si vas a usar la voz (paso 4).

## 1. Poner la carpeta en su lugar (2 min)

Descomprime el zip y muévelo a tu home:

```bash
unzip ~/Downloads/jarvis.zip -d ~/
cd ~/jarvis
```

Verifica que quedó completo:

```bash
ls -R | head -30
```

Deberías ver `CLAUDE.md`, `.claude/skills/`, `.claude/agents/`, `boveda/`, `voz/`, `hud/`.

---

## 2. Probar el cerebro (5 min)

```bash
cd ~/jarvis
claude
```

Claude Code lee `CLAUDE.md` automáticamente al arrancar aquí. Pruébalo:

```
> plan de hoy
```

Debe cargar la skill `plan-hoy`, leer los compromisos de Vantera, y escribir
`boveda/outputs/AAAA-MM-DD-plan.md`.

Prueba también:

```
> qué sabes de vantera
> métricas
```

**Importante:** arranca Claude Code *desde dentro* de `~/jarvis`. Si arrancas
en una carpeta padre, las skills se cargan solo cuando Claude toca un archivo
de `jarvis/`, y los agentes de la mesa y `.claude/settings.json` (el candado
de órdenes) no se cargan en absoluto.

Para que el candado aplique en **cualquier** carpeta, copia el bloque
`permissions.deny` de `.claude/settings.json` a `~/.claude/settings.json`
(scope de usuario). Deja el de proyecto como refuerzo.

Si quieres que las skills estén disponibles en cualquier carpeta, cópialas a tu
scope de usuario:

```bash
cp -R ~/jarvis/.claude/skills/* ~/.claude/skills/
```

Yo no lo haría todavía. Úsalas un par de semanas desde `~/jarvis` primero — vas
a querer editarlas, y es más fácil con una sola copia. Si lo haces, copia
también `.claude/agents/` o la mesa de expertos no tendrá miembros, y ten en
cuenta que `.claude/settings.json` (el bloqueo de órdenes de Robinhood) solo
aplica a sesiones que arrancan dentro de `~/jarvis`.

---

## 3. Generar el HUD (2 min)

```bash
cd ~/jarvis
python3 hud/generar.py
open hud/hud.html
```

Lee la bóveda y escribe un `hud.html` autocontenido con los datos incrustados.
No levanta servidor — se abre directo del disco, así que tus números nunca
salen de la máquina.

Regenéralo cuando quieras ver el estado actualizado. Para que se actualice solo
cada mañana (la primera vez, macOS puede pedir "Acceso total al disco" para
`cron`: Ajustes → Privacidad y seguridad → Acceso total al disco → añade
`/usr/sbin/cron`; revisa `hud/generar.log` al día siguiente):

```bash
crontab -e
# agrega (ruta absoluta y log: si falla, queda rastro en hud/generar.log):
0 7 * * * /usr/bin/python3 "$HOME/jarvis/hud/generar.py" >> "$HOME/jarvis/hud/generar.log" 2>&1
```

Si el cron deja de correr, el HUD lo dice en ámbar en el pie ("HUD
desactualizado: generado hace N h"). Un HUD viejo que parece nuevo es peor que
ninguno.

### Tenerlo en la pantalla, siempre

Dos archivos en `hud/`, para no volver a abrir la Terminal:

1. **`hud/abrir.command`** — doble clic en Finder: regenera el HUD y lo abre
   en una ventana propia (Chrome en modo app si lo tienes; si no, tu
   navegador). Pulsa ctrl+cmd+F para pantalla completa y déjalo ahí: la
   página se recarga sola cada 10 minutos. La primera vez macOS puede decir
   que no puede verificar el archivo: clic derecho → Abrir, una sola vez.
2. **`hud/instalar-launchd.sh`** — córrelo una vez desde la Terminal
   (`bash ~/jarvis/hud/instalar-launchd.sh`): instala un agente de `launchd`
   que regenera el HUD cada 10 minutos y al iniciar sesión, sin cron y sin
   permisos especiales. Con eso, lo que está en la pantalla siempre es lo
   último de la bóveda. Para quitarlo, las dos líneas comentadas al inicio
   del script.

El cron del paso anterior queda como alternativa; no hacen falta los dos.

### Actualizar los números del HUD

Los hitos y el contador de fundadores están al inicio de `hud/generar.py`:

```python
HITOS = [
    ("Stripe + Supabase Auth", date(2026, 9, 8),  None, None),
    ("Miembros fundadores",    date(2026, 9, 30), 0, 5),    # ← sube el 0 cuando cobres
    ("Criterio go/no-go",      date(2026, 12, 1), 0, 50),
]
```

Cuando llegue el primer cliente pagando, cambia ese `0` por `1`. Ese es el
número que manda en todo el sistema.

Mejor todavía: corre "métricas" en Claude Code. La skill escribe
`boveda/outputs/AAAA-MM-DD-metricas.md` con la línea `Fundadores pagando: N / 5`
y el HUD lee ese `N` de la corrida más reciente, por encima de la constante.
Así el número del HUD es el que se midió, no el que alguien recordó editar.

---

## 4. Voz local (10 min, opcional)

```bash
cd ~/jarvis/voz
./instalar.sh
```

Instala `whisper-cpp` y `sox` por Homebrew y baja el modelo (~148 MB).

Después **dale permiso de micrófono a la Terminal**: Ajustes del Sistema →
Privacidad y seguridad → Micrófono → activa Terminal. Sin esto la grabación
sale vacía sin error claro.

```bash
./hablar.sh "Sistema en línea"    # prueba el TTS
./escuchar.sh                     # graba y transcribe
./jarvis.sh                       # el bucle completo
```

Detalles y solución de problemas: `voz/LEEME.md`.

---

## 5. Conectores (opcional, pero es donde está el valor)

Las skills `bandeja` y `metricas` funcionan mucho mejor con conectores reales.
En Claude Code, con Gmail y Google Calendar conectados, `bandeja` te da correo y
agenda de verdad en vez de decir "sin dato".

Con el conector de Robinhood, `metricas` lee el portafolio — **solo lectura**.
La regla está escrita en `CLAUDE.md` y en la skill, y además está impuesta:
`.claude/settings.json` deniega las herramientas de órdenes de Robinhood
(`place_*`, `cancel_*`, `exercise_option`, `preview_*`, `review_*`) para
cualquier sesión de Claude Code que arranque en `~/jarvis`. Si Robinhood
renombra sus herramientas, actualiza esa lista.

---

## 6. Lectura de ETH (la página de análisis)

`analisis/` trae la página terminada (`eth.html`) con la última instantánea de
datos, el motor probabilístico (`motor_probabilidad.py`, necesita numpy:
`pip3 install numpy`) y el generador (`eth_pagina.py`). Se abre desde la
pestaña **ETH** del HUD o con `open ~/jarvis/analisis/eth.html`.

Para refrescarla con datos del día, en Claude Code desde `~/jarvis`:

```
> actualiza ETH
```

La skill `lectura-eth` baja las velas y la cotización con el conector de FMP,
corre el motor (~1 min) y regenera la página. Sin conector, la página se
regenera con los datos que ya están en `analisis/datos/` y lo dice en el pie.

## 7. Mesa de expertos (cuando una decisión importa)

No hay nada que instalar: son ocho agentes en `.claude/agents/` y la skill
`mesa-expertos`. Se cargan solos al arrancar Claude Code desde `~/jarvis`.

```
> convoca la mesa: ¿qué construyo primero, el cobro con Stripe o el login con Supabase?
```

Seis expertos (operador, producto, growth, finanzas, técnico, riesgo) opinan en
paralelo sin verse entre sí, un abogado del diablo ataca el consenso, y un
sintetizador escribe `boveda/outputs/AAAA-MM-DD-mesa.md` con una decisión y
tres acciones que caben en dos semanas. Tarda 10–20 minutos.

Úsala para decisiones de más de 2 horas o difíciles de revertir. Para el plan
del día sigue siendo `plan de hoy`. Los seis expertos y el abogado del diablo
solo leen disco y buscan en la web; el sintetizador escribe en la bóveda y no
tiene web. Ninguno tiene acceso a Robinhood, Gmail ni al calendario, por
diseño.

La primera mesa (3 sep 2026) está en la bóveda que recibiste con el sistema:
`boveda/outputs/2026-09-03-mesa.md`. Léela antes de convocar otra sobre lo
mismo. Si clonaste el sistema desde git, la bóveda no viene incluida (ver
`boveda/wiki/LEEME.md`).

---

## Cómo se usa un día normal

| Momento | Comando | Qué pasa |
|---|---|---|
| Mañana | `claude` → "resumen matutino" | Correo, agenda, horas libres reales de hoy |
| Al arrancar | "plan de hoy" | 2–3 prioridades que caben en esas horas |
| Cuando importe un número | "cómo vamos" | Fundadores pagando, días restantes, bloqueos |
| Noche | "cierra el día" | Qué se cumplió, qué queda para mañana |
| Domingo | "revisión semanal" | Horas reales trabajadas y si el ritmo llega al 1 dic |
| Cualquier momento | "recuerda que…" / "qué sabes de…" | Escribe y lee la bóveda |
| Decisión de más de 2 h | "convoca la mesa: …" | Siete ángulos, un memo con decisión y 3 acciones |
| Cuando importe ETH | "actualiza ETH" | Régimen, niveles y probabilidades en `analisis/eth.html` |

---

## Lo que este sistema hace y lo que no

**Hace:** te da un lugar donde el contexto no se pierde entre sesiones, y una
rutina que fuerza la pregunta incómoda cada domingo — ¿cuántas horas reales
trabajaste y se movió el número que importa?

**No hace:** trabajar por ti. Un plan bien escrito no abre la cuenta de Stripe.

La regla que más valor tiene aquí es la que ya escribiste tú el 2 de septiembre:
un solo proyecto hasta el 1 de diciembre. El sistema la hace cumplir — si le
propones una idea nueva, la anota en `boveda/wiki/parking-lot.md` y te devuelve
al trabajo. Esa es la función, no el HUD bonito.

Y aplica al sistema mismo: si `jarvis/` empieza a comerse horas de Vantera,
congélalo también. Ya está en el parking lot con esa nota.
