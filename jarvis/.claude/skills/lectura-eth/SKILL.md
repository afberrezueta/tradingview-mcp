---
name: lectura-eth
description: Regenerar la lectura sistemática de ETH (página analisis/eth.html) con datos frescos de Financial Modeling Prep y el motor probabilístico. Usar cuando Andres diga "actualiza ETH", "lectura de ETH", "cómo va ETH", "corre el motor de ETH" o "abre la página de ETH".
---

# Lectura de ETH — refrescar la página

Produce `analisis/eth.html`: régimen (SMA y HMM), niveles Donchian/ATR,
probabilidades de barrera, tasa base del sistema Turtle y últimas 72 h. Todo
local; la página se abre desde el disco. Todas las rutas de abajo son
relativas a la raíz de `jarvis/`.

FMP entrega fechas y horas en **hora de Nueva York** (America/New_York), no en
UTC. Convierte siempre antes de guardar.

## Pasos

1. **Velas diarias (incremental).** Lee la última fecha de
   `analisis/datos/eth_diario.csv`. Con el conector FMP (`crypto`, endpoint
   `cryptocurrency-historical-price-eod-full`, símbolo `ETHUSD`, `from_date` =
   esa fecha menos 5 días, `to_date` = hoy) trae solo las velas nuevas.
   Mezcla por fecha (la descarga reemplaza filas existentes de la misma fecha)
   y descarta la vela cuya fecha sea el día de hoy en Nueva York: está en
   curso y su rango es engañoso. Escribe el CSV con cabecera
   `fecha,open,high,low,close`, ascendente, una fila por día. Sin conector,
   usa el CSV existente y dilo: la página muestra la fecha de sus datos.
   Un script mínimo:

   ```python
   import csv, datetime, zoneinfo
   hoy_ny = datetime.datetime.now(zoneinfo.ZoneInfo("America/New_York")).date().isoformat()
   ruta = "analisis/datos/eth_diario.csv"
   filas = {r["fecha"]: r for r in csv.DictReader(open(ruta, encoding="utf-8"))}
   for v in descarga:   # lista de dicts de FMP: date, open, high, low, close
       if v["date"] >= hoy_ny: continue
       filas[v["date"]] = dict(fecha=v["date"], open=v["open"], high=v["high"], low=v["low"], close=v["close"])
   with open(ruta, "w", newline="", encoding="utf-8") as f:
       w = csv.DictWriter(f, fieldnames=["fecha", "open", "high", "low", "close"], lineterminator="\n"); w.writeheader()
       for k in sorted(filas): w.writerow(filas[k])
   ```

2. **Cotización.** `cryptocurrency-quote` de `ETHUSD` →
   `analisis/datos/eth_cotizacion.json`. Mapa de campos:

   | FMP | JSON local |
   |---|---|
   | `price` | `precio` |
   | `changePercentage` | `cambio_pct` |
   | `dayLow` / `dayHigh` | `min_dia` / `max_dia` |
   | `timestamp` (epoch, segundos) | `hora_utc` como `AAAA-MM-DD HH:MM` en UTC |
   | — | `fuente`: `"FMP cryptocurrency-quote"` |

   `hora_utc = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")`.

3. **Últimas 72 h (opcional).** `cryptocurrency-intraday-1-hour` de `ETHUSD`
   con `from_date` = hoy menos 3 días → `analisis/datos/eth_horas.json` con
   `desde`, `hasta` (texto `AAAA-MM-DD HH:MM`, en UTC) y `cierres` (lista de
   cierres por hora, ascendente en el tiempo; FMP la entrega descendente).
   Cada `date` de FMP viene como `AAAA-MM-DD HH:MM:SS` en hora de Nueva York;
   conviértela con `zoneinfo` y usa solo los primeros 16 caracteres:

   ```python
   NY, UTC = zoneinfo.ZoneInfo("America/New_York"), datetime.timezone.utc
   a_utc = lambda t: datetime.datetime.strptime(t[:16], "%Y-%m-%d %H:%M").replace(tzinfo=NY).astimezone(UTC).strftime("%Y-%m-%d %H:%M")
   ```

   Si falta, la página omite ese panel.
4. **Motor.** Desde `analisis/`:
   `python3 eth_pagina.py --niveles` imprime `S0` (la cotización si existe,
   si no el último cierre), `entrada` (máximo de los 20 días anteriores) y
   `salida` (mínimo de los 10 días anteriores). Luego
   `python3 motor_probabilidad.py datos/eth_diario.csv <S0> <entrada> <salida>`.
   Tarda ~1 minuto y escribe `datos/motor_resultados.json` junto al CSV.
   Necesita numpy (`pip3 install numpy` una vez); sin argumentos de niveles
   calcula los mismos valores por defecto. `--help` explica los parámetros.
5. **Página.** Desde `analisis/`, `python3 eth_pagina.py` escribe
   `analisis/eth.html`. Ábrela con `open analisis/eth.html` o desde la
   pestaña ETH del HUD (genera el HUD antes para que el enlace Panel exista).
6. **Captura.** Anota `boveda/raw/AAAA-MM-DD-eth.md` con frontmatter
   (`titulo`, `tipo: captura`, `fecha`, `tags: [eth, bot]`) y la señal en
   formato bot (LONG/FLAT, entrada, salida, régimen, probabilidades del
   motor) o "sin señal nueva" si aplica.

## Reglas

- Nunca se coloca una orden. La lectura es información; el humano ejecuta.
- Sin números inventados: si un dato no llegó, la página dice `sin dato`.
- No tocar el bot ni proponer mejoras (mantenimiento hasta el 1 dic 2026).
- Kelly no se reporta como cifra de tamaño; el tamaño lo decide
  `position_sizing` en el Mac.
- Los datos de mercado son públicos; ningún dato de portafolio entra aquí.
