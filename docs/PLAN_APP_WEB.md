# Plan: App + Página Web

> Plan para convertir este proyecto (el puente MCP entre Claude y TradingView Desktop) en un **producto**: una aplicación de escritorio y una página web pública.
> Lo armamos con cuatro "expertos" en paralelo (estrategia de producto, arquitectura, diseño y riesgos) y luego unimos sus conclusiones. Donde no estaban de acuerdo, aquí está la decisión y el porqué.

---

## 0. Resumen en 30 segundos

- **Qué es:** un *copiloto de trading con IA, en español*, que lee tu gráfico de TradingView y te ayuda a prepararte, practicar y revisar. **No da señales ni ejecuta órdenes reales**: tú decides.
- **Para quién (primero):** traders de futuros (ES/NQ) hispanohablantes que hacen evaluaciones de *prop firms*. Pagan $100–500 por evaluación y fallan por disciplina y preparación.
- **Producto:** app de escritorio (Windows + macOS) + web en español (landing, demo, lista de espera, docs, página de compatibilidad).
- **Negocio:** *open-core*. El MCP sigue siendo gratis y abierto; la app Pro cuesta **$19/mes** o **$149/año**, y hay una preventa de fundadores.
- **Antes de cobrar:** **cambiar el nombre** (no se puede usar "TradingView" en la marca) y obtener la **opinión de un abogado** sobre los Términos de TradingView y sobre la regulación de valores en Ecuador.

---

## 1. Lo que haría un experto del top 0.1% distinto a la mayoría

1. **Validar antes de construir.** Las 3 primeras semanas son solo landing + entrevistas + preventa. Si no hay demanda, no se escribe la app.
2. **Vender lo que el código abierto no da:** cero configuración, compatibilidad garantizada (arreglos en <48 h cuando TradingView se actualice) y flujos guiados en español. Las 84 herramientas no se venden: ya son gratis.
3. **La confianza es el producto.** Cada número muestra de dónde salió. Nada se cambia en el gráfico sin tu confirmación. Nunca hay "COMPRA YA".
4. **Riesgo legal primero, código después.** Los riesgos más grandes son de marca y regulatorios, no técnicos.
5. **Medir una sola cosa:** las *Sesiones Guiadas Semanales* (ver §7).

---

## 2. Producto

### Propuesta de valor
> "Tu coach de trading con IA dentro de TradingView, en español: plan pre-mercado, práctica en replay y revisión post-sesión, sin configurar nada."

### MVP de la app

| Prioridad | Qué incluye |
|---|---|
| **Debe tener** | Instalador firmado de un clic · abre TradingView con el puerto de depuración y verifica la conexión · registra el MCP en Claude automáticamente · avisa si tu versión de TradingView no es compatible · 3 flujos en español: **Brief Pre-mercado**, **Coach de Replay**, **Revisión Post-sesión** · diario local de sesiones y P&L del replay |
| **Debería tener** | Brief diario programado · pack de Pine Script · opción en inglés |
| **No tendrá (v1)** | App móvil · órdenes reales o conexión a broker · datos de mercado en la nube · cuentas multiusuario · marketplace |

### Pantallas de la app
- **Copiloto:** chat con respuestas en tarjetas (Niveles, Indicadores, Acción del precio), cada una con su fuente y el botón "Ver en gráfico".
- **Brief del gráfico:** una sola pantalla con cotización, indicadores, líneas/etiquetas/tablas de Pine y resumen de velas. Arriba, un reloj indica qué tan frescos son los datos.
- **Pine Studio:** el código con diferencias, errores marcados en la línea, consola e historial de versiones.
- **Coach de Replay:** selector de fecha, controles de paso/auto, barra de posición y P&L, y notas del coach en cada operación.
- **Escáner:** tabla de varios símbolos con cambio %, rango y miniaturas.
- **Diario:** línea de tiempo con capturas, sesiones de replay y respuestas guardadas; se puede exportar.
- **Ajustes:** estado de la conexión, qué hace la IA sola y qué te pregunta, colores de subida/bajada, tema.
- **Barra de estado fija:** conexión · símbolo/temporalidad · latencia · antigüedad de los datos.

---

## 3. Diseño (UX/UI)

