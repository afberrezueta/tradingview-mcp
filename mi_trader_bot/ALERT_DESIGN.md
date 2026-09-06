# ALERT_DESIGN — Rediseño de las alertas de Telegram
**Motores afectados:** Agentic (Donchian 20 + ATR 14) y ETH (acumulación por tramos)
**Alcance:** solo comunicación. Ninguna regla de trading, umbral, sizing o gatillo cambia.
**Estado:** propuesta. Este documento NO edita `agentic_scan_prompt.md` ni `eth_scan_prompt.md`; la sección 5 contiene los bloques exactos a sustituir.

---

## 1. Diagnóstico de los formatos actuales

### 1.1 Agentic — `agentic_scan_prompt.md`, líneas 30–43

```
📊 AGENTIC SCAN — {fecha}
Capital: ${valor} | Cash: ${cash}
Régimen: {ON/OFF} (TQQQ {pos}%, SOXL {pos}%)

Señales: {ninguna | TICKER cierre X > banda Y}
  → Propuesta: comprar ${monto} ({acciones} acc), stop {precio}, riesgo ${r}
Posiciones: {ninguna | TICKER P&L +x% (R: +y), stop {precio}}
Más cercano: {TICKER} a {x}% de ruptura ({precio objetivo})

Ejecutado hoy: {nada | COMPRA TICKER $x @ precio, stop y | VENTA ...}
Breakers: {OK | activo: motivo}
```

**D-A1 · La primera línea no informa de nada.** `📊 AGENTIC SCAN — {fecha}` es una etiqueta de proceso. La notificación push de Telegram corta a ~1 línea: Andrés ve el nombre del bot y una fecha, y tiene que abrir el mensaje **todos los días** para saber si se movió dinero. Es exactamente lo contrario de BLUF.

**D-A2 · El dato más importante está en la penúltima línea.** `Ejecutado hoy:` es la línea 9 de 10. Antes van capital, régimen, señales, posiciones y un ranking de proximidad. Pirámide invertida al revés.

**D-A3 · Doble campo para el mismo hecho → ambigüedad.** `→ Propuesta: comprar ${monto}...` y `Ejecutado hoy: ...` describen el mismo trade. El motor es autónomo (regla de la línea 14: *"puedes ejecutar sin confirmación"*), así que la palabra **"Propuesta"** es falsa: sugiere que Andrés debe aprobar algo. Para saber si la propuesta se ejecutó hay que leer tres líneas más abajo y cruzarlas mentalmente. Un ticket no se lee cruzando campos.

**D-A4 · `Más cercano: {TICKER} a {x}% de ruptura` es ruido puro y estructural.** Se emite los ~250 días hábiles del año y por definición **nunca es accionable** (si lo fuera, estaría en `Señales`). Es la línea que entrena a Andrés a no abrir el mensaje.

**D-A5 · `Breakers: OK` y `Régimen: ON` son confirmaciones de normalidad diarias.** El día que uno de los dos cambie a `activo: motivo` u `OFF`, se leerá con el mismo peso visual que los 200 días anteriores de `OK`. El reporting por excepción existe justo para evitar esto.

**D-A6 · Placeholders sin unidad ni referencia.** `P&L +x% (R: +y)` mezcla dos escalas sin decir cuál manda para la gestión; `riesgo ${r}` no dice si es en dólares o en % del capital; `Capital: ${valor}` es un número absoluto sin delta (¿subió?, ¿bajó?, ¿cuánto hoy?). Un número institucional siempre lleva unidad **y** referencia.

**D-A7 · El formato miente sobre el riesgo real.** La regla 11 promete *"Riesgo máx. por trade = 4% del capital"* y la línea 26 codifica `$4.36` (4% de ~$109). Con la cuenta en **$3,109**, el tope duro de `$49` por orden hace que el riesgo real por trade sea ~**0,16%** del capital, no 4%. El formato imprime `riesgo ${r}` sin denominador, así que la alerta nunca revela esa distancia. *(No toco la regla: el arreglo de comunicación es imprimir siempre riesgo en $ **y** en % del capital vivo.)*

**D-A8 · No existe campo para el estado del stop GTC.** La regla 17 obliga a colocar un `stop_market` GTC tras cada compra. Es el dato de riesgo más importante de la cuenta y el formato no tiene dónde confirmar que la orden está **viva**. Un stop huérfano (compra ejecutada, stop rechazado) se emite hoy como un mensaje visualmente idéntico a un día normal.

