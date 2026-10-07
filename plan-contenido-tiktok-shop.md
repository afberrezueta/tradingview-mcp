# Plan de contenido para TikTok Shop

> Fecha: 7 de octubre de 2026 · Mercado: **Estados Unidos** · Herramienta de producción: **Higgsfield** (plan Pro, 610 créditos)
> Continúa el plan de e-commerce (`plan-commerce-agent.md` y `productos-candidatos.md`, en la rama `claude/commerce-agents-evaluation-2a5wh2`).
> **Objetivo:** usar el contenido de TikTok para **validar** los 3 finalistas antes de Black Friday (27 de noviembre de 2026) y quedarte solo con el que venda.

---

## 0. Dónde estás hoy

| | Estado |
|---|---|
| Producto | 3 finalistas, **sin validar**: rulos sin calor + scrunchies, alfombra olfativa para perros, neceser organizador |
| Muestras físicas | **No pedidas todavía** |
| Cuenta de TikTok conectada a Higgsfield | **Ninguna** (verificado hoy con `tiktok_accounts`) |
| Cuenta de vendedor de TikTok Shop | Por confirmar |
| Créditos de Higgsfield | 610 |

**El bloqueo principal es físico, no creativo:** sin muestras no hay fotos reales del producto, y sin fotos reales no se puede producir contenido honesto para la tienda (ver sección 1).

---

## 1. Reglas que no se negocian

1. **El producto que aparece en el video tiene que ser el producto real.** Higgsfield parte de **tus fotos de la muestra**. No generes un producto "parecido" ni lo mejores con IA: si el cliente recibe algo distinto de lo que vio, tendrás devoluciones, malas reseñas y penalizaciones de TikTok Shop.
2. **Nada de reseñas falsas.** Un avatar o un actor de IA **no puede decir "yo lo usé y me cambió la vida"**. La regla de la FTC contra reseñas y testimonios falsos (en vigor desde octubre de 2024) prohíbe los testimonios inventados, también los generados con IA. La IA sí puede **presentar** o **demostrar** el producto, sin hacerse pasar por un cliente.
3. **Etiqueta el contenido generado con IA.** Activa la etiqueta "AI-generated" de TikTok al publicar cualquier video con personas o escenas realistas generadas por IA.
4. **Nada de promesas que no puedas probar.** Por ejemplo: "rizos en 5 minutos", "cura la ansiedad de tu perro" o "dura para siempre".
5. **Las reseñas reales salen de personas reales:** clientes y creadores afiliados (sección 6).

---

## 2. Fase 0: preparativos (semana del 7 al 13 de octubre)

| # | Tarea | Quién | Tiempo |
|---|---|---|---|
| 1 | Crear o confirmar tu **cuenta de vendedor de TikTok Shop US** (seller.us.tiktok.com) con los datos de tu corporación (EIN, cuenta bancaria de la empresa) | Tú | 1 h + días de aprobación |
| 2 | Crear o convertir tu cuenta de TikTok en **cuenta de empresa** y vincularla a la tienda | Tú | 15 min |
| 3 | **Conectar la cuenta de TikTok a Higgsfield** con el enlace que te paso en el chat | Tú, con 1 clic | 5 min |
| 4 | **Pedir muestras** de los 3 finalistas a un proveedor con almacén en EE. UU. (CJ Dropshipping, Spocket o Zendrop) | Tú | 1 h, ~$150 |
| 5 | Mientras llegan: revisar 10 videos que vendan bien de cada producto en TikTok y anotar el gancho de los primeros 3 segundos | Tú (o Claude, si le pasas los enlaces) | 1–2 h |

> Si TikTok Shop tarda en aprobarte, publica igual los videos de la sección 4 en la cuenta normal. Sirven para medir el interés antes de tener el carrito activo.

---

## 3. Fase 1: grabación real (el día que llegan las muestras, ~30 min por producto)

Con el móvil, en vertical (9:16), con luz de ventana y fondo limpio:

| Toma | Para qué |
|---|---|
| 3 fotos del producto sobre **fondo blanco** (de frente, de lado y abierto o en uso) | Imagen principal de la ficha y referencia para Higgsfield |
| 2 fotos en un ambiente real (baño, tocador, salón con el perro) | Referencia de estilo para Higgsfield |
| 10–15 s de **tus manos usando el producto** | Prueba real del producto; se monta con las tomas de IA |
| 10 s del **resultado** (rizos por la mañana, perro buscando premios, neceser lleno y cerrado) | La toma más importante: demuestra que funciona |
| 5 s de unboxing | Para el formato "lo que llegó" |

Sube las fotos al chat y yo las paso a Higgsfield.

---

## 4. Fase 2: producción con Higgsfield (por producto)

| Pieza | Herramienta de Higgsfield | Cantidad | Uso |
|---|---|---|---|
| Fotos de ficha (fondo blanco y escenas de uso) | Flujo `product-photoshoot`, a partir de tus fotos | 5–6 imágenes | Ficha de TikTok Shop |
| Videos de producto de 12–15 s (demostración, antes y después, unboxing) | Marketing Studio Video (`marketing_studio_video`) con tu foto del producto | 3 videos | Publicaciones orgánicas y anuncios |
| Variantes de gancho (los primeros 3–4 s) del video que mejor funcione | Ad Multiplier, modo `sections` → `hook` | 3 variantes | Pruebas A/B en anuncios |
| Videos de presentación con avatar (sin testimonio, con etiqueta de IA) | Flujo `ugc-video`, formato "product-only voiceover" o tutorial | 1–2 | Explicar cómo se usa |
| Montaje final con tus tomas reales, subtítulos y música comercial | Flujo `video-montage` y música de TikTok (`tiktok_music_trending`) | — | Todas las piezas |

### Presupuesto de créditos (610 en total)

| Bloque | Créditos | Regla |
|---|---|---|
| Producto 1 (rulos) | 150 | Pido un presupuesto (*quote*) antes de cada generación de video y no paso del bloque sin avisarte |
| Producto 2 (alfombra olfativa) | 150 | Igual |
| Producto 3 (neceser) | 150 | Igual |
| Reserva para el ganador (más variantes de cara a Black Friday) | 160 | Solo se usa cuando un producto pase la regla de "escalar" de la sección 7 |

> No sé el costo exacto en créditos de cada modelo hasta pedir el presupuesto con tu foto real; por eso trabajo con bloques fijos.

---

## 5. Guiones y ganchos (listos para producir)

Todos están pensados para durar 12–15 s: **gancho (0–3 s) → demostración (3–10 s) → resultado y llamada a la acción (10–15 s)**.

### Producto 1: rulos sin calor + scrunchies de satén ($27,99)

| # | Gancho (texto en pantalla y voz) | Demostración | Cierre |
|---|---|---|---|
| A | "Me fui a dormir así…" (cabeza con el rulo) | Corte a cámara rápida: cómo se enrolla en 20 s | "…y me desperté así." Rizos reales + "Link en el carrito naranja" |
| B | "Deja de quemarte el pelo con la plancha" | Plancha tachada → rulo de satén | Resultado + "Pack con 3 scrunchies incluido" |
| C | "Lo que llegó en mi pack de $28" | Unboxing: rulo, scrunchies, bolsa de satén | Primer uso + precio en pantalla |

### Producto 2: alfombra olfativa para perros ($32,99)

| # | Gancho | Demostración | Cierre |
|---|---|---|---|
| A | "Mi perro se come la comida en 30 segundos" | Esconder premios en la alfombra | El perro buscando (toma real) + "Ahora tarda 10 minutos" (solo si lo mediste) |
| B | "5 minutos de esto = perro cansado" | Perro olfateando en cámara lenta | "Juego de olfato para días de lluvia" + carrito |
| C | "¿Tu perro destroza todo cuando se aburre?" | Antes: cojín roto (escena de IA, etiquetada) → alfombra | Toma real del perro + oferta |

### Producto 3: neceser organizador de viaje ($34,99)

| # | Gancho | Demostración | Cierre |
|---|---|---|---|
| A | "Todo mi maquillaje en una bolsa" | Llenar el neceser en cámara rápida | Cerrado y en la maleta + "Ideal para regalo" |
| B | "POV: tu neceser actual" (caos) | Del caos al neceser ordenado | Compartimentos en primer plano + precio |
| C | "Regalo de Navidad por menos de $35" | Unboxing tipo regalo | "Llega antes de Navidad" (solo si el proveedor lo garantiza) |

