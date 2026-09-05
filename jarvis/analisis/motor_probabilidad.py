#!/usr/bin/env python3
"""
Motor probabilístico para la lectura sistemática de ETH (reglas del bot: Donchian 20/10, ATR-14).

Tres piezas, todas sobre velas diarias (FMP, 2019-01-01 → hoy):
  1. Régimen: HMM gaussiano de K estados sobre log-retornos diarios (Baum-Welch, forward-backward escalado).
  2. Barreras: P(cierre > entrada antes que cierre < salida) en 5/10/20 días, por tres métodos independientes
     (mezcla de régimen del HMM, bootstrap por bloques, browniano sin deriva con vol realizada).
  3. Tasa base: backtest del sistema Turtle 20/10 long-only con stop inicial 2×ATR, y el subconjunto
     condicionado a "14 días sin cierre nuevo por encima de la entrada" (la situación de hoy).

Uso:  python3 motor_probabilidad.py eth_long.json [precio_actual] [entrada] [salida]
Salida: motor_resultados.json + resumen por stdout. Solo lectura de datos: no coloca órdenes.
"""
import json, sys, math
import numpy as np

SEED = 20260905

def cargar(ruta):
    rows = json.load(open(ruta))
    c = np.array([r["c"] for r in rows]); h = np.array([r["h"] for r in rows]); l = np.array([r["l"] for r in rows])
    o = np.array([r["o"] for r in rows]); d = [r["d"] for r in rows]
    return d, o, h, l, c

def atr14(h, l, c):
    tr = np.maximum(h[1:] - l[1:], np.maximum(np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1])))
    out = np.full(len(c), np.nan); a = tr[:14].mean(); out[14] = a
    for k in range(15, len(c)):
        a = (a * 13 + tr[k-1]) / 14; out[k] = a
    return out

# ---------------------------------------------------------------- 1. HMM
def hmm_fit(x, K=3, iters=300, seed=SEED, tol=1e-7):
    """Baum-Welch para HMM gaussiano univariante. Devuelve parámetros, log-verosimilitud y posteriores."""
    rng = np.random.default_rng(seed); T = len(x)
    # inicialización por cuantiles de volatilidad móvil para que los estados nazcan separados
    mu = np.quantile(x, np.linspace(0.3, 0.7, K)); sd = np.quantile(np.abs(x - x.mean()), np.linspace(0.3, 0.9, K)) * 1.4826
    if seed != SEED:   # reinicios: perturbar la inicialización para buscar otros óptimos
        mu = mu + rng.normal(0, x.std() * 0.3, K); sd = sd * np.exp(rng.normal(0, 0.3, K))
    A = np.full((K, K), 0.05 / (K - 1)); np.fill_diagonal(A, 0.95); pi = np.full(K, 1.0 / K)
    ll_old = -np.inf
    for it in range(iters):
        B = np.exp(-0.5 * ((x[:, None] - mu[None, :]) / sd[None, :]) ** 2) / (sd[None, :] * math.sqrt(2 * math.pi)) + 1e-300
        alpha = np.zeros((T, K)); scale = np.zeros(T)
        alpha[0] = pi * B[0]; scale[0] = alpha[0].sum(); alpha[0] /= scale[0]
        for t in range(1, T):
            alpha[t] = (alpha[t-1] @ A) * B[t]; scale[t] = alpha[t].sum(); alpha[t] /= scale[t]
        beta = np.zeros((T, K)); beta[-1] = 1.0
        for t in range(T - 2, -1, -1):
            beta[t] = (A @ (B[t+1] * beta[t+1])) / scale[t+1]
        gamma = alpha * beta; gamma /= gamma.sum(1, keepdims=True)
        xi = np.zeros((K, K))
        for t in range(T - 1):
            m = (alpha[t][:, None] * A) * (B[t+1] * beta[t+1])[None, :]; xi += m / m.sum()
        pi = gamma[0]; A = xi / xi.sum(1, keepdims=True)
        w = gamma.sum(0); mu = (gamma * x[:, None]).sum(0) / w
        sd = np.sqrt((gamma * (x[:, None] - mu[None, :]) ** 2).sum(0) / w); sd = np.maximum(sd, 1e-5)
        ll = np.log(scale).sum()
        if ll - ll_old < tol: break
        ll_old = ll
    # ordenar estados por volatilidad ascendente (0 = más tranquilo)
    orden = np.argsort(sd); mu, sd = mu[orden], sd[orden]; A = A[orden][:, orden]; pi = pi[orden]
    gamma = gamma[:, orden]; alpha = alpha[:, orden]
    return dict(mu=mu, sd=sd, A=A, pi=pi, ll=ll, iters=it + 1, gamma=gamma, filtrado=alpha)

