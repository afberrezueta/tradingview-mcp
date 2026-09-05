---
name: lectura-eth
description: Regenerar la lectura sistemática de ETH (página analisis/eth.html) con datos frescos de Financial Modeling Prep y el motor probabilístico. Usar cuando Andres diga "actualiza ETH", "lectura de ETH", "cómo va ETH", "corre el motor de ETH" o "abre la página de ETH".
---

# Lectura de ETH — refrescar la página

Produce `analisis/eth.html`: régimen (SMA y HMM), niveles Donchian/ATR,
probabilidades de barrera, tasa base del sistema Turtle y últimas 72 h. Todo
local; la página se abre desde el disco.

## Pasos

1. **Datos diarios.** Con el conector FMP (`crypto`, endpoint
   `cryptocurrency-historical-price-eod-full`, símbolo `ETHUSD`, desde
   `2019-01-01` hasta hoy) escribe `analisis/datos/eth_diario.csv` con
   cabecera `fecha,open,high,low,close`, una fila por día, ordenado
   ascendente. Si el conector no está disponible, usa el CSV existente y dilo:
   la página mostrará la fecha de sus datos.
2. **Cotización.** `cryptocurrency-quote` de `ETHUSD` →
   `analisis/datos/eth_cotizacion.json` con `precio`, `cambio_pct`,
   `min_dia`, `max_dia`, `hora_utc` (AAAA-MM-DD HH:MM) y `fuente`.
3. **Últimas 72 h (opcional).** `cryptocurrency-intraday-1-hour` de los
   últimos tres días → `analisis/datos/eth_horas.json` con `desde`, `hasta`
   (texto) y `cierres` (lista de cierres por hora, ascendente). Si falta, la
   página omite ese panel.
4. **Motor.** Desde `analisis/`:
   `python3 motor_probabilidad.py datos/eth_diario.csv <precio> <entrada> <salida>`
   donde entrada = máximo de los 20 días anteriores y salida = mínimo de los
   10 días anteriores (el generador los imprime si se corre antes con
   `--niveles`). Tarda ~1 minuto y escribe `datos/motor_resultados.json`.
   Necesita numpy (`pip3 install numpy` una vez).
5. **Página.** `python3 eth_pagina.py` escribe `analisis/eth.html`. Ábrela con
   `open analisis/eth.html` o desde la pestaña ETH del HUD.
6. Anota una captura en `boveda/raw/AAAA-MM-DD-eth.md` con la señal en formato
   bot (LONG/FLAT, entrada, salida, régimen) y "sin señal nueva" si aplica.

## Reglas

- Nunca se coloca una orden. La lectura es información; el humano ejecuta.
- Sin números inventados: si un dato no llegó, la página dice `sin dato`.
- No tocar el bot ni proponer mejoras (mantenimiento hasta el 1 dic 2026).
- Kelly no se reporta como cifra de tamaño; el tamaño lo decide
  `position_sizing` en el Mac.
- Los datos de mercado son públicos; ningún dato de portafolio entra aquí.