### Principios
1. **Calma en la volatilidad.** Nada parpadea. Un cambio de precio se muestra como un tinte suave de 600 ms.
2. **Mostrar la certeza.** Cada dato lleva fuente, hora y nivel de certeza: *Observado*, *Inferido* o *Especulativo*.
3. **Denso pero tranquilo.** Números en fuente monoespaciada tabular y un solo elemento llamativo por pantalla.
4. **Asistente, no oráculo.** Se habla de "niveles" y "contexto", nunca de "señales". Sin dorados, sin neón, sin cuentas regresivas.
5. **Tú decides.** La IA puede leer libremente; para cambiar algo tiene que proponerlo y tú confirmarlo.

### Patrón clave: Proponer → Previsualizar → Confirmar
Para cambiar el gráfico (símbolo, dibujos, indicadores, alertas, operaciones de replay), la IA muestra una **tarjeta de propuesta**, por ejemplo "Agregar línea horizontal en 24,550". **Enter** aplica, **Esc** descarta y **⌘Z** deshace. Las operaciones de trading **siempre** preguntan, sin opción de "permitir siempre".

### Datos viejos (staleness)
| Antigüedad | Cómo se ve |
|---|---|
| 0–5 s | normal |
| 5–60 s | texto atenuado + icono de reloj |
| >60 s | patrón rayado + botón "Actualizar"; la certeza baja un nivel |

### Tokens de diseño (claro / oscuro)
- **Subida:** azul `#0A6CD6` / `#5AA9FF`. **Bajada:** naranja `#B85400` / `#FF9F43`. Son seguros para daltonismo y van siempre con ▲/▼ y signo +/−. Rojo/verde queda como opción.
- **Fondo:** `#FFFFFF` / `#0E0F11` · **Texto:** `#1D1D1F` / `#F2F2F4`.
- **Tipografía:** SF Pro / SF Mono (cifras tabulares). Tamaños de la app: 11 · 12 · 13 · 15 · 17 · 22 · 28.
- **Espaciado:** base de 4 pt (4, 8, 12, 16, 24, 32, 48, 64). Radios de 6 en controles y 10 en tarjetas.
- **Movimiento:** 120 ms (hover), 200 ms (paneles), 320 ms con resorte (hojas). Con "reducir movimiento" solo hay fundidos.
- **Liquid Glass** solo en la barra de herramientas, la barra lateral y la hoja de propuesta. **Nunca detrás de números.**
- **Regla:** todos los pares de colores pasan WCAG AA.

### Página web
- **Hero:** un gráfico real con el panel del copiloto al lado. Aparece la propuesta "¿Marcar PDH 24,550?", el cursor confirma y la línea aparece en el gráfico.
  - Título: **"Un copiloto que lee tu gráfico. Tú tomas las decisiones."**
  - CTA: "Descargar" · "Ver en GitHub" · "Unirme a la lista".
- **Orden de secciones:**
  1. Hero
  2. Cómo funciona (diagrama: Claude → MCP → TradingView)
  3. 5 funciones con capturas reales
  4. **Confianza**: corre local, no enviamos tus datos, tú apruebas todo, no es asesoría financiera
  5. **Estado de compatibilidad** (qué versiones de TradingView funcionan)
  6. Changelog
  7. FAQ
  8. Precios (desde la Fase 2)
- **Prohibido:** testimonios de ganancias y capturas de P&L.

---

## 4. Arquitectura

### La restricción clave
TradingView solo es controlable **desde la computadora del usuario** (CDP en `localhost:9222`). Una web en la nube **no puede ni debe** controlarlo. Por eso **la computadora del usuario es el servidor**: un proceso local usa `src/core` y la web solo sirve para marketing, descargas, documentación y licencias.

```
App de escritorio ──(socket local)──► Daemon local (Node, usa src/core) ──CDP──► TradingView Desktop
                                            │
                                            └──► Claude (con la clave del usuario o Claude Desktop)
Web (Astro en Vercel): landing · docs · compatibilidad · licencias (Stripe/Paddle)
```

