---
titulo: Cómo funciona analisis/
tipo: wiki
fecha: 2026-09-05
tags: [meta, analisis]
---

# analisis/ — lectura sistemática de ETH

| Archivo | Qué es |
|---|---|
| `eth.html` | La página terminada. Se abre desde el disco (pestaña ETH del HUD). Generada, no versionada. |
| `eth_pagina.py` | Generador: CSV + motor + cotización → `eth.html`. Sin red. |
| `motor_probabilidad.py` | HMM de régimen, barreras Monte Carlo, tasa base Turtle. numpy. |
| `exportar_web.py` | Convierte las salidas en los JSON que sirve la web pública (`web/datos/`). Sin red. |
| `alertas.py` | Compara la lectura de hoy con la anterior y dice qué cambió. Sin red. |
| `datos/eth_diario.csv` | Velas diarias 2019→hoy (fecha,open,high,low,close). Datos públicos de mercado. |
| `datos/eth_cotizacion.json` | Precio y hora de la última cotización. |
| `datos/eth_horas.json` | Cierres por hora de las últimas 72 h (opcional). |
| `datos/motor_resultados.json` | Salida del motor, con semilla fija (reproducible). Generada, no versionada. |

Refrescar: skill `lectura-eth` ("actualiza ETH") o a mano:

```bash
cd ~/jarvis/analisis
python3 eth_pagina.py --niveles          # imprime S0, entrada y salida
python3 motor_probabilidad.py datos/eth_diario.csv <S0> <entrada> <salida>
python3 eth_pagina.py && open eth.html
python3 exportar_web.py                  # refresca los datos de la web pública
python3 alertas.py                       # detecta qué cambió respecto a ayer
```

La web pública (`web/` y `api/` en la raíz del repo) muestra solo la capa
abierta: régimen, niveles y serie de precio. Las probabilidades y la tasa base
salen a `privado/motor.json`, fuera del directorio publicado y fuera de git:
esa es la capa que se cobrará, y cualquier archivo dentro de `web/` sería
descargable por cualquiera. El precio en vivo lo sirve `api/precio.js`, que guarda la clave
de FMP en una variable de entorno de Vercel y nunca la envía al navegador.

Aquí solo hay datos públicos de mercado; nada del portafolio. Ninguna orden
se coloca desde este sistema.
