#!/usr/bin/env python3
"""
Genera el HUD de JARVIS leyendo datos reales de la boveda.

Escribe un unico archivo hud/hud.html con los datos incrustados. No levanta
servidor ni expone nada por red -- se abre directo del disco.

    python3 hud/generar.py && open hud/hud.html

Solo usa la libreria estandar. Corre con el python3 que trae macOS.
"""

import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

DIAS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
            "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MESES_CORTO = ["ene", "feb", "mar", "abr", "may", "jun",
               "jul", "ago", "sep", "oct", "nov", "dic"]


def fecha_larga(d):
    return f"{DIAS_ES[d.weekday()]} {d.day} de {MESES_ES[d.month - 1]} de {d.year}"


def fecha_corta(d):
    return f"{d.day} {MESES_CORTO[d.month - 1]}"

RAIZ = Path(__file__).resolve().parent.parent
BOVEDA = RAIZ / "boveda"
HOY = date.today()

# Compromisos con fecha. Editalos aqui cuando cambien.
HITOS = [
    ("Stripe + Supabase Auth", date(2026, 9, 8), None, None),
    ("Miembros fundadores", date(2026, 9, 30), 0, 5),
    ("Criterio go/no-go", date(2026, 12, 1), 0, 50),
]

COMANDOS = [
    ("bandeja", "resumen matutino"),
    ("plan-hoy", "plan de hoy"),
    ("metricas", "como vamos"),
    ("revision-semanal", "cierra el dia"),
    ("boveda", "que sabes de..."),
    ("mesa-expertos", "convoca la mesa"),
]

DIRECTIVAS = [
    "Un solo proyecto activo: Vantera",
    "Cero proyectos nuevos hasta el 1 dic",
    "Nunca colocar ordenes -- solo lectura",
    "Portafolio nunca sale de esta maquina",
    "5-10 h/semana es el presupuesto real",
]


def leer(p):
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


def contar(carpeta, excluir=("LEEME.md",)):
    if not carpeta.exists():
        return 0
    return len([f for f in carpeta.rglob("*.md") if f.name not in excluir])


def outputs_recientes(n=6):
    d = BOVEDA / "outputs"
    if not d.exists():
        return []
    fs = [f for f in d.glob("*.md") if f.name != "LEEME.md"]
    fs.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    salida = []
    for f in fs[:n]:
        m = re.match(r"(\d{4}-\d{2}-\d{2})-(.+)\.md$", f.name)
        fecha, tipo = (m.group(1), m.group(2)) if m else ("--", f.stem)
        salida.append({"fecha": fecha, "tipo": tipo})
    return salida


def prioridades_de_hoy():
    """Prioridades del plan mas reciente que no sea futuro: (lista, fecha, total)."""
    d = BOVEDA / "outputs"
    if not d.exists():
        return [], None, 0
    planes = []
    for f in d.glob("*-plan.md"):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}-plan\.md", f.name):
            continue
        fd = fecha_de_nombre(f.name)
        if fd and fd <= HOY:
            planes.append((fd, f))
    if not planes:
        return [], None, 0
    fd, f = max(planes)
    texto = sin_codigo(leer(f))
    items = [limpiar_md(t) for t in
             re.findall(r"^#{2,3}\s+\d+[.)]\s+(.+?)\s*$", texto, re.MULTILINE)]
    items = [t for t in items if t]
    return items[:3], fd.isoformat(), len(items)


def sin_codigo(texto):
    """Quita bloques ``` / ~~~ y código inline para no contar ejemplos como datos."""
    texto = re.sub(r"^(`{3,}|~{3,})[^\n]*\n.*?^\1[^\n]*$", "", texto, flags=re.DOTALL | re.MULTILINE)
    texto = re.sub(r"```.*?```", "", texto, flags=re.DOTALL)
    return re.sub(r"`[^`\n]*`", "", texto)


def limpiar_md(t):
    """Deja un título legible: sin negritas, backticks ni corchetes de wikilink."""
    return re.sub(r"\*\*|`|\[\[|\]\]", "", t).strip()


def fecha_de_nombre(nombre):
    """AAAA-MM-DD al inicio del nombre, o None si no hay o no es una fecha válida."""
    m = re.match(r"(\d{4}-\d{2}-\d{2})", nombre)
    if not m:
        return None
    try:
        return date.fromisoformat(m.group(1))
    except ValueError:
        print(f"  aviso: fecha inválida en el nombre, se ignora: {nombre}", file=sys.stderr)
        return None