**D-A9 · No distingue ACCIÓN de OBSERVACIÓN de SIN CAMBIOS.** Mismo emoji `📊`, mismo tono y misma longitud el día que compra NVDA y el día que no ocurre absolutamente nada. En el scroll de Telegram los 250 mensajes del año son indistinguibles.

**D-A10 · Se rompe en móvil.** La sangría `  → Propuesta:` no se respeta de forma fiable en texto plano de Telegram, y las dos líneas en blanco gastan 2 de las 15 líneas del presupuesto sin aportar jerarquía.

---

### 1.2 ETH — `eth_scan_prompt.md`, bloque "Formato de salida (Telegram, máximo 12 líneas)"

```
🪙 ETH SCAN — {fecha}
Precio: ${precio} | Swing90d: ${swing} | DD: {x}%
Tramos: [{estado de los 4: ✓ ejecutado / · pendiente / ◦ activo}]
Acumulado (Agentic): {eth} ETH @ ${coste_medio}
Hoy: {nada | COMPRA tramo {n}: ${monto} @ ${precio} | BLOQUEADO: motivo}
Invalidación: {OK | técnica activa | fundamental activa}
Siguiente tramo: {n} a ${precio_objetivo} ({y}% más abajo)
```

**D-E1 · Mismo fallo de BLUF que Agentic:** primera línea = etiqueta; el hecho (`Hoy:`) es la línea 5 de 7.

**D-E2 · `Swing90d` es una etiqueta falsa.** `eth_accumulation_config.json` tiene `"swing_lookback_days": 365`, y su propio `_comment` explica por qué: *"con 90 dias el swing high era $2,516 y el motor no habria comprado nada"*. El prompt arrastra el error en Reglas (*"máximo cierre de los últimos `swing_lookback_days` (90) días"*) y `mcp/lib.js:164` lo propaga al output con el campo `swing_high_90d` aunque lea 365. Resultado: la alerta imprime **$4,715 etiquetado como "Swing90d"**. Un número correcto con etiqueta incorrecta es peor que no publicarlo: invita a Andrés a desconfiar del motor entero.

**D-E3 · `Tramos: [✓ · ◦ ·]` es criptográfico e ilegible en móvil.** Tres glifos casi idénticos (`·` vs `◦`), sin nivel, sin precio, sin importe. Andrés no puede responder desde el móvil a "¿cuánto capital me queda por desplegar y a qué precio entra el siguiente?" sin abrir el JSON de config.

**D-E4 · `Hoy: {nada | COMPRA | BLOQUEADO}` mete tres clases semánticas opuestas en un solo campo de texto libre:** una ejecución, un no-evento y un incidente. Son tres niveles de urgencia distintos compartiendo tipografía, posición y prefijo.

**D-E5 · `BLOQUEADO: motivo` no separa bloqueo rutinario de bloqueo de tesis.** "sin fondos" o "ya se compró un tramo hoy" son rutina; "invalidación fundamental activa" significa que la tesis CLARITY/tokenización se cayó y Andrés tiene que decidir algo. Hoy se leen igual.

**D-E6 · `Invalidación: OK` es otra confirmación diaria de normalidad** (mismo problema que D-A5).

**D-E7 · Falta el único KPI de un motor de acumulación: capital desplegado vs. reserva.** El formato da `{eth} ETH @ ${coste_medio}` pero no dice cuánto de los **$3,000** ya está dentro, cuánto queda, ni el P&L no realizado contra el coste medio. Es el dato que define si el motor va por delante o por detrás de su plan.

**D-E8 · Dos "próximos pasos" compitiendo.** `Siguiente tramo:` se imprime también los días en que hay un tramo **activo ahora**, así que el mensaje termina apuntando a un nivel más abajo justo el día en que la acción es aquí.

**D-E9 · Ningún ancla de tesis.** En un motor cuyo único acto es comprar caídas del −30% al −60%, no reportar que la tesis sigue viva hace que cada compra parezca un bot promediando a la baja en un cuchillo cayendo. Es el motivo por el que este mensaje "no se lee institucional".

---

### 1.3 Fallos comunes a los dos

