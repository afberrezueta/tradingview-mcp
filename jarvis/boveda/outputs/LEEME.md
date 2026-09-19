---
titulo: Cómo funciona outputs/
tipo: wiki
fecha: 2026-09-03
tags: [meta]
---

# outputs/ — entregables de JARVIS

Todo lo que el sistema produce. Nombre: `AAAA-MM-DD-tipo.md`

| Tipo | Skill que lo escribe | Cuándo |
|---|---|---|
| `-bandeja.md` | `bandeja` | mañana |
| `-plan.md` | `plan-hoy` | al arrancar el trabajo |
| `-metricas.md` | `metricas` | cuando importe un número |
| `-cierre.md` | `revision-semanal` (modo día) | fin del día |
| `-semana.md` | `revision-semanal` (modo semana) | domingos |
| `-mesa.md` | `mesa-expertos` | cuando una decisión cueste más de 2 h |

Estos archivos son el registro real de qué pasó. La revisión semanal los lee
todos — por eso el formato importa más que la prosa.

```bash
ls -t boveda/outputs/ | head -10           # lo más reciente
ls -t boveda/outputs/*metricas* | head -2  # comparar dos corridas
```
