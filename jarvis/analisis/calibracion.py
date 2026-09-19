#!/usr/bin/env python3
"""
Auditoría del motor: ¿las probabilidades que publica se cumplen?

Un modelo puede estar bien construido y aun así mentir. Si dice 0.50 y en la
historia eso ocurre el 30 % de las veces, el número no sirve para decidir, por
elegante que sea la matemática. Este script lo comprueba caminando hacia
adelante: en cada fecha usa SOLO datos anteriores a esa fecha, predice, y luego
mira qué pasó de verdad.

Tres preguntas, en orden de importancia:

  1. CALIBRACIÓN. Se agrupan las predicciones por decil y se compara la
     probabilidad dicha con la frecuencia observada. Se reporta la puntuación
     de Brier frente a la de predecir siempre la tasa base, porque acertar la
     media no es lo mismo que discriminar.
  2. TAMAÑO DE MUESTRA de la tasa base Turtle, con intervalo de Wilson. Un
     intervalo que cruza el 0.5 significa que la tasa de acierto no se
     distingue de una moneda.
  3. PERSISTENCIA. Se parte la historia en dos mitades y se mira si la ventaja
     de la primera sigue viva en la segunda. Casi ninguna sobrevive.

El estimador que se camina es el bootstrap por bloques sobre los retornos
previos, no el HMM completo: reajustar el HMM en cada fecha costaría días de
cómputo. Es una limitación real y se dice aquí en vez de esconderla. El
bootstrap es uno de los tres métodos que el motor publica, así que lo que se
audita es una tercera parte de lo que se vende, no un sustituto inventado.

Uso:  python3 calibracion.py
      python3 calibracion.py --paso 3 --rutas 4000 --horizonte 10
"""
import csv, json, math, sys
from pathlib import Path

try:
    import numpy as np
except ImportError:
    sys.exit("Falta numpy. Instálalo una vez con:  pip3 install numpy")

AQUI = Path(__file__).resolve().parent
DATOS = AQUI / "datos"
PRIVADO = AQUI.parent.parent / "privado"
SEMILLA = 20260906


def argumento(nombre, por_defecto, tipo=int):
    return tipo(sys.argv[sys.argv.index(nombre) + 1]) if nombre in sys.argv else por_defecto


def cargar():
    with open(DATOS / "eth_diario.csv", encoding="utf-8", newline="") as f:
        filas = sorted(csv.DictReader(f), key=lambda r: r["fecha"])
    d = [r["fecha"] for r in filas]
    o = np.array([float(r["open"]) for r in filas])
    h = np.array([float(r["high"]) for r in filas])
    l = np.array([float(r["low"]) for r in filas])
    c = np.array([float(r["close"]) for r in filas])
    return d, o, h, l, c


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / den
    medio = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (centro - medio, centro + medio)