| # | Fallo | Efecto |
|---|---|---|
| C1 | Primera línea = etiqueta de proceso, no conclusión | La push notification no informa; hay que abrir siempre |
| C2 | El hecho ejecutado va al final | Se lee el contexto antes que la decisión |
| C3 | Confirmaciones de normalidad diarias (`OK`, `ON`, `nada`) | Alert fatigue; se pierde la excepción cuando llega |
| C4 | Sin clase de mensaje (acción / observación / sin cambios / alerta) | Todos los días se ven iguales en el scroll |
| C5 | Texto libre en campos clave | El LLM redacta distinto cada día; imposible leer por patrón |
| C6 | Números sin referencia (sin % del capital, sin delta, sin unidad) | Parece un log, no un ticket |

---

## 2. Principios de diseño (con fuentes)

**P1 — BLUF: la conclusión en la primera línea.** El estándar de escritura del Ejército (AR 25-50) exige poner la decisión y la acción requerida arriba del todo; el lector quiere saber "¿cómo me afecta esto?" en la primera frase, no en la página 40.
→ https://en.wikipedia.org/wiki/BLUF_(communication) · https://hbr.org/2016/11/how-to-write-email-with-military-precision

**P2 — Etiqueta de clase en la primera palabra.** El correo militar antepone una palabra clave en mayúsculas (`ACTION`, `INFO`, `REQUEST`, `DECISION`) que clasifica el mensaje antes de leerlo. Aquí se traduce a cuatro clases fijas con un color: 🟢 EJECUTADO / 🟡 OBSERVACIÓN / ⚪ SIN CAMBIOS / 🔴 ALERTA.
→ https://www.cnbc.com/2019/04/23/ex-us-navy-officer-how-to-write-emails-with-military-precision.html

**P3 — Reporting por excepción: lo normal no ocupa línea.** El exception-based reporting define primero qué es "normal, aceptable o esperado" y solo publica lo que se sale. Las líneas `Breakers: OK` e `Invalidación: OK` desaparecen; solo existen cuando hay excepción.
→ https://www.hyperbots.com/glossary/exception-based-reporting · https://riskpublishing.com/risk-reporting-importance-and-best-practices/

**P4 — Accionabilidad estricta.** Regla de alerting SRE: si no hay nada que hacer, no debe llegar como si lo hubiera; una alerta bien afinada vale más que diez ruidosas. En equipos reales, ~3% de las alertas recibidas requieren acción inmediata — el resto es lo que rompe la confianza en el canal.
→ https://incident.io/blog/sre-alerting-best-practices · https://rootly.com/on-call-software/alert-fatigue

**P5 — Umbrales calibrados, ni anchos ni estrechos.** Reglas demasiado amplias generan alertas de bajo valor; demasiado estrechas ocultan lo importante. Aplicación directa: `Más cercano` solo se publica bajo un umbral (≤3% de la ruptura), no todos los días.
→ https://oneuptime.com/blog/post/2026-01-30-alert-rule-design/view · https://icinga.com/blog/alert-fatigue-monitoring/

**P6 — Estructura de trade ticket, no de narrativa.** Un ticket institucional es un conjunto fijo de campos: lado, cantidad, precio, tipo de orden, y controles de riesgo pre-trade (tamaño, exposición nocional, permisos de cuenta) como parte de la ejecución, no como apéndice.
→ https://www.tradestation.com/insights/institutional-order-execution-at-tradestation/ · https://finchtrade.com/blog/market-depth-and-slippage-strategies-for-institutional-trades

**P7 — El stop se comunica siempre, porque define la invalidación.** El stop va donde la idea se demuestra falsa, no donde el tamaño resulta cómodo; y la idea de trade incluye explícitamente stop inicial, gestión y parciales. Por eso el stop y su **estado de orden viva** son campos obligatorios del ticket, no opcionales.
→ https://academy.ftmo.com/lesson/how-to-create-a-trading-idea/

**P8 — Titular primero, detalle después (morning note).** La nota matinal se lee en dos minutos: un titular con la llamada principal, luego 2–3 frases de impacto (precio objetivo, cambio de recomendación), luego contexto de mercado. No es un resumen de noticias, es inteligencia accionable.
→ https://www.claudecodehq.com/playbooks/er-morning-note · https://genrptfinance.com/blogs/how-to-structure-a-sell-side-report-that-institutional-investors-actually-read/

**P9 — Brevedad con profundidad bajo demanda.** Una página que resume, con el detalle disponible al hacer drill-down. En Telegram: 12–15 líneas, y el histórico/log queda en `out/*.log` para quien quiera bajar.
→ https://riskpublishing.com/risk-reporting-importance-and-best-practices/

