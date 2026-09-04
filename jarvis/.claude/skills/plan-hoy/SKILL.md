---
name: plan-hoy
description: Escribir las 3 prioridades del día y aterrizarlas en la bóveda. Usar cuando Andres diga "plan de hoy", "qué hago hoy", "plan de mañana", "prioridades", o al empezar una sesión de trabajo sin dirección clara.
---

# Plan de hoy

Produce **entre una y tres** prioridades según las horas libres del día: tres
con 3 h o más, dos con ~2 h, una con menos de 1 h. Nunca cuatro. No una lista
de deseos.

## Antes de escribir nada

1. `date +%F` y `date +%A` — fecha y día de la semana.
2. Lee `boveda/outputs/` — busca el plan más reciente y la última revisión.
   Lo que quedó abierto ayer es candidato número uno para hoy.
3. Lee `boveda/wiki/vantera-capital.md` — los compromisos con fecha mandan.
4. Si hay conector de Calendar disponible, mira los eventos de hoy. Los turnos
   del hotel definen cuántas horas reales quedan.

## Cómo elegir

Filtro, en orden:

1. **¿Mueve Vantera hacia el próximo compromiso con fecha?** Si no, casi nunca
   entra. Los compromisos vivos están en `CLAUDE.md`.
2. **¿Cabe en las horas que quedan hoy?** Andres tiene 5–10 h/semana. Un día
   típico son 1–2 horas reales. Tres tareas de 3 horas no es un plan, es una
   mentira.
3. **¿Está bloqueando otra cosa?** Stripe bloquea cobrar. Auth bloquea el
   onboarding. Lo que desbloquea va primero.

Si una prioridad no pasa el filtro 1, di explícitamente por qué está ahí.

## Formato de salida

Escribe en `boveda/outputs/AAAA-MM-DD-plan.md`:

```markdown
---
titulo: Plan AAAA-MM-DD
tipo: plan
fecha: AAAA-MM-DD
tags: [plan, vantera]
---

# Plan — <día> <D> de <mes>

Horas disponibles hoy: ~2 (turno 15:00–23:00)
Próximo compromiso: 5 miembros fundadores — faltan 27 días

## 1. <Prioridad>
Por qué: <qué desbloquea>
Terminado se ve así: <criterio verificable, no "avanzar en">
Tiempo: <estimado>

## 2. ...

## 3. ...

## No hoy
- <cosa que tentó pero no cabe, con una línea de por qué>
```

Luego muéstralo en el chat, corto. No repitas el archivo entero.

## Reglas

- "Terminado se ve así" debe ser verificable por alguien más. "Trabajar en
  Stripe" no sirve. "Cuenta de Stripe creada y clave de prueba en `.env.local`"
  sí.
- Si el día tiene menos de 1 hora libre, escribe **una** prioridad; con ~2 h,
  dos. Un plan honesto de una tarea vale más que tres que no se van a hacer.
  El HUD avisa si un plan trae más de tres.
- Si Andres propone algo de un proyecto congelado, no lo pongas en el plan.
  Anótalo en `boveda/wiki/parking-lot.md` y dilo en una línea.