# ------------------------------------------------------------------ 1. calibración
def caminar(c, h, l, horizonte, paso, rutas, ventana=250, bloque=5):
    """Predice en cada fecha con datos previos y compara con lo que pasó después."""
    rng = np.random.default_rng(SEMILLA)
    r = np.diff(np.log(c))
    inicio = ventana + 21           # margen para la ventana y para el canal de 20 días
    fin = len(c) - horizonte - 1
    predichas, observadas, descartadas = [], [], 0

    for t in range(inicio, fin, paso):
        S0 = c[t]
        U = h[t - 20:t].max()       # máximo de los 20 días ANTERIORES
        L = l[t - 10:t].min()       # mínimo de los 10 días ANTERIORES
        if not (L < S0 < U):        # el precio ya rompió: la pregunta no aplica
            descartadas += 1
            continue

        # --- predicción, solo con el pasado ---
        pasado = r[t - ventana:t]
        n_bloques = int(np.ceil(horizonte / bloque))
        arranques = rng.integers(0, len(pasado) - bloque, size=(rutas, n_bloques))
        trozos = np.stack([pasado[a:a + bloque] for fila in arranques for a in fila])
        caminos = trozos.reshape(rutas, n_bloques * bloque)[:, :horizonte]
        precios = S0 * np.exp(np.cumsum(caminos, axis=1))

        arriba = precios > U
        abajo = precios < L
        # primer cruce de cada barrera; len(horizonte) si nunca cruzó
        t_arriba = np.where(arriba.any(axis=1), arriba.argmax(axis=1), horizonte)
        t_abajo = np.where(abajo.any(axis=1), abajo.argmax(axis=1), horizonte)
        gana_arriba = (t_arriba < t_abajo).sum()
        gana_abajo = (t_abajo < t_arriba).sum()
        decididas = gana_arriba + gana_abajo
        if decididas == 0:
            descartadas += 1
            continue
        # probabilidad condicionada a que alguna barrera se toque: es la que se compara
        p = gana_arriba / decididas

        # --- lo que pasó de verdad, sobre cierres ---
        futuro = c[t + 1:t + 1 + horizonte]
        toca_arriba = np.where(futuro > U)[0]
        toca_abajo = np.where(futuro < L)[0]
        if len(toca_arriba) == 0 and len(toca_abajo) == 0:
            descartadas += 1
            continue
        primero_arriba = toca_arriba[0] if len(toca_arriba) else 10**9
        primero_abajo = toca_abajo[0] if len(toca_abajo) else 10**9
        predichas.append(p)
        observadas.append(1 if primero_arriba < primero_abajo else 0)

    return np.array(predichas), np.array(observadas), descartadas


def fiabilidad(p, y, cortes=(0, .2, .35, .5, .65, .8, 1.01)):
    filas = []
    for i in range(len(cortes) - 1):
        m = (p >= cortes[i]) & (p < cortes[i + 1])
        n = int(m.sum())
        if n == 0:
            continue
        lo, hi = wilson(int(y[m].sum()), n)
        filas.append(dict(
            desde=round(cortes[i], 2), hasta=round(min(cortes[i + 1], 1.0), 2), n=n,
            dicha=round(float(p[m].mean()), 3),
            observada=round(float(y[m].mean()), 3),
            ic95=[round(max(lo, 0), 3), round(min(hi, 1), 3)],
        ))
    return filas


# ------------------------------------------------------------------ 2 y 3. tasa base
def atr14(h, l, c):
    tr = np.maximum(h[1:] - l[1:], np.maximum(np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1])))
    out = np.full(len(c), np.nan)
    a = tr[:14].mean()
    out[14] = a
    for k in range(15, len(c)):
        a = (a * 13 + tr[k - 1]) / 14
        out[k] = a
    return out


def turtle(d, h, l, c, desde=0, hasta=None):
    """Donchian 20/10 largo, stop inicial 2xATR. Devuelve la lista de R por operación."""
    hasta = hasta if hasta is not None else len(c)
    atr = atr14(h, l, c)
    ops, dentro, entrada, stop, riesgo, fecha_in = [], False, 0.0, 0.0, 0.0, None
    for i in range(max(desde, 21), hasta):
        if np.isnan(atr[i]):
            continue
        if not dentro:
            if c[i] > h[i - 20:i].max():
                dentro, entrada = True, c[i]
                riesgo = 2 * atr[i]
                stop = entrada - riesgo
                fecha_in = d[i]
        else:
            salida_canal = l[i - 10:i].min()
            if c[i] < stop or c[i] < salida_canal:
                ops.append(dict(fecha_in=fecha_in, fecha_out=d[i], R=(c[i] - entrada) / riesgo))
                dentro = False
    return ops


def resumen_ops(ops):
    if not ops:
        return dict(n=0)
    R = np.array([o["R"] for o in ops])
    ganan = int((R > 0).sum())
    lo, hi = wilson(ganan, len(R))
    ganancias = R[R > 0].sum()
    perdidas = -R[R <= 0].sum()
    return dict(
        n=len(R),
        p_ganar=round(ganan / len(R), 3),
        ic95_p=[round(lo, 3), round(hi, 3)],
        R_media=round(float(R.mean()), 3),
        R_mediana=round(float(np.median(R)), 3),
        profit_factor=round(float(ganancias / perdidas), 2) if perdidas > 0 else None,
        mejor=round(float(R.max()), 2),
        peor=round(float(R.min()), 2),
        R_sin_la_mejor=round(float((R.sum() - R.max()) / (len(R) - 1)), 3) if len(R) > 1 else None,
    )