**P10 — Escaneabilidad móvil.** La gente escanea; solo una minoría lee palabra por palabra, y decide si sigue leyendo por los primeros elementos "gancho". La notificación debe ser relevante y mínimamente disruptiva. Traducción operativa: una idea por línea, ~40–45 caracteres útiles antes del salto en pantalla de móvil, sin sangrías, sin líneas vacías salvo un único separador.
→ https://www.nngroup.com/articles/ten-usability-heuristics/ · https://www.toptal.com/designers/ux/notification-design · https://carbondesignsystem.com/patterns/notification-pattern/

**P11 — Consistencia posicional.** Cada dato siempre en la misma línea y con el mismo prefijo (`▸ RIESGO`, `▸ CUENTA`). Tras una semana, Andrés lee por posición y no por texto: mira la línea 1 y la línea `▸ RIESGO` y cierra el mensaje en 2 segundos.

**P12 — Vocabulario cerrado.** Los campos de estado usan una lista finita de tokens (`✓ viva`, `✗ SIN STOP`, `▶ ACTIVO`, `◻ pendiente`). Esto evita que el LLM improvise una redacción distinta cada día — que es lo que hoy hace que dos mensajes del mismo motor parezcan de bots distintos.

---

## 3. Formatos nuevos

### 3.0 Reglas comunes a los dos motores

**Clases de mensaje (excluyentes, precedencia 🔴 > 🟢 > 🟡 > ⚪):**

| Clase | Cuándo | Qué significa para Andrés |
|---|---|---|
| 🔴 **ALERTA** | Breaker/kill switch activo, stop GTC no colocado, orden rechazada, invalidación de tesis, sin fondos | **Tiene que mirar hoy** |
| 🟢 **EJECUTADO** | Se movió dinero: compra, venta parcial, stop recolocado | Acción tomada, solo verificar |
| 🟡 **OBSERVACIÓN** | No se movió dinero, pero algo está a ≤3% de disparar, o una posición cruzó +1R/+2R, o el régimen está OFF | Contexto relevante, sin acción |
| ⚪ **SIN CAMBIOS** | Nada que hacer y nada cerca | No abrir |

**Reglas de omisión (esto es lo que mata el ruido):**
1. El bloque `▸ TICKET` **solo existe** si la clase es 🟢. Nunca se escribe "Ejecutado: nada".
2. Nunca se escribe una línea para confirmar normalidad. No hay `Breakers: OK`, no hay `Invalidación: OK`, no hay `Régimen: ON`. Su ausencia **es** el OK.
3. `▸ PRÓXIMO` solo aparece si el objetivo está a ≤3% (Agentic) o si no hay tramo activo hoy (ETH).
4. La línea `🔴 EXCEPCIÓN` es la última y solo existe si hay excepción activa.
5. Cero líneas en blanco salvo **una** entre el titular y el cuerpo.
6. Sin sangrías. Sin tabuladores. Sin Markdown (el `curl` envía `text` plano).

**Opcional (cambio de 1 línea en los `.sh`, no requerido):** enviar los días ⚪ con `-d disable_notification=true` en la llamada a `sendMessage`. El mensaje sigue llegando como heartbeat, pero no vibra el teléfono. Es la implementación literal de P4.

---

### 3.1 Plantilla — Motor Agentic (máx. 15 líneas)

```
{🟢 EJECUTADO|🟡 OBSERVACIÓN|⚪ SIN CAMBIOS|🔴 ALERTA} · AGENTIC · {DD-mmm}
{titular ≤70 car.: qué se hizo, o la razón concreta de no hacer nada}

▸ TICKET {COMPRA|VENTA 50%|STOP↑} {TICKER}
  ${monto} · {acciones} acc @ ${precio_fill}
  Stop ${stop} · riesgo ${riesgo_usd} = {riesgo_pct}% del capital
  Gatillo: cierre ${close} > Donchian20 ${banda_sup} · ATR14 ${atr}
  Stop GTC: {✓ viva #{order_id} | ✗ NO COLOCADA}
▸ RIESGO {n}/2 pos · ${expuesto} ({expo_pct}%) · cash ${cash} ({cash_pct}%)
  {TICKER} {+|-}{x.x}% · {+|-}{y.y}R · stop ${stop} · {✓|✗ SIN STOP}
  {TICKER} {+|-}{x.x}% · {+|-}{y.y}R · stop ${stop} · {✓|✗ SIN STOP}
▸ CUENTA ${valor} · {+|-}{x.x}% día · {+|-}{x.x}% sem
▸ PRÓXIMO {TICKER} rompe en ${precio} ({x.x}% arriba)
🔴 EXCEPCIÓN {breaker|kill switch|orden rechazada}: {motivo} → {efecto operativo}
```

