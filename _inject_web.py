#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inyecta el filtro multi-select (deptos/ciudades) + panel combinado en la FUENTE web/.
Reutiliza los bloques CSS/HTML/JS ya validados de _build_ver3.py. CSS->styles.css, HTML->index.html, JS->app.js."""
import sys, os
ED = "/Users/federicoeckardtv./Library/CloudStorage/OneDrive-Personal/CLAUDE COWORK/elecciones-colombia-2026"
sys.path.insert(0, ED)
import _build_ver3 as b
W = ED + "/web"

def inject(path, old, new, label):
    h = open(path, encoding="utf-8").read()
    n = h.count(old)
    assert n == 1, "[%s] ancla x%d: %r" % (label, n, old[:50])
    open(path, "w", encoding="utf-8").write(h.replace(old, new, 1))
    print("  OK %-14s -> %s" % (label, os.path.basename(path)))

# 1) CSS -> styles.css
inject(W + "/styles.css", "/* ---------- Histórico multi-select ---------- */",
       b.CSS + "/* ---------- Histórico multi-select ---------- */", "CSS")
# 2) Paneles HTML -> index.html
inject(W + "/index.html", "    <!-- Participación y líder por departamento -->",
       b.HTML + "<!-- Participación y líder por departamento -->", "HTML paneles")
# 3) hook cargarDepartamentos -> app.js
inject(W + "/app.js", "      pintarDepartamentos(data);\n      pintarConteo(data);",
       "      pintarDepartamentos(data);\n      _postGeo();\n      pintarConteo(data);", "hook deptos")
# 4) hook cargarCiudades -> app.js
inject(W + "/app.js", "      pintarCiudades(d);\n      pintarPaloma();",
       "      pintarCiudades(d);\n      _postGeo();\n      pintarPaloma();", "hook ciudades")
# 5) módulo JS -> app.js
inject(W + "/app.js", "  function iniciarControles() {",
       b.JS + "  function iniciarControles() {", "módulo JS")
print("web/ inyectado OK (styles.css + index.html + app.js)")