def hmm_mejor(x, K, reinicios=5):
    mejor = None
    for s in range(reinicios):
        m = hmm_fit(x, K, seed=SEED + s)
        if mejor is None or m["ll"] > mejor["ll"]: mejor = m
    return mejor

# ---------------------------------------------------------------- 2. barreras
def barreras_hmm(m, S0, U, L, horizontes, n=60000, seed=SEED):
    rng = np.random.default_rng(seed); K = len(m["mu"]); H = max(horizontes)
    p0 = m["filtrado"][-1]; A = m["A"]
    estado = rng.choice(K, size=n, p=p0); logS = np.full(n, math.log(S0))
    arriba = np.zeros(n, bool); abajo = np.zeros(n, bool); dia_hit = np.full(n, H + 1)
    res = {}
    cum = np.cumsum(A, 1)
    for t in range(1, H + 1):
        u = rng.random(n); estado = (u[:, None] > cum[estado]).sum(1)
        logS += rng.normal(m["mu"][estado], m["sd"][estado])
        vivo = ~(arriba | abajo)
        nuevo_arriba = vivo & (logS > math.log(U)); nuevo_abajo = vivo & (logS < math.log(L))
        arriba |= nuevo_arriba; abajo |= nuevo_abajo
        if t in horizontes:
            res[t] = dict(p_entrada_primero=float(arriba.mean()), p_salida_primero=float(abajo.mean()), p_ninguna=float(1 - arriba.mean() - abajo.mean()))
    return res

def barreras_bootstrap(r, S0, U, L, horizontes, bloque=5, n=60000, seed=SEED):
    rng = np.random.default_rng(seed); H = max(horizontes); T = len(r)
    res = {}; logS = np.full(n, math.log(S0)); arriba = np.zeros(n, bool); abajo = np.zeros(n, bool)
    # bootstrap por bloques: cada camino concatena bloques de 'bloque' días tomados al azar
    t = 0; pasos = np.zeros((n, H))
    while t < H:
        ini = rng.integers(0, T - bloque, size=n)
        for j in range(bloque):
            if t + j < H: pasos[:, t + j] = r[ini + j]
        t += bloque
    for t in range(H):
        logS += pasos[:, t]; vivo = ~(arriba | abajo)
        arriba |= vivo & (logS > math.log(U)); abajo |= vivo & (logS < math.log(L))
        if (t + 1) in horizontes:
            res[t + 1] = dict(p_entrada_primero=float(arriba.mean()), p_salida_primero=float(abajo.mean()), p_ninguna=float(1 - arriba.mean() - abajo.mean()))
    return res

