# Plan: empezar un e-commerce desde cero y evaluar Claude Commerce Agents

> Documento de planificación. **No se ha escrito código, no se ha instalado nada y no se ha gastado dinero.**
> Fecha de la investigación: 5 de octubre de 2026 (versión 2).
> Repositorio revisado: `anthropics/commerce-agents` (último commit del 31 de agosto de 2026, licencia Apache 2.0).

---

## 0. Tu punto de partida

| | |
|---|---|
| Producto | **Ninguno todavía** |
| Modelos que te interesan | **Dropshipping**, o encontrar un **producto ganador** y comprarlo **al por mayor** en China o India |
| País fabricante | Se elegirá según el producto |
| Tiempo | 5–10 horas por semana |
| Nivel | Nuevo en Claude Code |

**Aún me faltan tres datos.** Cambian bastante el plan:

1. **¿En qué país venderás?** (Estados Unidos, España, México, Ecuador…). Los aranceles, los impuestos y las plataformas dependen del mercado donde vendes, no de donde vives.
2. **¿Cuánto dinero puedes invertir** sin que te afecte perderlo? (por ejemplo: menos de $1.000, $1.000–5.000, más de $5.000).
3. **¿Tienes ya empresa o RUC/NIF/EIN** para facturar e importar?

Mientras tanto, cuando un dato depende del país uso **Estados Unidos** como ejemplo, porque es donde hay más información pública. Lo marco con 🇺🇸.

---

## 1. Estudio de factibilidad

### 1.1 Primero, lo honesto: el orden correcto

El blueprint **Claude Commerce Agents** sirve para tiendas que **ya existen**: tienen catálogo, carrito, checkout y clientes haciendo preguntas. **Tú todavía no tienes producto ni tienda**, así que hoy el blueprint no tiene nada a lo que conectarse.

El orden que más probabilidades de éxito tiene es:

```
1. Encontrar y validar un producto  →  2. Vender las primeras unidades  →  3. Montar la tienda en serio  →  4. Automatizar con agentes de IA
```

La IA (Claude) **sí te sirve desde el primer día**, pero como **asistente de investigación**, no como agente de tienda. Te ayuda a analizar productos, comparar proveedores, calcular márgenes, redactar fichas y preparar mensajes a fábricas.

### 1.2 Qué es el blueprint (resumen)

Es **código de referencia**, no un producto que se instala y funciona solo. El README dice: *"This is a reference implementation; it is not maintained and does not accept contributions."* Si lo usas, el mantenimiento es tuyo.

| Pieza | Qué hace |
|---|---|
| **Agente comprador** (`shopping-agent/`) | Chat para tus clientes. Busca y compara productos, arma planes, llena el carrito, responde sobre pedidos y políticas, recuerda preferencias. **No cobra**: al final manda al cliente a tu checkout. |
| **Agente comerciante** (`merchant-agent/`) | Asistente para ti. Explica ventas, revisa fichas, alerta de stock, propone precios, promociones y campañas. **Todo cambio espera tu aprobación.** |
| **Plugin `commerce-builder`** | Plugin de Claude Code que te entrevista sobre tu tienda y genera el esqueleto del agente (`/scaffold-commerce-agent`). |
| `docs/` | Cómo conectar tus sistemas, reglas de seguridad y despliegue. |

Tecnología: Python + Next.js. Modelos por defecto: Claude Sonnet 5 (comprador), Opus 5 (comerciante) y Haiku 4.5 (memoria). El propio `docs/safety.md` aclara que las demos **no tienen autenticación ni límites de uso**: eso lo añade quien despliega.

### 1.3 ¿Encaja con tu caso?

| Etapa de tu negocio | ¿Encaja el blueprint? |
|---|---|
| **Ahora** (sin producto) | **No.** No hay catálogo ni clientes. |
| Dropshipping en Shopify con pocas ventas | **No compensa.** Shopify Inbox (gratis) o un chatbot de $0–100/mes hacen lo mismo sin programar. |
| Vendiendo en **Amazon** | **El agente comprador no aplica.** No puedes poner tu propio chat dentro de Amazon; allí el asistente es Rufus / "Alexa for Shopping". Para gestión, Amazon lanzó el 23/09/2026 un **plugin oficial para Claude** (beta en EE. UU., requiere plan Professional) que ya cubre inventario, precios y fichas. |
| **Marca propia en tu web**, con cientos de conversaciones al mes y productos que necesitan consejo | **Sí puede compensar.** Es su caso ideal. Realísticamente, a partir del mes 6–12. |

