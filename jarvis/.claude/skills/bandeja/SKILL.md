---
name: bandeja
description: Resumen matutino — correo, calendario y lo que requiere respuesta hoy. Usar cuando Andres diga "resumen matutino", "bandeja", "qué hay hoy", "buenos días", o al arrancar la primera sesión del día.
---

# Bandeja — resumen matutino

Un barrido de la mañana en menos de 60 segundos de lectura.

## Qué recoger

**Correo** (conector de Gmail, si está disponible):

- Búsqueda: `is:unread newer_than:1d` y por separado `is:starred is:unread`.
- Ignora newsletters, promociones y notificaciones automáticas salvo que
  contengan un número o una fecha que importe.
- Marca aparte cualquier cosa de: Stripe, Supabase, Vercel, el dominio
  vantera.capital, o alguien que responda a un correo de Vantera. Eso es la
  vía crítica.

**Calendario** (conector de Google Calendar, si está disponible):

- Eventos de hoy y de mañana.
- Calcula las **horas libres reales** de hoy: el hueco entre el turno de
  trabajo y el resto. Ese número va arriba del resumen — determina si el plan
  de hoy es de tres tareas o de una.

**Sistema:**

- `ls -t boveda/outputs/ | head -5` — qué produjo JARVIS últimamente.
- Si el último plan es de ayer o antes, dilo: hay un plan sin cerrar.

## Formato de salida

Escribe en `boveda/outputs/AAAA-MM-DD-bandeja.md` y muestra en el chat:

```markdown
---
titulo: Bandeja AAAA-MM-DD
tipo: bandeja
fecha: AAAA-MM-DD
tags: [bandeja, vantera]
---

# Bandeja — <día> <D> de <mes>

**Horas libres hoy: ~2** (turno 15:00–23:00)
**Vantera: faltan 27 días para los 5 fundadores**

## Requiere respuesta (3)
- **Stripe** — verificación de identidad pendiente. Bloquea cobrar. → hoy
- <remitente> — <qué pide, en 8 palabras>

## Para saber (2)
- <línea>

## Agenda
- 15:00 turno de trabajo
- (mañana) 09:00 —

## Sin cerrar
- Plan del 2 sep: 2 de 3 pendientes
```

## Reglas

- Máximo 5 items en "requiere respuesta". Si hay más, los 5 más urgentes y
  di cuántos quedan.
- Nunca cites el cuerpo completo de un correo. Ocho palabras de qué pide.
- No redactes respuestas aquí a menos que Andres lo pida. Esto es un barrido.
- Si un conector no está disponible, dilo en una línea y sigue con el resto.
  No inventes correos ni eventos.
- Datos personales y financieros: se resumen aquí, no se copian a ningún lado.