### Decisión: ¿SwiftUI (solo Mac) o Tauri (Windows + Mac)?
Los expertos no coincidieron: Arquitectura proponía SwiftUI nativo para Mac y Estrategia proponía Tauri con Windows primero.
**Decisión: Tauri para la v1, con el lenguaje visual de Apple.**
- Muchos traders de futuros en Latinoamérica usan Windows.
- Con Tauri, la app y la web comparten el mismo sistema de diseño (HTML/CSS).
- El daemon no tiene interfaz, así que una versión nativa en SwiftUI se puede agregar después sin reescribirlo.
- **Se verifica en la Fase 0:** el formulario de la lista de espera pregunta el sistema operativo. Si más del 70 % usa Mac, cambiamos a SwiftUI.

### La IA
- **v1:** el usuario usa **su propio Claude** (Claude Desktop o su propia clave API, guardada en el llavero del sistema). No tenemos costo de IA y el margen ronda el 90 %.
- **Modelos:** `claude-sonnet-5-5` por defecto · `claude-haiku-5-5` para resúmenes y comentarios en replay · `claude-opus-5-5` solo si el usuario lo activa, para revisar estrategias o Pine complejo.

### Datos
**Sin nube en la v1.** Todo se guarda en SQLite local: `journal_entry`, `replay_session`, `agent_run`, `pine_snapshot`. Usamos IDs ULID y borrado suave, para poder agregar sincronización en la v2 sin migraciones.

### Seguridad (no negociable)
1. TradingView se abre con `--remote-debugging-address=127.0.0.1`, y el daemon rechaza cualquier host que no sea local.
2. El daemon escucha en un **socket Unix** (permisos 0600), no en un puerto TCP.
3. **Inyección de prompts:** las etiquetas y tablas de Pine las escriben terceros. Todo lo que viene del gráfico se marca como *dato no confiable*, nunca como instrucción, y tiene límite de longitud.
4. **Niveles de permiso en el código, no en el prompt:**
   - *lectura* → automático
   - *cambiar gráfico* → se confirma una vez por sesión
   - *guardar Pine, alertas, layouts, operaciones de replay, `ui_click`* → se confirma **siempre**, mostrando el antes y el después
5. **Anti-alucinación:** cada precio que cita la IA se valida contra los datos leídos. Si no está en ellos, se rechaza.
6. Instaladores firmados y notarizados, con actualización automática.

### Estructura del monorepo
```
packages/core         ← src/core actual (exportar también stream, tab, pane, update)
packages/mcp-server   ← src/server.js + src/tools
packages/cli          ← src/cli
packages/daemon       ← bucle del agente, permisos, SQLite, socket local
packages/shared       ← esquemas, niveles de riesgo por herramienta
apps/desktop          ← Tauri
apps/web              ← Astro + funciones de Vercel (licencias)
```

---

## 5. Riesgos y cómo mitigarlos (de mayor a menor)

| # | Riesgo | Mitigación |
|---|---|---|
| 1 | **Marca y Términos de TradingView.** El propio README dice "no explotar comercialmente". | Cambiar el nombre ya, sin logo ni estética de TradingView; usar como mucho "funciona con…". Pedir la opinión de un abogado o buscar un acuerdo de partner **antes de cobrar**. Si no es viable, lanzar gratis y vender servicios relacionados (cursos, comunidad). |
| 2 | **Una actualización de TradingView rompe todo** | Prueba automática nocturna contra la última versión, interruptor de apagado por herramienta y respaldo con captura de pantalla. Solo planes mensuales, sin prometer disponibilidad. |
| 3 | **Regulación de asesoría de inversiones** (Ecuador: Superintendencia de Compañías, Valores y Seguros; también EE. UU., la UE, Brasil y México) | Describir, nunca recomendar. Bloquear palabras como "compra", "vende", "objetivo" o "tamaño". Pedir la opinión de un abogado local y lanzar solo en mercados revisados. |
| 4 | **Demandas por pérdidas** | Operar como empresa (S.A.S.), no como persona. Responsabilidad limitada a lo pagado, aceptación de "no es asesoría" al primer uso y nunca ejecutar órdenes reales. |
| 5 | **Seguridad** (puerto 9222 abierto, inyección de prompts) | Ver §4: seguridad. |
| 6 | **Costo de la IA** | El usuario trae su propio Claude. Si algún día nosotros pagamos la IA: cuotas por usuario y modelo barato primero. |
| 7 | **Tiendas de apps** | Solo descarga directa, con Stripe o Paddle como *merchant of record* (se encarga del IVA). |