def main():
    horizonte = argumento("--horizonte", 10)
    paso = argumento("--paso", 3)
    rutas = argumento("--rutas", 3000)

    d, o, h, l, c = cargar()
    print(f"Datos {d[0]} → {d[-1]} ({len(c)} velas)\n")

    # ---- 1. calibración ----
    p, y, descartadas = caminar(c, h, l, horizonte, paso, rutas)
    base = float(y.mean())
    brier = float(((p - y) ** 2).mean())
    brier_base = float(((base - y) ** 2).mean())
    tabla = fiabilidad(p, y)

    print(f"[1] CALIBRACIÓN · horizonte {horizonte} d · {len(p)} predicciones fuera de muestra "
          f"({descartadas} fechas descartadas por no aplicar)")
    print(f"    tasa base observada: {base:.3f}  ·  Brier del modelo: {brier:.4f}  ·  "
          f"Brier de decir siempre la base: {brier_base:.4f}")
    mejora = (brier_base - brier) / brier_base * 100
    print(f"    mejora sobre la base: {mejora:+.1f} %   (negativo = el modelo estorba)")
    print(f"    {'rango':>12}  {'n':>5}  {'dice':>6}  {'ocurre':>7}   IC 95 %")
    for f in tabla:
        print(f"    {f['desde']:.2f}–{f['hasta']:.2f}  {f['n']:>5}  {f['dicha']:>6.3f}  "
              f"{f['observada']:>7.3f}   {f['ic95'][0]:.3f}–{f['ic95'][1]:.3f}")

    # ---- 2. tasa base y su N ----
    todas = turtle(d, h, l, c)
    r_todas = resumen_ops(todas)
    print(f"\n[2] TASA BASE Turtle 20/10 · N = {r_todas['n']} operaciones en {len(c)} velas")
    print(f"    P(ganar) {r_todas['p_ganar']} · IC 95 % {r_todas['ic95_p'][0]}–{r_todas['ic95_p'][1]}"
          f"{'  ← cruza 0.5: no se distingue de una moneda' if r_todas['ic95_p'][0] < 0.5 < r_todas['ic95_p'][1] else ''}")
    print(f"    R media {r_todas['R_media']} · mediana {r_todas['R_mediana']} · "
          f"profit factor {r_todas['profit_factor']} · mejor operación {r_todas['mejor']} R")
    print(f"    R media quitando la mejor operación: {r_todas['R_sin_la_mejor']}")

    # ---- 3. persistencia ----
    mitad = len(c) // 2
    primera = resumen_ops(turtle(d, h, l, c, 0, mitad))
    segunda = resumen_ops(turtle(d, h, l, c, mitad, len(c)))
    print(f"\n[3] PERSISTENCIA · primera mitad ({d[0]} → {d[mitad]}) contra segunda ({d[mitad]} → {d[-1]})")
    for nombre, s in (("primera", primera), ("segunda", segunda)):
        if s["n"] == 0:
            print(f"    {nombre}: sin operaciones")
            continue
        print(f"    {nombre}: N={s['n']} · P(ganar) {s['p_ganar']} "
              f"(IC {s['ic95_p'][0]}–{s['ic95_p'][1]}) · R media {s['R_media']} · PF {s['profit_factor']}")

    PRIVADO.mkdir(parents=True, exist_ok=True)
    salida = PRIVADO / "calibracion.json"
    salida.write_text(json.dumps(dict(
        generado=d[-1], horizonte=horizonte, paso=paso, rutas=rutas, semilla=SEMILLA,
        metodo="bootstrap por bloques sobre los 250 retornos previos; el HMM no se camina por costo",
        calibracion=dict(n=len(p), tasa_base=round(base, 4), brier=round(brier, 5),
                         brier_base=round(brier_base, 5), mejora_pct=round(mejora, 2), tabla=tabla),
        tasa_base=r_todas, persistencia=dict(primera=primera, segunda=segunda),
    ), indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nescrito {salida}")


if __name__ == "__main__":
    main()
