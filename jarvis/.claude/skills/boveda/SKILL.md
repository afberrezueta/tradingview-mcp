---
name: boveda
description: Leer y escribir la memoria en Markdown del sistema. Usar cuando Andres diga "recuerda que...", "anota...", "qué sabes de...", "busca en la bóveda", cuando pregunte por algo que ya se discutió antes, o cuando termine una sesión de trabajo que produjo conocimiento que debe persistir.
---

# Bóveda — leer y escribir memoria

La bóveda es la única fuente de verdad de este sistema. Todo es Markdown en disco.

## Estructura

```
boveda/raw/       AAAA-MM-DD-tema.md      capturas crudas, append-only
boveda/wiki/      tema.md                 conocimiento depurado, editable
boveda/outputs/   AAAA-MM-DD-tipo.md      entregables de JARVIS
```

## Para LEER (pregunta del tipo "qué sabes de X")

1. `ls boveda/wiki/` y `ls boveda/wiki/proyectos/` para ver qué existe.
2. `grep -ril "<término>" boveda/` para encontrar menciones. Busca también
   sinónimos y el nombre en el otro idioma.
3. Lee las notas relevantes completas — no respondas desde el nombre del archivo.
4. Responde con lo que dice la bóveda. Si la bóveda no lo tiene, dilo en una
   frase y ofrece anotarlo.
5. Cita las notas que usaste al final: `— boveda/wiki/vantera-capital.md`

## Para ESCRIBIR

**Captura cruda** (algo que Andres dijo, un pegado, una idea suelta):

```
boveda/raw/2026-09-03-nombre-corto.md
```

Frontmatter mínimo:

```yaml
---
titulo: Lo que sea
tipo: captura
fecha: 2026-09-03
tags: [vantera, stripe]
---
```

Luego el contenido tal cual. No lo interpretes ni lo pulas.

**Nota de wiki** (conocimiento que ya está asentado):

1. Primero `grep` para ver si el sujeto ya tiene nota bajo otro nombre.
2. Si existe, **edita** — no crees una duplicada. Actualiza en vez de
   sobreescribir: "usa Supabase Auth (antes evaluó Clerk)" es mejor que
   reemplazar la línea.
3. Si no existe, créala con frontmatter `tipo: wiki` y enlázala desde
   `boveda/wiki/indice.md`.
4. Enlaza sujetos relacionados con `[[wikilinks]]`.

## Reglas

- Una nota por sujeto. Un hecho sobre X va solo en la nota de X.
- Si una nota de wiki pasa de ~200 líneas, condénsala o divídela.
- Nunca borres una línea de `raw/`. En `wiki/` sí puedes reescribir.
- Fechas siempre en formato `AAAA-MM-DD`. Usa `date +%F` para obtener hoy.
- Si Andres propone un proyecto nuevo, va a `boveda/wiki/parking-lot.md`
  con fecha — no se desarrolla hasta el 1 de diciembre de 2026.

## Mantenimiento (skill "limpieza de bóveda")

Cuando Andres pida limpiar:

- Notas en `raw/` de más de 30 días cuyo contenido ya esté en `wiki/`: márcalas
  con `estado: procesado` en el frontmatter. No las borres.
- Enlaces rotos: `grep -o '\[\[[^]]*\]\]' -r boveda/wiki/` y verifica que cada
  destino exista.
- Notas de wiki sin ningún enlace entrante: repórtalas, no las borres.
