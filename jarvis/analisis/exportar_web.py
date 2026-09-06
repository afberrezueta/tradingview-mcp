#!/usr/bin/env python3
"""
Exporta las salidas del motor a JSON estáticos que sirve la web pública (web/datos/).

Separa lo público de lo que se cobra, y los escribe en sitios distintos a propósito:
  web/datos/publico.json  — régimen, niveles, serie de precio. Se publica.
  privado/motor.json      — probabilidades y tasa base. NO se publica ni se versiona.

La capa de pago no puede vivir dentro de web/: todo lo que hay ahí queda
descargable por cualquiera que sepa la URL, y el repositorio es público. Se
vende el cálculo del día, no el método: el método está en el código, a la vista.

Uso:  python3 exportar_web.py            (desde jarvis/analisis/)
      python3 exportar_web.py --salida ../../web/datos --privado ../../privado
"""
import csv, json, math, sys, os
from pathlib import Path

AQUI = Path(__file__).resolve().parent
DATOS = AQUI / "datos"
RAIZ = AQUI.parent.parent
SALIDA_POR_DEFECTO = RAIZ / "web" / "datos"
PRIVADO_POR_DEFECTO = RAIZ / "privado"


def leer_json(nombre):
    ruta = DATOS / nombre
    if not ruta.exists():
        return None
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def leer_velas():
    with open(DATOS / "eth_diario.csv", encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    filas.sort(key=lambda r: r["fecha"])
    return filas


def sma(valores, periodo, i):
    if i - periodo + 1 < 0:
        return None
    return sum(valores[i - periodo + 1:i + 1]) / periodo


def indicadores(filas):
    """Régimen y niveles: derivados solo de precio, sin el motor. Esto es lo público."""
    c = [float(r["close"]) for r in filas]
    h = [float(r["high"]) for r in filas]
    l = [float(r["low"]) for r in filas]
    i = len(c) - 1
    s50, s200 = sma(c, 50, i), sma(c, 200, i)
    # ATR-14 de Wilder
    trs = [max(h[k] - l[k], abs(h[k] - c[k - 1]), abs(l[k] - c[k - 1])) for k in range(1, i + 1)]
    a = sum(trs[:14]) / 14
    for t in trs[14:]:
        a = (a * 13 + t) / 14
    # los "días anteriores" excluyen la vela de hoy, igual que el motor
    entrada = max(h[-21:-1])
    salida = min(l[-11:-1])
    if s50 and s200:
        regimen = "alcista" if c[i] > s200 and s50 > s200 else ("bajista" if c[i] < s200 and s50 < s200 else "mixto")
    else:
        regimen = "sin dato"
    return dict(
        fecha=filas[-1]["fecha"],
        cierre=round(c[i], 2),
        sma50=round(s50, 2) if s50 else None,
        sma200=round(s200, 2) if s200 else None,
        sobre_sma200=round((c[i] / s200 - 1) * 100, 2) if s200 else None,
        regimen=regimen,
        atr14=round(a, 2),
        atr_pct=round(a / c[i] * 100, 2),
        entrada=round(entrada, 2),
        salida=round(salida, 2),
        velas=len(c),
        desde=filas[0]["fecha"],
    )


def serie(filas, dias=180):
    """Serie recortada para el gráfico: fecha, cierre, canal Donchian-20 y SMA-200."""
    c = [float(r["close"]) for r in filas]
    h = [float(r["high"]) for r in filas]
    l = [float(r["low"]) for r in filas]
    puntos = []
    inicio = max(200, len(filas) - dias)
    for i in range(inicio, len(filas)):
        puntos.append(dict(
            d=filas[i]["fecha"],
            c=round(c[i], 2),
            a=round(max(h[i - 20:i]), 2),
            b=round(min(l[i - 20:i]), 2),
            s=round(sma(c, 200, i), 2),
        ))
    return puntos


def main():
    salida = Path(sys.argv[sys.argv.index("--salida") + 1]) if "--salida" in sys.argv else SALIDA_POR_DEFECTO
    privado = Path(sys.argv[sys.argv.index("--privado") + 1]) if "--privado" in sys.argv else PRIVADO_POR_DEFECTO
    salida.mkdir(parents=True, exist_ok=True)
    privado.mkdir(parents=True, exist_ok=True)

    filas = leer_velas()
    ind = indicadores(filas)
    cot = leer_json("eth_cotizacion.json") or {}
    motor = leer_json("motor_resultados.json")

    publico = dict(
        simbolo="ETHUSD",
        generado=ind["fecha"],
        indicadores=ind,
        cotizacion_respaldo=dict(
            precio=cot.get("precio"),
            hora_utc=cot.get("hora_utc"),
            fuente=cot.get("fuente"),
        ),
        serie=serie(filas),
    )
    (salida / "publico.json").write_text(json.dumps(publico, separators=(",", ":")), encoding="utf-8")

    if motor:
        b = motor.get("barreras", {})
        tb = motor.get("tasa_base", {})
        pago = dict(
            fecha_datos=motor.get("fecha_datos"),
            velas=motor.get("velas"),
            semilla=motor.get("semilla"),
            regimen=motor.get("regimen", {}).get("estados"),
            estado_hoy=motor.get("regimen", {}).get("estado_mas_probable_hoy"),
            barreras=dict(
                S0=b.get("S0"), entrada=b.get("entrada"), salida=b.get("salida"),
                metodos={k: v for k, v in b.items() if isinstance(v, dict)},
            ),
            tasa_base={k: v for k, v in tb.items() if k != "abierta"},
            distribucion=motor.get("distribucion"),
        )
        destino = privado / "motor.json"
        destino.write_text(json.dumps(pago, separators=(",", ":")), encoding="utf-8")
        print(f"escrito {destino}  (capa de pago: fuera de web/, sin versionar)")
    else:
        print("aviso: no hay motor_resultados.json; la web mostrará solo la capa pública")

    print(f"escrito {salida/'publico.json'} · {len(publico['serie'])} puntos · datos al {ind['fecha']}")


if __name__ == "__main__":
    main()