Notas de relleno:
- Línea 1: la clase va **antes** que el nombre del motor. Es lo único que se ve en la push.
- Línea 2 (titular): frase única, en pasado si hubo acción (*"Comprado CRCL $49, stop $168.20"*), o causa concreta si no la hubo (*"Sin señales: los 8 tickers por debajo de su banda Donchian"*). Prohibido "sin novedad" a secas.
- `▸ RIESGO` con 0 posiciones se colapsa a: `▸ RIESGO 0/2 pos · sin exposición · cash ${cash} (100%)`.
- `riesgo_pct` se calcula sobre el capital **real de hoy**, no sobre el $4.36 hardcodeado (fix de D-A7, sin tocar la regla de sizing).
- Régimen risk-off: no lleva línea propia; va en el titular como causa (*"Régimen risk-off (TQQQ 18%, SOXL 11%): no se abren posiciones"*).

---

### 3.2 Plantilla — Motor ETH (máx. 15 líneas)

```
{🟢 COMPRADO|🟡 ZONA ACTIVA|⚪ SIN CAMBIOS|🔴 ALERTA} · ETH · {DD-mmm}
{titular ≤70 car.: tramo ejecutado e importe, o razón de no comprar}

▸ TICKET COMPRA TRAMO {n}/4
  ${monto} · {eth} ETH @ ${precio} · spread {x.xx}%
  Nivel {dd_nivel}% desde máx · banda ±{band}% · preview {✓ limpio|✗ alerta}
▸ ESCALERA (máx {lookback}d ${swing_high})
  T1 −30% ${p1} · ${m1} · {✓ {dd-mmm} | ▶ ACTIVO | ◻ pendiente}
  T2 −40% ${p2} · ${m2} · {✓ {dd-mmm} | ▶ ACTIVO | ◻ pendiente}
  T3 −50% ${p3} · ${m3} · {✓ {dd-mmm} | ▶ ACTIVO | ◻ pendiente}
  T4 −60% ${p4} · ${m4} · {✓ {dd-mmm} | ▶ ACTIVO | ◻ pendiente}
▸ POSICIÓN {eth} ETH · coste ${coste_medio} · mkt ${valor_mkt} · {+|-}{x.x}%
▸ CAPITAL ${desplegado} de ${capital} · ${reserva} en reserva
▸ ETH ${precio} · {dd}% desde máx · próximo T{n} a ${precio} ({x.x}% abajo)
🔴 EXCEPCIÓN {sin fondos|invalidación técnica|invalidación fundamental}: {motivo}
```

Notas de relleno:
- `▸ ESCALERA (máx 365d $4,715)` sustituye a `Swing90d` y a la fila de glifos `[✓ · ◦ ·]` (fix de D-E2 y D-E3). `{lookback}` se lee de `swing_lookback_days` del config, nunca se escribe a mano.
- Los importes `${m1..m4}` salen de `tranche_pcts × capital_usd`: con la config actual, $600 / $750 / $900 / $750.
- `▸ CAPITAL` es el KPI que hoy no existe (fix de D-E7).
- La última línea de datos funde precio + drawdown + próximo tramo, y el "próximo" se omite si el tramo activo es hoy (fix de D-E8).
- Ancla de tesis: solo aparece cuando cambia de estado, como 🔴 EXCEPCIÓN. Mientras la tesis viva, silencio (P3).

---

## 4. Ejemplos renderizados

### 4.1 Agentic — día con ejecución (🟢), cuenta $3,109

```
🟢 EJECUTADO · AGENTIC · 06-sep
Comprado CRCL $49 @ $187.40, stop $168.20. 2/2 posiciones, sin hueco.

▸ TICKET COMPRA CRCL
  $49.00 · 0.2615 acc @ $187.40
  Stop $168.20 · riesgo $5.02 = 0.16% del capital
  Gatillo: cierre $187.40 > Donchian20 $184.90 · ATR14 $12.80
  Stop GTC: ✓ viva #7f31a9c4
▸ RIESGO 2/2 pos · $100.35 (3.2%) · cash $3,008.65 (96.8%)
  CRCL +0.0% · 0.0R · stop $168.20 · ✓
  MSTR +4.8% · +0.8R · stop $291.50 · ✓
▸ CUENTA $3,109 · +0.1% día · +0.4% sem
```