def enlaces_boveda():
    """Cuenta wikilinks reales para dibujar el grafo."""
    wiki = BOVEDA / "wiki"
    if not wiki.exists():
        return 0
    total = 0
    for f in wiki.rglob("*.md"):
        if f.name == "LEEME.md":
            continue
        total += len(re.findall(r"\[\[([^\]]+)\]\]", sin_codigo(leer(f))))
    return total


def capturas_esta_semana():
    d = BOVEDA / "raw"
    if not d.exists():
        return 0
    corte = HOY - timedelta(days=6)  # hoy y los seis días anteriores
    n = 0
    for f in d.glob("*.md"):
        fd = fecha_de_nombre(f.name)
        if fd and fd >= corte:
            n += 1
    return n


def parking_lot():
    """Cuenta cada idea listada (con o sin fecha), ignorando los ejemplos en código."""
    texto = sin_codigo(leer(BOVEDA / "wiki" / "parking-lot.md"))
    return len(re.findall(r"^\s*[-*+]\s+\S", texto, re.MULTILINE))


def fundadores_desde_metricas():
    """Lee 'Fundadores pagando: N / M' de la última corrida de la skill metricas.

    Devuelve (N, fecha) o (None, None) si no hay corrida. Ese número manda sobre
    la constante de HITOS: así el HUD refleja lo que la skill midió, no lo que
    alguien editó a mano.
    """
    d = BOVEDA / "outputs"
    if not d.exists():
        return None, None
    corridas = [f for f in d.glob("*-metricas.md")
                if re.fullmatch(r"\d{4}-\d{2}-\d{2}-metricas\.md", f.name) and fecha_de_nombre(f.name)]
    if not corridas:
        return None, None
    ultima = max(corridas, key=lambda f: f.name)
    m = re.search(r"Fundadores pagando:\s*(\d+)\s*/\s*(\d+)", leer(ultima))
    if not m:
        return None, None
    return int(m.group(1)), ultima.name[:10]


def md_a_html(texto):
    """Conversor mínimo de Markdown (lo que escriben las skills) a HTML seguro."""
    import html as _h
    lineas = texto.split("\n"); out = []; lista = None; tabla = []; parrafo = []
    def inline(t):
        t = _h.escape(t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t); t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
        t = re.sub(r"\*(?!\s)(.+?)\*", r"<i>\1</i>", t); t = re.sub(r"\[\[([^\]]+)\]\]", r"<u>\1</u>", t)
        return t
    def cierra_parrafo():
        if parrafo: out.append("<p>" + inline(" ".join(parrafo)) + "</p>"); parrafo.clear()
    def cierra_lista():
        nonlocal lista
        if lista: out.append(f"</{lista}>"); lista = None
    def cierra_tabla():
        if tabla:
            filas = [f for f in tabla if not re.match(r"^\|?\s*:?-{2,}", f)]
            html_f = []
            for k, f in enumerate(filas):
                celdas = [c.strip() for c in f.strip().strip("|").split("|")]
                tag = "th" if k == 0 else "td"
                html_f.append("<tr>" + "".join(f"<{tag}>{inline(c)}</{tag}>" for c in celdas) + "</tr>")
            out.append("<table>" + "".join(html_f) + "</table>"); tabla.clear()
    en_codigo = False
    for ln in lineas:
        if ln.startswith("```"):
            cierra_parrafo(); cierra_lista(); cierra_tabla()
            if en_codigo: out.append("</pre>")
            else: out.append("<pre>")
            en_codigo = not en_codigo; continue
        if en_codigo: out.append(_h.escape(ln)); continue
        if ln.strip().startswith("|"): cierra_parrafo(); cierra_lista(); tabla.append(ln); continue
        cierra_tabla()
        m = re.match(r"^(#{1,4})\s+(.*)", ln)
        if m: cierra_parrafo(); cierra_lista(); out.append(f"<h{len(m.group(1))+1}>{inline(m.group(2))}</h{len(m.group(1))+1}>"); continue
        m = re.match(r"^\s*(?:[-*]|\d+[.)])\s+(.*)", ln)
        if m:
            cierra_parrafo(); tipo = "ol" if re.match(r"^\s*\d", ln) else "ul"
            if lista != tipo: cierra_lista(); out.append(f"<{tipo}>"); lista = tipo
            out.append(f"<li>{inline(m.group(1))}</li>"); continue
        if not ln.strip(): cierra_parrafo(); cierra_lista(); continue
        parrafo.append(ln.strip())
    cierra_parrafo(); cierra_lista(); cierra_tabla()
    return "\n".join(out)