---

## 6. Fase 3: publicación (del 21 de octubre al 16 de noviembre)

| | Plan |
|---|---|
| Frecuencia orgánica | 1–2 videos al día **por cuenta**, rotando los 3 productos (unos 3–4 videos por producto a la semana) |
| Horario | Pruébalo tú: 12:00–14:00 y 19:00–22:00, hora del este de EE. UU., y quédate con el que mejor funcione |
| Cómo publicar | Higgsfield → `tiktok_prepare_publish` (abre un formulario para revisar el texto, elegir la música y activar la etiqueta de IA antes de publicar). **Ningún video se publica sin tu aprobación.** |
| Anuncios | GMV Max o Spark Ads de TikTok sobre el video orgánico que mejor funcione, **con el límite ya fijado de $300 por producto** |
| Afiliados | Activa el plan de afiliados de TikTok Shop (comisión del 10–20 %) y envía muestras gratis a 5–10 creadores pequeños (5.000–50.000 seguidores) por producto. **Sus videos son las reseñas reales que tú no puedes fabricar.** |
| Directos (LIVE) | Opcional: un directo de 30 min a la semana con el producto ganador desde noviembre |

---

## 7. Fase 4: medir y decidir (cada lunes)

| Métrica | Dónde verla | Señal buena | Señal mala |
|---|---|---|---|
| Retención a los 3 s | TikTok Analytics | > 50 % | < 30 % → cambiar el gancho |
| % de visionado completo | TikTok Analytics | > 25 % | < 10 % → acortar el video |
| Clics al producto / vistas | TikTok Shop Seller Center | > 1 % | < 0,3 % |
| Conversión (pedidos / clics) | Seller Center | > 2 % | < 0,5 % → revisar precio, ficha y reseñas |
| Costo por venta en anuncios | Ads Manager | < margen bruto (~$20) | > margen bruto → parar |

> Estos umbrales son **referencias del sector, no reglas oficiales de TikTok**. Úsalos para comparar tus 3 productos entre sí.

### Reglas de decisión (el 16 de noviembre)

- **Escalar:** el producto con **≥ 30 ventas y costo por venta menor que el margen**. Recibe la reserva de 160 créditos, más presupuesto de anuncios y el empuje de Black Friday.
- **Mantener en orgánico:** ventas, pero con anuncios que no salen rentables. Sigue solo con publicaciones orgánicas y afiliados.
- **Cortar:** < 5 ventas después de $300 en anuncios y unos 15 videos. Sustitúyelo por el candidato #4 o #5 de `productos-candidatos.md`.

---

## 8. Calendario

| Semana | Qué pasa |
|---|---|
| 7–13 oct | Fase 0: cuentas, conectar TikTok a Higgsfield, pedir muestras |
| 14–20 oct | Llegan las muestras → Fase 1 (grabación) → Fase 2 (producción del producto 1) |
| 21–27 oct | Producción de los productos 2 y 3 · empiezan las publicaciones orgánicas · se envían muestras a afiliados |
| 28 oct – 9 nov | Anuncios de prueba ($300 por producto) · revisión cada lunes |
| 10–16 nov | Decisión: escalar, mantener o cortar |
| 17–30 nov | Todo al ganador: variantes de gancho, contenido de regalo, Black Friday (27 nov) y Cyber Monday (30 nov) |
| Dic | Contenido de Navidad con el ganador; decidir si pasa a compra al por mayor (regla de 30–50 ventas del plan general) |

---

## 9. Qué puedo hacer yo (Claude) y qué te toca a ti

| Claude puede | Te toca a ti |
|---|---|
| Producir fotos y videos en Higgsfield a partir de tus fotos | Pedir las muestras y grabar las tomas reales |
| Escribir guiones, textos, hashtags y fichas de producto | Crear la cuenta de vendedor y aprobar cada publicación |
| Preparar cada publicación en TikTok (`tiktok_prepare_publish`) | Pulsar "publicar" y gestionar los anuncios y los pagos |
| Analizar tus métricas si me pegas los números o capturas | Hablar con los creadores afiliados |
| Pedir presupuesto de créditos antes de cada generación | Decidir con las reglas de la sección 7 |
