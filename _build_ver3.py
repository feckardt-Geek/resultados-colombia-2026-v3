#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera Resultados..._ver3.html: filtro multi-select de departamentos/ciudades + Selección combinada."""
import os
BASE = os.path.dirname(os.path.abspath(__file__))   # carpeta del proyecto (multiplataforma)
SRC = os.path.join(BASE, "Resultados_Elecciones_Colombia_2026.html")
OUT = os.path.join(BASE, "Resultados_Elecciones_Colombia_2026_ver3.html")

CSS = """/* ---------- Filtro geográfico multi-select (ver3) ---------- */
.geo__bar{display:flex;flex-direction:column;gap:14px;}
.geo__row{display:flex;gap:14px;align-items:flex-start;flex-wrap:wrap;}
.geo__legend{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--clay-osc);font-weight:700;min-width:104px;padding-top:6px;}
.geo__chips{display:flex;flex-wrap:wrap;gap:7px;max-height:132px;overflow:auto;flex:1;min-width:240px;}
.geo__chip{font-size:12.5px;border:1px solid var(--linea);background:#fff;color:var(--tinta);border-radius:999px;padding:5px 11px;cursor:pointer;transition:.15s;line-height:1;font-weight:600;}
.geo__chip:hover{border-color:var(--clay-claro);}
.geo__chip.is-on{background:var(--clay);border-color:var(--clay);color:#fff;}
.geo__act{display:flex;gap:6px;align-items:center;}
.geo__btn{font-size:11.5px;border:1px solid var(--linea);background:var(--marfil);border-radius:8px;padding:6px 10px;cursor:pointer;color:var(--clay-osc);font-weight:700;}
.geo__btn:hover{border-color:var(--clay-claro);}
.geo__count{font-weight:600;}
.combo__grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
@media(max-width:720px){.combo__grid{grid-template-columns:1fr;}}
.combo__card{border:1px solid var(--linea);border-radius:14px;padding:16px 18px;background:#fff;}
.combo__card--u{grid-column:1/-1;border-color:var(--clay-claro);box-shadow:var(--sombra);}
.combo__h{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--clay-osc);font-weight:700;margin-bottom:10px;}
.combo__lead{display:flex;align-items:center;gap:10px;margin-bottom:6px;}
.combo__nom{font-family:'Fraunces',serif;font-size:21px;font-weight:600;line-height:1.1;}
.combo__pct{margin-left:auto;font-family:'Fraunces',serif;font-size:21px;font-weight:600;font-variant-numeric:tabular-nums;}
.combo__meta{font-size:12.5px;color:var(--tinta-suave);margin-bottom:12px;}
.combo__bars{display:flex;flex-direction:column;gap:9px;}
.combo__row{display:grid;grid-template-columns:1fr auto;gap:4px 10px;align-items:center;}
.combo__cn{font-size:12.5px;font-weight:600;}
.combo__cp{font-size:12.5px;font-weight:600;font-variant-numeric:tabular-nums;}
.combo__pista{grid-column:1/-1;height:7px;border-radius:999px;background:var(--linea);overflow:hidden;}
.combo__fill{height:100%;border-radius:999px;transition:width .5s ease;}

"""

HTML = """    <!-- ===== Filtro geográfico multi-select (ver3) ===== -->
    <section class="panel" id="panelGeoFiltro">
      <div class="panel__header">
        <h2>Filtro por territorio</h2>
        <span class="dept__sub">Selecciona 1 o varios departamentos y ciudades · <span id="geoCount" class="geo__count">sin filtro (todo el pa&iacute;s)</span></span>
      </div>
      <div class="geo__bar">
        <div class="geo__row">
          <span class="geo__legend">Departamentos</span>
          <div class="geo__chips" id="geoChipsDep"></div>
          <div class="geo__act">
            <button class="geo__btn" data-geo-all="dep">Todos</button>
            <button class="geo__btn" data-geo-clr="dep">Limpiar</button>
          </div>
        </div>
        <div class="geo__row">
          <span class="geo__legend">Ciudades</span>
          <div class="geo__chips" id="geoChipsCiu"></div>
          <div class="geo__act">
            <button class="geo__btn" data-geo-all="ciu">Todas</button>
            <button class="geo__btn" data-geo-clr="ciu">Limpiar</button>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== Selecci&oacute;n combinada (ver3) ===== -->
    <section class="panel" id="panelGeoCombo" style="display:none">
      <div class="panel__header">
        <h2>Selecci&oacute;n combinada</h2>
        <span class="dept__sub" id="comboSub"></span>
      </div>
      <div class="combo__grid" id="comboGrid"></div>
      <p class="vs__nota">Suma de los territorios elegidos. % sobre votos v&aacute;lidos (consistente con el tablero); participaci&oacute;n sobre censo; candidatos seg&uacute;n el top-3 reportado por territorio. Uni&oacute;n sin doble conteo: una ciudad dentro de un departamento ya seleccionado no se vuelve a sumar.</p>
    </section>

    """