### Criterios para parar o pivotar
1. Si TradingView envía una carta de cese o rechaza la alianza → pivotar a datos con licencia (Polygon, Alpaca, IBKR) o a su librería oficial de gráficos.
2. Si el abogado dice que hace falta registrarse como asesor y el modo "solo describir" deja el producto sin valor → cambiar a producto educativo.
3. Si la conexión se rompe más de 1 vez por trimestre o un arreglo tarda más de 72 h → replantear la dependencia.

---

## 6. Hoja de ruta

| Fase | Semanas | Qué se hace | Para pasar a la siguiente fase |
|---|---|---|---|
| **0 · Validar** | 0–3 | Nuevo nombre · landing en español + demo de 60 s · lista de espera (pregunta el SO) · 15 entrevistas · consulta legal | ≥300 en la lista · ≥60 % hispanohablantes · ≥25 preventas de fundador ($199, máximo 150) · revisión legal hecha |
| **1 · Beta privada** | 4–10 | App con los 3 flujos · 50 usuarios · página de compatibilidad | ≥70 % llega a su primer brief en <10 min · ≥40 % sigue activo en la semana 4 · ≥3 flujos por usuario por semana · arreglos en <48 h |
| **2 · Lanzamiento pago** | 11–20 | Precios públicos · alianzas con comunidades de trading | ≥150 usuarios de pago · ≥$2.5k MRR · prueba→pago ≥15 % · churn <8 % · ≥2 alianzas |
| **3 · Expandir** | 20+ | Inglés · segmento de desarrolladores Pine · versión nativa para Mac | — |

---

## 7. Métricas

- **North Star:** **Sesiones Guiadas Semanales**, es decir, los días de trading en que el usuario completa al menos un flujo (brief, replay o revisión).
- **Activación:** % de instalaciones con un flujo exitoso en menos de 24 h.
- **Confiabilidad:** % de chequeos de conexión que pasan y % de llamadas a herramientas que funcionan.
- **Retención:** % de usuarios activos en la semana 4.
- **Conversión:** % de pruebas que pasan a pago.

---

## 8. Cómo lo ejecutamos con agentes y skills (automático)

| Paso | Agentes y skills |
|---|---|
| Validación y mensajes | `agentic-council:Strategist`, `marketing:competitive-brief`, `herald-messaging-strategy`, `searchfit-seo:content-strategy` |
| Legal | `agentic-council:Guardian`, `legal:compliance-check`, `legal:legal-risk-assessment` (+ un abogado humano) |
| Fundamentos de diseño | MCP `hig` → `hig_get_tokens`, `apple-design` → `hig_search`, `better-design` → `resolve-design-system "Apple"` |
| Sistema de diseño | `agentic-council:design-system-architecture`, `figma:figma-generate-library` |
| Pantallas + web | `figma:figma-generate-design`, `detent` (animaciones), `figma-use-motion` |
| Crítica | `design:design-critique`, `agentic-council:visual-audit` |
| Accesibilidad | `design:accessibility-review`, `agentic-council:a11y-audit`, `tesserai check_contrast` |
| Textos | `design:ux-copy` (propuestas y avisos legales en español) |
| Construcción | `agentic-council:Architect`, `engineering:system-design`, `figma:figma-design-to-code` |
| Seguridad | `agentic-council:threat-model`, `security-review`, `hawkscan` |
| Calidad | `engineering:testing-strategy`, `code-review` |
| Lanzamiento | `engineering:deploy-checklist`, Vercel (web), `product-tracking-skills:product-tracking-design-tracking-plan` |

---

## 9. Próximos 7 días (concreto)

1. Elegir **3 nombres** sin "TradingView" y comprobar que los dominios estén libres.
2. Agendar **consulta legal** (Términos de TradingView + regulación de valores en Ecuador).
3. Publicar la **landing en español** con lista de espera y pregunta del sistema operativo.
4. Hacer **5 entrevistas** con traders de prop firms.
5. Crear en Figma los **tokens de diseño** y el **hero** de la web.
