---
name: metricas
description: Extraer los números reales del negocio y el portafolio. Usar cuando Andres diga "métricas", "cómo vamos", "los números", "cuántos clientes", "cómo va el portafolio", o cuando cualquier decisión dependa de una cifra actual.
---

# Métricas

Un número inventado en este sistema es peor que ningún número. Si una fuente
no responde, escribe `sin dato` y sigue.

## La métrica que manda

**Miembros fundadores pagando.** Todo lo demás es contexto.

```
Meta 30 sep 2026:  5 pagando a $49/mo
Meta 1 dic 2026:  50 clientes  ← criterio go/no-go del proyecto
```

Cada vez que corras esta skill, la primera línea de la salida es esa cuenta y
los días que faltan. `date +%F` para calcular.

## Fuentes

**Vantera — negocio:**

| Métrica | De dónde |
|---|---|
| Clientes pagando / MRR | Stripe (cuando exista). Hasta entonces: `sin dato — Stripe no abierto` |
| Registros / signups | Supabase (cuando exista Auth) |
| Tráfico y deploys | Vercel, proyecto `vantera-capital-app` |

Si Stripe todavía no está abierto, eso **es** el hallazgo. Dilo así: "0 clientes
porque no hay forma de cobrar — Stripe sigue sin abrir, día N de 7."

**Portafolio — solo lectura:**

- Conector de Robinhood: las dos cuentas por separado. Cuáles son y qué papel
  tiene cada una está en `boveda/wiki/proyectos/mi-trader-bot.md` — léelo
  antes; los identificadores no se copian a esta skill.
- FMP para precios de referencia si hace falta validar.

**Prohibido aquí:** colocar órdenes. Ninguna herramienta de compra/venta se
llama desde esta skill ni desde ninguna otra. Solo lectura, siempre.

**Bot — mantenimiento:**

- `mi_trader_bot` está en modo mantenimiento. Reporta solo si algo se rompió:
  el cron no corrió, no llegó la señal a Telegram, un engine tiró error.
- No propongas mejoras al bot. Está congelado hasta el 1 de diciembre.

## Formato de salida

Escribe en `boveda/outputs/AAAA-MM-DD-metricas.md`:

```markdown
---
titulo: Métricas AAAA-MM-DD
tipo: metricas
fecha: AAAA-MM-DD
tags: [metricas, vantera]
---

# Métricas — AAAA-MM-DD

## Vantera
Fundadores pagando: 0 / 5 — faltan 27 días
MRR: $0
Registros: sin dato (Supabase Auth no cableado)
Bloqueo: Stripe sin abrir — día 2 de 7 de la semana comprometida

## Portafolio (solo lectura)
<cuenta del bot>: $X
<cuenta de largo plazo>: $X

## Bot
Última señal Telegram: <fecha> — OK / falló
```

## Reglas

- Nunca proyectes ni estimes. Solo lo que devolvió la fuente.
- Si un número empeoró, dilo primero y sin suavizarlo.
- El portafolio nunca sale de la bóveda local ni del chat privado. Sin
  artifacts públicos, sin APIs, sin copias en otros proyectos.
- Compara siempre contra la corrida anterior: `ls -t boveda/outputs/*metricas* | head -2`.