*(Sin línea `▸ PRÓXIMO` porque el cupo de posiciones está lleno; sin línea de excepción porque no hay ninguna. 11 líneas.)*

### 4.2 Agentic — día sin cambios (⚪), el caso más frecuente

```
⚪ SIN CAMBIOS · AGENTIC · 09-sep
Sin señales: los 8 tickers por debajo de su banda Donchian20.

▸ RIESGO 2/2 pos · $103.10 (3.3%) · cash $3,008.65 (96.8%)
  CRCL +1.4% · +0.2R · stop $168.20 · ✓
  MSTR +5.1% · +0.9R · stop $291.50 · ✓
▸ CUENTA $3,112 · +0.1% día · +0.5% sem
```

*(7 líneas. Sin `Régimen: ON`, sin `Breakers: OK`, sin `Más cercano`. Nada que hacer y el mensaje lo dice en la primera palabra.)*

### 4.3 ETH — día con ejecución de tramo (🟢)

```
🟢 COMPRADO · ETH · 06-sep
Tramo 2 ejecutado: $750 @ $2,491, −47% desde máx. Reserva $1,650.

▸ TICKET COMPRA TRAMO 2/4
  $750.00 · 0.3011 ETH @ $2,491.00 · spread 0.06%
  Nivel −40% desde máx · banda ±1.5% · preview ✓ limpio
▸ ESCALERA (máx 365d $4,715)
  T1 −30% $3,300.50 · $600 · ✓ 24-ago
  T2 −40% $2,829.00 · $750 · ✓ 06-sep
  T3 −50% $2,357.50 · $900 · ◻ pendiente
  T4 −60% $1,886.00 · $750 · ◻ pendiente
▸ POSICIÓN 0.4898 ETH · coste $2,756.23 · mkt $1,220.09 · −9.6%
▸ CAPITAL $1,350 de $3,000 · $1,650 en reserva
▸ ETH $2,491 · −47.2% desde máx · próximo T3 a $2,357.50 (−5.4% abajo)
```

*(13 líneas. Andrés sabe en la primera línea que se movieron $750, y en la línea `▸ CAPITAL` cuánta munición queda, sin abrir nada.)*

### 4.4 ETH — día con zona activa pero bloqueado (🔴)

```
🔴 ALERTA · ETH · 07-sep
T3 activo a $2,357.50 pero solo hay $8 de cash: no se compró.

▸ ESCALERA (máx 365d $4,715)
  T1 −30% $3,300.50 · $600 · ✓ 24-ago
  T2 −40% $2,829.00 · $750 · ✓ 06-sep
  T3 −50% $2,357.50 · $900 · ▶ ACTIVO
  T4 −60% $1,886.00 · $750 · ◻ pendiente
▸ POSICIÓN 0.4898 ETH · coste $2,756.23 · mkt $1,151.99 · −14.7%
▸ CAPITAL $1,350 de $3,000 · $1,650 en reserva
▸ ETH $2,352 · −50.1% desde máx · tramo activo hoy
🔴 EXCEPCIÓN sin fondos: cash $8 < buffer $5 + tramo $900 → transferir o el T3 se pierde
```

*(11 líneas. La excepción dice el efecto operativo, no solo la causa.)*

---

## 5. Cambios a aplicar (REEMPLAZAR → POR)

> No he editado ninguno de los dos archivos. Aquí quedan los bloques literales.

### 5.1 `agentic_scan_prompt.md` — líneas 30–43

**REEMPLAZAR esto:**

~~~
## Formato de salida (Telegram, máximo 15 líneas)
```
📊 AGENTIC SCAN — {fecha}
Capital: ${valor} | Cash: ${cash}
Régimen: {ON/OFF} (TQQQ {pos}%, SOXL {pos}%)

Señales: {ninguna | TICKER cierre X > banda Y}
  → Propuesta: comprar ${monto} ({acciones} acc), stop {precio}, riesgo ${r}
Posiciones: {ninguna | TICKER P&L +x% (R: +y), stop {precio}}
Más cercano: {TICKER} a {x}% de ruptura ({precio objetivo})

Ejecutado hoy: {nada | COMPRA TICKER $x @ precio, stop y | VENTA ...}
Breakers: {OK | activo: motivo}
```
~~~

**POR esto:**

~~~
## Formato de salida (Telegram, máximo 15 líneas)

