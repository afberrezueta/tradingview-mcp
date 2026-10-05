# Plan: evaluación de Claude Commerce Agents para mi e-commerce

> Documento de planificación. **No se ha escrito código ni se ha instalado nada en tu negocio.**
> Fecha de la investigación: 5 de octubre de 2026.
> Repositorio revisado: `anthropics/commerce-agents` (último commit del 31 de agosto de 2026, licencia Apache 2.0).

---

## 0. Antes de empezar: falta un dato tuyo

El campo **"Mi negocio: [DESCRIBE AQUÍ…]"** llegó vacío. Por eso el documento evalúa tres escenarios y te dice qué cambia en cada uno:

| Escenario | Código en este documento |
|---|---|
| Tienda en **Shopify** | **S** |
| **Amazon FBA** (u otro marketplace) | **A** |
| **Web propia** (WooCommerce, código propio, etc.) | **W** |

Cuando me digas qué vendes, dónde, cuánto vendes al mes y en qué país, ajusto el plan a tu caso y descarto lo que no aplique.

**Tiempo disponible que asumo:** 5–10 horas por semana. **Nivel que asumo:** nuevo en Claude Code y en programación.

---

## 1. Estudio de factibilidad

### 1.1 Qué es el blueprint (en lenguaje sencillo)

Es un **proyecto de referencia**: código de ejemplo que muestra cómo construir dos asistentes con Claude. No es un producto que se instala y funciona solo. Tú (o un desarrollador) tienes que **conectarlo a tus sistemas**: catálogo, carrito, pedidos, inventario.

El mismo README lo dice: *"This is a reference implementation; it is not maintained and does not accept contributions."* Es decir, Anthropic no lo va a actualizar ni a corregir errores. Si lo usas, el mantenimiento es tuyo.

Lo que trae:

| Pieza | Qué es |
|---|---|
| `shopping-agent/` | El **agente comprador**: el chat que ve tu cliente en tu tienda |
| `merchant-agent/` | El **agente comerciante**: el asistente que usas tú (o tu equipo) para administrar la tienda |
| `commerce-common/` | Piezas compartidas: seguridad, memoria, configuración |
| `examples/` | 4 tiendas de demostración ficticias (retail, viajes, telecom, entradas) con su web en Next.js |
| `plugins/commerce-builder/` | Un **plugin de Claude Code** que te entrevista y genera el esqueleto de tu propio agente |
| `docs/` | `backends.md` (cómo conectar tus sistemas), `safety.md` (reglas de seguridad), `deployment.md` (dónde desplegar) |

Tecnología: Python 3.11+ (backend) y Node 22 / Next.js (páginas web). Modelos por defecto: **Claude Sonnet 5** para el agente comprador, **Claude Opus 5** para el comerciante y **Claude Haiku 4.5** para la memoria.

Se puede ejecutar de tres maneras: con la **Messages API** (tú alojas el servidor), con el **Agent SDK**, o con **Managed Agents** (Anthropic aloja el agente y él llama a tu servidor).

### 1.2 El agente comprador (para tus clientes)

Tiene cinco "habilidades" (carpeta `shopping-agent/skills/`):

1. **Búsqueda y descubrimiento** — "busco una tienda de campaña para dos personas por menos de 250 $".
2. **Investigación de compra** — compara productos y explica diferencias.
3. **Planificación** — arma una lista para un objetivo ("lo que necesito para acampar").
4. **Atención al cliente** — estado de pedidos, políticas de devolución, envíos.
5. **Memoria y personalización** — recuerda preferencias que el cliente le dio.

Puntos importantes:

- **No cobra ni crea pedidos.** La herramienta `checkout` solo muestra el carrito y te pasa el enlace a **tu** checkout (o al checkout alojado de la plataforma). El pago siempre lo hace tu sistema.
- Para conectarlo tienes que programar una clase llamada `StorefrontBackend` con métodos como `search_products`, `get_product_details`, `add_to_cart`, `get_orders`, `search_policies`, `checkout_handoff`.
- Se puede empezar pequeño: implementar solo búsqueda y detalle de producto y dejar el resto apagado.

### 1.3 El agente comerciante (para ti)