def memo_mesa():
    """Último memo de la mesa de expertos (outputs/*-mesa*.md), ya convertido a HTML."""
    d = BOVEDA / "outputs"
    if not d.exists(): return None
    memos = [f for f in d.glob("*-mesa*.md") if fecha_de_nombre(f.name)]
    if not memos: return None
    f = max(memos, key=lambda f: f.name)
    texto = leer(f)
    cuerpo = re.sub(r"^---.*?---\s*", "", texto, count=1, flags=re.DOTALL)
    return {"archivo": f.name, "fecha": f.name[:10], "html": md_a_html(cuerpo)}


def construir_datos():
    fundadores, fecha_metricas = fundadores_desde_metricas()
    hitos = []
    for nombre, fecha, actual, meta in HITOS:
        if meta and fundadores is not None:
            actual = fundadores  # clientes pagando: la skill metricas manda
        dias = (fecha - HOY).days
        hitos.append({
            "nombre": nombre,
            "fecha": fecha_corta(fecha),
            "dias": dias,
            "actual": actual,
            "meta": meta,
            "vencido": dias < 0,
        })

    prios, fecha_plan, total_prios = prioridades_de_hoy()
    plan_viejo = bool(fecha_plan) and fecha_plan != HOY.isoformat()

    return {
        "generado": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "fecha_larga": fecha_larga(HOY),
        "hitos": hitos,
        "vitales": {
            "notas_wiki": contar(BOVEDA / "wiki"),
            "capturas": contar(BOVEDA / "raw"),
            "outputs": contar(BOVEDA / "outputs"),
            "enlaces": enlaces_boveda(),
            "capturas_semana": capturas_esta_semana(),
            "parking": parking_lot(),
        },
        "prioridades": prios,
        "total_prioridades": total_prios,
        "fecha_plan": fecha_plan,
        "plan_viejo": plan_viejo,
        "fecha_metricas": fecha_metricas,
        "recientes": outputs_recientes(),
        "mesa": memo_mesa(),
        "eth": (RAIZ / "analisis" / "eth.html").exists(),
        "comandos": [{"skill": s, "frase": f} for s, f in COMANDOS],
        "directivas": DIRECTIVAS,
    }


