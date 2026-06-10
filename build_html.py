#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera un HTML AUTONOMO y compartible con los resultados (datos incrustados).

- Funciona sin servidor: abrelo con doble clic en cualquier navegador.
- Se puede enviar por correo/WhatsApp como un solo archivo.
- Para ACTUALIZARLO (incluida la 2.a vuelta del 21 de junio):
      python3 build_html.py
  vuelve a consultar el feed oficial de la Registraduria y reescribe el archivo.
"""
import json
import os
import time
from pathlib import Path

import server  # reutiliza las funciones de datos del dashboard

BASE = Path(__file__).resolve().parent
WEB = BASE / "web"
OUT = BASE / "Resultados_Elecciones_Colombia_2026.html"


def _safe(obj):
    """JSON seguro para incrustar dentro de <script> (evita romper con </script>)."""
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


print("Consultando datos oficiales de la Registraduria...")
snap = {
    "resultados": server.obtener_resultados(),
    "departamentos": server.obtener_departamentos(),
    "ciudades": server.obtener_ciudades(),
    "exterior": server.obtener_exterior(),
    "polymarket": server.obtener_polymarket(),
}
try:
    serie = json.loads(server.SERIE_FILE.read_text("utf-8")) if server.SERIE_FILE.exists() else []
except Exception:
    serie = []
snap["serie"] = {"serie": serie}

try:
    geo = json.loads((WEB / "colombia.geojson").read_text("utf-8"))
except Exception:
    geo = {"type": "FeatureCollection", "features": []}

try:
    hist2022 = json.loads((WEB / "historico_2022_departamentos.json").read_text("utf-8"))
except Exception:
    hist2022 = {"r1": {}, "r2": {}}

print("Consultando municipios de cada departamento (drill-down; puede tardar 1-2 min)...")
munis = {}
try:
    for _nom, _code in server._lista_departamentos():
        if not _code:
            continue
        munis[_code] = server.obtener_municipios(_code)
    print(f"  municipios embebidos para {len(munis)} departamentos.")
except Exception as e:
    print("  (aviso: no se pudieron consultar todos los municipios:", e, ")")

html = (WEB / "index.html").read_text("utf-8")
css = (WEB / "styles.css").read_text("utf-8")
appjs = (WEB / "app.js").read_text("utf-8")
asis_css = (WEB / "asistente.css").read_text("utf-8")
asis_js = (WEB / "asistente.js").read_text("utf-8")
escr_js = (WEB / "escrutinio.js").read_text("utf-8")

# URL del proxy de IA (Cloudflare Worker) para el chat en la version publica.
# Pasala al construir:  IA_PROXY_URL="https://<algo>.workers.dev" python build_html.py
IA_PROXY = os.environ.get("IA_PROXY_URL", "").strip()

# 1) CSS en linea (tablero + asistente)
html = html.replace('<link rel="stylesheet" href="/styles.css" />', f"<style>\n{css}\n</style>")
html = html.replace('<link rel="stylesheet" href="/asistente.css" />', f"<style>\n{asis_css}\n</style>")

# 2) app.js: redirige fetch() a una version que usa los datos incrustados
appjs = appjs.replace("fetch(", "fetchSnap(")

shim = (
    "window.__SNAP__ = " + _safe(snap) + ";\n"
    "window.__GEO__ = " + _safe(geo) + ";\n"
    "window.__HIST2022__ = " + _safe(hist2022) + ";\n"
    "window.__MUNIS__ = " + _safe(munis) + ";\n"
    "(function(){\n"
    "  var map={'/api/resultados':'resultados','/api/departamentos':'departamentos',"
    "'/api/ciudades':'ciudades','/api/exterior':'exterior','/api/polymarket':'polymarket','/api/serie':'serie'};\n"
    "  var orig = window.fetch ? window.fetch.bind(window) : null;\n"
    "  window.fetchSnap = async function(path, opts){\n"
    "    if (orig){ try{ var r=await orig(path,opts); if(r && r.ok) return r; }catch(e){} }\n"
    "    if (path === '/colombia.geojson') return {ok:true, json:async function(){return window.__GEO__;}};\n"
    "    if (path === '/historico_2022_departamentos.json') return {ok:true, json:async function(){return window.__HIST2022__;}};\n"
    "    if (path.indexOf('/api/municipios') === 0){ var dep=decodeURIComponent((path.split('dep=')[1]||'').split('&')[0]); var dd=window.__MUNIS__[dep]; return {ok:!!dd, json:async function(){return dd||{municipios:[]};}}; }\n"
    "    var k=map[path]; if(k!==undefined && window.__SNAP__[k]!==undefined) return {ok:true, json:async function(){return window.__SNAP__[k];}};\n"
    "    return {ok:false,status:404,json:async function(){return {};}};\n"
    "  };\n"
    "})();\n"
)

script_block = f"<script>{shim}</script>\n<script>\n{appjs}\n</script>"
html = html.replace('<script src="/app.js"></script>', script_block)

# 2b) Asistente IA: se inyecta TAL CUAL (su fetch apunta al proxy, no a datos
#     incrustados). window.IA_PROXY_URL define el Worker de Cloudflare.
# Escrutinio: usa el snapshot incrustado (window.__SNAP__); su fetch NO se reescribe.
html = html.replace('<script src="/escrutinio.js"></script>', f"<script>\n{escr_js}\n</script>")

asis_block = (f'<script>window.IA_PROXY_URL={json.dumps(IA_PROXY)};</script>\n'
              f"<script>\n{asis_js}\n</script>")
html = html.replace('<script src="/asistente.js"></script>', asis_block)
if not IA_PROXY:
    print("  AVISO: sin IA_PROXY_URL -> el chat de IA no funcionara en la version "
          "publica (si en la local). Define IA_PROXY_URL al construir para activarlo.")

# 3) Banner de "copia compartible"
corte = snap["resultados"].get("fecha_corte_txt", "")
bol = snap["resultados"].get("boletin", "")
banner = (
    '<div style="background:#1A1915;color:#F0EEE6;text-align:center;'
    'font-family:Inter,sans-serif;font-size:12.5px;padding:7px 12px;">'
    f'Copia compartible &middot; datos al corte {corte} (boletin {bol}). '
    'Resultados preliminares oficiales de la Registraduria Nacional.</div>'
)
html = html.replace('<body>', '<body>\n' + banner)

# comentario con instrucciones de actualizacion
html = (f'<!-- HTML autonomo generado {time.strftime("%Y-%m-%d %H:%M")} '
        f'(corte {corte}). Para actualizar: python3 build_html.py -->\n') + html

OUT.write_text(html, "utf-8")
kb = OUT.stat().st_size // 1024
print(f"HTML generado: {OUT}  ({kb} KB)")
print("Abrelo con doble clic; puedes enviarlo como un solo archivo.")
