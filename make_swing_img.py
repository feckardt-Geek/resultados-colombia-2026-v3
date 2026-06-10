#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera una imagen (mapa de swing 2022->2026) para compartir."""
import json, re, unicodedata
from fpdf import FPDF
import server

BASE = __file__.rsplit("/", 1)[0]
NAVY = (26, 25, 21); GRAY = (107, 101, 87); LINE = (214, 209, 196)
COLS = {  # buckets de giro
    "fd": (184, 92, 40),   "ld": (224, 163, 106),
    "sc": (201, 194, 178), "li": (185, 143, 192), "fi": (110, 42, 110),
}


def canon(s):
    n = re.sub(r"[^A-Z]", "", unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().upper())
    if "BOGOTA" in n: return "BOGOTA"
    if n.startswith("VALLE"): return "VALLE"
    if n.startswith("NORTEDESAN"): return "NORTEDESANTANDER"
    if "GUAJIRA" in n: return "LAGUAJIRA"
    if "SANANDRES" in n or "ARCHIPIE" in n: return "SANANDRES"
    return n


def color(sw):
    if sw is None: return (227, 223, 211)
    if sw > 6: return COLS["fd"]
    if sw > 1.5: return COLS["ld"]
    if sw >= -1.5: return COLS["sc"]
    if sw >= -6: return COLS["li"]
    return COLS["fi"]


# --- swing por departamento ---
hist = json.load(open(BASE + "/data/historico_2022_departamentos.json"))["r1"]
dep = server.obtener_departamentos()["departamentos"]
swing = {}
for d in dep:
    k = canon(d["nombre"]); h = hist.get(k)
    if not h: continue
    cep = next((x for x in (d["primero"], d["segundo"]) if "Cepeda" in x["nombre"]), {"pct": 0})["pct"]
    esp = next((x for x in (d["primero"], d["segundo"]) if "Espriella" in x["nombre"]), {"pct": 0})["pct"]
    swing[k] = round((esp + d["paloma"]["pct"] - cep) - ((h["rodolfo"]["p"] + h["fico"]["p"]) - h["petro"]["p"]), 1)

geo = json.load(open(BASE + "/web/colombia.geojson"))

# --- bbox ---
mnx = mny = 1e9; mxx = mxy = -1e9
def each(co, f):
    if isinstance(co[0], (int, float)): f(co)
    else:
        for c in co: each(c, f)
def upd(p):
    global mnx, mxx, mny, mxy
    mnx = min(mnx, p[0]); mxx = max(mxx, p[0]); mny = min(mny, p[1]); mxy = max(mxy, p[1])
for ft in geo["features"]:
    each(ft["geometry"]["coordinates"], upd)

# --- lienzo (pt) ---
W, H = 900, 1195
X0, Y0, X1, Y1 = 45, 175, 855, 1075          # área del mapa
sc = min((X1 - X0) / (mxx - mnx), (Y1 - Y0) / (mxy - mny))
ox = X0 + ((X1 - X0) - (mxx - mnx) * sc) / 2
oy = Y0 + ((Y1 - Y0) - (mxy - mny) * sc) / 2
def px(lon): return ox + (lon - mnx) * sc
def py(lat): return oy + (mxy - lat) * sc

pdf = FPDF(unit="pt", format=(W, H)); pdf.set_auto_page_break(False); pdf.add_page()
pdf.set_fill_color(250, 249, 245); pdf.rect(0, 0, W, H, "F")
# franja superior
pdf.set_fill_color(*NAVY); pdf.rect(0, 0, W, 6, "F")

# Título
pdf.set_text_color(*NAVY); pdf.set_font("Helvetica", "B", 30)
pdf.set_xy(45, 34); pdf.cell(0, 34, "¿Hacia donde se movio Colombia?")
pdf.set_text_color(*GRAY); pdf.set_font("Helvetica", "", 15)
pdf.set_xy(45, 78); pdf.cell(0, 20, "Giro politico por departamento  ·  2022  ->  2026 (1.a vuelta)")
pdf.set_draw_color(184, 92, 40); pdf.set_line_width(2); pdf.line(45, 108, 120, 108)

# --- dibujar departamentos ---
pdf.set_draw_color(250, 249, 245); pdf.set_line_width(0.6)
for ft in geo["features"]:
    sw = swing.get(canon(ft["properties"].get("dpt")))
    pdf.set_fill_color(*color(sw))
    g = ft["geometry"]; polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    for poly in polys:
        ring = poly[0]
        pts = [(px(p[0]), py(p[1])) for p in ring]
        if len(pts) >= 3:
            pdf.polygon(pts, style="DF")

# --- leyenda ---
ly = 1088
items = [("fd", "Giro fuerte a la derecha"), ("ld", "Leve a la derecha"),
         ("sc", "Sin cambio"), ("li", "Leve a la izquierda"), ("fi", "Fuerte a la izquierda")]
pdf.set_font("Helvetica", "", 10.5);
x = 45
for key, lab in items:
    pdf.set_fill_color(*COLS[key]); pdf.rect(x, ly, 13, 13, "F")
    pdf.set_text_color(*GRAY); pdf.set_xy(x + 17, ly - 1); w = pdf.get_string_width(lab) + 22
    pdf.cell(w, 15, lab)
    x += 17 + pdf.get_string_width(lab) + 16

# --- nota / dato clave ---
pdf.set_text_color(*NAVY); pdf.set_font("Helvetica", "B", 11)
pdf.set_xy(45, 1114)
pdf.cell(0, 14, "La derecha redujo su margen en casi todo el pais (morado): el voto personal de Rodolfo no se hereda...")
pdf.set_xy(45, 1130)
pdf.cell(0, 14, "...pero hoy va UNIFICADA tras De la Espriella y LIDERA la 1.a vuelta. El mapa de ganadores casi no cambio.")
pdf.set_text_color(*GRAY); pdf.set_font("Helvetica", "", 9.5)
pdf.set_xy(45, 1148)
pdf.cell(0, 12, "Se movieron a la derecha (naranja): Bogota +10,8, Atlantico +6.  Mas a la izquierda: Santander -20, Arauca -25.  ( + der / - izq )")
pdf.set_xy(45, 1163)
pdf.set_font("Helvetica", "", 8.5)
pdf.cell(0, 11, "Fuente: Registraduria Nacional (preconteo 2026, 100% mesas) + resultados oficiales 2022.  ·  Comparacion por bloques, 1.a vuelta.")

out = BASE + "/swing_colombia_2022_2026.pdf"
pdf.output(out)
print("PDF:", out)