JS = """  // ====== (ver3) Filtro geográfico multi-select + Selección combinada ======
  const _geoSel = { dep: new Set(), ciu: new Set() };
  let _geoWired = false;

  function montarChips(sel, items, set) {
    const cont = document.querySelector(sel);
    if (!cont || !items.length) return;
    if (cont.childElementCount === items.length) { // evita re-render en cada refresco
      [...cont.children].forEach((ch) => ch.classList.toggle("is-on", set.has(ch.dataset.name)));
      return;
    }
    const dim = sel === "#geoChipsDep" ? "dep" : "ciu";
    cont.innerHTML = items.map((it) => {
      const n = it.nombre, on = set.has(n) ? " is-on" : "";
      return '<button class="geo__chip' + on + '" data-geo="' + dim + '" data-name="' + n.replace(/"/g, "&quot;") + '">' + n + "</button>";
    }).join("");
  }

  function wireGeo() {
    const root = $("panelGeoFiltro");
    if (!root) return;
    root.addEventListener("click", (e) => {
      const chip = e.target.closest("[data-geo]");
      if (chip) {
        const set = chip.dataset.geo === "dep" ? _geoSel.dep : _geoSel.ciu;
        const n = chip.dataset.name;
        if (set.has(n)) set.delete(n); else set.add(n);
        chip.classList.toggle("is-on");
        aplicarFiltro(); return;
      }
      const all = e.target.closest("[data-geo-all]");
      if (all) {
        const k = all.dataset.geoAll;
        const items = k === "dep" ? ((_deptData && _deptData.departamentos) || []) : ((_ciuData && _ciuData.ciudades) || []);
        const set = k === "dep" ? _geoSel.dep : _geoSel.ciu;
        items.forEach((it) => set.add(it.nombre));
        cont_force(k); aplicarFiltro(); return;
      }
      const clr = e.target.closest("[data-geo-clr]");
      if (clr) {
        const k = clr.dataset.geoClr;
        (k === "dep" ? _geoSel.dep : _geoSel.ciu).clear();
        cont_force(k); aplicarFiltro();
      }
    });
  }
  function cont_force(k) { // fuerza re-pintado de chips de una dimensión
    const sel = k === "dep" ? "#geoChipsDep" : "#geoChipsCiu";
    const c = document.querySelector(sel); if (c) c.innerHTML = "";
    montarChips(sel, k === "dep" ? ((_deptData && _deptData.departamentos) || []) : ((_ciuData && _ciuData.ciudades) || []), k === "dep" ? _geoSel.dep : _geoSel.ciu);
  }

  function _postGeo() {
    montarChips("#geoChipsDep", (_deptData && _deptData.departamentos) || [], _geoSel.dep);
    montarChips("#geoChipsCiu", (_ciuData && _ciuData.ciudades) || [], _geoSel.ciu);
    if (!_geoWired) { wireGeo(); _geoWired = true; }
    aplicarFiltro();
  }

  function aplicarFiltro() {
    const selD = _geoSel.dep, selC = _geoSel.ciu;
    document.querySelectorAll("#deptBody tr").forEach((tr) => {
      const nom = (tr.querySelector(".dept__nom") ? tr.querySelector(".dept__nom").textContent : "").trim();
      tr.style.display = (selD.size === 0 || selD.has(nom)) ? "" : "none";
    });
    document.querySelectorAll("#ciuBody tr").forEach((tr) => {
      const nom = (tr.querySelector(".dept__nom") ? tr.querySelector(".dept__nom").textContent : "").trim();
      tr.style.display = (selC.size === 0 || selC.has(nom)) ? "" : "none";
    });
    const dS = $("deptSub"); if (dS && _deptData) dS.textContent = selD.size
      ? selD.size + " de " + (_deptData.departamentos || []).length + " departamentos (filtrado)"
      : (_deptData.departamentos || []).length + " departamentos · participación sobre censo local";
    const cS = $("ciuSub"); if (cS && _ciuData) cS.textContent = selC.size
      ? selC.size + " de " + (_ciuData.ciudades || []).length + " ciudades (filtrado)"
      : (_ciuData.ciudades || []).length + " ciudades · ordenadas por población";
    const gc = $("geoCount");
    if (gc) gc.textContent = (selD.size || selC.size) ? (selD.size + " depto(s) · " + selC.size + " ciudad(es)") : "sin filtro (todo el país)";
    renderCombo();
  }

  function _aggSet(geos) {
    let votantes = 0, censo = 0, validos = 0; const cand = {};
    geos.forEach((g) => {
      votantes += g.votantes || 0;
      if (g.participacion_pct) censo += (g.votantes || 0) / (g.participacion_pct / 100);
      if (g.primero && g.primero.pct) validos += (g.primero.votos || 0) / (g.primero.pct / 100);
      [g.primero, g.segundo, g.paloma].forEach((s) => {
        if (!s || s.codpar == null) return;
        if (!cand[s.codpar]) cand[s.codpar] = { nombre: s.nombre, color: s.color, votos: 0 };
        cand[s.codpar].votos += s.votos || 0;
      });
    });
    return { votantes, censo, validos, lista: Object.values(cand).sort((a, b) => b.votos - a.votos) };
  }
  function _comboCard(titulo, geos, extra) {
    if (!geos.length) return "";
    const a = _aggSet(geos);
    const lead = a.lista[0] || { nombre: "—", color: "#CFC9BA", votos: 0 };
    const den = a.validos || a.votantes || 1;
    const leadPct = (lead.votos / den) * 100;
    const part = a.censo ? (a.votantes / a.censo) * 100 : 0;
    const top = a.lista.slice(0, 4), maxv = Math.max.apply(null, top.map((c) => c.votos).concat([1]));
    const bars = top.map((c) => {
      const p = (c.votos / den) * 100;
      return '<div class="combo__row"><span class="combo__cn"><span class="dept__dot" style="background:' + c.color + ';display:inline-block;margin-right:5px"></span>' + c.nombre + '</span>' +
        '<span class="combo__cp">' + pct(p) + '</span>' +
        '<span class="combo__pista"><span class="combo__fill" style="width:' + ((c.votos / maxv) * 100) + '%;background:' + c.color + '"></span></span></div>';
    }).join("");
    return '<div class="combo__card' + (extra || "") + '"><div class="combo__h">' + titulo + '</div>' +
      '<div class="combo__lead"><span class="dept__dot" style="background:' + lead.color + '"></span>' +
      '<span class="combo__nom">' + lead.nombre + '</span><span class="combo__pct">' + pct(leadPct) + '</span></div>' +
      '<div class="combo__meta">' + fmt.format(a.votantes) + ' votantes · participación ' + pct(part) + '</div>' +
      '<div class="combo__bars">' + bars + '</div></div>';
  }
  function renderCombo() {
    const panel = $("panelGeoCombo"), grid = $("comboGrid");
    if (!panel || !grid) return;
    const selD = _geoSel.dep, selC = _geoSel.ciu;
    if (!selD.size && !selC.size) { panel.style.display = "none"; return; }
    const depObjs = ((_deptData && _deptData.departamentos) || []).filter((d) => selD.has(d.nombre));
    const depCodes = new Set(depObjs.map((d) => d.codigo));
    const ciuObjs = ((_ciuData && _ciuData.ciudades) || []).filter((c) => selC.has(c.nombre));
    const ciuNoDup = ciuObjs.filter((c) => !depCodes.has(String(c.codigo).slice(0, 2)));
    let cards = "";
    if (depObjs.length) cards += _comboCard(depObjs.length + " departamento(s) seleccionado(s)", depObjs);
    if (ciuObjs.length) cards += _comboCard(ciuObjs.length + " ciudad(es) seleccionada(s)", ciuObjs);
    if (depObjs.length && ciuObjs.length) cards += _comboCard("Unión del ámbito (sin doble conteo)", depObjs.concat(ciuNoDup), " combo__card--u");
    grid.innerHTML = cards;
    const dup = ciuObjs.length - ciuNoDup.length;
    const cs = $("comboSub");
    if (cs) cs.textContent = depObjs.length + " depto(s) + " + ciuObjs.length + " ciudad(es)" + (dup > 0 ? " · " + dup + " ciudad(es) ya dentro de un depto seleccionado" : "");
    panel.style.display = "";
  }

"""

def repl(h, old, new):
    assert h.count(old) == 1, "ANCLA x%d: %r" % (h.count(old), old[:60])
    return h.replace(old, new, 1)

def build_ver3():
    html = open(SRC, encoding="utf-8").read()
    html = repl(html, "/* ---------- Histórico multi-select ---------- */",
                CSS + "/* ---------- Histórico multi-select ---------- */")
    html = repl(html, "    <!-- Participación y líder por departamento -->",
                HTML + "<!-- Participación y líder por departamento -->")
    html = repl(html, "      pintarDepartamentos(data);\n      pintarConteo(data);",
                "      pintarDepartamentos(data);\n      _postGeo();\n      pintarConteo(data);")
    html = repl(html, "      pintarCiudades(d);\n      pintarPaloma();",
                "      pintarCiudades(d);\n      _postGeo();\n      pintarPaloma();")
    html = repl(html, "  function iniciarControles() {",
                JS + "  function iniciarControles() {")
    open(OUT, "w", encoding="utf-8").write(html)
    return OUT

if __name__ == "__main__":
    out = build_ver3()
    print("OK ver3 escrito:", out)
    print("tamaño:", os.path.getsize(out), "bytes")