Clasifica el mensaje ANTES de escribirlo. Precedencia 🔴 > 🟢 > 🟡 > ⚪:
- 🔴 ALERTA: breaker o kill switch activo, stop GTC no colocado, orden rechazada por `review_equity_order`.
- 🟢 EJECUTADO: se movió dinero hoy (compra, venta 50%, stop recolocado).
- 🟡 OBSERVACIÓN: sin movimiento, pero algún ticker a ≤3% de su banda, o una posición cruzó +1R/+2R, o el régimen está risk-off.
- ⚪ SIN CAMBIOS: nada que hacer y nada a ≤3%.

Reglas de escritura (obligatorias):
- La línea 1 empieza por la clase. Es lo único visible en la notificación del móvil.
- La línea 2 es un titular ≤70 caracteres: qué se hizo, o la causa concreta de no hacer nada. Nunca "sin novedad".
- El bloque ▸ TICKET solo se escribe si la clase es 🟢. Si no hubo ejecución, se omite entero: no escribas "Ejecutado: nada".
- NO escribas líneas de normalidad. Nada de "Breakers: OK", "Régimen: ON", "Invalidación: OK". Su ausencia es el OK.
- ▸ PRÓXIMO solo si el ticker más cercano está a ≤3% de su banda y hay hueco de posición. Si no, se omite.
- 🔴 EXCEPCIÓN es la última línea y solo existe si hay una activa; incluye el efecto operativo, no solo la causa.
- `riesgo_pct` se calcula sobre el valor real de la cuenta de hoy (`get_portfolio`), no sobre una constante.
- Texto plano: sin Markdown, sin sangrías, sin tabuladores, sin líneas vacías salvo la que separa el titular del cuerpo.

```
{🟢 EJECUTADO|🟡 OBSERVACIÓN|⚪ SIN CAMBIOS|🔴 ALERTA} · AGENTIC · {DD-mmm}
{titular ≤70 car.}

▸ TICKET {COMPRA|VENTA 50%|STOP↑} {TICKER}
  ${monto} · {acciones} acc @ ${precio_fill}
  Stop ${stop} · riesgo ${riesgo_usd} = {riesgo_pct}% del capital
  Gatillo: cierre ${close} > Donchian20 ${banda_sup} · ATR14 ${atr}
  Stop GTC: {✓ viva #{order_id} | ✗ NO COLOCADA}
▸ RIESGO {n}/2 pos · ${expuesto} ({expo_pct}%) · cash ${cash} ({cash_pct}%)
  {TICKER} {+|-}{x.x}% · {+|-}{y.y}R · stop ${stop} · {✓|✗ SIN STOP}
▸ CUENTA ${valor} · {+|-}{x.x}% día · {+|-}{x.x}% sem
▸ PRÓXIMO {TICKER} rompe en ${precio} ({x.x}% arriba)
🔴 EXCEPCIÓN {tipo}: {motivo} → {efecto operativo}
```
~~~

*(La línea 44, `Escribe el mensaje final en el archivo ...`, se queda igual.)*

---

### 5.2 `eth_scan_prompt.md` — bloque "Formato de salida (Telegram, máximo 12 líneas)"

**REEMPLAZAR esto:**

~~~
## Formato de salida (Telegram, máximo 12 líneas)
```
🪙 ETH SCAN — {fecha}
Precio: ${precio} | Swing90d: ${swing} | DD: {x}%
Tramos: [{estado de los 4: ✓ ejecutado / · pendiente / ◦ activo}]
Acumulado (Agentic): {eth} ETH @ ${coste_medio}
Hoy: {nada | COMPRA tramo {n}: ${monto} @ ${precio} | BLOQUEADO: motivo}
Invalidación: {OK | técnica activa | fundamental activa}
Siguiente tramo: {n} a ${precio_objetivo} ({y}% más abajo)
```
~~~

**POR esto:**

~~~
## Formato de salida (Telegram, máximo 15 líneas)

Clasifica el mensaje ANTES de escribirlo. Precedencia 🔴 > 🟢 > 🟡 > ⚪:
- 🔴 ALERTA: sin fondos para el tramo activo, invalidación técnica o fundamental, preview con alerta o spread >1%.
- 🟢 COMPRADO: se ejecutó un tramo hoy.
- 🟡 ZONA ACTIVA: hay un tramo en banda pero no se compró por una razón rutinaria (ya se compró un tramo hoy).
- ⚪ SIN CAMBIOS: ningún tramo en banda.

