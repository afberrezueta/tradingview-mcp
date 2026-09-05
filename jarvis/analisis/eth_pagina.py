#!/usr/bin/env python3
"""
Genera analisis/eth.html — la lectura sistemática de ETH — a partir de:
  datos/eth_diario.csv         fecha,open,high,low,close (ascendente)        obligatorio
  datos/motor_resultados.json  salida de motor_probabilidad.py               opcional (sección "sin dato")
  datos/eth_cotizacion.json    precio, cambio_pct, min_dia, max_dia, hora_utc opcional (usa el último cierre)
  datos/eth_horas.json         desde, hasta, cierres (por hora, ascendente)  opcional (omite el panel)

Sin red, sin servidor: la página se abre desde el disco.
    python3 eth_pagina.py            escribe eth.html
    python3 eth_pagina.py --niveles  imprime S0, entrada (máx 20 d) y salida (mín 10 d) para el motor
"""
import csv, json, math, statistics, sys
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
DATOS = RAIZ / "datos"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def leer_json(nombre):
    p = DATOS / nombre
    return json.load(open(p, encoding="utf-8")) if p.exists() else None


def cargar_csv():
    with open(DATOS / "eth_diario.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda r: r["fecha"])
    d = [r["fecha"] for r in rows]
    o = [float(r["open"]) for r in rows]; h = [float(r["high"]) for r in rows]
    l = [float(r["low"]) for r in rows]; c = [float(r["close"]) for r in rows]
    return d, o, h, l, c


def sma(a, p, i):
    return sum(a[i - p + 1:i + 1]) / p if i - p + 1 >= 0 else None


def rsi(a, p, i):
    ag = sum(max(a[k] - a[k - 1], 0) for k in range(1, p + 1)) / p
    al = sum(max(a[k - 1] - a[k], 0) for k in range(1, p + 1)) / p
    for k in range(p + 1, i + 1):
        ch = a[k] - a[k - 1]; ag = (ag * (p - 1) + max(ch, 0)) / p; al = (al * (p - 1) + max(-ch, 0)) / p
    return 100.0 if al == 0 else 100 - 100 / (1 + ag / al)


def atr(h, l, c, p, i):
    trs = [max(h[k] - l[k], abs(h[k] - c[k - 1]), abs(l[k] - c[k - 1])) for k in range(1, i + 1)]
    a = sum(trs[:p]) / p
    for t in trs[p:]:
        a = (a * (p - 1) + t) / p
    return a


def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k / n; den = 1 + z * z / n; cc = (p + z * z / (2 * n)) / den
    hw = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (cc - hw, cc + hw)


def f0(x): return f"{x:,.0f}"
def f2(x): return f"{x:,.2f}"
def pct(x, s=1): return f"{x:+.{s}f} %"
def fecha_larga(s):
    y, m, dd = s.split("-"); return f"{int(dd)} {MESES[int(m) - 1]} {y}"
def esc(t): return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def indicadores(d, o, h, l, c):
    i = len(c) - 1; last = c[i]
    r = [math.log(c[k] / c[k - 1]) for k in range(1, len(c))]
    bo = [k for k in range(20, len(c)) if c[k] > max(h[k - 20:k])]
    e = dict(fecha_vela=d[i], cierre=last, sma50=sma(c, 50, i), sma200=sma(c, 200, i), rsi14=rsi(c, 14, i), atr14=atr(h, l, c, 14, i),
             donchian20_alto=max(h[i - 20:i]), donchian20_bajo=min(l[i - 20:i]), donchian10_bajo=min(l[i - 10:i]),
             donchian55_alto=max(h[i - 55:i]), donchian55_bajo=min(l[i - 55:i]),
             ultimo_breakout=d[bo[-1]] if bo else None, cierre_breakout=c[bo[-1]] if bo else None,
             max_cierre_desde_breakout=max(c[bo[-1]:]) if bo else None,
             vol20=statistics.pstdev(r[-20:]) * math.sqrt(365) * 100, max_52s=max(h[-365:]), min_52s=min(l[-365:]),
             fecha_max_52s=d[len(h) - 365 + h[-365:].index(max(h[-365:]))],
             cambio_1d=(c[i] / c[i - 1] - 1) * 100, cambio_7d=(c[i] / c[i - 7] - 1) * 100,
             cambio_30d=(c[i] / c[i - 30] - 1) * 100, cambio_90d=(c[i] / c[i - 90] - 1) * 100,
             rsi_hace_7=rsi(c, 14, i - 7))
    e["atr_pct"] = e["atr14"] / last * 100
    e["stop_2atr"] = (e["max_cierre_desde_breakout"] or last) - 2 * e["atr14"]
    e["stop_3atr"] = (e["max_cierre_desde_breakout"] or last) - 3 * e["atr14"]
    e["sobre_sma200"] = (last / e["sma200"] - 1) * 100
    e["regimen"] = "alcista" if (last > e["sma200"] and e["sma50"] > e["sma200"]) else ("mixto" if last > e["sma200"] else "bajista")
    e["dd_52s"] = (last / e["max_52s"] - 1) * 100
    serie = []
    for k in range(max(20, len(c) - 180), len(c)):
        serie.append(dict(d=d[k], c=round(c[k], 2), h=round(h[k], 2), l=round(l[k], 2), dh=round(max(h[k - 20:k]), 2),
                          dl=round(min(l[k - 20:k]), 2), s200=round(sma(c, 200, k), 2) if sma(c, 200, k) else None, bo=k in bo))
    return e, serie


def panel_horas(horas):
    if not horas or not horas.get("cierres"): return "", "[]", ""
    cs = horas["cierres"]; desde = datetime.strptime(horas["desde"], "%Y-%m-%d %H:%M")
    etiquetas = []
    for k in range(len(cs)):
        t = desde + timedelta(hours=k)
        if t.hour == 0 or k == 0: etiquetas.append([k, f"{t.day} {MESES[t.month - 1]}"])
    imax = cs.index(max(cs)); tmax = desde + timedelta(hours=imax)
    html = f"""
    <section class="panel">
      <h2 class="titulo"><span>Últimas {len(cs)} horas · cierre por hora</span><span class="leyenda">{esc(horas['desde'])} → {esc(horas['hasta'])} UTC</span></h2>
      <div class="grafico" id="h"></div>
      <div class="prosa" style="margin-top:8px"><p>Máximo horario {f0(max(cs))} el {tmax.day} {MESES[tmax.month-1]} a las {tmax:%H:%M} UTC; mínimo {f0(min(cs))}; último cierre horario {f2(cs[-1])}.</p></div>
    </section>"""
    return html, json.dumps(cs), json.dumps(dict(etiquetas=etiquetas, imax=imax, tmax=f"{tmax.day} {MESES[tmax.month-1]} {tmax:%H:%M}"))


def seccion_motor(m, e):
    if not m:
        return """<section class="panel"><h2 class="titulo"><span>Motor probabilístico</span><span class="leyenda">sin dato</span></h2>
        <div class="prosa"><p>No hay <code>datos/motor_resultados.json</code>. Corre <code>python3 motor_probabilidad.py datos/eth_diario.csv &lt;precio&gt; &lt;entrada&gt; &lt;salida&gt;</code> y vuelve a generar la página.</p></div></section>""", "[]"
    nombre = {"tendencia": "normal"}
    reg = m["regimen"]; est = reg["estados"]; colores = ["#4f7cbf", "#22a086", "#c0504e"]
    barra = "".join(f'<i style="flex:{x["p_hoy"]:.3f};background:{colores[k]}" title="{nombre.get(x["nombre"],x["nombre"])} {x["p_hoy"]*100:.0f} %"></i>' for k, x in enumerate(est))
    filas_est = "".join(f'<tr><td><i style="background:{colores[k]}"></i>{nombre.get(x["nombre"],x["nombre"])}</td><td>{x["mu_diario_pct"]:+.2f} %</td><td>{x["vol_anual_pct"]:.0f} %</td><td>{x["duracion_esperada_dias"]:.0f} d</td><td>{x["p_media_historica"]*100:.0f} %</td><td><b>{x["p_hoy"]*100:.0f} %</b></td></tr>' for k, x in enumerate(est))
    b = m["barreras"]; hz = [str(x) for x in b["horizontes"]]
    def fila_b(nom, key):
        return f'<tr><td>{nom}</td>' + "".join(f'<td><b>{b[key][z]["p_entrada_primero"]:.2f}</b> / {b[key][z]["p_salida_primero"]:.2f}</td>' for z in hz) + "</tr>"
    tabla_b = fila_b("Mezcla de régimen (HMM)", "hmm") + fila_b("Bootstrap del último año", "bootstrap_250d") + fila_b("Browniano, vol. 20 d", "gbm_vol20")
    analitico = b["gbm_vol20"]["infinito_analitico"]["p_entrada_primero"]
    tb = m["tasa_base"]; t = tb["todas"]; ic = wilson(round(t["p_ganar"] * t["n"]), t["n"]); cz = tb["concentracion"]; u = tb["ultimas_10"]
    costo = tb["costos"].get("0.3%_por_lado", {}); v = tb.get("vivos_al_dia", {}); ab = tb.get("abierta")
    dist = m["distribucion"]["hmm_20d"]; pc = dist["percentiles_pct"]
    vivos = ""
    if v and v.get("n"):
        vivos = f"""
        <div class="grupo" style="margin-top:10px">La posición del sistema · día {v['dia']}{f" · {ab['R_abierto']:+.2f} R" if ab else ""}</div>
        <table class="mini">
          <tr><td>Operaciones que llegaron vivas al día {v['dia']}</td><td><b>{v['n']} de {t['n']}</b></td></tr>
          <tr><td>P(R restante &gt; 0) · IC 95 %</td><td><b>{v['p_restante_positivo']:.2f}</b> · {v['ic95_p_restante'][0]:.2f}–{v['ic95_p_restante'][1]:.2f}</td></tr>
          <tr><td>R restante · mediana · p25–p75</td><td>{v['R_restante_mediana']:+.2f} · {v['R_restante_p25']:+.2f} a {v['R_restante_p75']:+.2f}</td></tr>
          <tr><td>P(R final &gt; 0)</td><td>{v['p_final_positivo']:.2f}</td></tr>
        </table>"""
    return f"""
  <section class="panel motor">
    <h2 class="titulo"><span>Motor probabilístico · verificado por cuatro revisores independientes</span><span class="leyenda">HMM · Monte Carlo · tasa base {esc(tb['desde'][:4])}→hoy</span></h2>
    <div class="tres">
      <div>
        <div class="sub">Régimen · HMM gaussiano de 3 estados</div>
        <div class="barra-reg">{barra}</div>
        <table class="mini estados"><tr><th>estado</th><th>μ/día</th><th>σ anual</th><th>dura</th><th>histórico</th><th>hoy</th></tr>{filas_est}</table>
        <div class="grafico" id="reg"></div>
        <div class="prosa"><p>"Normal" es el estado por defecto de ETH, no una tendencia: su deriva positiva viene de 2019–2021 y desaparece al ajustar con 3 años. Los estados duran 4–6 días y a 20 días la mezcla ya es la estacionaria: el régimen de hoy no cambia el pronóstico a 20 días. El filtrado reacciona a un solo día.</p></div>
      </div>
      <div>
        <div class="sub">¿Cierre &gt; {f0(b['entrada'])} antes que cierre &lt; {f0(b['salida'])}?</div>
        <table class="mini barreras"><tr><th>método</th>{"".join(f"<th>{z} d</th>" for z in hz)}</tr>{tabla_b}</table>
        <div class="prosa"><p><b>entrada</b> / salida, desde {f0(b['S0'])}. Sin horizonte y sin deriva: {analitico:.2f}. Es una moneda al aire con ligera ventaja de la salida porque está más cerca ({(math.log(b['salida']/b['S0']))*100:+.1f} % frente a {(math.log(b['entrada']/b['S0']))*100:+.1f} %). Las barreras son móviles: el mínimo de 10 d sube si el precio sube y el máximo de 20 d baja cuando expira el día que lo marcó.</p></div>
        <div class="sub">Retorno a 20 días · mezcla HMM</div>
        <div class="abanico"><span class="p5">p5 {pc['5']:+.0f} %</span><span class="p50">mediana {pc['50']:+.1f} %</span><span class="p95">p95 {pc['95']:+.0f} %</span></div>
        <div class="prosa"><p>P(retorno &gt; 0) = {dist['p_positivo']:.2f} con la deriva histórica; sin deriva queda cerca de 0.46. La diferencia es la prima que el lector quiera asignar al pasado alcista de ETH.</p></div>
      </div>
      <div>
        <div class="sub">Tasa base · Turtle 20/10, stop 2×ATR, long-only</div>
        <table class="mini">
          <tr><td>Operaciones {esc(tb['desde'][:4])}→hoy</td><td><b>{t['n']}</b></td></tr>
          <tr><td>P(ganar) · IC 95 %</td><td><b>{t['p_ganar']:.2f}</b> · {ic[0]:.2f}–{ic[1]:.2f}</td></tr>
          <tr><td>R media · IC 95 %</td><td><b>{t['R_media']:+.2f}</b> · {cz['ic95_bootstrap_R_media'][0]:+.2f} a {cz['ic95_bootstrap_R_media'][1]:+.2f}</td></tr>
          <tr><td>R mediana</td><td>{t['R_mediana']:+.2f}</td></tr>
          <tr><td>Profit factor · R media sin la mejor op.</td><td>{t['profit_factor']:.1f} · {cz['R_media_sin_top1']:+.2f}</td></tr>
          <tr><td>3 mejores op. sobre el R total</td><td>{cz['top3_fraccion']*100:.0f} % (mejor: {cz['top1_R']:+.1f} R)</td></tr>
          <tr><td>Últimas 10 · P(ganar) · R media</td><td>{u['p_ganar']:.2f} · {u['R_media']:+.2f}</td></tr>
          <tr><td>Con costos 0.3 % por lado</td><td>P {costo.get('p_ganar', float('nan')):.2f} · R {costo.get('R_media', float('nan')):+.2f}</td></tr>
        </table>{vivos}
        <div class="prosa"><p>La ventaja histórica no es distinguible de cero con esta muestra (t = {cz['t_stat']:.2f}) y está concentrada en 2020–2021. Fracción de Kelly: no estimable; no se reporta como cifra de tamaño.</p></div>
      </div>
    </div>
  </section>""", json.dumps(reg["serie_180"])


PLANTILLA = r'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ETH Lectura Sistemática</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500&display=swap">
<style>
:root{--bg:#07090c;--panel:#0c1015;--linea:#1b2530;--linea-suave:#141c24;--texto:#c8d4de;--tenue:#7d8f9c;--apagado:#3d4a56;--s1:#22a086;--s2:#b9843a;--ok:#4ec9b0;--aviso:#d7a55a;--critico:#d1605e;--banda:rgba(200,212,222,.055);--mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;--sans:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif}
*{box-sizing:border-box}html{color-scheme:dark}body{margin:0;background:var(--bg);color:var(--texto);font:13px/1.5 var(--mono);-webkit-font-smoothing:antialiased;min-height:100vh}
.marco{max-width:1180px;margin:0 auto;padding:18px 16px 40px}
nav.jarvis{display:flex;gap:18px;font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--apagado);margin-bottom:12px}nav.jarvis a{color:var(--tenue);text-decoration:none}nav.jarvis a.activa{color:var(--ok)}nav.jarvis a:hover{color:#eef6fa}
header{display:grid;grid-template-columns:1fr auto;gap:16px;align-items:end;border-bottom:1px solid var(--linea);padding-bottom:14px;margin-bottom:16px}
.ojo{font-size:10px;letter-spacing:.22em;text-transform:uppercase;color:var(--apagado)}h1{margin:4px 0 0;font:600 20px/1.2 var(--mono);letter-spacing:.06em;color:var(--texto)}h1 small{font-weight:400;color:var(--tenue);letter-spacing:0}
.precio{text-align:right}.precio .n{font-size:40px;line-height:1;color:#eef6fa;font-weight:500;letter-spacing:-.02em;text-shadow:0 0 28px rgba(34,160,134,.25)}.precio .n small{font-size:16px;color:var(--tenue);font-weight:400}.precio .f{font-size:10.5px;color:var(--tenue);margin-top:6px}
.pill{display:inline-flex;align-items:center;gap:6px;padding:2px 8px;border-radius:999px;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;border:1px solid}.pill i{width:7px;height:7px;border-radius:50%;background:currentColor;display:inline-block}
.pill.ok{color:var(--ok);border-color:rgba(78,201,176,.35)}.pill.aviso{color:var(--aviso);border-color:rgba(215,165,90,.35)}.pill.critico{color:var(--critico);border-color:rgba(209,96,94,.35)}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:12px}@media(max-width:860px){.tiles{grid-template-columns:repeat(2,1fr)}}
.tile{background:var(--panel);border:1px solid var(--linea);padding:12px 13px;min-height:96px;display:flex;flex-direction:column;gap:6px}.tile .k{font-size:9.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--apagado)}.tile .v{font-size:22px;line-height:1.1;color:#eef6fa;font-weight:500;font-variant-numeric:tabular-nums}.tile .v small{font-size:12px;color:var(--tenue);font-weight:400}.tile .d{font-size:11px;color:var(--tenue);margin-top:auto}
.rejilla{display:grid;grid-template-columns:minmax(0,2fr) minmax(280px,1fr);gap:12px;align-items:start}@media(max-width:860px){.rejilla{grid-template-columns:1fr}}
.panel{background:var(--panel);border:1px solid var(--linea);padding:12px 13px}.titulo{display:flex;justify-content:space-between;align-items:baseline;gap:12px;font-size:9.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--apagado);margin:0 0 10px;padding-bottom:6px;border-bottom:1px solid var(--linea)}
.leyenda{display:flex;gap:14px;font-size:10px;letter-spacing:.04em;text-transform:none;color:var(--tenue)}.leyenda span::before{content:"";display:inline-block;width:14px;height:2px;vertical-align:middle;margin-right:6px;background:var(--c)}.leyenda .banda::before{height:8px;background:var(--banda);border:1px solid var(--linea)}
.grafico{position:relative}.grafico svg{display:block;width:100%;height:auto;overflow:visible}
.tip{position:absolute;pointer-events:none;background:#101822;border:1px solid var(--linea);padding:6px 8px;font-size:11px;line-height:1.45;color:var(--texto);white-space:nowrap;display:none;box-shadow:0 8px 24px rgba(0,0,0,.45)}.tip b{color:#eef6fa;font-weight:500}.tip .m{color:var(--tenue)}
table.niveles{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}table.niveles td{padding:5px 0;border-top:1px dotted var(--linea-suave);vertical-align:baseline}table.niveles td:last-child{text-align:right;color:#eef6fa;font-weight:500}table.niveles tr.clave td:last-child{color:var(--ok)}table.niveles tr.salida td:last-child{color:var(--critico)}table.niveles td .sub{display:block;font-size:10px;color:var(--apagado)}
.grupo{font-size:9.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--apagado);padding:10px 0 2px}
.fila2{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:12px;margin-top:12px}@media(max-width:860px){.fila2{grid-template-columns:1fr}}
pre.senal{margin:0;background:#080c10;border:1px solid var(--linea);padding:10px 12px;font:12px/1.6 var(--mono);color:#eef6fa;white-space:pre-wrap;word-break:break-word}pre.senal .c{color:var(--tenue)}
.prosa{font:13.5px/1.55 var(--sans);color:var(--texto);max-width:62ch}.prosa p{margin:0 0 8px}.prosa strong,.prosa b{color:#eef6fa;font-weight:500}.prosa code{font:11.5px var(--mono);color:var(--ok)}
.motor{margin-top:12px}.tres{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}@media(max-width:960px){.tres{grid-template-columns:1fr}}
.sub{font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--tenue);margin:6px 0 8px}
.barra-reg{display:flex;height:10px;gap:2px;margin:4px 0 10px}.barra-reg i{display:block;height:100%}
table.mini{width:100%;border-collapse:collapse;font-size:11.5px;font-variant-numeric:tabular-nums;margin-bottom:8px}table.mini td,table.mini th{padding:4px 6px 4px 0;border-top:1px dotted var(--linea-suave);vertical-align:top}table.mini th{text-align:left;font-weight:500;color:var(--apagado);font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;border-top:0}table.mini td:last-child,table.mini th:last-child{text-align:right;padding-right:0}table.mini td:not(:first-child){text-align:right;white-space:nowrap}table.mini b{color:#eef6fa;font-weight:500}table.estados td i{display:inline-block;width:9px;height:9px;margin-right:6px;vertical-align:-1px}
.abanico{display:grid;grid-template-columns:1fr 1fr 1fr;font-size:11px;margin:6px 0 8px;background:linear-gradient(90deg,rgba(209,96,94,.25),rgba(200,212,222,.05) 50%,rgba(34,160,134,.25));padding:6px 8px}.abanico .p5{color:var(--critico)}.abanico .p50{text-align:center;color:#eef6fa}.abanico .p95{text-align:right;color:var(--ok)}
.fuente{margin-top:14px;padding-top:10px;border-top:1px solid var(--linea);display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;font-size:10px;letter-spacing:.06em;color:var(--apagado)}
details{margin-top:12px}summary{cursor:pointer;font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:var(--tenue)}summary:focus-visible,a:focus-visible{outline:2px solid var(--ok);outline-offset:2px}
.tabla{overflow-x:auto;margin-top:8px}table.datos{border-collapse:collapse;font-variant-numeric:tabular-nums;font-size:11px;min-width:560px}table.datos th{text-align:right;font-weight:500;color:var(--apagado);letter-spacing:.08em;font-size:9.5px;text-transform:uppercase;padding:4px 10px;border-bottom:1px solid var(--linea)}table.datos th:first-child,table.datos td:first-child{text-align:left}table.datos td{text-align:right;padding:3px 10px;border-bottom:1px dotted var(--linea-suave);color:var(--texto)}
</style></head><body>
<div class="marco">
  <nav class="jarvis"><a href="../hud/hud.html">Panel</a><a class="activa" href="#">ETH</a><a href="../hud/hud.html#mesa">Mesa</a></nav>
  <header>
    <div><div class="ojo">JARVIS · lectura sistemática · privada</div>
      <h1>ETH / USD <small>— reglas del bot: Donchian 20/10 · ATR-14 · régimen SMA-200</small></h1></div>
    <div class="precio"><div class="n">$%%PRECIO_ENT%%<small>.%%PRECIO_DEC%%</small></div><div class="f">%%HORA%% · %%CAMBIO_HOY%% hoy · rango del día %%RANGO_DIA%%</div></div>
  </header>
  <div class="tiles">
    <div class="tile"><div class="k">Régimen</div><div class="v"><span class="pill %%REG_CLASE%%"><i></i>%%REG_TXT%%</span></div><div class="d">%%REG_DESC%%</div></div>
    <div class="tile"><div class="k">Señal de hoy</div><div class="v"><span class="pill %%SEN_CLASE%%"><i></i>%%SEN_TXT%%</span></div><div class="d">%%SEN_DESC%%</div></div>
    <div class="tile"><div class="k">RSI-14 · ATR-14</div><div class="v">%%RSI%% <small>· $%%ATR%% (%%ATR_PCT%% %)</small></div><div class="d">RSI hace 7 días: %%RSI7%%. Vol. 20 d anualizada %%VOL20%% %.</div></div>
    <div class="tile"><div class="k">30 d · 90 d · desde máx. anual</div><div class="v">%%C30%% <small>· %%C90%% · %%DD52%%</small></div><div class="d">Máximo del último año %%MAX52%% (%%MAX52_FECHA%%); mínimo %%MIN52%%.</div></div>
  </div>
  <div class="rejilla">
    <section class="panel">
      <h2 class="titulo"><span>Cierre diario · %%N_DIAS%% días · canal Donchian-20</span><span class="leyenda"><span style="--c:var(--s1)">Cierre ETH</span><span style="--c:var(--s2)">SMA-200</span><span class="banda">Canal 20 d</span></span></h2>
      <div class="grafico" id="g"><div class="tip" id="tip"></div></div>
    </section>
    <aside class="panel">
      <h2 class="titulo"><span>Niveles del sistema</span><span class="leyenda">USD</span></h2>
      <table class="niveles">
        <tr><td colspan="2" class="grupo">Entrada</td></tr>
        <tr class="clave"><td>Entrada nueva<span class="sub">cierre diario &gt; máximo 20 d</span></td><td>%%D20A%%</td></tr>
        %%FILAS_SISTEMA%%
        <tr><td colspan="2" class="grupo">Salida</td></tr>
        <tr class="salida"><td>Salida Turtle<span class="sub">cierre &lt; mínimo 10 d</span></td><td>%%D10B%%</td></tr>
        <tr class="salida"><td>Stop 2×ATR<span class="sub">desde máx. cierre post-breakout</span></td><td>%%STOP2%%</td></tr>
        <tr><td>Stop 3×ATR</td><td>%%STOP3%%</td></tr>
        <tr><td colspan="2" class="grupo">Referencia</td></tr>
        <tr><td>Donchian-20 bajo</td><td>%%D20B%%</td></tr>
        <tr><td>Donchian-55 alto / bajo</td><td>%%D55A%% / %%D55B%%</td></tr>
        <tr><td>SMA-50 / SMA-200</td><td>%%SMA50%% / %%SMA200%%</td></tr>
        <tr><td>Máx. / mín. último año</td><td>%%MAX52%% / %%MIN52%%</td></tr>
      </table>
    </aside>
  </div>
  <div class="fila2">
    %%PANEL_HORAS%%
    <section class="panel">
      <h2 class="titulo"><span>Qué dice el sistema</span><span class="leyenda">formato del bot</span></h2>
<pre class="senal">%%BLOQUE_SENAL%%</pre>
      <div class="prosa" style="margin-top:10px"><p>%%PROSA_SISTEMA%%</p></div>
    </section>
  </div>
  %%SECCION_MOTOR%%
  <details><summary>Últimas 20 velas diarias (tabla)</summary>
    <div class="tabla"><table class="datos"><thead><tr><th>Fecha</th><th>Cierre</th><th>Máx.</th><th>Mín.</th><th>Donchian alto</th><th>Donchian bajo</th><th>SMA-200</th></tr></thead><tbody>%%FILAS%%</tbody></table></div>
  </details>
  <div class="fuente"><span>Datos: %%FUENTE%%. Cálculo propio (eth_pagina.py + motor_probabilidad.py).</span><span>No es asesoría. Desde JARVIS nunca se coloca una orden; el humano ejecuta.</span></div>
</div>
<script>
const D = %%DATA%%;
const fmt = n => n.toLocaleString('en-US',{maximumFractionDigits:0}); const fmt2 = n => n.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
const MESES = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic']; const NS='http://www.w3.org/2000/svg';
function el(tag,attrs,parent){const n=document.createElementNS(NS,tag);for(const k in attrs)n.setAttribute(k,attrs[k]);if(parent)parent.appendChild(n);return n;}
const F='IBM Plex Mono, monospace';
(function(){ /* gráfico principal */
  const W=760,H=400,m={t:14,r:62,b:26,l:8}; const pts=D.pts,n=pts.length; const cont=document.getElementById('g'),tip=document.getElementById('tip');
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':'Cierre diario de ETH con canal Donchian de 20 días y SMA-200'},cont);
  const lo=Math.min(...pts.map(p=>Math.min(p.l,p.dl,p.s200||1e9))),hi=Math.max(...pts.map(p=>Math.max(p.h,p.dh,p.s200||0)));
  const paso=(hi-lo)>1500?500:250; const y0=Math.floor(lo/paso)*paso,y1=Math.ceil(hi/paso)*paso;
  const x=i=>m.l+(W-m.l-m.r)*i/(n-1),y=v=>m.t+(H-m.t-m.b)*(1-(v-y0)/(y1-y0)); const yUlt=y(pts[n-1].c);
  for(let v=y0;v<=y1;v+=paso){el('line',{x1:m.l,x2:W-m.r,y1:y(v),y2:y(v),stroke:'#141c24'},svg);if(Math.abs(y(v)-yUlt)<10)continue;el('text',{x:W-m.r+8,y:y(v)+3.5,fill:'#5a6b7a','font-size':'10','font-family':F},svg).textContent=fmt(v);}
  pts.forEach((p,i)=>{if(p.d.slice(8,10)==='01'){el('text',{x:x(i),y:H-8,fill:'#5a6b7a','font-size':'10','text-anchor':'middle','font-family':F},svg).textContent=MESES[+p.d.slice(5,7)-1];}});
  const arriba=pts.map((p,i)=>`${x(i)},${y(p.dh)}`).join(' L'),abajo=pts.slice().reverse().map((p,j)=>`${x(n-1-j)},${y(p.dl)}`).join(' L');
  el('path',{d:`M${arriba} L${abajo} Z`,fill:'rgba(200,212,222,.055)',stroke:'none'},svg);
  el('path',{d:'M'+arriba,fill:'none',stroke:'#1b2530'},svg); el('path',{d:'M'+pts.map((p,i)=>`${x(i)},${y(p.dl)}`).join(' L'),fill:'none',stroke:'#1b2530'},svg);
  const nivel=(v,color,dash,txt,dy,px)=>{el('line',{x1:m.l,x2:W-m.r,y1:y(v),y2:y(v),stroke:color,'stroke-dasharray':dash,opacity:.85},svg);el('text',{x:m.l+px,y:y(v)+dy,fill:color,'font-size':'9.5','font-family':F},svg).textContent=txt;};
  nivel(D.e.d20a,'#4ec9b0','4 4','entrada nueva '+fmt(D.e.d20a),-4,4); nivel(D.e.d10b,'#d1605e','4 4','salida 10 d '+fmt(D.e.d10b),-4,4); nivel(D.e.stop2,'#d1605e','1.5 3.5','stop 2×ATR '+fmt(D.e.stop2),11,150);
  el('path',{d:'M'+pts.map((p,i)=>p.s200?`${x(i)},${y(p.s200)}`:null).filter(Boolean).join(' L'),fill:'none',stroke:'#b9843a','stroke-width':2,'stroke-linejoin':'round'},svg);
  el('path',{d:'M'+pts.map((p,i)=>`${x(i)},${y(p.c)}`).join(' L'),fill:'none',stroke:'#22a086','stroke-width':2,'stroke-linejoin':'round','stroke-linecap':'round'},svg);
  pts.forEach((p,i)=>{if(p.bo)el('circle',{cx:x(i),cy:y(p.c),r:4.5,fill:'#0c1015',stroke:'#22a086','stroke-width':2},svg);});
  const L=pts[n-1]; el('circle',{cx:x(n-1),cy:y(L.c),r:4,fill:'#22a086',stroke:'#0c1015','stroke-width':2},svg);
  el('text',{x:x(n-1)+8,y:y(L.c)+4,fill:'#c8d4de','font-size':'10.5','font-weight':'600','font-family':F},svg).textContent=fmt(L.c);
  if(L.s200)el('text',{x:x(n-1)-4,y:y(L.s200)-6,fill:'#b9843a','font-size':'9.5','text-anchor':'end','font-family':F},svg).textContent='SMA-200';
  const cx=el('line',{x1:0,x2:0,y1:m.t,y2:H-m.b,stroke:'#3d4a56','stroke-dasharray':'2 3',opacity:0},svg),dot=el('circle',{r:4,fill:'#22a086',stroke:'#0c1015','stroke-width':2,opacity:0},svg);
  const zona=el('rect',{x:m.l,y:m.t,width:W-m.l-m.r,height:H-m.t-m.b,fill:'transparent'},svg);
  function mueve(ev){const r=svg.getBoundingClientRect();const px=(ev.clientX-r.left)*W/r.width;const i=Math.max(0,Math.min(n-1,Math.round((px-m.l)/(W-m.l-m.r)*(n-1))));const p=pts[i];
    cx.setAttribute('x1',x(i));cx.setAttribute('x2',x(i));cx.setAttribute('opacity',1);dot.setAttribute('cx',x(i));dot.setAttribute('cy',y(p.c));dot.setAttribute('opacity',1);
    const f=p.d.slice(8,10)+' '+MESES[+p.d.slice(5,7)-1]+' '+p.d.slice(0,4);
    tip.innerHTML=`<b>${f}</b>${p.bo?' · <span style="color:#22a086">breakout 20 d</span>':''}<br>cierre <b>${fmt2(p.c)}</b> <span class="m">máx ${fmt(p.h)} · mín ${fmt(p.l)}</span><br><span class="m">canal 20 d</span> ${fmt(p.dl)}–${fmt(p.dh)} · <span class="m">SMA-200</span> ${p.s200?fmt(p.s200):'—'}`;
    tip.style.display='block';const cw=cont.clientWidth,tw=tip.offsetWidth;let left=(x(i)/W)*cw+12;if(left+tw>cw)left=(x(i)/W)*cw-tw-12;tip.style.left=left+'px';tip.style.top=Math.max(0,(y(p.c)/H)*cont.clientHeight-40)+'px';}
  zona.addEventListener('mousemove',mueve);zona.addEventListener('touchmove',e=>{mueve(e.touches[0]);e.preventDefault();},{passive:false});
  zona.addEventListener('mouseleave',()=>{tip.style.display='none';cx.setAttribute('opacity',0);dot.setAttribute('opacity',0);});
})();
(function(){ /* últimas horas */
  const h=D.horas; if(!h||!h.length||!document.getElementById('h'))return; const W=520,H=120,m={t:10,r:48,b:18,l:6},n=h.length,cont=document.getElementById('h');
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':'Cierre horario de ETH'},cont);
  const lo=Math.floor(Math.min(...h)/50)*50,hi=Math.ceil(Math.max(...h)/50)*50; const x=i=>m.l+(W-m.l-m.r)*i/(n-1),y=v=>m.t+(H-m.t-m.b)*(1-(v-lo)/(hi-lo));
  [lo,hi].forEach(v=>{el('line',{x1:m.l,x2:W-m.r,y1:y(v),y2:y(v),stroke:'#141c24'},svg);el('text',{x:W-m.r+8,y:y(v)+3.5,fill:'#5a6b7a','font-size':'10','font-family':F},svg).textContent=v.toLocaleString('en-US');});
  D.hmeta.etiquetas.forEach(([i,t])=>{el('line',{x1:x(i),x2:x(i),y1:m.t,y2:H-m.b,stroke:'#1b2530','stroke-dasharray':'2 3'},svg);el('text',{x:x(i)+3,y:H-6,fill:'#5a6b7a','font-size':'10','font-family':F},svg).textContent=t;});
  const linea=h.map((v,i)=>`${x(i)},${y(v)}`).join(' L'); el('path',{d:`M${x(0)},${y(lo)} L${linea} L${x(n-1)},${y(lo)} Z`,fill:'rgba(34,160,134,.10)'},svg); el('path',{d:'M'+linea,fill:'none',stroke:'#22a086','stroke-width':2,'stroke-linejoin':'round'},svg);
  const im=D.hmeta.imax; el('circle',{cx:x(im),cy:y(h[im]),r:3.5,fill:'#0c1015',stroke:'#d7a55a','stroke-width':2},svg); el('text',{x:x(im)-6,y:y(h[im])-7,fill:'#d7a55a','font-size':'9.5','text-anchor':'end','font-family':F},svg).textContent=fmt(h[im])+' · '+D.hmeta.tmax;
  el('circle',{cx:x(n-1),cy:y(h[n-1]),r:3.5,fill:'#22a086',stroke:'#0c1015','stroke-width':2},svg); el('text',{x:x(n-1)+7,y:y(h[n-1])+4,fill:'#c8d4de','font-size':'10','font-weight':'600','font-family':F},svg).textContent=h[n-1].toLocaleString('en-US');
})();
(function(){ /* franja de régimen */
  const s=D.reg; const cont=document.getElementById('reg'); if(!s||!s.length||!cont)return; const W=360,H=90,m={t:6,r:6,b:16,l:6},n=s.length; const C=['#4f7cbf','#22a086','#c0504e'];
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,role:'img','aria-label':'Probabilidad filtrada de cada régimen, últimos días'},cont);
  const x=i=>m.l+(W-m.l-m.r)*i/(n-1),y=v=>m.t+(H-m.t-m.b)*(1-v);
  for(let k=0;k<3;k++){const top=s.map((p,i)=>`${x(i)},${y(p.p.slice(0,k+1).reduce((a,b)=>a+b,0))}`).join(' L'),bot=s.slice().reverse().map((p,j)=>{const i=n-1-j;return `${x(i)},${y(p.p.slice(0,k).reduce((a,b)=>a+b,0))}`;}).join(' L');el('path',{d:`M${top} L${bot} Z`,fill:C[k],opacity:.85},svg);}
  s.forEach((p,i)=>{if(p.d.slice(8,10)==='01')el('text',{x:x(i),y:H-4,fill:'#5a6b7a','font-size':'9','text-anchor':'middle','font-family':F},svg).textContent=MESES[+p.d.slice(5,7)-1];});
})();
</script></body></html>'''


def main():
    d, o, h, l, c = cargar_csv(); e, serie = indicadores(d, o, h, l, c)
    if "--niveles" in sys.argv:
        print(f"S0={c[-1]} entrada={e['donchian20_alto']} salida={e['donchian10_bajo']}"); return
    m = leer_json("motor_resultados.json"); q = leer_json("eth_cotizacion.json") or {}; horas = leer_json("eth_horas.json")
    precio = q.get("precio", c[-1]); hora = q.get("hora_utc", f"cierre {e['fecha_vela']}") + (" UTC" if "hora_utc" in q else "")
    cambio_hoy = pct(q["cambio_pct"], 2) if "cambio_pct" in q else "sin dato"
    rango = f"{f0(q['min_dia'])}–{f0(q['max_dia'])}" if "min_dia" in q else "sin dato"
    ab = (m or {}).get("tasa_base", {}).get("abierta") if m else None
    # señal
    hoy_breakout = c[-1] > e["donchian20_alto"]
    if hoy_breakout: sen = ("ok", "Entrada · breakout hoy", f"Cierre {f0(c[-1])} por encima del máximo de 20 días ({f0(e['donchian20_alto'])}).")
    elif ab and c[-1] < e["donchian10_bajo"]: sen = ("critico", "Salida · mínimo 10 d", f"Cierre {f0(c[-1])} por debajo del mínimo de 10 días ({f0(e['donchian10_bajo'])}).")
    elif ab: sen = ("aviso", "Mantener · sin entrada", f"Sistema dentro desde el {fecha_larga(ab['fecha_in'])} a {f0(ab['entrada'])} ({ab['R_abierto']:+.2f} R). Máximo cierre desde entonces {f0(ab['max_cierre'])}; hoy {(c[-1]/ab['max_cierre']-1)*100:+.1f} %.")
    else: sen = ("aviso", "Fuera · esperar", f"Sin posición. Entrada nueva solo con cierre diario &gt; {f0(e['donchian20_alto'])}.")
    reg_clase = {"alcista": "ok", "mixto": "aviso", "bajista": "critico"}[e["regimen"]]
    hmm = ""
    if m: est = m["regimen"]["estados"]; nm = {"tendencia": "normal"}; hmm = " HMM: " + " · ".join(f"{nm.get(x['nombre'], x['nombre'])} {x['p_hoy']*100:.0f} %" for x in est) + "."
    reg_desc = f"Cierre {e['sobre_sma200']:+.1f} % sobre SMA-200 ({f0(e['sma200'])}); SMA-50 ({f0(e['sma50'])}) {'por encima' if e['sma50']>e['sma200'] else 'por debajo'}.{hmm}"
    filas_sis = ""
    if ab:
        filas_sis = f'<tr><td>Entrada del sistema<span class="sub">{fecha_larga(ab["fecha_in"])}, cierre · {ab["R_abierto"]:+.2f} R</span></td><td>{f0(ab["entrada"])}</td></tr><tr><td>Máximo cierre desde la entrada</td><td>{f0(ab["max_cierre"])}</td></tr>'
    elif e["ultimo_breakout"]:
        filas_sis = f'<tr><td>Último breakout<span class="sub">{fecha_larga(e["ultimo_breakout"])}, cierre</span></td><td>{f0(e["cierre_breakout"])}</td></tr>'
    stop_ini = f'<tr><td>Stop inicial del sistema<span class="sub">entrada − 2×ATR de la entrada</span></td><td>{f0(ab["stop"])}</td></tr>' if ab else ""
    # bloque señal
    hmm_corto = ""
    if m:
        nm = {"tendencia": "normal"}
        hmm_corto = " · HMM " + " ".join(f"{nm.get(x['nombre'], x['nombre'])} {x['p_hoy']*100:.0f}%" for x in m["regimen"]["estados"])
    if ab:
        bloque = (f'ETH · LONG <span class="c">(sistema Turtle dentro desde {ab["fecha_in"]} @ {ab["entrada"]:.1f} · {ab["R_abierto"]:+.2f} R · stop inicial {f0(ab["stop"])})</span>\n'
                  f'Entrada nueva : cierre diario &gt; {f0(e["donchian20_alto"])} <span class="c">(no aplica: ya hay posición, sin piramidación)</span>\n'
                  f'Salida        : cierre diario &lt; {f0(e["donchian10_bajo"])} <span class="c">(mín 10 d)</span> · trailing 2×ATR {f0(e["stop_2atr"])} <span class="c">(regla del bot)</span>\n'
                  f'Régimen       : SMA {e["regimen"]}{hmm_corto}\n'
                  f'<span class="c">{"Señal nueva hoy: " + sen[1] if hoy_breakout or sen[0]=="critico" else "Sin señal nueva hoy."} Tamaño de posición: sin dato (position_sizing vive en el Mac).</span>')
        prosa = (f"Un sistema Turtle estricto entró el <b>{fecha_larga(ab['fecha_in'])} a {f0(ab['entrada'])}</b> y va {ab['R_abierto']:+.2f} R; el máximo cierre desde entonces es {f0(ab['max_cierre'])}. "
                 f"{'Ni la salida de 10 días ni el stop se han tocado. ' if sen[0]!='critico' else 'Hoy se cumple la salida: cierre bajo el mínimo de 10 días. '}"
                 f"Un cierre bajo {f0(e['donchian10_bajo'])} cierra; un cierre sobre {f0(e['donchian20_alto'])} no añade nada a un sistema sin piramidación.")
    else:
        bloque = (f'ETH · FLAT <span class="c">(sin posición del sistema)</span>\nEntrada nueva : cierre diario &gt; {f0(e["donchian20_alto"])}\nSalida        : n/a\nRégimen       : SMA {e["regimen"]}\n<span class="c">{"Señal nueva hoy: entrada." if hoy_breakout else "Sin señal nueva hoy."}</span>')
        prosa = f"El sistema está fuera. La entrada exige un cierre diario por encima de {f0(e['donchian20_alto'])}; el régimen SMA es {e['regimen']}."
    panel_h, horas_js, hmeta = panel_horas(horas)
    sec_motor, reg_js = seccion_motor(m, e)
    filas = "".join(f"<tr><td>{p['d']}</td><td>{f2(p['c'])}</td><td>{f2(p['h'])}</td><td>{f2(p['l'])}</td><td>{f0(p['dh'])}</td><td>{f0(p['dl'])}</td><td>{f0(p['s200']) if p['s200'] else '—'}</td></tr>" for p in serie[-20:])
    data = json.dumps(dict(pts=serie, horas=json.loads(horas_js), hmeta=json.loads(hmeta) if hmeta else {}, reg=json.loads(reg_js),
                           e=dict(d20a=round(e["donchian20_alto"], 2), d10b=round(e["donchian10_bajo"], 2), stop2=round(e["stop_2atr"], 2))), ensure_ascii=False)
    for ch, rep in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026")): data = data.replace(ch, rep)
    fuente = f"velas diarias {d[0]} → {d[-1]}" + (f"; cotización {esc(q.get('fuente','FMP'))} {esc(q['hora_utc'])} UTC" if 'hora_utc' in q else "; sin cotización en vivo")
    ent, dec = f"{precio:,.2f}".split(".")
    html = PLANTILLA
    for k, v in dict(PRECIO_ENT=ent, PRECIO_DEC=dec, HORA=esc(hora), CAMBIO_HOY=cambio_hoy, RANGO_DIA=rango, REG_CLASE=reg_clase, REG_TXT=e["regimen"].capitalize(), REG_DESC=reg_desc,
                     SEN_CLASE=sen[0], SEN_TXT=sen[1], SEN_DESC=sen[2], RSI=f"{e['rsi14']:.1f}", ATR=f0(e["atr14"]), ATR_PCT=f"{e['atr_pct']:.1f}", RSI7=f"{e['rsi_hace_7']:.0f}", VOL20=f"{e['vol20']:.0f}",
                     C30=pct(e["cambio_30d"]), C90=pct(e["cambio_90d"]), DD52=pct(e["dd_52s"]), MAX52=f0(e["max_52s"]), MAX52_FECHA=fecha_larga(e["fecha_max_52s"])[2:], MIN52=f0(e["min_52s"]), N_DIAS=str(len(serie)),
                     D20A=f0(e["donchian20_alto"]), FILAS_SISTEMA=filas_sis + stop_ini, D10B=f0(e["donchian10_bajo"]), STOP2=f0(e["stop_2atr"]), STOP3=f0(e["stop_3atr"]), D20B=f0(e["donchian20_bajo"]),
                     D55A=f0(e["donchian55_alto"]), D55B=f0(e["donchian55_bajo"]), SMA50=f0(e["sma50"]), SMA200=f0(e["sma200"]), PANEL_HORAS=panel_h, BLOQUE_SENAL=bloque, PROSA_SISTEMA=prosa,
                     SECCION_MOTOR=sec_motor, FILAS=filas, FUENTE=fuente, DATA=data).items():
        html = html.replace(f"%%{k}%%", v)
    assert "%%" not in html, "quedó un marcador sin sustituir"
    (RAIZ / "eth.html").write_text(html, encoding="utf-8")
    print(f"eth.html generado · {e['fecha_vela']} · cierre {c[-1]} · régimen {e['regimen']} · señal: {sen[1]}")


if __name__ == "__main__":
    main()