### 1.4 Factibilidad de los dos modelos de negocio

#### A) Dropshipping

**Qué es:** vendes en tu tienda online y el proveedor envía el producto directamente al cliente. No compras inventario.

| A favor | En contra |
|---|---|
| Poca inversión inicial ($300–1.500) | Márgenes bajos; la publicidad se come gran parte |
| Pruebas varios productos rápido | Envíos más lentos y menos control de calidad |
| No guardas stock | Mucha competencia vendiendo lo mismo |
| Ideal para **validar** si un producto se vende | 🇺🇸 **Desde el 29/08/2025, EE. UU. eliminó la exención "de minimis"** para todos los países: todo paquete paga aranceles, aunque valga menos de $800 (verificado: Orden Ejecutiva 14324, CBP). El dropshipping directo desde China a EE. UU. es mucho menos rentable que antes. |

**Consecuencia práctica 🇺🇸:** si haces dropshipping hacia EE. UU., conviene usar proveedores con **almacén en EE. UU.** (por ejemplo Spocket, Zendrop o los almacenes de CJ Dropshipping en EE. UU.). Así los aranceles se pagan una vez en la importación grande y no en cada paquete.

#### B) Comprar al por mayor (wholesale / marca propia)

**Qué es:** compras un lote a una fábrica (en China o India), lo traes a tu país y lo vendes con tu marca, en tu web o en Amazon FBA.

| A favor | En contra |
|---|---|
| Mejor margen por unidad | Inversión inicial alta (afirmación del sector: $2.500–5.000 como mínimo realista para Amazon FBA de marca propia) |
| Controlas calidad, empaque y marca | Riesgo de quedarte con stock que no se vende |
| Construyes un activo (marca) | Importar exige trámites: código arancelario (HTS), agente de aduanas, certificaciones |
| Envíos rápidos al cliente | Pedido mínimo (MOQ) típico de cientos de unidades |

**Regla clave:** **no compres al por mayor un producto que no hayas validado antes.** Por eso el plan usa el dropshipping (o pocas unidades) como prueba y el wholesale como segundo paso.

#### C) China o India: cómo elegir

| | **China** | **India** |
|---|---|---|
| Fuerte en | Casi todo: electrónica, hogar, herramientas, accesorios, plásticos, gadgets | Textiles y algodón, ropa, cuero, joyería y bisutería, artesanía, decoración, productos naturales |
| Plataformas | Alibaba, 1688 (requiere agente), Made-in-China, ferias de Cantón | IndiaMART, TradeIndia, Alibaba (sección India), exportadores directos |
| Pedido mínimo | Flexible; muchos proveedores aceptan lotes pequeños | Suele ser más alto y menos estandarizado |
| Velocidad y logística | Muy madura (agentes, inspección, fulfillment) | Buena, pero menos ecosistema para pequeños vendedores |
| 🇺🇸 Aranceles | **Más altos** que para casi cualquier otro país; varían mucho según el producto | **Más bajos** que China en general (fuentes del sector hablan de ~10 % de media en 2026) |

⚠️ **Los aranceles cambian a menudo y dependen del código exacto del producto (HTS).** Antes de comprar cualquier lote, confirma la tasa con el buscador oficial (hts.usitc.gov en EE. UU.) o con un agente de aduanas. Las cifras de esta tabla son orientativas.

**Recomendación:** elige primero el **producto** y después el **país** según dónde se fabrique mejor y cuánto arancel paga. Tú mismo lo planteaste así, y es lo correcto.

### 1.5 Costos estimados (Fases 1–3, sin agentes de IA)