Reglas de escritura (obligatorias):
- La línea 1 empieza por la clase. Es lo único visible en la notificación del móvil.
- La línea 2 es un titular ≤70 caracteres: tramo e importe si se compró, o la causa concreta de no comprar.
- El bloque ▸ TICKET solo se escribe si la clase es 🟢; si no, se omite entero.
- La cabecera de la escalera usa el lookback REAL del config: "▸ ESCALERA (máx {swing_lookback_days}d ${swing_high})". No escribas "Swing90d" ni ningún número de días fijo.
- Los importes de cada tramo salen de `tranche_pcts × capital_usd` (hoy: $600 / $750 / $900 / $750).
- NO escribas líneas de normalidad: nada de "Invalidación: OK".
- El "próximo tramo" va en la última línea de datos y se omite si hay un tramo activo hoy (escribe "tramo activo hoy").
- 🔴 EXCEPCIÓN es la última línea y solo existe si hay una activa; incluye el efecto operativo, no solo la causa.
- Texto plano: sin Markdown, sin sangrías, sin tabuladores, sin líneas vacías salvo la que separa el titular del cuerpo.

```
{🟢 COMPRADO|🟡 ZONA ACTIVA|⚪ SIN CAMBIOS|🔴 ALERTA} · ETH · {DD-mmm}
{titular ≤70 car.}

▸ TICKET COMPRA TRAMO {n}/4
  ${monto} · {eth} ETH @ ${precio} · spread {x.xx}%
  Nivel {dd_nivel}% desde máx · banda ±{band}% · preview {✓ limpio|✗ alerta}
▸ ESCALERA (máx {lookback}d ${swing_high})
  T1 −30% ${p1} · ${m1} · {✓ {dd-mmm} | ▶ ACTIVO | ◻ pendiente}
  T2 −40% ${p2} · ${m2} · {✓ {dd-mmm} | ▶ ACTIVO | ◻ pendiente}
  T3 −50% ${p3} · ${m3} · {✓ {dd-mmm} | ▶ ACTIVO | ◻ pendiente}
  T4 −60% ${p4} · ${m4} · {✓ {dd-mmm} | ▶ ACTIVO | ◻ pendiente}
▸ POSICIÓN {eth} ETH · coste ${coste_medio} · mkt ${valor_mkt} · {+|-}{x.x}%
▸ CAPITAL ${desplegado} de ${capital} · ${reserva} en reserva
▸ ETH ${precio} · {dd}% desde máx · próximo T{n} a ${precio} ({x.x}% abajo)
🔴 EXCEPCIÓN {tipo}: {motivo} → {efecto operativo}
```
~~~

*(La última línea, `Escribe el mensaje final en ...`, se queda igual, pero el máximo pasa de 12 a 15 líneas.)*

---

### 5.3 Corrección de etiqueta (opcional, no cambia ninguna regla de trading)

En `eth_scan_prompt.md`, sección **Reglas (no negociables)**:

**REEMPLAZAR:**
```
- Swing high = máximo cierre de los últimos `swing_lookback_days` (90) días: ...
```
**POR:**
```
- Swing high = máximo cierre de los últimos `swing_lookback_days` días del config (hoy 365): ...
```

Motivo: el valor efectivo siempre sale del JSON (`365`); el `(90)` del texto es un residuo que contradice el `_comment` del propio config y es el origen de la etiqueta falsa "Swing90d" en la alerta. El comportamiento del motor no cambia.

**Nota relacionada (fuera del alcance de este documento):** `mcp/lib.js:164` devuelve el campo `swing_high_90d` aunque lea `swing_lookback_days=365`. Si algún día la alerta se genera desde `ethZones()` en lugar de a mano, ese nombre de campo reintroduce el bug D-E2. Renombrarlo a `swing_high` es un cambio de código, no de prompt.

---

## 6. Checklist de aceptación

Un mensaje es válido si cumple las 8:

1. La primera palabra clasifica el mensaje (🔴/🟢/🟡/⚪).
2. La primera línea responde "¿tengo que hacer algo?" sin abrir el mensaje.
3. No hay ninguna línea que confirme normalidad.
4. Si hubo ejecución, existe bloque ▸ TICKET con importe, precio, stop, riesgo en $ y en % del capital real.
5. Si hay posiciones abiertas, cada una muestra su stop y si la orden está viva.
6. Ningún número aparece sin unidad ni referencia.
7. ≤15 líneas, ≤1 línea en blanco, sin sangrías ni Markdown.
8. Los mismos datos siempre en las mismas líneas y con los mismos prefijos.
