#!/usr/bin/env python3
"""
Detector de cambios de estado: el núcleo del sistema de alertas.

Compara la lectura de hoy con la última guardada y dice qué cambió. No envía
nada por sí solo: escribe dos archivos y quien quiera los usa.

  privado/alertas.json    — el detalle completo, incluidas las probabilidades.
                            No se publica ni se versiona.
  web/datos/aviso.json    — el aviso público: qué pasó, sin las cifras del motor.
                            Un cruce de nivel es deducible de precios públicos,
                            así que decirlo no regala nada. Las probabilidades sí
                            se callan.

Reglas que vigila, todas derivadas del sistema del bot (Donchian 20/10, ATR-14):
  entrada       el cierre superó el máximo de los 20 días anteriores
  salida        el cierre perdió el mínimo de los 10 días anteriores
  cerca         el precio quedó a menos de media ATR de un nivel
  regimen       cambió el régimen de medias (alcista / mixto / bajista)
  estado_hmm    cambió el estado más probable del modelo de régimen (privado)

Uso:  python3 alertas.py                 (desde jarvis/analisis/)
      python3 alertas.py --sin-guardar   calcula y muestra, no mueve el estado
"""
import json, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
PUBLICO = RAIZ / "web" / "datos" / "publico.json"
PRIVADO = RAIZ / "privado"
AVISO = RAIZ / "web" / "datos" / "aviso.json"

# Cuánto pesa cada aviso. Sirve para decidir si se molesta a alguien un domingo.
SEVERIDAD = {"entrada": "alta", "salida": "alta", "regimen": "media", "estado_hmm": "media", "cerca": "baja"}


def cargar(ruta):
    if not Path(ruta).exists():
        return None
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def estado_actual():
    """Instantánea comparable de la lectura de hoy. Si falta el motor, va sin él."""
    pub = cargar(PUBLICO)
    if not pub:
        sys.exit(f"No existe {PUBLICO}. Corre antes exportar_web.py.")
    ind = pub["indicadores"]
    motor = cargar(PRIVADO / "motor.json")
    return dict(
        fecha=ind["fecha"],
        cierre=ind["cierre"],
        entrada=ind["entrada"],
        salida=ind["salida"],
        atr14=ind["atr14"],
        regimen=ind["regimen"],
        estado_hmm=(motor or {}).get("estado_hoy"),
        dentro=ind["cierre"] > ind["entrada"],
    )


def comparar(hoy, ayer):
    """Devuelve la lista de avisos. Sin estado previo no inventa un cruce."""
    avisos = []

    if hoy["cierre"] > hoy["entrada"]:
        # Solo es noticia si ayer no estaba por encima. Sin historial, se calla.
        if ayer is None or ayer["cierre"] <= ayer["entrada"]:
            avisos.append(dict(
                tipo="entrada",
                titulo="El cierre superó el máximo de 20 días",
                detalle=f"Cierre {hoy['cierre']:.2f} por encima de {hoy['entrada']:.2f}.",
                nivel=hoy["entrada"],
            ))
    if hoy["cierre"] < hoy["salida"]:
        if ayer is None or ayer["cierre"] >= ayer["salida"]:
            avisos.append(dict(
                tipo="salida",
                titulo="El cierre perdió el mínimo de 10 días",
                detalle=f"Cierre {hoy['cierre']:.2f} por debajo de {hoy['salida']:.2f}.",
                nivel=hoy["salida"],
            ))

    if ayer and hoy["regimen"] != ayer["regimen"]:
        avisos.append(dict(
            tipo="regimen",
            titulo=f"El régimen pasó de {ayer['regimen']} a {hoy['regimen']}",
            detalle="Cambió la relación entre el cierre y las medias de 50 y 200 días.",
            nivel=None,
        ))

    if ayer and hoy["estado_hmm"] and hoy["estado_hmm"] != ayer.get("estado_hmm"):
        avisos.append(dict(
            tipo="estado_hmm",
            titulo=f"El modelo pasó de {ayer.get('estado_hmm')} a {hoy['estado_hmm']}",
            detalle="Cambió el estado de volatilidad más probable del modelo de régimen.",
            nivel=None,
            privado=True,   # esto sí es del motor: no sale al aviso público
        ))

    # "Cerca" solo cuando no hubo cruce: si ya cruzó, decir que está cerca sobra.
    if not any(a["tipo"] in ("entrada", "salida") for a in avisos):
        umbral = hoy["atr14"] / 2
        for tipo, nivel, texto in (
            ("entrada", hoy["entrada"], "del máximo de 20 días"),
            ("salida", hoy["salida"], "del mínimo de 10 días"),
        ):
            distancia = abs(hoy["cierre"] - nivel)
            if distancia <= umbral:
                avisos.append(dict(
                    tipo="cerca",
                    titulo=f"El precio quedó a menos de media ATR {texto}",
                    detalle=f"Faltan {distancia:.2f} para {nivel:.2f}; media ATR es {umbral:.2f}.",
                    nivel=nivel,
                ))

    for a in avisos:
        a["severidad"] = SEVERIDAD[a["tipo"]]
    return avisos


def main():
    guardar = "--sin-guardar" not in sys.argv
    PRIVADO.mkdir(parents=True, exist_ok=True)

    hoy = estado_actual()
    anterior_ruta = PRIVADO / "estado_anterior.json"
    ayer = cargar(anterior_ruta)

    if ayer and ayer.get("fecha") == hoy["fecha"]:
        print(f"Ya se evaluó el cierre del {hoy['fecha']}. Nada nuevo que comparar.")
        avisos = cargar(PRIVADO / "alertas.json") or {"avisos": []}
        avisos = avisos.get("avisos", [])
    else:
        avisos = comparar(hoy, ayer)
        completo = dict(fecha=hoy["fecha"], estado=hoy, anterior=ayer, avisos=avisos)
        (PRIVADO / "alertas.json").write_text(json.dumps(completo, indent=1, ensure_ascii=False), encoding="utf-8")
        if guardar:
            anterior_ruta.write_text(json.dumps(hoy, ensure_ascii=False), encoding="utf-8")

    # Aviso público: se omite lo que solo sabe el motor.
    publicos = [
        dict(tipo=a["tipo"], titulo=a["titulo"], detalle=a["detalle"], severidad=a["severidad"])
        for a in avisos if not a.get("privado")
    ]
    AVISO.write_text(json.dumps(dict(fecha=hoy["fecha"], avisos=publicos), ensure_ascii=False), encoding="utf-8")

    if not avisos:
        print(f"{hoy['fecha']}: sin cambios de estado. Cierre {hoy['cierre']:.2f}, "
              f"entrada {hoy['entrada']:.2f}, salida {hoy['salida']:.2f}.")
    else:
        print(f"{hoy['fecha']}: {len(avisos)} aviso(s)")
        for a in avisos:
            marca = " (privado)" if a.get("privado") else ""
            print(f"  [{a['severidad']}] {a['titulo']}{marca}\n      {a['detalle']}")
    print(f"escrito {PRIVADO/'alertas.json'} y {AVISO}")


if __name__ == "__main__":
    main()