| Concepto | Dropshipping (validación) | Wholesale (marca propia) |
|---|---|---|
| Tienda Shopify (plan básico, pago mensual; confirma el precio en tu país) | ~$30–40/mes (suele haber prueba barata los primeros meses) | Igual |
| Claude Pro (asistente de investigación) | ~$20/mes | ~$20/mes |
| App de proveedores (Spocket/Zendrop) | $0–50/mes | — |
| Muestras de producto | $50–200 | $100–300 |
| Publicidad de prueba (Meta/TikTok/Google) | $300–1.000 | $1.000–3.000 |
| Primer lote de inventario | — | $1.500–3.000 (afirmación del sector) |
| Envío internacional, aduana, agente | Incluido por el proveedor | $300–1.000+ |
| Marca, fotos, registro de marca | Opcional | $500–2.000 |
| **Total aproximado** | **$500–1.500** | **$3.000–8.000** |

**Costo de los agentes de IA (solo más adelante):** API de Claude con precios oficiales: Sonnet 5 $2/$10, Opus 5 $5/$25, Haiku 4.5 $1/$5 por millón de tokens (entrada/salida). Mi estimación es de ~$0,03–0,10 por conversación de cliente, y de $50–200/mes para el blueprint en producción pequeña (API + hosting).

### 1.6 Riesgos

| Riesgo | Gravedad | Cómo reducirlo |
|---|---|---|
| **Perder dinero en publicidad sin vender** | Alta | Presupuesto de prueba cerrado (ej. $300) y reglas de "parar" definidas antes de empezar |
| **Elegir un producto saturado** | Alta | Usar la ficha de puntuación de la Fase 1; evitar lo que ya venden miles de tiendas iguales |
| **Aranceles y aduanas** | Alta 🇺🇸 | Calcular el costo puesto en destino ("landed cost") antes de fijar precio; usar almacenes en el país de venta |
| **Proveedor poco fiable** | Media | Pedir muestras, usar pago protegido (por ejemplo Trade Assurance en Alibaba), revisar historial, inspección antes del envío |
| **Productos regulados** | Media | Evitar al principio: suplementos, cosmética, juguetes infantiles, electrónica con baterías, alimentos y productos médicos (exigen certificaciones) |
| **Propiedad intelectual** | Media | No vender copias de marcas ni diseños patentados |
| **Legal e impuestos** | Depende del país | Registrar el negocio y entender el impuesto sobre ventas o IVA de tu mercado |
| **Expectativas irreales** | Alta | Ver la sección 3: la mayoría de tiendas nuevas no llega a ser rentable el primer año |

---

## 2. Alternativas

Comparo cinco caminos. Puntuación del 1 (malo) al 5 (excelente) **para ti**: sin producto, 5–10 h por semana, principiante.

| | **1. Dropshipping directo desde China** | **2. Dropshipping con almacén local + validación** | **3. Wholesale directo (China/India) en Amazon FBA** | **4. Wholesale directo en tu web** | **5. Construir ya el blueprint de agentes** |
|---|---|---|---|---|---|
| Inversión inicial | $300–1.000 | $500–1.500 | $3.000–8.000 | $3.000–8.000 | $50–200/mes + 60–120 h |
| Riesgo de pérdida | Medio | **Bajo** | Alto | Alto | Alto (tiempo) |
| Margen potencial | Bajo 🇺🇸 (aranceles por paquete) | Bajo–medio | Medio–alto | Medio–alto | No aplica sin producto |
| Velocidad para aprender si hay demanda | Rápida | **Rápida** | Lenta (meses) | Lenta | No aplica |
| Encaje con 5–10 h/semana | 4 | **5** | 3 | 2 | 1 |
| Probabilidad de éxito estimada | Baja | **Media** | Media (si el producto está validado) | Baja–media | Muy baja ahora |

### Recomendación

**Camino 2 → luego 3 o 4.** En concreto:

1. **Encuentra 3 productos candidatos** con método (Fase 1), usando Claude como investigador.
2. **Valídalos barato**: dropshipping desde almacén local, o unas pocas unidades, con un presupuesto de publicidad cerrado.
3. **Solo cuando un producto venda de forma repetida** (por ejemplo, 30–50 ventas con margen positivo), **pasa a comprar al por mayor** en China o India, según el producto y el arancel.
4. **Los agentes de IA para clientes vienen después**: primero Shopify Inbox (gratis) y, mucho más adelante, el blueprint si tu marca crece.