Cinco habilidades (`merchant-agent/skills/`):

1. **Rendimiento** — "¿por qué bajaron las ventas esta semana?" (resumen, métricas, análisis con SQL).
2. **Catálogo y fichas** — detectar y corregir fichas incompletas.
3. **Inventario** — alertas de stock bajo, propuestas de reposición.
4. **Precios y promociones**.
5. **Campañas de marketing** — borradores.

Punto clave de seguridad: **todo cambio queda "en espera"** hasta que una persona lo aprueba. El agente propone; tú apruebas. Para conectarlo hay que programar `MerchantBackend` (8 métodos de lectura y varios de escritura). Un piloto puede ser **solo lectura**.

### 1.4 ¿Encaja con tu caso?

El blueprint asume que **tú controlas la tienda**: catálogo, carrito y checkout propios, y una web donde poner el chat.

| | **S — Shopify** | **A — Amazon FBA** | **W — Web propia** |
|---|---|---|---|
| Agente comprador | **Aplica, con trabajo.** Shopify ya ofrece un servidor MCP de tienda (Storefront MCP) con catálogo, carrito y políticas que tu backend puede llamar. Tienes que alojar el servidor y meter el chat en tu tema. | **No aplica.** No puedes poner tu propio chat dentro de Amazon. En Amazon, el asistente de compra es el de Amazon (Rufus, ahora "Alexa for Shopping"). Lo que sí puedes hacer es **optimizar tus fichas** para que ese asistente las recomiende. | **Aplica y es donde más sentido tiene**, pero tienes que programar todo el puente con tu catálogo y tu carrito. |
| Agente comerciante | Aplica. Pero Shopify ya incluye **Sidekick** gratis en el panel, que cubre parte de esto. | **Técnicamente posible** (el README dice que puede actuar como vendedor en un marketplace), **pero Amazon lanzó el 23/09/2026 un plugin oficial para Claude** (Amazon Selling Partner, beta en EE. UU., requiere plan Professional) que ya hace inventario, precios, fichas y analítica sin programar. Construirlo tú sería reinventar algo que ya existe. | Aplica. Tendrías que conectar tu analítica, inventario y pedidos. |
| Veredicto | **Viable pero no prioritario**: primero prueba lo que Shopify ya te da gratis. | **El blueprint no es para ti como vendedor de Amazon.** Usa el plugin oficial de Amazon + Claude. | **Viable** si tienes volumen y preguntas de clientes complejas. |

**Si vendes en varios canales** (por ejemplo, Amazon + Shopify), el agente comprador solo sirve para el canal propio.

### 1.5 Costos estimados

**API de Claude** (precios oficiales, verificados en platform.claude.com/docs, octubre 2026; USD por millón de tokens):

| Modelo | Entrada | Salida | Lectura de caché |
|---|---|---|---|
| Claude Sonnet 5 (comprador) | $2 | $10 | $0,20 |
| Claude Opus 5 (comerciante) | $5 | $25 | $0,50 |
| Claude Haiku 4.5 (memoria) | $1 | $5 | $0,10 |

**Mi estimación** (no es un dato oficial; depende de cuánto hable cada cliente y del tamaño de tu catálogo):

| Concepto | Estimación |
|---|---|
| Una conversación de cliente (5–6 mensajes, con caché activa) | ~$0,03 – $0,10 |
| 1.000 conversaciones/mes | ~$30 – $100/mes |
| Agente comerciante: un resumen diario + algunas preguntas | ~$10 – $40/mes |
| Hosting del backend (servidor pequeño: Railway, Render, Fly.io o un VPS) | ~$5 – $25/mes |
| Web del chat (Vercel; el plan gratuito no permite uso comercial, Pro cuesta ~$20/mes por persona) | $0 – $20/mes |
| Dominio, monitoreo básico | $0 – $15/mes |
| **Total mensual del blueprint en producción pequeña** | **~$50 – $200/mes** |
| **Pruebas iniciales** (ejecutar la demo y experimentar) | **~$5 – $20 en créditos de API** |

El costo grande **no es el dinero sino el tiempo**: ver la sección 4.

Para comparar:

- Chatbots ya hechos para Shopify: desde gratis (Shopify Inbox) hasta ~$100–$500/mes.
- Plugin oficial de Amazon para Claude: el conector no tiene costo publicado; necesitas un plan de Claude (Pro ~$20/mes) y el plan Professional de Amazon que ya pagas.

### 1.6 Riesgos técnicos

| Riesgo | Gravedad | Explicación sencilla |
|---|---|---|
| **No tiene mantenimiento** | Alta | Nadie va a corregir errores ni actualizar dependencias. Quedan bajo tu responsabilidad. |
| **Faltan piezas de producción** | Alta | El propio `docs/safety.md` dice que las demos **no tienen autenticación** ni límites de uso. Tú tendrías que añadir: inicio de sesión, límites contra abuso, manejo de datos personales y registros. |
| **Curva de aprendizaje** | Alta (para alguien nuevo) | Python, TypeScript/Next.js, APIs, despliegue. Claude Code ayuda mucho, pero hay que entender lo que se publica. |
| **Respuestas incorrectas del agente** | Media | El blueprint trae buenas defensas (solo afirma precios que salen de tus datos, cercado de texto de terceros), pero hay que **probarlo con preguntas reales** antes de abrirlo a clientes (lo que el plugin llama *evals*). |
| **Costos que crecen** | Media | Un bot abusado o un catálogo muy grande puede disparar el gasto. Pon un límite de gasto en la consola de Anthropic desde el primer día. |
| **Plataforma cambiante** | Media | Shopify cambió su API de catálogo en 2026 (deprecó un endpoint en abril, migración hasta junio). Amazon acaba de abrir su plugin en beta. Las integraciones cambiarán. |
| **Seguridad de claves** | Media | La clave de la API de Claude y las credenciales de la tienda nunca deben subirse a GitHub. |
| **Privacidad / legal** | Depende del país | La memoria del cliente es dato personal (GDPR en Europa, leyes locales en LatAm). Necesitarás aviso de privacidad. |

---

## 2. Alternativas

Comparo cuatro opciones. Puntuación del 1 (malo) al 5 (excelente) **para tu situación** (5–10 h/semana, principiante).

| | **Opción 1: Blueprint tal cual** | **Opción 2: Agente propio simple con la API de Claude** | **Opción 3: Chatbot ya hecho** | **Opción 4 (híbrida): Herramientas ya hechas + Claude con conectores oficiales** |
|---|---|---|---|---|
| Qué es | Clonar `commerce-agents`, usar `/scaffold-commerce-agent`, conectar tus sistemas, desplegar | Un chat pequeño (una página + un servidor) que responde con tu catálogo y tus políticas en un archivo | Shopify Inbox (gratis), Tidio Lyro (desde ~$39/mes), Rep AI (~$99/mes), Gorgias, etc. | Cliente: chatbot ya hecho (S/W) o fichas optimizadas para Rufus (A). Tú: Claude con el conector oficial (plugin de Amazon Selling Partner, o MCP de Shopify) |
| Tiempo hasta algo usable | 2–4 meses | 3–6 semanas | 1 semana | 1–2 semanas |
| Horas totales estimadas | 60–120 h | 25–50 h | 5–10 h | 10–20 h |
| Costo mensual | $50–200 | $20–80 | $0–150 | $20–150 |
| Control y personalización | 5 | 3 | 2 | 3 |
| Riesgo técnico | 2 | 3 | 5 | 5 |
| Encaje con Amazon (A) | 1 | 1 | 1 | **5** |
| Encaje con Shopify (S) | 3 | 3 | **5** | **5** |
| Encaje con web propia (W) | **4** | 4 | 4 | 4 |
| Probabilidad de éxito con tu tiempo | Baja–media | Media | **Alta** | **Alta** |

### Recomendación

**Opción 4 (híbrida)**, aunque no sea la que propusiste. Razones:

1. **Te da resultados en 1–2 semanas**, no en meses, y con poco riesgo.
2. **Usa piezas oficiales y mantenidas** (Amazon, Shopify, Anthropic) en vez de un código de referencia sin mantenimiento.
3. **Mide primero si hay demanda real**: si el chatbot ya hecho recibe pocas preguntas o no sube ventas, construir el blueprint no habría tenido sentido.
4. **No cierra la puerta al blueprint**: queda como Fase 4 opcional, con criterios claros para decidir si vale la pena.