PLANTILLA = r"""<!doctype html>
<html lang="es"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>JARVIS</title>
<style>
  :root{
    --bg:#07090c; --panel:#0c1015; --linea:#1b2530;
    --texto:#c8d4de; --tenue:#5a6b7a; --apagado:#3d4a56;
    --acento:#4ec9b0; --ambar:#d7a55a; --rojo:#d1605e;
    --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--texto);font:12px/1.5 var(--mono);
       -webkit-font-smoothing:antialiased;min-height:100vh}
  a{color:inherit}
  .marco{max-width:1500px;margin:0 auto;padding:14px}

  header{display:flex;align-items:baseline;gap:16px;flex-wrap:wrap;
         border-bottom:1px solid var(--linea);padding-bottom:10px;margin-bottom:14px}
  .logo{font-size:15px;letter-spacing:.42em;color:var(--acento);font-weight:600}
  .sub{color:var(--apagado);letter-spacing:.16em;font-size:10px;text-transform:uppercase}
  .reloj{margin-left:auto;text-align:right}
  .reloj .h{font-size:24px;color:var(--texto);letter-spacing:.04em;line-height:1.1}
  .reloj .f{color:var(--apagado);font-size:10px}

  .rejilla{display:grid;grid-template-columns:230px 1fr 300px;gap:14px;align-items:start}
  @media(max-width:1100px){.rejilla{grid-template-columns:1fr}}

  .panel{background:var(--panel);border:1px solid var(--linea);padding:12px 13px}
  .titulo{font-size:9px;letter-spacing:.2em;color:var(--apagado);text-transform:uppercase;
          margin:0 0 10px;padding-bottom:6px;border-bottom:1px solid var(--linea)}
  .panel + .panel{margin-top:12px}

  .vital{display:flex;justify-content:space-between;align-items:baseline;padding:5px 0}
  .vital + .vital{border-top:1px dotted #141c24}
  .vital .n{font-size:17px;color:var(--acento);letter-spacing:.02em}
  .vital .e{font-size:10px;color:var(--tenue);text-align:right;max-width:60%}

  .centro{display:flex;flex-direction:column;gap:12px}
  .escena{position:relative;background:var(--panel);border:1px solid var(--linea);
          height:330px;overflow:hidden}
  canvas{display:block;width:100%;height:100%}
  .sobre{position:absolute;inset:0;display:flex;flex-direction:column;
         align-items:center;justify-content:center;pointer-events:none;text-align:center}
  /* velo radial: el texto se lee sobre el grafo sin taparlo */
  .sobre::before{content:"";position:absolute;left:50%;top:50%;
    width:420px;height:250px;transform:translate(-50%,-50%);
    background:radial-gradient(ellipse at center,rgba(7,9,12,.93) 0%,
               rgba(7,9,12,.72) 42%,rgba(7,9,12,0) 72%)}
  .sobre > *{position:relative}
  .gigante{font-size:70px;line-height:1;color:#eef6fa;letter-spacing:-.02em;
           text-shadow:0 0 40px rgba(78,201,176,.45),0 0 14px rgba(7,9,12,.9)}
  .gigante small{font-size:28px;color:#7d8f9c}
  .etiqueta{margin-top:10px;font-size:10px;letter-spacing:.24em;color:#8fa3b0;
            text-transform:uppercase}
  .cuenta{margin-top:4px;font-size:11px;color:var(--ambar)}

  .hitos{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
  @media(max-width:700px){.hitos{grid-template-columns:1fr}}
  .hito{background:var(--panel);border:1px solid var(--linea);padding:10px 12px}
  .hito .nom{font-size:10px;color:var(--tenue);text-transform:uppercase;letter-spacing:.1em}
  .hito .dias{font-size:22px;margin-top:5px;color:var(--texto)}
  .hito .dias span{font-size:10px;color:var(--apagado);letter-spacing:.1em}
  .hito.urgente .dias{color:var(--ambar)}
  .hito.vencido .dias{color:var(--rojo)}
  .barra{height:2px;background:#141c24;margin-top:8px}
  .barra i{display:block;height:100%;background:var(--acento)}

  ol.prio{margin:0;padding-left:17px}
  ol.prio li{padding:4px 0;color:var(--texto)}
  ol.prio li::marker{color:var(--acento)}
  .aviso{color:var(--ambar);font-size:10px;margin-top:8px;padding-top:7px;
         border-top:1px dotted #141c24}
  .vacio{color:var(--apagado);font-style:italic}

  .cmd{display:flex;justify-content:space-between;gap:10px;padding:4px 0;font-size:11px}
  .cmd + .cmd{border-top:1px dotted #141c24}
  .cmd b{color:var(--acento);font-weight:500}
  .cmd i{color:var(--apagado);font-style:normal;font-size:10px}

  ul.dir{margin:0;padding:0;list-style:none}
  ul.dir li{padding:4px 0 4px 13px;position:relative;font-size:10.5px;color:var(--tenue)}
  ul.dir li::before{content:"▸";position:absolute;left:0;color:var(--apagado)}

  .rec{display:flex;justify-content:space-between;padding:3px 0;font-size:10.5px}
  .rec + .rec{border-top:1px dotted #141c24}
  .rec b{color:var(--texto);font-weight:400}
  .rec i{color:var(--apagado);font-style:normal}

  .nav{display:flex;gap:18px;font-size:10px;letter-spacing:.2em;text-transform:uppercase;
       color:var(--apagado);margin-bottom:10px}
  .nav a{color:var(--tenue);text-decoration:none}
  .nav a.activa{color:var(--acento)}
  .nav a:hover{color:var(--texto)}
  .nav a[hidden]{display:none}
  .mesa{margin-top:14px}
  .memo{font-size:12px;line-height:1.55;max-width:80ch}
  .memo h2{font-size:13px;color:var(--texto);margin:14px 0 6px;letter-spacing:.04em}
  .memo h3{font-size:11px;color:var(--tenue);letter-spacing:.14em;text-transform:uppercase;margin:12px 0 4px}
  .memo p{margin:0 0 8px}
  .memo b{color:#eef6fa;font-weight:500}
  .memo ul,.memo ol{margin:0 0 8px;padding-left:18px}
  .memo li{margin:2px 0}
  .memo li::marker{color:var(--acento)}
  .memo code{color:var(--acento);font-size:11px}
  .memo table{border-collapse:collapse;margin:6px 0 10px;font-variant-numeric:tabular-nums}
  .memo th,.memo td{border-bottom:1px dotted #141c24;padding:3px 10px 3px 0;text-align:left;vertical-align:top}
  .memo th{color:var(--apagado);font-size:10px;letter-spacing:.1em;text-transform:uppercase}
  .memo pre{background:#080c10;border:1px solid var(--linea);padding:8px 10px;overflow-x:auto;font-size:11px}
  .memo .vacio{color:var(--apagado);font-style:italic}
  footer{margin-top:14px;padding-top:9px;border-top:1px solid var(--linea);
         display:flex;justify-content:space-between;color:var(--apagado);
         font-size:9.5px;letter-spacing:.1em;flex-wrap:wrap;gap:8px}
</style>
</head><body>
<div class="marco">

  <nav class="nav" id="nav">
    <a href="#panel" class="activa">Panel</a>
    <a href="../analisis/eth.html" id="nav-eth">ETH</a>
    <a href="#mesa">Mesa</a>
  </nav>
  <header id="panel">
    <div>
      <div class="logo">J A R V I S</div>
      <div class="sub">Inteligencia centralizada &middot; local</div>
    </div>
    <div class="reloj"><div class="h" id="reloj">--:--</div><div class="f" id="fecha"></div></div>
  </header>

  <div class="rejilla">

    <div>
      <div class="panel">
        <h2 class="titulo">Vitales del sistema</h2>
        <div id="vitales"></div>
      </div>
      <div class="panel">
        <h2 class="titulo">Directivas</h2>
        <ul class="dir" id="directivas"></ul>
      </div>
    </div>

    <div class="centro">
      <div class="escena">
        <canvas id="grafo"></canvas>
        <div class="sobre">
          <div class="gigante" id="metrica">0<small>/5</small></div>
          <div class="etiqueta" id="etiqueta">Miembros fundadores</div>
          <div class="cuenta" id="cuenta"></div>
        </div>
      </div>
      <div class="hitos" id="hitos"></div>
      <div class="panel">
        <h2 class="titulo">Prioridades de hoy</h2>
        <div id="prioridades"></div>
      </div>
    </div>

    <div>
      <div class="panel">
        <h2 class="titulo">Panel de comandos</h2>
        <div id="comandos"></div>
      </div>
      <div class="panel">
        <h2 class="titulo">Salidas recientes</h2>
        <div id="recientes"></div>
      </div>
    </div>

  </div>

  <section class="panel mesa" id="mesa">
    <h2 class="titulo">Mesa de expertos &middot; <span id="mesa-fecha"></span></h2>
    <div id="mesa-cuerpo" class="memo"></div>
  </section>

  <footer>
    <span id="generado"></span>
    <span>Sin red &middot; sin API &middot; los datos no salen de esta maquina</span>
  </footer>
</div>

<script>
const D = __DATOS__;
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

/* ---- reloj ---- */
function tic(){
  const n = new Date();
  document.getElementById('reloj').textContent =
    String(n.getHours()).padStart(2,'0')+':'+String(n.getMinutes()).padStart(2,'0');
}
tic(); setInterval(tic, 10000);
/* pantalla viva: recarga el archivo cada 10 min para tomar la ultima regeneracion */
setInterval(() => location.reload(), 10 * 60 * 1000);
document.getElementById('fecha').textContent = D.fecha_larga;
document.getElementById('generado').textContent = 'Generado ' + D.generado
  + (D.fecha_metricas ? ' · clientes según métricas del ' + D.fecha_metricas : '');
/* si el cron dejó de correr, que se note: un HUD de hace días parece actual */
const edadHoras = (Date.now() - new Date(D.generado.replace(' ', 'T'))) / 36e5;
if (edadHoras > 26){
  document.getElementById('generado').innerHTML =
    '<span style="color:var(--ambar)">HUD desactualizado: generado hace ' + Math.round(edadHoras)
    + ' h. Corre python3 hud/generar.py</span>';
}

/* ---- vitales ---- */
const V = D.vitales;
const filas = [
  [V.notas_wiki,      'notas en la wiki'],
  [V.enlaces,         'enlaces del grafo'],
  [V.capturas,        'capturas crudas'],
  [V.outputs,         'salidas entregadas'],
  [V.capturas_semana, 'capturas esta semana'],
  [V.parking,         'ideas en el parking lot'],
];
document.getElementById('vitales').innerHTML = filas.map(
  ([n,e]) => `<div class="vital"><span class="n">${n}</span><span class="e">${e}</span></div>`
).join('');

/* ---- hitos ---- */
document.getElementById('hitos').innerHTML = D.hitos.map(h => {
  const cls = h.vencido ? 'vencido' : (h.dias <= 7 ? 'urgente' : '');
  const prog = (h.meta && h.meta > 0) ? Math.min(100, (h.actual/h.meta)*100) : 0;
  const txt = h.vencido ? `${Math.abs(h.dias)} <span>DIAS TARDE</span>`
                        : `${h.dias} <span>DIAS</span>`;
  const barra = h.meta ? `<div class="barra"><i style="width:${prog}%"></i></div>` : '';
  return `<div class="hito ${cls}">
    <div class="nom">${esc(h.nombre)}</div>
    <div class="dias">${txt}</div>
    ${barra}</div>`;
}).join('');

/* ---- metrica central ---- */
const meta = D.hitos.find(h => h.meta && !h.vencido) || D.hitos.find(h => h.meta);
if (meta){
  document.getElementById('metrica').innerHTML = `${meta.actual}<small>/${meta.meta}</small>`;
  document.getElementById('etiqueta').textContent = meta.nombre;
  document.getElementById('cuenta').textContent =
    meta.vencido ? `vencido hace ${Math.abs(meta.dias)} dias`
                 : `faltan ${meta.dias} dias`;
}

/* ---- prioridades ---- */
const P = document.getElementById('prioridades');
if (D.prioridades.length){
  P.innerHTML = '<ol class="prio">' + D.prioridades.map(p=>`<li>${esc(p)}</li>`).join('') + '</ol>'
    + (D.total_prioridades > 3 ? `<div class="aviso">El plan tiene ${D.total_prioridades} prioridades; la skill pide tres.</div>` : '')
    + (D.plan_viejo ? `<div class="aviso">El plan mas reciente es del ${esc(D.fecha_plan)}. Corre "plan de hoy".</div>` : '');
} else if (D.fecha_plan){
  P.innerHTML = `<div class="vacio">Plan del ${esc(D.fecha_plan)} sin prioridades numeradas (## 1., ## 2. ...).</div>`;
} else {
  P.innerHTML = '<div class="vacio">Sin plan todavia. Di "plan de hoy" en Claude Code.</div>';
}

/* ---- comandos y directivas ---- */
document.getElementById('comandos').innerHTML = D.comandos.map(
  c => `<div class="cmd"><b>${c.skill}</b><i>"${c.frase}"</i></div>`).join('');
document.getElementById('directivas').innerHTML = D.directivas.map(
  d => `<li>${d}</li>`).join('');

/* ---- mesa de expertos ---- */
if (!D.eth) document.getElementById('nav-eth').hidden = true;
if (D.mesa){
  document.getElementById('mesa-fecha').textContent = D.mesa.fecha;
  document.getElementById('mesa-cuerpo').innerHTML = D.mesa.html;   // HTML generado por md_a_html, ya escapado
} else {
  document.getElementById('mesa-fecha').textContent = 'sin memo';
  document.getElementById('mesa-cuerpo').innerHTML = '<div class="vacio">Todavia no hay memos. Di "convoca la mesa: ..." en Claude Code.</div>';
}

/* ---- salidas recientes ---- */
const R = document.getElementById('recientes');
R.innerHTML = D.recientes.length
  ? D.recientes.map(r=>`<div class="rec"><b>${esc(r.tipo)}</b><i>${esc(r.fecha)}</i></div>`).join('')
  : '<div class="vacio">Nada todavia.</div>';

/* ---- grafo animado: esfera de nodos, densidad proporcional a la boveda ---- */
(function(){
  const c = document.getElementById('grafo'), x = c.getContext('2d');
  let W, H, R, nodos = [], t = 0;
  // La esfera crece con la boveda: mas notas y capturas -> mas nodos.
  const N = Math.max(120, Math.min(340, (V.notas_wiki + V.outputs) * 14 + V.capturas * 5 + 120));

  function medir(){
    const r = c.getBoundingClientRect(), d = window.devicePixelRatio || 1;
    W = r.width; H = r.height; R = Math.min(W, H) * 0.42;
    c.width = W * d; c.height = H * d;
    x.setTransform(d, 0, 0, d, 0, 0);
  }
  function sembrar(){
    nodos = [];
    for (let i = 0; i < N; i++){
      // distribucion uniforme sobre la esfera (espiral de Fibonacci)
      const k = i + .5;
      const phi = Math.acos(1 - 2 * k / N);
      const theta = Math.PI * (1 + Math.sqrt(5)) * k;
      nodos.push({
        x: Math.sin(phi) * Math.cos(theta),
        y: Math.sin(phi) * Math.sin(theta),
        z: Math.cos(phi),
        r: .82 + Math.random() * .18,       // grosor de la corteza
        pulso: Math.random() * Math.PI * 2
      });
    }
  }
  function pintar(){
    t += 1;
    const a = t * .0022, cy = Math.cos(a), sy = Math.sin(a);
    const inc = .38, ci = Math.cos(inc), si = Math.sin(inc);
    x.clearRect(0, 0, W, H);

    const pts = nodos.map(n => {
      // rotacion en Y, luego inclinacion en X
      const rx =  n.x * cy + n.z * sy;
      const rz = -n.x * sy + n.z * cy;
      const ry =  n.y * ci - rz * si;
      const rz2 = n.y * si + rz * ci;
      const persp = 1 / (1.9 - rz2 * .55);       // los del frente, mas grandes
      const rad = R * n.r;
      return {
        x: W / 2 + rx * rad * persp * 1.05,
        y: H / 2 + ry * rad * persp * 1.05,
        p: persp,
        f: (rz2 + 1) / 2                          // 0 atras, 1 adelante
      };
    });

    // aristas entre vecinos cercanos = el grafo de wikilinks
    x.lineWidth = .5;
    for (let i = 0; i < pts.length; i++){
      for (let j = i + 1; j < pts.length; j++){
        const dx = pts[i].x - pts[j].x, dy = pts[i].y - pts[j].y;
        const d2 = dx * dx + dy * dy;
        if (d2 < 1900){
          const op = (1 - d2 / 1900) * .17 * ((pts[i].f + pts[j].f) / 2 + .25);
          x.strokeStyle = `rgba(78,201,176,${op})`;
          x.beginPath(); x.moveTo(pts[i].x, pts[i].y); x.lineTo(pts[j].x, pts[j].y); x.stroke();
        }
      }
    }
    pts.forEach((p, i) => {
      const brillo = (.22 + Math.abs(Math.sin(t * .011 + nodos[i].pulso)) * .34) * (.3 + p.f * .9);
      x.fillStyle = `rgba(158,232,212,${Math.min(.92, brillo)})`;
      x.beginPath(); x.arc(p.x, p.y, .75 + p.p * 1.15, 0, 6.284); x.fill();
    });
    requestAnimationFrame(pintar);
  }
  medir(); sembrar(); pintar();
  window.addEventListener('resize', () => { medir(); sembrar(); });
})();
</script>
</body></html>
"""


def main():
    datos = construir_datos()
    # \u003c etc. siguen siendo JSON válido, pero el navegador ya no ve un </script>
    # ni HTML dentro de los datos, vengan de donde vengan en la bóveda.
    j = json.dumps(datos, ensure_ascii=False)
    for c, e in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026"),
                 ("\u2028", "\\u2028"), ("\u2029", "\\u2029")):
        j = j.replace(c, e)
    html = PLANTILLA.replace("__DATOS__", j)
    destino = RAIZ / "hud" / "hud.html"
    destino.write_text(html, encoding="utf-8")
    v = datos["vitales"]
    print(f"HUD generado: {destino}")
    print(f"  {v['notas_wiki']} notas · {v['enlaces']} enlaces · "
          f"{v['capturas']} capturas · {v['outputs']} salidas")
    for h in datos["hitos"]:
        estado = f"{abs(h['dias'])} días tarde" if h["vencido"] else f"faltan {h['dias']} días"
        cuenta = f" · {h['actual']}/{h['meta']}" if h["meta"] else ""
        print(f"  {h['nombre']}: {estado}{cuenta}")
    if datos["fecha_metricas"]:
        print(f"  clientes pagando según métricas del {datos['fecha_metricas']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
