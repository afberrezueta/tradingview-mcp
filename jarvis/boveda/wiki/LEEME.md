---
titulo: Cómo funciona wiki/
tipo: wiki
fecha: 2026-09-03
tags: [meta]
---

# wiki/ — conocimiento depurado

Una nota por sujeto, editable, enlazada con dobles corchetes (wikilinks). El punto de
entrada es `indice.md`; toda nota nueva se enlaza desde ahí.

Esta carpeta **no se versiona en ningún repo público**: contiene el perfil,
los proyectos y las cuentas. Si clonaste el sistema desde git y la ves vacía,
copia tu bóveda desde la copia local (o desde el zip original) y regenera el
HUD con `python3 hud/generar.py`.

Notas mínimas para que las skills funcionen:

- `indice.md` — índice
- `perfil.md` — quién eres, restricciones reales
- `vantera-capital.md` — proyecto activo y compromisos con fecha
- `parking-lot.md` — ideas congeladas con fecha
- `congelados.md` — proyectos cerrados y por qué
- `proyectos/<nombre>.md` — una nota por proyecto en mantenimiento
