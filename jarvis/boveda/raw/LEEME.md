---
titulo: Cómo funciona raw/
tipo: wiki
fecha: 2026-09-03
tags: [meta]
---

# raw/ — capturas crudas

Todo lo que entra sin procesar: notas de voz transcritas, pegados, ideas
sueltas, resultados de comandos.

- Nombre de archivo: `AAAA-MM-DD-tema-corto.md`
- **Append-only.** Nunca edites una captura vieja; escribe una nueva.
- No se interpreta ni se pule aquí. Eso pasa cuando la información sube a `wiki/`.

Frontmatter mínimo:

```yaml
---
titulo: Lo que sea
tipo: captura
fecha: 2026-09-03
tags: [vantera]
---
```

Cuando el contenido de una captura ya vive en `wiki/`, márcala con
`estado: procesado` en el frontmatter. No la borres.
