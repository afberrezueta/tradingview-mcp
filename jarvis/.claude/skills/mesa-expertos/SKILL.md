---
name: mesa-expertos
description: Convocar una mesa de expertos — varios agentes con ángulos distintos (operador, producto, growth, finanzas, técnico, riesgo, abogado del diablo) opinan en paralelo sobre una decisión y un sintetizador escribe un memo con una decisión y tres acciones. Usar cuando Andres diga "mesa de expertos", "convoca la mesa", "consulta a los expertos", "segunda opinión", "qué opinan los expertos", o cuando una decisión de Vantera implique más de 2 horas de trabajo o sea difícil de revertir.
---

# Mesa de expertos

Una decisión, siete ángulos, un memo. La mesa no trabaja por Andres: decide
qué vale la pena hacer con las 5–10 horas de la semana y qué no.

## Cuándo convocarla (y cuándo no)

**Sí:** decisiones que cuestan más de 2 horas o son difíciles de revertir —
qué construir primero, qué precio, qué canal, si posponer un compromiso, qué
hacer si Stripe rechaza la cuenta.

**No:** el plan del día (eso es `plan-hoy`), preguntas con respuesta en la
bóveda (eso es `boveda`), ni más de una mesa por semana sobre el mismo tema.
Convocar la mesa para no ejecutar es procrastinación con buena letra; si ya
hay un memo de esta semana sobre el tema, léelo y devuelve a Andres al trabajo.

**Nunca** sobre un proyecto congelado ni uno nuevo: anótalo en
`boveda/wiki/parking-lot.md` con fecha y dilo en una línea. Excepción: Andres
dice explícitamente que quiere la mesa aunque esté congelado; entonces se
convoca y el memo lo deja registrado.

## Los miembros

Agentes en `.claude/agents/`. Cada uno tiene su lente y las mismas reglas
duras (bóveda primero, horas en todo, `sin dato`, nunca órdenes, nunca
portafolio fuera de la bóveda, un solo proyecto activo).

| Agente | Ángulo | Convocar |
|---|---|---|
| `mesa-operador` | horas, secuencia, ruta crítica, regla de proyecto único | siempre |
| `mesa-producto` | qué recibe el que paga, mínimo vendible | si toca producto/planes |
| `mesa-growth` | aritmética de clientes, oferta, canal, mensajes | si toca clientes |
| `mesa-finanzas` | economía unitaria, precios, Stripe, LLC | si toca dinero |
| `mesa-tecnico` | camino de implementación más corto, horas técnicas | si toca código |
| `mesa-riesgo` | regulación de señales, Stripe, términos, riesgo operativo | siempre que se cobre |
| `mesa-abogado-diablo` | ataca el consenso, supuesto que tumba el plan | siempre, segunda ronda |
| `mesa-sintetizador` | decisión + 3 acciones + memo en la bóveda | siempre, al final |

Mínimo: operador + dos expertos relevantes + abogado del diablo +
sintetizador. Por defecto, todos.

Los agentes tienen la lista de herramientas restringida a lectura de disco y
búsqueda web (el sintetizador además escribe). Ningún miembro puede llamar
conectores externos: eso hace imposible que la mesa toque Robinhood, Gmail o
el calendario aunque se lo pidan.

## Protocolo

### 0. Guardia (30 segundos)

- ¿Es un proyecto congelado o nuevo? → parking lot, no se convoca.
- ¿Hay ya un `boveda/outputs/*-mesa.md` de esta semana sobre lo mismo?
  (`ls -t boveda/outputs/*-mesa.md | head -3`) → léelo, resume la decisión,
  no se convoca.

### 1. Encuadre (lo escribe el moderador — esta sesión)

Antes de llamar a nadie, redacta el **encuadre** en el chat, en este formato,
y úsalo como texto idéntico para todos los expertos:

```
PREGUNTA: <una línea, la que Andres hizo, aterrizada>
FECHA: <date +%F> · faltan <N> días para <próximo compromiso>
CONTEXTO: <3–6 líneas sacadas de la bóveda: estado, bloqueos, decisiones ya tomadas>
RESTRICCIONES: 5–10 h/semana · un solo proyecto activo hasta el 1 dic 2026 ·
  sin órdenes · sin exponer portafolio · sin números inventados
LO QUE YA SE DECIDIÓ Y NO SE REABRE: <lista corta, o "nada">
ENTREGA: responde en tu formato, máximo ~450 palabras, en español.
```

Para el contexto, lee `boveda/wiki/vantera-capital.md`, el último plan y el
último cierre en `boveda/outputs/`. No inventes el estado: si algo no está en
la bóveda, escribe `sin dato`.

### 2. Primera ronda — expertos en paralelo

Lanza a todos los expertos elegidos **en un solo mensaje, con una llamada a la
herramienta Agent por experto** (`subagent_type` = nombre del agente, por
ejemplo `mesa-producto`), pasándole a cada uno el encuadre completo. Así
corren a la vez. No los lances uno por uno.

Si un agente no está disponible (por ejemplo, las skills se copiaron al scope
de usuario sin la carpeta `agents/`), usa el agente general con el contenido
de `.claude/agents/<nombre>.md` como prompt, seguido del encuadre.

### 3. Segunda ronda — contrainterrogatorio

Lanza `mesa-abogado-diablo` con el encuadre **más las respuestas completas de
todos los expertos**. Devuelve el supuesto que tumba el plan, tres objeciones
con test barato, contradicciones y la defensa de no hacer nada.

Solo si una objeción cambia de verdad una recomendación, vuelve a lanzar al
experto afectado con la objeción (una vez, no más). Normalmente no hace falta:
el sintetizador resuelve.

### 4. Síntesis

Lanza `mesa-sintetizador` con: encuadre, todas las respuestas de la primera
ronda y la del abogado del diablo. Escribe `boveda/outputs/AAAA-MM-DD-mesa.md`
con la plantilla fija (decisión, coincidencias, desacuerdos resueltos, 3
acciones con horas que caben en 2 semanas, no hacer, objeciones y qué se hizo
con cada una, supuesto a comprobar, riesgos aceptados, datos que faltan,
parking lot, fuentes).

### 5. Cierre en el chat

Muestra, corto: la ruta del memo, la decisión en dos frases y las tres
acciones con horas. Nada más — el memo ya está en la bóveda.

Si la decisión cambia algo durable (un precio, una fecha, una regla), aplícalo
en la nota de wiki correspondiente siguiendo la skill `boveda` (editar, no
duplicar) y dilo en una línea.

## Reglas

- Máximo tres acciones en el memo y la suma de horas cabe en dos semanas. Si
  la mesa propone más, el sintetizador recorta; no se negocia con el
  presupuesto.
- Un número sin fuente es `sin dato`. Las fuentes web van con URL al final del
  memo.
- La mesa opina; Andres ejecuta. Ninguna acción del memo la ejecuta un agente
  sin que Andres la pida después de leer el memo.
- La mesa consume unos 10–20 minutos de Claude. Es barato para una decisión
  de 10 horas y caro para una de 30 minutos. Usa el criterio de arriba.
- Datos personales y de portafolio: se leen de la bóveda, se resumen, nunca se
  copian al memo más allá de lo que ya dice la wiki.