def barreras_gbm(sigma_d, S0, U, L, horizontes, n=60000, seed=SEED):
    rng = np.random.default_rng(seed); H = max(horizontes); res = {}
    logS = np.full(n, math.log(S0)); arriba = np.zeros(n, bool); abajo = np.zeros(n, bool)
    for t in range(1, H + 1):
        logS += rng.normal(-0.5 * sigma_d ** 2, sigma_d, n); vivo = ~(arriba | abajo)
        arriba |= vivo & (logS > math.log(U)); abajo |= vivo & (logS < math.log(L))
        if t in horizontes:
            res[t] = dict(p_entrada_primero=float(arriba.mean()), p_salida_primero=float(abajo.mean()), p_ninguna=float(1 - arriba.mean() - abajo.mean()))
    # horizonte infinito, sin deriva: P(U antes que L) = ln(S0/L) / ln(U/L)
    res["infinito_analitico"] = dict(p_entrada_primero=math.log(S0 / L) / math.log(U / L))
    return res

# ---------------------------------------------------------------- 3. tasa base Turtle 20/10
def backtest_turtle(d, o, h, l, c, atr, n_ent=20, n_sal=10, k_stop=2.0):
    """Long-only. Entrada: cierre > máximo de los n_ent días anteriores (excluido hoy), al cierre de ese día.
    Salida al cierre cuando cierre < mínimo de los n_sal días anteriores o cierre < entrada - k_stop*ATR(entrada).
    Mientras hay posición no se abren otras. Sin costos."""
    trades = []; en = False; T = len(c)
    for t in range(max(n_ent, 15), T):
        if not en:
            if c[t] > h[t-n_ent:t].max() and not np.isnan(atr[t]):
                en = True; e = dict(i=t, entrada=c[t], atr=atr[t], stop=c[t] - k_stop * atr[t], mfe=c[t], mae=c[t], nuevo_max_dia=None)
        else:
            e["mfe"] = max(e["mfe"], c[t]); e["mae"] = min(e["mae"], c[t])
            if e["nuevo_max_dia"] is None and c[t] > e["entrada"]: e["nuevo_max_dia"] = t - e["i"]
            if c[t] < l[t-n_sal:t].min() or c[t] < e["stop"]:
                R = (c[t] - e["entrada"]) / (k_stop * e["atr"])
                trades.append(dict(fecha_in=d[e["i"]], fecha_out=d[t], entrada=float(e["entrada"]), atr_in=float(e["atr"]), salida=float(c[t]), dias=t - e["i"],
                                   R=float(R), ret=float(c[t] / e["entrada"] - 1), mfe_R=float((e["mfe"] - e["entrada"]) / (k_stop * e["atr"])),
                                   mae_R=float((e["mae"] - e["entrada"]) / (k_stop * e["atr"])),
                                   nuevo_max_en_14=bool(e["nuevo_max_dia"] is not None and e["nuevo_max_dia"] <= 14)))
                en = False
    abierta = None
    if en: abierta = dict(fecha_in=d[e["i"]], entrada=float(e["entrada"]), stop=float(e["stop"]), dias=T - 1 - e["i"], R_abierto=float((c[-1] - e["entrada"]) / (k_stop * e["atr"])),
                          max_cierre=float(e["mfe"]), nuevo_max_en_14=bool(e["nuevo_max_dia"] is not None and e["nuevo_max_dia"] <= 14))
    return trades, abierta

def supervivencia(d, c, atr, trades_all, dia=16, k_stop=2.0):
    """Trades vivos al día `dia` tras la entrada: R acumulado a ese día y R que quedó por delante hasta la salida."""
    idx = {dd: i for i, dd in enumerate(d)}; filas = []
    for t in trades_all:
        if t["dias"] < dia: continue
        i0 = idx[t["fecha_in"]]; r_dia = (c[i0 + dia] - t["entrada"]) / (k_stop * t["atr_in"])
        filas.append(dict(fecha_in=t["fecha_in"], R_al_dia=float(r_dia), R_final=t["R"], R_restante=float(t["R"] - r_dia)))
    if not filas: return dict(n=0)
    rr = np.array([f["R_restante"] for f in filas]); rf = np.array([f["R_final"] for f in filas])
    def wilson(k, n, z=1.96):
        p = k / n; den = 1 + z * z / n; cc = (p + z * z / (2 * n)) / den; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den; return [cc - h, cc + h]
    return dict(dia=dia, n=len(filas), p_restante_positivo=float((rr > 0).mean()), ic95_p_restante=wilson(int((rr > 0).sum()), len(filas)),
                R_restante_media=float(rr.mean()), R_restante_mediana=float(np.median(rr)), R_restante_p25=float(np.percentile(rr, 25)), R_restante_p75=float(np.percentile(rr, 75)),
                p_final_positivo=float((rf > 0).mean()), R_final_mediana=float(np.median(rf)), R_al_dia_media=float(np.mean([f["R_al_dia"] for f in filas])))