Según tu escenario:

- **A (Amazon):** plugin oficial de Amazon en Claude para la gestión + optimizar fichas para Rufus/Alexa for Shopping. **No construir el blueprint.**
- **S (Shopify):** Shopify Inbox (gratis) o un chatbot de pago para clientes + Sidekick y Claude con conector de Shopify para ti. El blueprint, solo si tras 2–3 meses ves que las herramientas ya hechas se quedan cortas.
- **W (web propia):** chatbot ya hecho para empezar. Es el escenario donde el blueprint tiene más posibilidades de compensar más adelante.

---

## 3. Estudio de mercado

> **Cómo leer esta sección:** separo los **datos verificados** (fuente oficial o primaria que pude comprobar) de las **afirmaciones** (cifras de empresas que venden estas herramientas o de blogs, sin estudio público que las respalde). Trata las afirmaciones con escepticismo.

### 3.1 Datos verificados

| Dato | Fuente |
|---|---|
| Precios de la API: Sonnet 5 $2/$10, Opus 5 $5/$25, Haiku 4.5 $1/$5 por millón de tokens. El precio de Sonnet 5 queda fijo (se canceló la subida prevista para el 1/09/2026). | [Página oficial de precios de Anthropic](https://platform.claude.com/docs/en/about-claude/pricing) |
| Amazon anunció el 23/09/2026 (Accelerate) un plugin de Seller Assistant para Amazon Quick y Claude. | [About Amazon (oficial)](https://www.aboutamazon.com/news/innovation-at-amazon/seller-assistant-plugin-amazon-quick-claude) |
| Shopify presentó su Spring '26 Edition centrada en *agentic commerce* (catálogo legible por agentes, Universal Commerce Protocol). | [Shopify News (oficial)](https://www.shopify.com/news/spring-26-edition-dev) |
| Shopify Inbox es gratuito en la App Store y se describe como un asistente de ventas con IA en la tienda. | Ficha de la Shopify App Store (citada en guías del sector; confirma el precio en la App Store antes de decidir) |
| El blueprint no cobra, no crea pedidos y no cambia listados sin aprobación humana; no trae autenticación. | Código y `README.md` / `docs/safety.md` del repo (revisados directamente) |

### 3.2 Afirmaciones de empresas o de terceros (no verificadas)

| Afirmación | Quién lo dice | Comentario |
|---|---|---|
| "El chat con IA multiplica la conversión por 4 (12,3 % vs 3,1 %)" | Alhena (vende asistentes de compra) | Interés comercial directo. Probablemente hay sesgo de selección: quien abre el chat ya tenía más intención de compra. |
| "Los comercios ven +10–20 % de conversión entre quienes usan el asistente y +10–15 % en ticket medio" | Destilabs y otros proveedores | Rango típico de marketing, sin metodología pública. |
| "El tráfico que llega desde asistentes de IA convierte un 42 % mejor" (Adobe) | Blogs que citan a Adobe | Habla de visitas que **llegan** desde ChatGPT/Perplexity, no de un chat **en tu tienda**. Es otra cosa. |
| "El 45 % de compradores usa IA para descubrir productos" (NRF/Salesforce) | Blogs que citan la encuesta | Encuesta, no comportamiento medido. Indica tendencia, no ventas. |
| "Rufus: más de 250 M de usuarios; quien lo usa convierte un 60 % más" | Herramientas para vendedores de Amazon, citando a Amazon | Las cifras de uso vienen de Amazon; la de conversión no la pude confirmar en fuente primaria. |
| "Optimizar fichas para Rufus da +20–35 % de conversión en 30–60 días" | Agencias y herramientas de Amazon | Afirmación de quien vende el servicio. |
| "Las tiendas Shopify se hicieron visibles en ChatGPT, Copilot y Gemini por defecto (5,6 M de tiendas)" | Blogs de agencias | Plausible y coherente con el anuncio oficial, pero el número exacto no lo verifiqué. |
| Precios de chatbots (Tidio desde ~$39/mes con Lyro, Rep AI ~$99/mes, Gorgias + ~$0,90–1 por resolución) | Comparativas de blogs (eesel.ai, tidio.com, etc.) | Cambian a menudo. Confírmalos en la App Store antes de pagar. |

### 3.3 Competidores y soluciones similares

| Tipo | Ejemplos | Para quién |
|---|---|---|
| Asistentes nativos de plataforma | Shopify Inbox (cliente), Shopify Sidekick (comerciante), Amazon Rufus/Alexa for Shopping (comprador en Amazon), Amazon Seller Assistant + plugin de Claude (vendedor) | Quien ya está en esa plataforma: el punto de partida más barato |
| Chatbots de ventas/soporte para tiendas | Tidio (Lyro), Gorgias, Rep AI, Zipchat, Ochatbot, Richpanel | Tiendas Shopify/Woo pequeñas y medianas |
| Plataformas de agentes de soporte | Intercom Fin y similares | Volumen alto de tickets |
| Construir a medida | Blueprint `commerce-agents`, Agent SDK, Managed Agents | Tiendas con catálogo complejo, necesidades específicas o equipo técnico |

### 3.4 ¿Hay demanda real para tu tipo de negocio?

**No puedo responder bien sin saber qué vendes.** Señales generales:

- La tendencia hacia la compra asistida por IA es real y la están empujando Amazon y Shopify (verificado).
- El beneficio de un chat en tu tienda **depende mucho del producto**: rinde más donde el cliente necesita consejo (tallas, compatibilidades, cosmética, suplementos, electrónica, equipamiento) y menos en productos simples o de compra por impulso.
- **La forma más fiable de saberlo es medir tu propio caso**: cuántas preguntas te hacen hoy los clientes (email, WhatsApp, mensajes de Amazon) y de qué tipo. Eso está en la Fase 0 del plan.

---

## 4. Plan de trabajo completo

### 4.1 Resumen de fases

| Fase | Objetivo | Horas | Semanas (a 5–10 h/sem) |
|---|---|---|---|
| **0. Diagnóstico** | Definir tu caso y medir el punto de partida | 4–6 h | Semana 1 |
| **1. Primer entregable** | Algo que puedas probar en menos de una semana | 4–8 h | Semana 1 |
| **2. Piloto de cara al cliente** | Asistente para clientes (S/W) u optimización de fichas (A) | 10–20 h | Semanas 2–4 |
| **3. Asistente de gestión para ti** | Claude + conector oficial, solo lectura y luego cambios con aprobación | 8–15 h | Semanas 3–6 |
| **4. (Opcional) Blueprint** | Solo si las fases 2–3 justifican construir algo propio | 60–120 h | Semanas 7–20 |
| **5. Medición y decisión** | Comparar con el punto de partida y decidir siguiente paso | 2–4 h por revisión | Cada mes |

### 4.2 Fase 0 — Diagnóstico (semana 1, 4–6 h)

Tareas:

1. Completar la descripción del negocio: qué vendes, canales, pedidos/mes, país, idioma de tus clientes.
2. Recopilar **30–50 preguntas reales** de clientes de las últimas semanas (email, chat, mensajes de Amazon, redes). Copiarlas en una hoja de cálculo.
3. Clasificarlas: ¿producto/recomendación?, ¿estado de pedido?, ¿devoluciones?, ¿envíos?
4. Anotar tu punto de partida: tasa de conversión, ticket medio, horas por semana que dedicas a responder y a tareas de gestión (inventario, precios, fichas).

Herramientas: hoja de cálculo (Google Sheets/Excel). Sin código.

**Por qué importa:** esas 30–50 preguntas serán tu "examen" para cualquier asistente que pruebes, sea ya hecho o propio.

### 4.3 Fase 1 — Primer entregable (menos de una semana, 4–8 h)

Elige **una** según tu escenario:

- **A (Amazon):** conectar el **plugin oficial de Amazon Selling Partner** en Claude (requiere plan Professional; está en beta en EE. UU.; si vendes en otro país, comprueba disponibilidad). Pedirle: "dame un resumen de ventas y stock de esta semana y dime qué fichas tienen problemas". Resultado: un **informe semanal** que antes hacías a mano.
- **S (Shopify):** activar **Shopify Inbox** (gratis) en tu tienda y pasarle tus 30 preguntas de prueba. En paralelo, probar Sidekick en tu panel con preguntas de gestión. Resultado: **un chat funcionando** y una hoja con qué respuestas fueron buenas o malas.
- **W (web propia):** probar la versión gratuita de un chatbot (por ejemplo, Tidio) con tus políticas y 20 productos; pasarle las 30 preguntas. Resultado: el mismo que en S.
- **Alternativa para "ver" el blueprint (cualquier escenario):** ejecutar la demo `retail` en tu ordenador con Claude Code (1–2 h, ~$2–5 en créditos de API). Sirve para entender qué hace, **no** para tu tienda todavía.

**Criterio de éxito:** al menos 70 % de tus preguntas de prueba con respuesta correcta, o un informe que te ahorre más de 1 h por semana.

### 4.4 Fase 2 — Piloto de cara al cliente (semanas 2–4, 10–20 h)

- **S/W:** dejar el chatbot activo 2–3 semanas. Revisar cada semana las conversaciones. Ajustar políticas y preguntas frecuentes. Medir: conversaciones, preguntas que derivó a humano, ventas atribuidas.
- **A:** reescribir las 5–10 fichas principales en lenguaje natural que responda las preguntas reales de clientes (lo que los asistentes como Rufus usan para recomendar). Puedes usar Claude para redactar y el plugin de Amazon para aplicar los cambios **con tu aprobación**. Medir conversión por ficha antes y después.

### 4.5 Fase 3 — Asistente de gestión para ti (semanas 3–6, 8–15 h)

1. Conectar el conector oficial (Amazon Selling Partner o el de Shopify) a Claude.
2. Empezar **solo lectura**: resumen semanal, alertas de stock, fichas con problemas.
3. Pasar después a **cambios con aprobación**: borradores de precios, promociones o reposiciones que tú confirmas.
4. Guardar las instrucciones que más usas como un *prompt* fijo o una skill para repetirlas cada semana.

### 4.6 Fase 4 — Blueprint (opcional, semanas 7–20, 60–120 h)

**Solo pasar a esta fase si se cumplen al menos dos condiciones:**

- Tienes más de ~300–500 conversaciones de clientes al mes.
- Las herramientas ya hechas fallan en algo concreto y repetido (catálogo con muchas variantes, recomendaciones técnicas, varios idiomas, reglas propias).
- Tienes tienda propia (S o W). **No aplica a A.**
- Tienes presupuesto para ~$50–200/mes y para un desarrollador si te atascas.

Sub-fases:

| Paso | Tarea | Herramientas / repos | Horas |
|---|---|---|---|
| 4.1 | Instalar Python 3.11, Node 22; clonar el repo; ejecutar la demo | `anthropics/commerce-agents`, Claude Code | 3–5 |
| 4.2 | Instalar el plugin y ejecutar `/scaffold-commerce-agent` (te entrevista sobre tu stack) | Plugin `commerce-builder` | 3–5 |
| 4.3 | Implementar solo `search_products` y `get_product_details` contra tu catálogo (en S: Storefront MCP de Shopify) | Tu repositorio nuevo en GitHub | 15–25 |
| 4.4 | Crear el examen automático con tus 30–50 preguntas: `/author-commerce-evals` | Plugin `commerce-builder` | 6–10 |
| 4.5 | Añadir carrito y entrega al checkout de la plataforma (`checkout_handoff`) | Docs `backends.md` | 10–20 |
| 4.6 | Lo que el blueprint no trae: autenticación, límites de uso, aviso de privacidad, registros | `docs/safety.md` | 10–25 |
| 4.7 | Desplegar backend (Railway/Render/Fly) y web (Vercel); límite de gasto en la consola de Anthropic | — | 6–12 |
| 4.8 | Prueba con un 10 % del tráfico, revisar conversaciones, ajustar | — | 6–15 |

A 5–10 h por semana, esto son **entre 2 y 5 meses**. Por eso va al final y es opcional.

### 4.7 Fase 5 — Medición y decisión (mensual)

Comparar con el punto de partida de la Fase 0: conversión, ticket medio, horas ahorradas por semana, costo mensual. Regla simple: **si el ahorro más las ventas extra no superan el costo (incluido tu tiempo) en 2–3 meses, simplificar o parar.**

### 4.8 Lista de herramientas y repositorios

| Herramienta | Para qué | Fase |
|---|---|---|
| Hoja de cálculo | Preguntas de prueba y métricas | 0–5 |
| Claude (claude.ai, plan Pro) + conectores oficiales | Asistente de gestión | 1, 3 |
| Plugin Amazon Selling Partner (A) | Gestión de Amazon desde Claude | 1, 3 |
| Shopify Inbox / Sidekick (S) | Chat para clientes / gestión | 1–3 |
| Chatbot de terceros (Tidio, Rep AI, Gorgias…) (S/W) | Chat para clientes | 1–2 |
| Claude Code | Ejecutar la demo y, si llega, construir el blueprint | 1 (opcional), 4 |
| `anthropics/commerce-agents` + plugin `commerce-builder` | Blueprint | 4 |
| Cuenta en la consola de Anthropic (clave API + límite de gasto) | Blueprint / demo | 1 (opcional), 4 |
| GitHub (repo privado propio) | Guardar tu agente | 4 |
| Railway / Render / Fly.io, Vercel | Alojar el agente | 4 |

---

## 5. Próximos pasos (necesito tu aprobación)

1. **Dime tu caso**: qué vendes, dónde (Shopify / Amazon / web propia), pedidos o ventas por mes, país.
2. **Confirma la recomendación** (Opción 4, híbrida) o dime si prefieres otra.
3. Con eso, ajusto este documento a tu escenario y te guío en el **primer entregable** paso a paso.

Hasta que lo apruebes no se instala nada ni se escribe código.

---

### Fuentes

- Repositorio revisado: https://github.com/anthropics/commerce-agents (README, CLAUDE.md, `docs/backends.md`, `docs/safety.md`, `docs/deployment.md`, `plugins/commerce-builder/README.md`, `*/backend.py`, `*/config.py`)
- [Precios oficiales de la API de Claude](https://platform.claude.com/docs/en/about-claude/pricing)
- [Amazon: Seller Assistant plugin para Amazon Quick y Claude](https://www.aboutamazon.com/news/innovation-at-amazon/seller-assistant-plugin-amazon-quick-claude)
- [The Next Web: Amazon Seller Assistant plugin brings seller data to Claude](https://thenextweb.com/news/amazon-seller-assistant-plugin-claude-quick)
- [Shopify: Agentic commerce for every developer, Spring '26 Edition](https://www.shopify.com/news/spring-26-edition-dev)
- [Gamut: Shopify MCP Developer's 2026 Setup Guide](https://www.gamut.so/blog/shopify-mcp-guide)
- [eesel.ai: 8 best AI chatbot apps for Shopify in 2026](https://www.eesel.ai/blog/best-shopify-chatbot-apps)
- [Tidio: 13 Best Shopify Chatbot Apps for 2026](https://www.tidio.com/blog/shopify-chatbot/)
- [Ringly: AI sidekick for Shopify](https://www.ringly.io/blog/ai-sidekick-shopify)
- [Jarvio: Amazon Rufus, what sellers need to know in 2026](https://jarvio.io/blog/amazon-rufus-sellers-guide-2026)
- [Amalytix: Alexa for Shopping (formerly Rufus) 2026](https://www.amalytix.com/en/knowledge/ai/amazon-rufus-guide-2026/)
- [Alhena: AI shopping assistant conversion rates](https://alhena.ai/blog/ai-shopping-assistant-conversion-rates/) (proveedor; afirmaciones no verificadas)
- [Digital Applied: AI traffic converts 42% better](https://www.digitalapplied.com/blog/ai-traffic-converts-42-percent-better-2026-channel-strategy)
- [Destilabs: AI Shopping Assistant cost & ROI](https://www.destilabs.com/blog/ai-shopping-assistant-2026) (proveedor; afirmaciones no verificadas)
