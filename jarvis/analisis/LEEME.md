---
titulo: Cómo funciona analisis/
tipo: wiki
fecha: 2026-09-05
tags: [meta, analisis]
---

# analisis/ — lectura sistemática de ETH

| Archivo | Qué es |
|---|---|
| `eth.html` | La página terminada. Se abre desde el disco (pestaña ETH del HUD). |
| `eth_pagina.py` | Generador: CSV + motor + cotización → `eth.html`. Sin red. |
| `motor_probabilidad.py` | HMM de régimen, barreras Monte Carlo, tasa base Turtle. numpy. |
| `datos/eth_diario.csv` | Velas diarias 2019→hoy (fecha,open,high,low,close). Datos públicos de mercado. |
| `datos/eth_cotizacion.json` | Precio y hora de la última cotización. |
| `datos/eth_horas.json` | Cierres por hora de las últimas 72 h (opcional). |
| `datos/motor_resultados.json` | Salida del motor, con semilla fija (reproducible). |

Refrescar: skill `lectura-eth` ("actualiza ETH") o a mano:

```bash
cd ~/jarvis/analisis
python3 eth_pagina.py --niveles          # imprime S0, entrada y salida
python3 motor_probabilidad.py datos/eth_diario.csv <S0> <entrada> <salida>
python3 eth_pagina.py && open eth.html
```

Aquí solo hay datos públicos de mercado; nada del portafolio. Ninguna orden
se coloca desde este sistema.