def stats(tr):
    if not tr: return dict(n=0)
    R = np.array([t["R"] for t in tr]); w = R > 0
    pf = float(R[w].sum() / -R[~w].sum()) if (~w).any() else float("inf")   # 0 si no hay ganadores, inf si no hay perdedores
    curva = np.cumsum(R); dd = float((curva - np.maximum.accumulate(curva)).min())
    b = R[w].mean() / -R[~w].mean() if (~w).any() and w.any() else float("nan")
    p = w.mean(); kelly = float(p - (1 - p) / b) if b == b and b > 0 else float("nan")
    return dict(n=int(len(R)), p_ganar=float(p), R_media=float(R.mean()), R_mediana=float(np.median(R)), R_ganancia_media=float(R[w].mean()) if w.any() else None,
                R_perdida_media=float(R[~w].mean()) if (~w).any() else None, profit_factor=pf, max_dd_R=dd, dias_media=float(np.mean([t["dias"] for t in tr])),
                kelly=kelly, medio_kelly=kelly / 2 if kelly == kelly else None,
                percentiles_R={q: float(np.percentile(R, q)) for q in (5, 25, 50, 75, 95)})

# ---------------------------------------------------------------- main
def main():
    ruta = sys.argv[1]; S0 = float(sys.argv[2]) if len(sys.argv) > 2 else None
    d, o, h, l, c = cargar(ruta); atr = atr14(h, l, c)
    if S0 is None: S0 = float(c[-1])
    U = float(sys.argv[3]) if len(sys.argv) > 3 else float(h[-20:].max()); L = float(sys.argv[4]) if len(sys.argv) > 4 else float(l[-10:].min())
    r = np.diff(np.log(c))
    # 1. HMM (3 estados) sobre todo el histórico; comparación con 2 estados por BIC
    m3 = hmm_mejor(r, 3); m2 = hmm_mejor(r, 2)
    def bic(m, K): return -2 * m["ll"] + (K * K - K + 2 * K + K - 1) * math.log(len(r))
    p_hoy = m3["filtrado"][-1]; dur = 1 / (1 - np.diag(m3["A"]))
    etiquetas = ["calma", "normal", "turbulencia"]   # ordenados por volatilidad; los nombres describen μ y σ ajustados
    regimen = dict(K=3, estados=[dict(nombre=etiquetas[k], mu_diario_pct=float(m3["mu"][k] * 100), vol_anual_pct=float(m3["sd"][k] * math.sqrt(365) * 100),
                                      duracion_esperada_dias=float(dur[k]), p_hoy=float(p_hoy[k]), p_media_historica=float(m3["gamma"][:, k].mean())) for k in range(3)],
                   transicion=m3["A"].round(4).tolist(), loglik=float(m3["ll"]), iteraciones=int(m3["iters"]), bic3=bic(m3, 3), bic2=bic(m2, 2),
                   p_hoy_2estados=m2["filtrado"][-1].round(4).tolist(), vol2=(m2["sd"] * math.sqrt(365) * 100).round(1).tolist(),
                   estado_mas_probable_hoy=etiquetas[int(p_hoy.argmax())],
                   serie_180=[dict(d=d[len(d) - 180 + k], p=m3["filtrado"][len(m3["filtrado"]) - 180 + k].round(3).tolist()) for k in range(180)])
    # 2. barreras
    horizontes = [5, 10, 20]; sigma20 = float(r[-20:].std(ddof=1))
    barreras = dict(S0=S0, entrada=U, salida=L, horizontes=horizontes,
                    hmm=barreras_hmm(m3, S0, U, L, horizontes), bootstrap_250d=barreras_bootstrap(r[-250:], S0, U, L, horizontes),
                    gbm_vol20=barreras_gbm(sigma20, S0, U, L, horizontes), sigma20_diaria_pct=sigma20 * 100)
    # 3. tasa base
    trades, abierta = backtest_turtle(d, o, h, l, c, atr)
    cond = [t for t in trades if not t["nuevo_max_en_14"]]; sin_cond = [t for t in trades if t["nuevo_max_en_14"]]
    rng_b = np.random.default_rng(SEED); Rs = np.array([t["R"] for t in trades])
    ic_R = [float(np.percentile([rng_b.choice(Rs, len(Rs)).mean() for _ in range(20000)], q)) for q in (2.5, 97.5)]
    top = sorted(Rs)[::-1]
    concentracion = dict(R_total=float(Rs.sum()), top1_R=float(top[0]), top3_R=float(sum(top[:3])), top3_fraccion=float(sum(top[:3]) / Rs.sum()),
                         R_media_sin_top1=float(np.delete(Rs, Rs.argmax()).mean()), ic95_bootstrap_R_media=ic_R, t_stat=float(Rs.mean() / (Rs.std(ddof=1) / math.sqrt(len(Rs)))))
    costos = {}
    for c_lado in (0.001, 0.003, 0.006):
        Rc = np.array([t["R"] - (2 * c_lado * t["entrada"]) / (2 * t["atr_in"]) for t in trades]); costos[f"{c_lado*100:.1f}%_por_lado"] = dict(p_ganar=float((Rc > 0).mean()), R_media=float(Rc.mean()))
    tasa_base = dict(todas=stats(trades), sin_nuevo_max_en_14=stats(cond), con_nuevo_max_en_14=stats(sin_cond),
                     vivos_al_dia=supervivencia(d, c, atr, trades, dia=16), ultimas_10=stats(trades[-10:]), concentracion=concentracion, costos=costos,
                     fraccion_sin_nuevo_max=float(len(cond) / len(trades)), abierta=abierta,
                     ultimas=[dict(fecha_in=t["fecha_in"], fecha_out=t["fecha_out"], R=round(t["R"], 2), dias=t["dias"], seguimiento=t["nuevo_max_en_14"]) for t in trades[-10:]],
                     desde=d[0], hasta=d[-1], nota="entrada al cierre del día del breakout; salida al cierre; sin costos ni deslizamiento")
    # 4. distribución de retorno a 20 días (mezcla HMM y bootstrap)
    rng = np.random.default_rng(SEED); K = 3; n = 60000; p0 = m3["filtrado"][-1]; cum = np.cumsum(m3["A"], 1)
    est = rng.choice(K, size=n, p=p0); acc = np.zeros(n)
    for t in range(20):
        est = (rng.random(n)[:, None] > cum[est]).sum(1); acc += rng.normal(m3["mu"][est], m3["sd"][est])
    ret20 = np.exp(acc) - 1
    dist = dict(hmm_20d=dict(p_positivo=float((ret20 > 0).mean()), percentiles_pct={q: float(np.percentile(ret20, q) * 100) for q in (5, 25, 50, 75, 95)},
                             es5_pct=float(ret20[ret20 <= np.percentile(ret20, 5)].mean() * 100)))
    out = dict(fecha_datos=d[-1], velas=len(c), precio_ref=S0, atr14=float(atr[-1]), regimen=regimen, barreras=barreras, tasa_base=tasa_base, distribucion=dist, semilla=SEED)
    json.dump(out, open("motor_resultados.json", "w"), indent=1, default=float)
    # resumen
    print(f"Datos {d[0]} → {d[-1]} ({len(c)} velas). S0={S0} entrada={U} salida={L} ATR14={atr[-1]:.1f}")
    print("\n[1] RÉGIMEN (HMM 3 estados)")
    for e in regimen["estados"]: print(f"  {e['nombre']:10s} μ={e['mu_diario_pct']:+.3f}%/d  σ={e['vol_anual_pct']:.0f}%/a  dur≈{e['duracion_esperada_dias']:.0f}d  P(hoy)={e['p_hoy']:.3f}  freq hist={e['p_media_historica']:.2f}")
    print(f"  BIC 3 estados={regimen['bic3']:.0f} vs 2 estados={regimen['bic2']:.0f}  (menor es mejor) · 2 estados P(hoy)={regimen['p_hoy_2estados']} vol={regimen['vol2']}")
    print("\n[2] BARRERAS  P(cierre>entrada primero) / P(cierre<salida primero) / P(ninguna)")
    for met in ("hmm", "bootstrap_250d", "gbm_vol20"):
        print("  " + met.ljust(15) + "  ".join(f"{hz}d: {barreras[met][hz]['p_entrada_primero']:.2f}/{barreras[met][hz]['p_salida_primero']:.2f}/{barreras[met][hz]['p_ninguna']:.2f}" for hz in horizontes))
    print(f"  analítico sin horizonte (browniano sin deriva): P(entrada antes que salida)={barreras['gbm_vol20']['infinito_analitico']['p_entrada_primero']:.2f}")
    print("\n[3] TASA BASE Turtle 20/10, stop 2×ATR, ETH 2019→")
    for k in ("todas", "con_nuevo_max_en_14", "sin_nuevo_max_en_14"):
        s = tasa_base[k]; print(f"  {k:22s} n={s['n']:3d} P(ganar)={s['p_ganar']:.2f} R̄={s['R_media']:+.2f} mediana={s['R_mediana']:+.2f} PF={s['profit_factor']:.2f} maxDD={s['max_dd_R']:.1f}R días={s['dias_media']:.0f} Kelly={s['kelly']:.2f}")
    v = tasa_base["vivos_al_dia"]; cz = tasa_base["concentracion"]
    print(f"  vivos al día {v['dia']}: n={v['n']} P(R restante>0)={v['p_restante_positivo']:.2f} IC95={v['ic95_p_restante'][0]:.2f}-{v['ic95_p_restante'][1]:.2f} mediana restante={v['R_restante_mediana']:+.2f}R media={v['R_restante_media']:+.2f}R · P(R final>0)={v['p_final_positivo']:.2f}")
    print(f"  concentración: top3={cz['top3_fraccion']:.0%} del R total · R media sin el mejor={cz['R_media_sin_top1']:+.2f} · IC95 bootstrap R media=[{cz['ic95_bootstrap_R_media'][0]:+.2f},{cz['ic95_bootstrap_R_media'][1]:+.2f}] t={cz['t_stat']:.2f}")
    u = tasa_base["ultimas_10"]; print(f"  últimas 10: P(ganar)={u['p_ganar']:.2f} R media={u['R_media']:+.2f} · costos 0.3%/lado: P={tasa_base['costos']['0.3%_por_lado']['p_ganar']:.2f} R={tasa_base['costos']['0.3%_por_lado']['R_media']:+.2f}")
    print(f"  posición abierta: {abierta}")
    print(f"\n[4] RETORNO 20 d (mezcla HMM): P(>0)={dist['hmm_20d']['p_positivo']:.2f}  p5={dist['hmm_20d']['percentiles_pct'][5]:+.1f}% p50={dist['hmm_20d']['percentiles_pct'][50]:+.1f}% p95={dist['hmm_20d']['percentiles_pct'][95]:+.1f}%  ES5={dist['hmm_20d']['es5_pct']:+.1f}%")

if __name__ == "__main__":
    main()
