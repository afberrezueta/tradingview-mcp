---
name: revision-semanal
description: Cerrar el día o la semana — qué se hizo, qué no, y si el proyecto sigue en curso hacia su criterio go/no-go. Usar cuando Andres diga "cierra el día", "revisión semanal", "cómo estuvo la semana", los domingos, o al final de una sesión de trabajo larga.
---

# Revisión — cierre de día y de semana

Dos modos. Elige por el día de la semana o por lo que pida Andres.

---

## Modo A — cierre de día (5 minutos)

1. Lee `boveda/outputs/AAAA-MM-DD-plan.md` de hoy.
2. Por cada prioridad del plan (una a tres): ¿se cumplió el "terminado se ve
   así"? Sí / No / Parcial. Sin narrativa.
3. Pregunta a Andres qué pasó con las que no. Una línea basta.
4. Escribe `boveda/outputs/AAAA-MM-DD-cierre.md`:

```markdown
---
titulo: Cierre AAAA-MM-DD
tipo: cierre
fecha: AAAA-MM-DD
tags: [cierre, vantera]
---

# Cierre — AAAA-MM-DD

1. Stripe abierto — ✅
2. Supabase Auth cableado — ❌ (no hubo tiempo, turno se alargó)
3. Copy del onboarding — ⚠️ parcial

Mañana arranca con: Supabase Auth
```

5. Deja la primera prioridad de mañana en cola al final del archivo.

---

## Modo B — revisión semanal (domingos, 20 minutos)

1. Lee todos los `boveda/outputs/` de los últimos 7 días.
2. Corre la skill `metricas`.
3. Contesta estas cuatro, en este orden:

**¿Cuántas horas reales se trabajaron?**
Cuenta los cierres de día. Compara contra las 5–10 h/semana disponibles. Si
fueron 2, ese es el hallazgo — no el resto del análisis.

**¿La métrica que manda se movió?**
Fundadores pagando: cuántos al inicio de la semana, cuántos al final. Si no se
movió, di exactamente qué la bloqueó.

**¿Seguimos en curso hacia el 1 de diciembre?**
Faltan N semanas para 50 clientes. Al ritmo de esta semana, ¿se llega? Haz la
aritmética y muéstrala. Si el ritmo actual no llega, dilo con el número.

**¿Se rompió la regla del proyecto único?**
Revisa `boveda/wiki/parking-lot.md` y las capturas de la semana. ¿Cuántas horas
se fueron en cosas que no eran Vantera? Repórtalo sin adornos.

4. Escribe `boveda/outputs/AAAA-MM-DD-semana.md`, con el frontmatter estándar
   (`titulo`, `tipo: semana`, `fecha`, `tags`) y las cuatro respuestas en ese
   orden.

---

## Reglas

- Esta skill no motiva. Reporta. Si la semana fue mala, la salida dice que la
  semana fue mala.
- No propongas rehacer el plan de los 3 meses cada semana. El criterio go/no-go
  es el 1 de diciembre; hasta entonces se ejecuta.
- Una excepción: si **tres semanas seguidas** la métrica que manda no se movió,
  eso sí es señal de que el plan —no el esfuerzo— tiene un problema. Dilo
  explícitamente y sugiere revisar el supuesto que falló.
- Nunca cierres una semana sin el número de horas trabajadas. Es el dato que
  más explica todo lo demás.