Por qué no empezar directamente con wholesale: arriesgas $3.000–8.000 en un producto que nadie ha comprado todavía. Por qué no construir ya el blueprint: no hay tienda ni clientes a los que conectarlo.

---

## 3. Estudio de mercado

> **Cómo leer esta sección:** separo los **datos verificados** (fuente oficial o primaria) de las **afirmaciones** (cifras de empresas que venden herramientas o cursos, sin estudio público). Muchas cifras sobre dropshipping vienen de quien vende software de dropshipping.

### 3.1 Datos verificados

| Dato | Fuente |
|---|---|
| 🇺🇸 EE. UU. suspendió la exención "de minimis" ($800 libres de aranceles) para **todos los países** desde el **29/08/2025**; para China ya se había suspendido en mayo de 2025. Cada envío comercial necesita una declaración aduanera y paga aranceles. | [Casa Blanca, Orden Ejecutiva 14324](https://www.whitehouse.gov/presidential-actions/2025/07/suspending-duty-free-de-minimis-treatment-for-all-countries/), [CBP](https://www.cbp.gov/newsroom/national-media-release/cbp-ready-enforce-end-de-minimis-loophole-securing-borders-and) |
| 🇺🇸 En junio de 2026 la suspensión pasó a ser **indefinida** para envíos que no van por correo postal. | [Federal Register, 24/06/2026](https://www.federalregister.gov/documents/2026/06/24/2026-12670/indefinite-suspension-of-the-de-minimis-exemption-for-merchandise-arriving-through-all-modes-other) |
| Precios de la API de Claude: Sonnet 5 $2/$10, Opus 5 $5/$25, Haiku 4.5 $1/$5 por millón de tokens. | [Anthropic, precios oficiales](https://platform.claude.com/docs/en/about-claude/pricing) |
| Amazon lanzó el 23/09/2026 un plugin de Seller Assistant para Claude y Amazon Quick. | [About Amazon](https://www.aboutamazon.com/news/innovation-at-amazon/seller-assistant-plugin-amazon-quick-claude) |
| Shopify lanzó en 2026 funciones de *agentic commerce*: catálogo legible por asistentes de IA y el Universal Commerce Protocol. | [Shopify News](https://www.shopify.com/news/spring-26-edition-dev) |
| El blueprint no cobra, no crea pedidos, no cambia listados sin aprobación humana y no trae autenticación. | Código y documentación del repo, revisados directamente |

### 3.2 Afirmaciones del sector (no verificadas)

| Afirmación | Quién lo dice | Comentario |
|---|---|---|
| "Solo el 1–5 % de los dropshippers logra un negocio con beneficio constante; el 80–90 % fracasa el primer año" | TrueProfit y blogs del sector | No hay un estudio público con metodología. Aun así, coincide en la dirección: **la mayoría no lo logra**. |
| "Margen neto típico: 10–20 % en productos de menos de $30, 15–25 % entre $30–100, 25–40 % por encima de $100" | TrueProfit, Printful, otros | Interés comercial, pero útil como referencia: **los productos baratos dejan muy poco**. |
| "Un principiante factura $0–2.000 al mes" | TrueProfit (dice haber analizado 1.200 tiendas) | Ojo: es **facturación**, no ganancia. |
| "Mínimo realista para Amazon FBA marca propia: $2.500–5.000; primer lote $1.000–3.000" | Guías de vendedores de Amazon | Rango razonable, pero depende mucho del producto. |
| "Aranceles 🇺🇸 de China: ~25–37,5 % en muchas categorías, más en otras; India ~10 % de media" | Calculadoras y consultoras de aranceles | **Cambian con frecuencia.** Confirma siempre con el código HTS del producto concreto. |
| "Con los aranceles, los proveedores con almacén en EE. UU. (Spocket, etc.) suelen salir más baratos por unidad que el envío directo desde China" | SaleHoo, Spocket y blogs | Lógico tras el fin de "de minimis", pero hay que hacer la cuenta con cada producto. |
| "Shoppers que usan Rufus convierten un 60 % más" | Herramientas para vendedores de Amazon | No lo confirmé en fuente primaria. |

### 3.3 Competidores y herramientas que te encontrarás

| Tipo | Ejemplos | Para qué |
|---|---|---|
| Proveedores de dropshipping | CJ Dropshipping (gratis, almacenes en EE. UU./Europa), Spocket (desde ~$40/mes, almacenes EE. UU./UE), Zendrop ($0–79/mes), AliExpress | Fase 2 (validación) |
| Mayoristas / fábricas | Alibaba, 1688, Made-in-China (China); IndiaMART, TradeIndia (India) | Fase 4 (escala) |
| Investigación de producto | Google Trends, Amazon Best Sellers / Movers & Shakers, TikTok Creative Center, Meta Ad Library; de pago: Jungle Scout, Helium 10, Sell The Trend | Fase 1 |
| Tiendas | Shopify (recomendado para empezar), WooCommerce, Amazon, TikTok Shop, Mercado Libre (LatAm) | Fase 3 |
| Asistentes de IA | Claude (investigación ahora), Shopify Inbox/Sidekick, plugin de Amazon, blueprint Commerce Agents (más adelante) | Todas las fases |

### 3.4 ¿Hay demanda?

Un "producto ganador" no se encuentra en una lista de internet: si aparece en una lista pública, miles de personas ya lo están vendiendo. La demanda **se demuestra con tus propias pruebas**:

- **Señales previas** (gratis): búsquedas estables o crecientes en Google Trends; reseñas en Amazon con quejas que tú puedas resolver; anuncios que llevan meses activos en Meta Ad Library (si alguien paga un anuncio durante meses, probablemente le funciona).
- **Señal real** (con dinero): personas desconocidas que **pagan** por el producto con un presupuesto de anuncios pequeño.

---

## 4. Plan de trabajo completo

### 4.1 Resumen de fases

| Fase | Objetivo | Horas | Semanas (a 5–10 h/sem) | Dinero |
|---|---|---|---|---|
| **0. Bases** | País de venta, presupuesto, reglas de riesgo | 3–5 h | Semana 1 | $0 |
| **1. Investigación de producto** | 20 ideas → 3 finalistas con puntuación | 12–20 h | Semanas 1–3 | $0–20 (Claude Pro) |
| **2. Validación barata** | Muestras + tienda mínima + prueba de anuncios | 15–25 h | Semanas 4–7 | $500–1.500 |
| **3. Tienda en serio** | Marca, fichas, políticas, atención al cliente con IA básica | 15–25 h | Semanas 8–12 | $50–150/mes |
| **4. Wholesale** | Comprar el producto ganador en China o India | 20–40 h | Semanas 12–20 | $2.500–8.000 |
| **5. Agentes de IA avanzados** | Blueprint Commerce Agents u otra opción, si el volumen lo justifica | 60–120 h | Mes 6–12+ | $50–200/mes |

### 4.2 Fase 0 — Bases (semana 1, 3–5 h)

1. Responder las tres preguntas de la sección 0 (país de venta, presupuesto, empresa).
2. Escribir tus **reglas de riesgo** antes de gastar nada. Por ejemplo: "Máximo $300 por producto en anuncios de prueba. Si tras $300 no hay al menos 3 ventas, paro ese producto."
3. Informarte (1–2 h) de qué necesitas legalmente para vender en tu país: registro de negocio e impuestos.

### 4.3 Fase 1 — Investigación de producto (semanas 1–3, 12–20 h)

**Ficha de puntuación** (cada criterio de 1 a 5):

| Criterio | Qué buscar |
|---|---|
| Precio de venta | Entre $30 y $100: deja margen para publicidad |
| Margen | Precio de venta ≥ 3 veces el costo puesto en destino (producto + envío + arancel) |
| Tamaño y peso | Pequeño, ligero, no frágil |
| Problema que resuelve | Resuelve algo concreto o es claramente "wow" en video |
| Competencia | Hay demanda, pero no 500 tiendas idénticas |
| Mejora posible | Las reseñas negativas de la competencia muestran algo que puedes mejorar |
| Regulación | Sin certificaciones complicadas (evitar suplementos, cosmética, juguetes infantiles, baterías, alimentos) |
| Recompra o accesorios | Se vuelve a comprar o permite vender complementos |
| País de fabricación | Se fabrica bien en China o India; arancel razonable |

Tareas:

1. Sacar 20 ideas de Amazon Movers & Shakers, TikTok Creative Center, Meta Ad Library y Google Trends.
2. Pedir a Claude que analice cada una con la ficha: reseñas, rango de precios, posibles códigos arancelarios, regulación.
3. Quedarte con **3 finalistas** y calcular el costo puesto en destino de cada uno.
4. Buscar 2–3 proveedores por finalista: uno de dropshipping con almacén local y uno de fábrica en China o India.

### 4.4 Fase 2 — Validación barata (semanas 4–7, 15–25 h)

1. Pedir **muestras** de los 3 finalistas. Comprobar calidad y grabar tus propios videos y fotos.
2. Crear una **tienda Shopify mínima**: una página de producto, políticas de envío y devolución, y un pago de prueba que funcione.
3. Conectar un proveedor con almacén local (Spocket, Zendrop o CJ) para entregar los pedidos.
4. Lanzar anuncios con el **presupuesto cerrado** de la Fase 0.
5. **Decidir con números:**
   - **Seguir** si hay ventas con margen positivo después de publicidad.
   - **Ajustar** si hay clics pero no ventas (precio, página, fotos).
   - **Parar** si no hay interés.

### 4.5 Fase 3 — Tienda en serio (semanas 8–12, 15–25 h)

- Nombre y marca simple, fotos propias, fichas bien escritas (Claude te ayuda a redactarlas).
- Activar **Shopify Inbox** (gratis) para atender a clientes. Este es tu primer "agente" de IA, sin programar.
- Usar **Sidekick** (incluido en Shopify) y Claude para el resumen semanal de ventas.
- Guardar todas las preguntas de clientes: serán el "examen" de cualquier agente futuro.

### 4.6 Fase 4 — Wholesale (semanas 12–20, 20–40 h)

**Pasar a esta fase solo si:** el producto lleva al menos 30–50 ventas con margen positivo y tienes el capital sin endeudarte.

1. Elegir el país (China o India) según calidad, MOQ y arancel del código HTS exacto.
2. Pedir cotizaciones a 3–5 fábricas. Claude puede redactar los mensajes en inglés y comparar las respuestas.
3. Pedir muestras finales con tu marca y empaque.
4. Pagar con protección (Trade Assurance o similar) y contratar una **inspección antes del envío**.
5. Contratar un **agente de aduanas o transitario** (freight forwarder) para importar.
6. Enviar el stock a tu almacén, a un 3PL o a Amazon FBA.

### 4.7 Fase 5 — Agentes de IA avanzados (mes 6–12+)

Revisar el blueprint **Claude Commerce Agents** solo cuando:

- Tengas tienda propia con **más de ~300–500 conversaciones de clientes al mes**.
- Las herramientas ya hechas se queden cortas en algo concreto.
- Tengas presupuesto ($50–200/mes) y tiempo (60–120 h), o un desarrollador.

Pasos en ese momento:

1. Clonar el repo.
2. Ejecutar la demo `retail`.
3. Instalar el plugin `commerce-builder`.
4. Ejecutar `/scaffold-commerce-agent`.
5. Conectar solo búsqueda y detalle de producto.
6. Crear el examen con tus preguntas reales (`/author-commerce-evals`).
7. Añadir autenticación y límites.
8. Desplegar con un límite de gasto.

Si vendes en **Amazon**, usa el plugin oficial de Amazon para Claude en lugar del blueprint.

### 4.8 Primer entregable (menos de una semana, sin gastar dinero)

**"Tabla de 10 productos candidatos con puntuación y 3 finalistas"**, en una hoja de cálculo:

| Producto | Precio de venta | Costo estimado puesto en destino | Margen | País de fabricación | Puntuación (ficha 4.3) | Proveedores encontrados | Riesgos |
|---|---|---|---|---|---|---|---|

Cómo lo haremos juntos (unas 4–6 horas en total):

1. Me dices país de venta, presupuesto y 2–3 temas que te gusten (por ejemplo: mascotas, cocina, deporte, hogar).
2. Yo investigo en la web y propongo 10 candidatos con datos y fuentes.
3. Tú revisas cada uno (Amazon, TikTok, Alibaba/IndiaMART) y ajustas las puntuaciones.
4. Elegimos 3 finalistas para pedir muestras en la Fase 2.

Este entregable no requiere instalar nada ni pagar nada, y puedes probarlo de inmediato: es la base de todo lo demás.

### 4.9 Herramientas y repositorios

| Herramienta | Para qué | Fase |
|---|---|---|
| Claude (claude.ai, plan Pro) | Investigación, cálculos, mensajes a proveedores, redacción | 1–5 |
| Hoja de cálculo | Ficha de productos, costos, resultados | 0–5 |
| Google Trends, Amazon Best Sellers, TikTok Creative Center, Meta Ad Library | Ideas y señales de demanda | 1 |
| Alibaba / IndiaMART | Fábricas | 1, 4 |
| Spocket / Zendrop / CJ Dropshipping | Dropshipping con almacén local | 2 |
| Shopify (+ Inbox, Sidekick) | Tienda, atención y gestión | 2–3 |
| Buscador arancelario oficial (ej. hts.usitc.gov 🇺🇸) y agente de aduanas | Costo de importación | 1, 4 |
| `anthropics/commerce-agents` + plugin `commerce-builder` | Agentes avanzados | 5 |

---

## 5. Próximos pasos (necesito tu aprobación)

1. Responde las tres preguntas de la sección 0: **país de venta, presupuesto, empresa**.
2. Dime **2–3 temas** que te interesen o conozcas (te da ventaja vender algo que entiendes).
3. Confirma si apruebas el camino recomendado: **validar con dropshipping desde almacén local y luego pasar a wholesale**.

Con eso preparo el **primer entregable** (tabla de 10 candidatos). Hasta que lo apruebes no se instala nada, no se escribe código y no se gasta dinero.

---

### Fuentes

**Oficiales**
- [Casa Blanca: Suspending Duty-Free De Minimis Treatment for All Countries (EO 14324)](https://www.whitehouse.gov/presidential-actions/2025/07/suspending-duty-free-de-minimis-treatment-for-all-countries/)
- [CBP: ready to enforce end of de minimis](https://www.cbp.gov/newsroom/national-media-release/cbp-ready-enforce-end-de-minimis-loophole-securing-borders-and)
- [Federal Register: Indefinite Suspension of the De Minimis Exemption (24/06/2026)](https://www.federalregister.gov/documents/2026/06/24/2026-12670/indefinite-suspension-of-the-de-minimis-exemption-for-merchandise-arriving-through-all-modes-other)
- [Anthropic: precios de la API](https://platform.claude.com/docs/en/about-claude/pricing)
- [About Amazon: Seller Assistant plugin para Claude](https://www.aboutamazon.com/news/innovation-at-amazon/seller-assistant-plugin-amazon-quick-claude)
- [Shopify: Spring '26 Edition](https://www.shopify.com/news/spring-26-edition-dev)
- Repositorio: https://github.com/anthropics/commerce-agents (README, CLAUDE.md, `docs/backends.md`, `docs/safety.md`, `docs/deployment.md`, plugin `commerce-builder`)

**Del sector (afirmaciones, leer con cautela)**
- [TrueProfit: Dropshipping success rate 2026](https://trueprofit.io/blog/dropshipping-success-rate)
- [Printful: How profitable is dropshipping](https://www.printful.com/blog/how-profitable-is-dropshipping)
- [SaleHoo: Best dropshipping suppliers, new tariff reality](https://www.salehoo.com/learn/directories-for-the-best-dropshipping-wholesale-suppliers)
- [Shopify blog: Dropshipping suppliers](https://www.shopify.com/blog/dropshipping-suppliers)
- [Seller Metrics: Amazon FBA private label cost](https://sellermetrics.app/amazon-fba-private-label/)
- [Tax Foundation: Trump tariffs tracker](https://taxfoundation.org/research/all/federal/trump-tariffs-trade-war/)
- [Ginger Control: Importing from India, tariffs](https://gingercontrol.com/blog/importing-from-india-tariff-guide)
- [Zonos: US tariff tracker](https://zonos.com/docs/guides/us-tariff-changes)
- [eesel.ai: Shopify chatbot apps 2026](https://www.eesel.ai/blog/best-shopify-chatbot-apps)
- [Jarvio: Amazon Rufus 2026](https://jarvio.io/blog/amazon-rufus-sellers-guide-2026)
