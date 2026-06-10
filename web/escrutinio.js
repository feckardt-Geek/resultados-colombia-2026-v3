/* Panel "Escrutinio oficial vs. Preconteo" — Colombia 2026, 1.ª vuelta.
   - Preconteo: se toma del feed en vivo (local) o del snapshot incrustado (público).
   - Escrutinio: cifras OFICIALES de la Registraduría (escrutinio del 31 may 2026).
     La Registraduría reportó 99,94% de coincidencia con el preconteo; las
     diferencias por candidato son mínimas y NO se publican desagregadas por
     departamento como dato abierto. */
(function () {
  "use strict";

  // Cifras oficiales del ESCRUTINIO (totales nacionales). Fuente: Registraduría.
  var ESC = [
    { rx: /espriella/i, nombre: "Abelardo de la Espriella", votos: 10361413, pct: 43.74 },
    { rx: /cepeda/i,    nombre: "Iván Cepeda",              votos: 9688245,  pct: 40.90 },
    { rx: /valencia/i,  nombre: "Paloma Valencia",          votos: 1639668,  pct: 6.92 }
  ];

  var fmt = new Intl.NumberFormat("es-CO");
  function pctTxt(n) { return (n == null ? 0 : n).toFixed(2).replace(".", ",") + " %"; }
  function deltaVotos(n) { return (n > 0 ? "+" : (n < 0 ? "−" : "")) + fmt.format(Math.abs(n)); }
  function deltaPp(n) {
    var s = Math.abs(n).toFixed(2).replace(".", ",");
    return (n > 0 ? "+" : (n < 0 ? "−" : "")) + s + " pp";
  }

  function getPreconteo() {
    // Público: datos incrustados por build_html.py
    if (window.__SNAP__ && window.__SNAP__.resultados) {
      return Promise.resolve(window.__SNAP__.resultados);
    }
    // Local: feed en vivo
    return fetch("/api/resultados")
      .then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; });
  }

  function render(pre) {
    var panel = document.getElementById("panelEscrutinio");
    if (!panel) return;
    var cands = (pre && pre.candidatos) || [];
    function findPre(rx) {
      for (var i = 0; i < cands.length; i++) {
        if (rx.test(cands[i].nombre || "")) return cands[i];
      }
      return null;
    }

    var filas = ESC.map(function (e) {
      var p = findPre(e.rx) || { votos: 0, porcentaje: 0 };
      var pPct = (p.porcentaje != null ? p.porcentaje : p.pct) || 0;  // preconteo usa 'porcentaje'
      var dv = (e.votos || 0) - (p.votos || 0);
      var dp = (e.pct || 0) - pPct;
      var cls = dv === 0 ? "" : (dv > 0 ? " esc__delta--up" : " esc__delta--down");
      return '<tr>' +
        '<td class="esc__nom">' + e.nombre + '</td>' +
        '<td class="num">' + fmt.format(p.votos || 0) +
          '<span class="esc__pct">' + pctTxt(pPct) + '</span></td>' +
        '<td class="num">' + fmt.format(e.votos) +
          '<span class="esc__pct">' + pctTxt(e.pct) + '</span></td>' +
        '<td class="num esc__delta' + cls + '">' + deltaVotos(dv) +
          '<span class="esc__pct">' + deltaPp(dp) + '</span></td>' +
        '</tr>';
    }).join("");

    var body = panel.querySelector("[data-esc=body]");
    if (body) body.innerHTML = filas;
    panel.style.display = "";
  }

  function init() { getPreconteo().then(render); }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
