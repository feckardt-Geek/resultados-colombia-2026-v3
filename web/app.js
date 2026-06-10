/* Dashboard Elecciones Colombia 2026 — lógica de cliente */
(function () {
  "use strict";

  const REFRESCO_SEG = 60;        // auto-refresco cada 60 s
  let cuenta = REFRESCO_SEG;
  let timerCuenta = null;

  const $ = (id) => document.getElementById(id);

  const fmt = new Intl.NumberFormat("es-CO");
  const pct = (n) => (n ?? 0).toFixed(2).replace(".", ",") + " %";

  // Nombre corto reconocible (apellido principal), no la última palabra
  function nombreCorto(n) {
    n = n || "";
    if (/espriella/i.test(n)) return "De la Espriella";
    if (/cepeda/i.test(n)) return "Cepeda";
    if (/valencia/i.test(n)) return "Valencia";
    if (/fajardo/i.test(n)) return "Fajardo";
    return n.split(" ").slice(-1)[0];
  }

  // Celda de "1.º/2.º lugar": nombre con punto de color + (% · votos)
  const placeCell = (x) => {
    x = x || { nombre: "—", color: "#CFC9BA", pct: 0, votos: 0 };
    return `
      <div class="plc__name"><span class="dept__dot" style="background:${x.color}"></span><span>${x.nombre}</span></div>
      <div class="plc__sub"><span class="plc__pct">${pct(x.pct)}</span> · <strong class="plc__vot">${fmt.format(x.votos || 0)}</strong> votos</div>`;
  };

  // Celda de participación: participación + abstención + habilitados (censo)
  function partCell(o) {
    const ab = (o.abstencion_pct != null) ? o.abstencion_pct : (100 - (o.participacion_pct || 0));
    return '<div class="dept__part">' + pct(o.participacion_pct) + '</div>' +
      '<div class="part__ab">Abst. ' + pct(ab) + '</div>' +
      '<div class="part__hab">' + fmt.format(o.censo || 0) + ' hab.</div>';
  }
  // Celda compacta de Valencia (Paloma): % + votos
  const palCell = (p) => {
    p = p || { pct: 0, votos: 0 };
    return `<td class="num plc__pal"><div class="hrow__pct">${pct(p.pct)}</div>` +
      `<div class="hrow__vot">${fmt.format(p.votos || 0)}</div></td>`;
  };

  function relojAhora() {
    const d = new Date();
    return d.toLocaleTimeString("es-CO", { hour12: false });
  }

  function tickReloj() { $("reloj").textContent = relojAhora(); }

  function pintarAviso(data) {
    const aviso = $("aviso");
    const punto = $("avisoPunto");
    const esOficial = (data.fuente || "").startsWith("OFICIAL");
    punto.classList.toggle("punto--vivo", esOficial);
    const etiqueta = esOficial ? "DATOS OFICIALES" : data.fuente;
    const corte = data.fecha_corte_txt ? ` · Corte: ${data.fecha_corte_txt}` : "";
    $("avisoTexto").innerHTML =
      `<strong>${etiqueta}</strong> · ` +
      `Boletín / actualización N.° ${data.boletin}${corte} · ` +
      `Fuente: <a href="${data.fuente_url}" target="_blank" rel="noopener" ` +
      `style="color:var(--clay-osc)">Registraduría Nacional</a>`;
    $("pieNota").textContent = data.fuente_nota || "";
  }

  function pintarMetricas(data) {
    $("boletinNum").textContent = data.boletin;

    $("mMesasPct").textContent = pct(data.porcentaje_mesas);
    $("mMesasDet").textContent =
      `${fmt.format(data.mesas_informadas)} de ${fmt.format(data.mesas_total)} mesas`;
    $("barraMesas").style.width = Math.min(100, data.porcentaje_mesas) + "%";

    $("mVotos").textContent = fmt.format(data.votos_totales);
    $("mVotosDet").textContent = pct(data.participacion_pct) + " de participación";

    const lider = data.candidatos[0];
    if (lider) {
      $("mLider").textContent = lider.nombre;
      $("mLiderPct").textContent = pct(lider.porcentaje) + " · " + lider.partido;
    }
  }

  function pintarVs(data) {
    const panel = $("panelVs");
    const c = data.comparativo;
    if (!c) { panel.style.display = "none"; return; }
    panel.style.display = "";

    const ce = c.cepeda.pct || 0;
    const de = c.suma.pct || 0;
    const total = ce + de || 100;
    $("vsCe").style.width = (ce / total) * 100 + "%";
    $("vsDe").style.width = (de / total) * 100 + "%";
    $("vsCeIn").textContent = ce >= 8 ? pct(ce) : "";
    $("vsDeIn").textContent = de >= 8 ? pct(de) : "";

    $("vsCePct").textContent = pct(ce);
    $("vsDePct").textContent = pct(de);
    $("vsCeN").textContent = fmt.format(c.cepeda.votos || 0) + " votos";
    $("vsBreak").textContent =
      "De la Espriella " + pct(c.abelardo.pct) + " + Valencia " + pct(c.paloma.pct);

    const gap = Math.round(Math.abs(de - ce) * 100) / 100;
    $("vsGap").textContent = "vs";
    const ganaBloque = de > ce;
    $("vsNota").textContent = ganaBloque
      ? "Si el bloque de derecha (De la Espriella + Valencia) sumara sus votos, " +
        "superaría a Cepeda por " + pct(gap) + ". Es una suma hipotética: no implica " +
        "que esos votos se transfieran en una eventual segunda vuelta."
      : "Cepeda supera por " + pct(gap) + " a la suma de De la Espriella + Valencia. " +
        "Suma hipotética; no implica transferencia de votos en segunda vuelta.";
  }

  function pintarParticipacion(data) {
    const part = data.participacion_pct ?? 0;
    const abs = data.abstencion_pct ?? Math.max(0, 100 - part);
    $("pCenso").textContent = fmt.format(data.censo);

    // La barra se normaliza a (participación + abstención) para que sume 100%.
    const total = part + abs || 100;
    $("segPart").style.width = (part / total) * 100 + "%";
    $("segAbs").style.width = (abs / total) * 100 + "%";

    $("pPartPct").textContent = pct(part);
    $("pAbsPct").textContent = pct(abs);
    $("pPartN").textContent = "(" + fmt.format(data.votos_totales) + " votantes)";
    if (data.abstencion != null)
      $("pAbsN").textContent = "(" + fmt.format(data.abstencion) + ")";

    const esOficial = (data.fuente || "").startsWith("OFICIAL");
    $("pNota").textContent = esOficial
      ? "Cifra provisional calculada sobre el censo electoral con las mesas " +
        "escrutadas hasta ahora (" + pct(data.porcentaje_mesas) + " de mesas). " +
        "La participación sube y la abstención baja a medida que avanza el conteo; " +
        "el dato definitivo se conoce al 100% de mesas."
      : "Participación y abstención simuladas (no oficiales).";

    // Desglose de votos
    const g = data.desglose || {};
    $("dValPct").textContent = pct(g.validos_pct); $("dValN").textContent = fmt.format(g.validos || 0);
    $("dBlaPct").textContent = pct(g.blanco_pct);  $("dBlaN").textContent = fmt.format(g.blanco || 0);
    $("dNulPct").textContent = pct(g.nulos_pct);   $("dNulN").textContent = fmt.format(g.nulos || 0);
    $("dNmaPct").textContent = pct(g.no_marcados_pct); $("dNmaN").textContent = fmt.format(g.no_marcados || 0);
  }

  function pintarDepartamentos(data) {
    const panel = $("panelDept");
    const deptos = data.departamentos || [];
    if (!deptos.length) { panel.style.display = "none"; return; }
    panel.style.display = "";

    $("deptSub").textContent =
      deptos.length + " departamentos · participación sobre censo local";

    const body = $("deptBody");
    body.innerHTML = "";
    deptos.forEach((d) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="dept__nom">${d.nombre}</td>
        <td class="plc">${placeCell(d.primero)}</td>
        <td class="plc">${placeCell(d.segundo)}</td>
        <td class="plc">${placeCell(d.paloma)}</td>
        <td class="num">${partCell(d)}</td>
        <td class="num">${pct(d.mesas_pct)}</td>`;
      body.appendChild(tr);
    });
  }

  function pintarConteo(data) {
    const panel = $("panelConteo");
    const conteo = data.conteo || [];
    if (!conteo.length) { panel.style.display = "none"; return; }
    panel.style.display = "";

    const totalDeptos = (data.departamentos || []).length;
    const max = Math.max(...conteo.map((c) => c.ganados), 1);
    $("conteoSub").textContent =
      "de " + totalDeptos + " departamentos escrutados hasta ahora";

    const body = $("conteoBody");
    body.innerHTML = "";
    conteo.forEach((c, i) => {
      const row = document.createElement("div");
      row.className = "cnt";
      row.innerHTML = `
        <div class="cnt__pos">${i + 1}</div>
        <div class="cnt__body">
          <div class="cnt__top">
            <span class="cnt__dot" style="background:${c.color}"></span>
            <span class="cnt__nom">${c.nombre}</span>
          </div>
          <div class="cnt__pista">
            <div class="cnt__barra" style="background:${c.color}"></div>
          </div>
        </div>
        <div class="cnt__num">
          <div class="cnt__g">${c.ganados}</div>
          <div class="cnt__lbl">deptos.</div>
        </div>`;
      body.appendChild(row);
      requestAnimationFrame(() => {
        row.querySelector(".cnt__barra").style.width = (c.ganados / max) * 100 + "%";
      });
    });
  }

  async function cargarDepartamentos() {
    try {
      const r = await fetch("/api/departamentos", { cache: "no-store" });
      if (!r.ok) return;
      const data = await r.json();
      _deptData = data;
      pintarDepartamentos(data);
      _postGeo();
      pintarConteo(data);
      pintarMapa(data);
      pintarPaloma();
      pintarSwing();
      pintarExplorar();
    } catch (e) { /* silencioso */ }
  }

  function pintarCandidatos(data) {
    const cont = $("candidatos");
    const max = Math.max(...data.candidatos.map((c) => c.porcentaje), 1);
    cont.innerHTML = "";

    data.candidatos.forEach((c, i) => {
      const lider = i === 0;
      const fila = document.createElement("div");
      fila.className = "cand" + (lider ? " cand--lider" : "");
      fila.innerHTML = `
        <div class="cand__pos">${i + 1}</div>
        <div class="cand__cuerpo">
          <div class="cand__fila">
            <span class="cand__nombre">${c.nombre}</span>
            <span class="cand__partido">${c.partido}</span>
          </div>
          <div class="cand__pista">
            <div class="cand__barra" style="background:${c.color}"></div>
          </div>
        </div>
        <div class="cand__cifras">
          <div class="cand__pct">${pct(c.porcentaje)}</div>
          <div class="cand__votos">${fmt.format(c.votos)} votos</div>
        </div>`;
      cont.appendChild(fila);
      // animación de barra (ancho relativo al líder)
      requestAnimationFrame(() => {
        fila.querySelector(".cand__barra").style.width =
          (c.porcentaje / max) * 100 + "%";
      });
    });
  }

  function pintarCiudades(data) {
    const panel = $("panelCiudades");
    const c = data.ciudades || [];
    if (!c.length) { panel.style.display = "none"; return; }
    panel.style.display = "";
    $("ciuSub").textContent = c.length + " ciudades · ordenadas por población";

    const body = $("ciuBody");
    body.innerHTML = "";
    c.forEach((x, i) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="num dept__rank">${i + 1}</td>
        <td class="dept__nom">${x.nombre}</td>
        <td class="plc">${placeCell(x.primero)}</td>
        <td class="plc">${placeCell(x.segundo)}</td>
        <td class="plc">${placeCell(x.paloma)}</td>
        <td class="num">${partCell(x)}</td>
        <td class="num">${pct(x.mesas_pct)}</td>`;
      body.appendChild(tr);
    });
  }

  async function cargarCiudades() {
    try {
      const r = await fetch("/api/ciudades", { cache: "no-store" });
      if (!r.ok) return;
      const d = await r.json();
      _ciuData = d;
      pintarCiudades(d);
      _postGeo();
      pintarPaloma();
      pintarExplorar();
    } catch (e) { /* silencioso: panel se oculta solo */ }
  }

  // ====== Datos históricos verificados (Registraduría / Wikipedia) ======
  const HISTORICO = {
    "2014": { v1: "25 may 2014", v2: "15 jun 2014",
      m1: { censo: 33023716, votos: 13222354, abst: 60.04 },
      m2: { censo: 33023716, votos: 15818214, abst: 52.10 },
      r1: [
        { n: "Óscar Iván Zuluaga", p: "Centro Democrático", v: 3769005, pct: 29.28, c: "#2C3E50" },
        { n: "Juan Manuel Santos", p: "Partido de la U", v: 3310794, pct: 25.72, c: "#E67E22" },
        { n: "Marta Lucía Ramírez", p: "Conservador", v: 1997980, pct: 15.52, c: "#2980B9" },
        { n: "Clara López", p: "Polo Democrático", v: 1958518, pct: 15.22, c: "#C0392B" },
        { n: "Enrique Peñalosa", p: "Alianza Verde", v: 1064758, pct: 8.27, c: "#27AE60" }],
      r2: [
        { n: "Juan Manuel Santos", p: "Partido de la U", v: 7839342, pct: 50.99, c: "#E67E22" },
        { n: "Óscar Iván Zuluaga", p: "Centro Democrático", v: 6917001, pct: 44.99, c: "#2C3E50" }] },
    "2018": { v1: "27 may 2018", v2: "17 jun 2018",
      m1: { censo: 36227267, votos: 19643676, abst: 45.78 },
      m2: { censo: 36227267, votos: 19536404, abst: 46.00 },
      r1: [
        { n: "Iván Duque", p: "Centro Democrático", v: 7616857, pct: 39.36, c: "#2C3E50" },
        { n: "Gustavo Petro", p: "Colombia Humana", v: 4855069, pct: 25.09, c: "#8C378C" },
        { n: "Sergio Fajardo", p: "Coalición Colombia", v: 4602916, pct: 23.78, c: "#27AE60" },
        { n: "Germán Vargas Lleras", p: "Cambio Radical", v: 1412392, pct: 7.30, c: "#C0392B" },
        { n: "Humberto de la Calle", p: "Liberal", v: 396151, pct: 2.05, c: "#B22222" }],
      r2: [
        { n: "Iván Duque", p: "Centro Democrático", v: 10398689, pct: 54.03, c: "#2C3E50" },
        { n: "Gustavo Petro", p: "Colombia Humana", v: 8040449, pct: 41.77, c: "#8C378C" }] },
    "2022": { v1: "29 may 2022", v2: "19 jun 2022",
      m1: { censo: 39002239, votos: 21442300, abst: 45.02 },
      m2: { censo: 39002239, votos: 22687910, abst: 41.83 },
      r1: [
        { n: "Gustavo Petro", p: "Pacto Histórico", v: 8542020, pct: 40.34, c: "#8C378C" },
        { n: "Rodolfo Hernández", p: "Liga Gob. Anticorrupción", v: 5965531, pct: 28.17, c: "#E67E22" },
        { n: "Federico «Fico» Gutiérrez", p: "Equipo por Colombia", v: 5069526, pct: 23.94, c: "#2980B9" },
        { n: "Sergio Fajardo", p: "Centro Esperanza", v: 885291, pct: 4.18, c: "#27AE60" },
        { n: "John Milton Rodríguez", p: "Colombia Justa Libres", v: 271386, pct: 1.28, c: "#7F8C8D" }],
      r2: [
        { n: "Gustavo Petro", p: "Pacto Histórico", v: 11292758, pct: 50.42, c: "#8C378C" },
        { n: "Rodolfo Hernández", p: "Liga Gob. Anticorrupción", v: 10604656, pct: 47.35, c: "#E67E22" }] },
  };
  const REF = {
    petroR1: { v: 8542020, pct: 40.34 },
    derecha2022R1: { v: 11035057, pct: 52.11 },
  };

  let _ultimo = null;  // último payload nacional (para el slider de proyección)
  let _deptData = null, _ciuData = null, _extData = null;  // para exportar CSV

  // ---- (1+2) Comparación 2026 vs 2022 ----
  function pintarComp(data) {
    const c = data.comparativo; if (!c) return;
    $("cmpCeNow").textContent = fmt.format(c.cepeda.votos) + " · " + pct(c.cepeda.pct);
    $("cmpDeNow").textContent = fmt.format(c.suma.votos) + " · " + pct(c.suma.pct);
    const dCe = c.cepeda.pct - REF.petroR1.pct;
    const dDe = c.suma.pct - REF.derecha2022R1.pct;
    const sg = (n) => (n >= 0 ? "+" : "−") + pct(Math.abs(n));
    $("cmpCeDelta").textContent =
      `Cepeda va ${sg(dCe)} frente a Petro en la 1.ª vuelta de 2022 (${fmt.format(Math.abs(c.cepeda.votos - REF.petroR1.v))} votos de diferencia).`;
    $("cmpDeDelta").textContent =
      `La derecha 2026 va ${sg(dDe)} frente a Rodolfo+Fico en 2022 (${fmt.format(Math.abs(c.suma.votos - REF.derecha2022R1.v))} votos de diferencia).`;
  }

  // ---- (4) Proyección a 2.ª vuelta ----
  const _bloc = (nombre) => {
    const s = nombre.toLowerCase();
    if (s.includes("espriella")) return "fin_de";
    if (s.includes("cepeda")) return "fin_ce";
    if (s.includes("valencia") || s.includes("uribe") || s.includes("botero")) return "der";
    if (s.includes("barreras") || s.includes("caicedo") || s.includes("matamoros")) return "izq";
    if (s.includes("blanco")) return "x";
    return "cen"; // Fajardo, Claudia López, Lizcano, Murillo, otros
  };
  // ---- Proyección 2.ª vuelta con 4 bolsas ajustables ----
  // _proyReparto[k] = % de esa bolsa que va a De la Espriella (resto a Cepeda)
  const _proyReparto = { paloma: 80, fajardo: 45, uribe: 85, botero: 65, lopez: 45, indecisos: 50, blanco: 50 };
  const _PROY_GRUPOS = [
    { key: "paloma", label: "Paloma Valencia", color: "#4BAFE7", frag: "valencia" },
    { key: "fajardo", label: "Sergio Fajardo", color: "#27AE60", frag: "fajardo" },
    { key: "uribe", label: "Miguel Uribe Londoño", color: "#004B87", frag: "uribe" },
    { key: "botero", label: "Santiago Botero", color: "#617F89", frag: "botero" },
    { key: "lopez", label: "Claudia López", color: "#C9B400", frag: "claudia" },
    { key: "indecisos", label: "Indecisos / otros", color: "#7F8C8D", frag: null },
    { key: "blanco", label: "Voto en blanco", color: "#9AA0A6", frag: "blanco" },
  ];
  let _proyPools = null, _proySlidersBuilt = false;

  function _buildProySliders() {
    const cont = $("proySliders");
    if (!cont) return;
    cont.innerHTML = "";
    _PROY_GRUPOS.forEach((g) => {
      const row = document.createElement("div");
      row.className = "proy__sl";
      row.innerHTML = `
        <div class="proy__sl-top">
          <span class="proy__sl-nom"><span class="dept__dot" style="background:${g.color}"></span>${g.label}
            <span class="proy__sl-vot" id="pv_${g.key}"></span></span>
          <span class="proy__sl-rep" id="pr_${g.key}"></span>
        </div>
        <input type="range" min="0" max="100" step="5" value="${_proyReparto[g.key]}" id="ps_${g.key}" />`;
      cont.appendChild(row);
      row.querySelector("input").addEventListener("input", (e) => {
        _proyReparto[g.key] = Number(e.target.value);
        _recomputeProy();
      });
    });
    _proySlidersBuilt = true;
  }

  function pintarProyeccion(data) {
    const cands = data.candidatos || [];
    const votos = (frag) => { const c = cands.find((x) => frag && new RegExp(frag, "i").test(x.nombre)); return c ? c.votos : 0; };
    const pools = { deBase: votos("espriella"), ceBase: votos("cepeda") };
    const nombradas = ["espriella", "cepeda"];
    _PROY_GRUPOS.forEach((g) => {
      if (g.key === "indecisos") return;
      pools[g.key] = votos(g.frag);
      if (g.frag) nombradas.push(g.frag);
    });
    let indecisos = 0;
    cands.forEach((c) => {
      if (nombradas.some((k) => new RegExp(k, "i").test(c.nombre))) return;
      indecisos += c.votos;
    });
    pools.indecisos = indecisos;
    _proyPools = pools;
    if (!_proySlidersBuilt) _buildProySliders();
    _recomputeProy();
  }

  function _recomputeProy() {
    if (!_proyPools) return;
    const P = _proyPools, r = _proyReparto;
    let projDe = P.deBase, projCe = P.ceBase;
    _PROY_GRUPOS.forEach((g) => {
      const v = P[g.key] || 0, a = (r[g.key] || 0) / 100;
      projDe += v * a;
      projCe += v * (1 - a);
    });
    const tot = projDe + projCe || 1;
    const pDe = (projDe / tot) * 100, pCe = (projCe / tot) * 100;
    $("proyDe").style.width = pDe + "%";
    $("proyCe").style.width = pCe + "%";
    $("proyDeIn").textContent = "De la Espriella " + pct(pDe);
    $("proyCeIn").textContent = pct(pCe) + " Cepeda";
    const gana = pDe >= pCe ? "De la Espriella" : "Cepeda";
    $("proyResumen").innerHTML =
      `Con este reparto ganaría <strong>${gana}</strong> por <strong>${pct(Math.abs(pDe - pCe))}</strong> ` +
      `(${fmt.format(Math.round(Math.max(projDe, projCe)))} vs ${fmt.format(Math.round(Math.min(projDe, projCe)))} votos).`;
    _PROY_GRUPOS.forEach((g) => {
      const v = P[g.key] || 0, a = r[g.key] || 0;
      const pv = $("pv_" + g.key); if (pv) pv.textContent = "(" + fmt.format(v) + " votos)";
      const pr = $("pr_" + g.key);
      if (pr) pr.innerHTML = `<b style="color:#CE742A">${a}%</b> Espriella · <b style="color:#8C378C">${100 - a}%</b> Cepeda`;
    });
  }

  // ---- (6) Polymarket ----
  function _pmList(el, arr) {
    el.innerHTML = "";
    (arr || []).forEach((o) => {
      const p = Math.round(o.prob * 100);
      const d = document.createElement("div");
      d.className = "pm";
      d.innerHTML = `<span class="pm__nom">${o.nombre}</span>
        <span class="pm__pct">${p}%</span>
        <span class="pm__pista"><span class="pm__fill" style="width:${p}%"></span></span>`;
      el.appendChild(d);
    });
  }
  async function cargarPolymarket() {
    try {
      const r = await fetch("/api/polymarket", { cache: "no-store" });
      if (!r.ok) return;
      const d = await r.json();
      if (!d.ok && !(d.presidencia || []).length) { $("panelPoly").style.display = "none"; return; }
      $("panelPoly").style.display = "";
      _pmList($("polyR1"), d.primera_ganador);
      _pmList($("polyAdv"), d.pasa_segunda);
      _pmList($("polyPres"), d.presidencia);
      if (d.url) $("polyLink").href = d.url;
    } catch (e) { $("panelPoly").style.display = "none"; }
  }

  // ---- (3) Histórico multi-select ----
  function pintarHistorico() {
    const anios = [...document.querySelectorAll(".hAnio:checked")].map((x) => x.value);
    const vueltas = [...document.querySelectorAll(".hVuelta:checked")].map((x) => x.value);
    const grid = $("histGrid");
    grid.innerHTML = "";
    if (!anios.length || !vueltas.length) {
      grid.innerHTML = '<p style="color:var(--tinta-suave);font-size:13px">Selecciona al menos una elección y una vuelta.</p>';
      return;
    }
    anios.forEach((a) => {
      vueltas.forEach((v) => {
        const data = HISTORICO[a]; if (!data) return;
        const lista = data[v] || [];
        const card = document.createElement("div");
        card.className = "hcard";
        const filas = lista.map((x, i) => `
          <div class="hrow">
            <span class="hrow__pos">${i + 1}</span>
            <span>
              <div class="hrow__nom"><span class="dept__dot" style="background:${x.c};display:inline-block;margin-right:5px"></span>${x.n}</div>
              <div class="hrow__par">${x.p}</div>
            </span>
            <span class="hrow__num">
              <div class="hrow__pct">${pct(x.pct)}</div>
              <div class="hrow__vot">${fmt.format(x.v)}</div>
            </span>
          </div>`).join("");
        const m = data[v === "r1" ? "m1" : "m2"];
        const meta = m ? '<div class="hcard__meta">' +
          '<span>Habilitados <b>' + fmt.format(m.censo) + '</b></span>' +
          '<span>Votación <b>' + fmt.format(m.votos) + '</b></span>' +
          '<span>Abstención <b>' + pct(m.abst) + '</b></span></div>' : "";
        card.innerHTML = `
          <div class="hcard__head">
            <span class="hcard__anio">${a}</span>
            <span class="hcard__v">${v === "r1" ? "1.ª vuelta · " + data.v1 : "2.ª vuelta · " + data.v2}</span>
          </div>${meta}${filas}`;
        grid.appendChild(card);
      });
    });
  }

  // ---- (5) Análisis y predicciones ----
  function pintarAnalisis(data) {
    const cs = (data.candidatos || []).filter((c) => !/blanco/i.test(c.nombre));
    if (cs.length < 2) return;
    const a = cs[0], b = cs[1];
    const margen = Math.abs(a.porcentaje - b.porcentaje);
    const difVotos = Math.abs(a.votos - b.votos);
    $("analisisBody").innerHTML = `
      <p class="ana__key">Con el ${pct(data.porcentaje_mesas)} de mesas escrutadas, <strong>${a.nombre} (${pct(a.porcentaje)})</strong>
        encabeza la primera vuelta, seguido de <strong>${b.nombre} (${pct(b.porcentaje)})</strong>.
        Ambos pasan a una <strong>segunda vuelta el 21 de junio de 2026</strong>, separados por
        <strong>${pct(margen)}</strong> (${fmt.format(difVotos)} votos): uno de los márgenes más estrechos de la historia reciente.</p>
      <p><strong>Claves para la segunda vuelta:</strong></p>
      <ul>
        <li>La <strong>suma de la derecha</strong> (De la Espriella + Valencia, ${pct((data.comparativo || {}).suma ? data.comparativo.suma.pct : 0)}) supera hoy a Cepeda, pero los votos <em>no</em> se transfieren en bloque de forma automática.</li>
        <li>El <strong>centro</strong> (Fajardo, Claudia López, Lizcano, Murillo) y la <strong>abstención</strong> (${pct(data.abstencion_pct)}) serán decisivos: con ~52% de participación, hay un gran caudal de votos en juego.</li>
        <li>Históricamente las segundas vueltas reordenan el mapa: en 2022 Petro pasó de 40,3% a 50,4%, y en 2014 Santos remontó desde el 2.º lugar para ganar.</li>
      </ul>
      <p><strong>Qué dicen los analistas:</strong> las encuestas de mayo (Invamer, Guarumo, AtlasIntel, CNC) daban a <strong>Cepeda primero</strong>; el fuerte ascenso de <strong>De la Espriella</strong> fue la sorpresa de la jornada. El mercado <strong>Polymarket</strong> da hoy una ventaja clara a De la Espriella para la Presidencia, pero la estrechez del margen y el comportamiento del centro mantienen el escenario <strong>abierto y competitivo</strong>.</p>
      <p class="ana__src">Fuentes: Registraduría Nacional (resultados), El Tiempo, Infobae, La República, CNN en Español (cobertura y análisis), Polymarket (mercado). Las predicciones son interpretativas, no garantizan resultados.</p>`;
  }

  // ====== (ver3) Filtro geográfico multi-select + Selección combinada ======
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
      return '<div class="combo__row"><span class="combo__cn">' +
        '<span class="combo__cn-nom"><span class="dept__dot" style="background:' + c.color + ';display:inline-block;margin-right:5px"></span>' + c.nombre + '</span>' +
        '<span class="combo__cn-vot">' + fmt.format(c.votos) + ' votos</span></span>' +
        '<span class="combo__cp">' + pct(p) + '</span>' +
        '<span class="combo__pista"><span class="combo__fill" style="width:' + ((c.votos / maxv) * 100) + '%;background:' + c.color + '"></span></span></div>';
    }).join("");
    return '<div class="combo__card' + (extra || "") + '"><div class="combo__h">' + titulo + '</div>' +
      '<div class="combo__lead"><span class="dept__dot" style="background:' + lead.color + '"></span>' +
      '<span class="combo__nom">' + lead.nombre + '</span><span class="combo__pct">' + pct(leadPct) + '</span></div>' +
      '<div class="combo__meta">' + fmt.format(Math.round(a.censo)) + ' habilitados · ' + fmt.format(a.votantes) + ' votantes · participación ' + pct(part) + ' · abstención ' + pct(part ? 100 - part : 0) + '</div>' +
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
    renderMunicipios(depObjs);
  }

  // Drill-down: municipios del departamento seleccionado, con los 3 candidatos
  const _muniCache = {};
  function _muniTabla(munis) {
    const cel = (c, color) =>
      '<td class="num"><div class="hrow__pct" style="color:' + color + '">' + pct(c.pct) +
      '</div><div class="hrow__vot"><strong>' + fmt.format(c.votos) + '</strong></div></td>';
    const filas = munis.map((m) =>
      '<tr><td class="dept__nom">' + m.nombre + '</td>' +
      cel(m.abelardo, "#CE742A") + cel(m.cepeda, "#8C378C") + cel(m.paloma, "#2980B9") +
      '<td class="num">' + fmt.format(m.votantes) + '</td></tr>').join("");
    return '<div class="dept-wrap"><table class="dept-tabla"><thead><tr>' +
      '<th>Municipio</th><th class="num">De la Espriella</th><th class="num">Cepeda</th>' +
      '<th class="num">Valencia</th><th class="num">Total votantes</th></tr></thead><tbody>' +
      filas + '</tbody></table></div>';
  }
  function _muniBloque(d, data) {
    const munis = (data && data.municipios) || [];
    return '<div class="muni__h">Municipios de <strong>' + d.nombre + '</strong> <span>(' +
      munis.length + ')</span></div>' +
      (munis.length ? _muniTabla(munis) : '<div class="muni__load">Sin municipios.</div>');
  }
  async function renderMunicipios(depObjs) {
    const cont = $("comboMunis");
    if (!cont) return;
    if (!depObjs.length) { cont.innerHTML = ""; return; }
    cont.innerHTML = "";
    for (const d of depObjs) {
      const blk = document.createElement("div");
      blk.className = "muni__block";
      cont.appendChild(blk);
      let data = _muniCache[d.codigo];
      if (data) { blk.innerHTML = _muniBloque(d, data); continue; }
      blk.innerHTML = '<div class="muni__h">Municipios de <strong>' + d.nombre +
        '</strong></div><div class="muni__load">Cargando municipios…</div>';
      try {
        const r = await fetch("/api/municipios?dep=" + encodeURIComponent(d.codigo), { cache: "no-store" });
        data = await r.json();
        _muniCache[d.codigo] = data;
      } catch (e) { data = { municipios: [] }; }
      blk.innerHTML = _muniBloque(d, data);
    }
  }

  function iniciarControles() {
    document.querySelectorAll(".hAnio, .hVuelta").forEach((el) =>
      el.addEventListener("change", pintarHistorico));
    pintarHistorico();
    document.querySelectorAll("#seg2022 .seg2022__b").forEach((b) =>
      b.addEventListener("click", () => pintar2022(b.dataset.v)));
    const bcsv = $("btnCsv");
    if (bcsv) bcsv.addEventListener("click", exportarCSV);
    tickR2();
    setInterval(tickR2, 1000);
  }

  // ---- Mapa de Colombia coloreado por ganador ----
  let _geo = null;
  // NFD + mayúsculas; [^A-Z] elimina marcas diacríticas, espacios y puntuación.
  const _norm = (s) => (s || "").normalize("NFD").toUpperCase().replace(/[^A-Z]/g, "");
  function _geoKey(dpt) {
    const g = _norm(dpt);
    if (g.includes("BOGOTA")) return "BOGOTADC";
    if (g.includes("ANDRES") || g.includes("ARCHIPIE")) return "SANANDRES";
    if (g.includes("VALLEDELCAUCA")) return "VALLE";
    if (g.includes("NORTEDESANTANDER")) return "NORTEDESAN";
    return g;
  }
  async function _ensureGeo() {
    if (_geo) return _geo;
    const r = await fetch("/colombia.geojson", { cache: "force-cache" });
    _geo = await r.json();
    return _geo;
  }
  async function pintarMapa(deptData) {
    const depts = (deptData && deptData.departamentos) || [];
    if (!depts.length) return;
    let geo;
    try { geo = await _ensureGeo(); } catch (e) { $("panelMapa").style.display = "none"; return; }

    const byKey = {};
    depts.forEach((d) => { byKey[_norm(d.nombre)] = d; });

    // Proyección equirectangular simple sobre el bounding box
    let minLon = 1e9, maxLon = -1e9, minLat = 1e9, maxLat = -1e9;
    const eachPt = (co, f) => { if (typeof co[0] === "number") f(co); else co.forEach((c) => eachPt(c, f)); };
    geo.features.forEach((ft) => eachPt(ft.geometry.coordinates, ([lon, lat]) => {
      if (lon < minLon) minLon = lon; if (lon > maxLon) maxLon = lon;
      if (lat < minLat) minLat = lat; if (lat > maxLat) maxLat = lat;
    }));
    const W = 560, H = Math.round(W * (maxLat - minLat) / (maxLon - minLon));
    const scale = Math.min(W / (maxLon - minLon), H / (maxLat - minLat));
    const px = (lon) => ((lon - minLon) * scale).toFixed(1);
    const py = (lat) => ((maxLat - lat) * scale).toFixed(1);
    const ring = (r) => r.map((c, i) => (i ? "L" : "M") + px(c[0]) + "," + py(c[1])).join("") + "Z";
    const geomPath = (gm) => (gm.type === "Polygon" ? [gm.coordinates] : gm.coordinates)
      .map((poly) => poly.map(ring).join("")).join("");

    const svg = $("mapaSvg");
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    let nDe = 0, nCe = 0, html = "";
    geo.features.forEach((ft) => {
      const win = byKey[_geoKey(ft.properties.dpt)];
      const color = win ? win.color : "#E3DFD3";
      if (win) { if (/espriella/i.test(win.lider)) nDe++; else if (/cepeda/i.test(win.lider)) nCe++; }
      const tip = win
        ? `${win.nombre}: ${win.lider} ${pct(win.primero.pct)} · 2.º ${win.segundo.nombre} ${pct(win.segundo.pct)}`
        : ft.properties.dpt;
      html += `<path d="${geomPath(ft.geometry)}" fill="${color}" stroke="#FAF9F5" stroke-width="0.7" class="mapa__dpt" data-tip="${tip.replace(/"/g, "")}"/>`;
    });
    svg.innerHTML = html;
    $("mapaNde").textContent = nDe;
    $("mapaNce").textContent = nCe;
    $("mapaSub").textContent = `${depts.length} departamentos · ganador por mayoría`;
    $("panelMapa").style.display = "";

    const tipEl = $("mapaTip");
    svg.querySelectorAll(".mapa__dpt").forEach((p) => {
      p.addEventListener("mousemove", (e) => {
        const r = $("mapaSvg").parentElement.getBoundingClientRect();
        tipEl.style.display = "block";
        tipEl.textContent = p.dataset.tip;
        tipEl.style.left = (e.clientX - r.left + 14) + "px";
        tipEl.style.top = (e.clientY - r.top + 14) + "px";
      });
      p.addEventListener("mouseleave", () => { tipEl.style.display = "none"; });
    });
  }

  // ---- Encuestas finales (mayo 2026) vs resultado real ----
  const POLLS = [
    { firma: "AtlasIntel", fecha: "18–21 may", cep: 37.7, abe: 36.3, val: 13.9, faj: 3.8 },
    { firma: "Invamer", fecha: "13–20 may", cep: 44.6, abe: 31.6, val: 14.0, faj: 2.4 },
    { firma: "CNC", fecha: "16–22 may", cep: 33.4, abe: 30.9, val: 12.6, faj: 2.1 },
    { firma: "Guarumo–EcoAnalítica", fecha: "11–19 may", cep: 37.1, abe: 27.5, val: 21.7, faj: 3.2 },
    { firma: "CELAG", fecha: "may", cep: 41.1, abe: 19.1, val: 16.6, faj: 1.9 },
    { firma: "Corp. M. Maldonado", fecha: "19–22 may", cep: 37.3, abe: 19.3, val: 29.2, faj: 2.3 },
  ];
  function pintarEncuestas(data) {
    const find = (frag) => (data.candidatos || []).find((c) => new RegExp(frag, "i").test(c.nombre));
    const A = { cep: find("Cepeda"), abe: find("Espriella"), val: find("Valencia"), faj: find("Fajardo") };
    if (!A.cep || !A.abe) return;
    const act = { cep: A.cep.porcentaje, abe: A.abe.porcentaje,
      val: (A.val || {}).porcentaje || 0, faj: (A.faj || {}).porcentaje || 0 };
    $("encActual").innerHTML =
      `<strong>Resultado real</strong> (escrutado ${pct(data.porcentaje_mesas)}): ` +
      `<strong style="color:#CE742A">De la Espriella ${pct(act.abe)}</strong> · ` +
      `<strong style="color:#8C378C">Cepeda ${pct(act.cep)}</strong> · ` +
      `Valencia ${pct(act.val)} · Fajardo ${pct(act.faj)}`;

    const actLeader = act.abe > act.cep ? "abe" : "cep";
    const rows = POLLS.map((p) => {
      const mae = (Math.abs(p.cep - act.cep) + Math.abs(p.abe - act.abe) +
        Math.abs(p.val - act.val) + Math.abs(p.faj - act.faj)) / 4;
      return { ...p, mae, orden: (p.abe > p.cep ? "abe" : "cep") === actLeader };
    }).sort((a, b) => a.mae - b.mae);

    const body = $("encBody");
    body.innerHTML = "";
    rows.forEach((p, i) => {
      const tr = document.createElement("tr");
      if (i === 0) tr.className = "enc__best";
      tr.innerHTML = `
        <td class="dept__nom">${i === 0 ? "★ " : ""}${p.firma}<div class="hrow__par">${p.fecha} 2026</div></td>
        <td class="num">${p.cep.toFixed(1)} %</td>
        <td class="num">${p.abe.toFixed(1)} %</td>
        <td class="num">${p.val.toFixed(1)} %</td>
        <td class="num">${p.faj.toFixed(1)} %</td>
        <td class="num enc__mae">${p.mae.toFixed(1)}</td>
        <td class="num">${p.orden ? '<span style="color:#3E7A55">✓</span>' : '<span style="color:#B45F44">✗</span>'}</td>`;
      body.appendChild(tr);
    });
    const best = rows[0];
    $("encNota").innerHTML =
      `Todas las encuestas de mayo daban a <strong>Cepeda</strong> como primero; el resultado <strong>invirtió el orden</strong>. ` +
      `La que más se acercó fue <strong>${best.firma}</strong> (error medio <strong>${best.mae.toFixed(1)} puntos</strong>), ` +
      `que fue la que mejor capturó el ascenso de De la Espriella. «Error medio» = promedio de la diferencia absoluta ` +
      `en los 4 candidatos principales. Fuente de encuestas: Wikipedia (sondeos presidenciales 2026).`;
  }

  // ---- Colombianos en el exterior (por país) ----
  function pintarExterior(d) {
    $("panelExterior").style.display = "";
    $("extSub").textContent =
      `${fmt.format(d.votantes)} votantes · ${d.paises.length} países · ${pct(d.mesas_pct)} de mesas`;
    const max = Math.max(...d.candidatos.map((c) => c.pct), 1);
    $("extTop").innerHTML = d.candidatos.map((c) => `
      <div class="extc">
        <span class="extc__nom"><span class="dept__dot" style="background:${c.color};display:inline-block;margin-right:6px"></span>${c.nombre}</span>
        <span class="extc__pista"><span class="extc__barra" style="width:${(c.pct / max) * 100}%;background:${c.color}"></span></span>
        <span class="extc__cif"><strong>${pct(c.pct)}</strong> · ${fmt.format(c.votos)}</span>
      </div>`).join("");
    const body = $("extBody");
    body.innerHTML = "";
    d.paises.forEach((p) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="dept__nom">${p.nombre}</td>
        <td><div class="dept__lider"><span class="dept__dot" style="background:${p.color}"></span><span>${p.lider || "—"}</span></div></td>
        <td class="num">${pct(p.lider_pct)}</td>
        <td class="num">${fmt.format(p.votantes)}</td>
        <td class="num">${pct(p.mesas_pct)}</td>`;
      body.appendChild(tr);
    });
  }
  async function cargarExterior() {
    try {
      const r = await fetch("/api/exterior", { cache: "no-store" });
      if (!r.ok) return;
      const d = await r.json();
      if (!d.ok || !(d.paises || []).length) { $("panelExterior").style.display = "none"; return; }
      _extData = d;
      pintarExterior(d);
      pintarPaloma();
    } catch (e) { $("panelExterior").style.display = "none"; }
  }

  // ---- Desempeño de Paloma Valencia ----
  function pintarPaloma() {
    if (!_ultimo) return;
    const cands = (_ultimo.candidatos || []).filter((c) => !/blanco/i.test(c.nombre));
    const pal = cands.find((c) => /valencia/i.test(c.nombre));
    if (!pal) return;
    $("panelPaloma").style.display = "";
    const pos = cands.indexOf(pal) + 1;
    $("palPct").textContent = pct(pal.porcentaje);
    $("palVotos").textContent = fmt.format(pal.votos) + " votos";
    $("palPos").textContent = pos + ".º lugar nacional";
    $("palSub").textContent = "Centro Democrático · tercera fuerza";

    const de = cands.find((c) => /espriella/i.test(c.nombre)) || { porcentaje: 0 };
    const ce = cands.find((c) => /cepeda/i.test(c.nombre)) || { porcentaje: 0 };
    const max = Math.max(de.porcentaje, ce.porcentaje, pal.porcentaje, 1);
    const bar = (nom, p, color) =>
      `<div class="pal__b"><span class="pal__nom">${nom}</span>` +
      `<span class="pal__pista"><span class="pal__fill" style="width:${p / max * 100}%;background:${color}"></span></span>` +
      `<span class="pal__v">${pct(p)}</span></div>`;
    $("palBar3").innerHTML =
      bar("De la Espriella", de.porcentaje, "#CE742A") +
      bar("Cepeda", ce.porcentaje, "#8C378C") +
      bar("Valencia", pal.porcentaje, "#2980B9");

    const rows = (arr) => arr.length
      ? arr.map((x) => `<div class="pal__row"><span class="pal__rn">${x.nombre}</span><span class="pal__rp">${pct(x.paloma.pct)}</span></div>`).join("")
      : '<span style="color:var(--tinta-suave);font-size:13px">cargando…</span>';
    const topN = (lista) => (lista || []).filter((d) => d.paloma)
      .slice().sort((a, b) => b.paloma.pct - a.paloma.pct).slice(0, 5);
    $("palDept").innerHTML = rows(topN(_deptData && _deptData.departamentos));
    $("palCiu").innerHTML = rows(topN(_ciuData && _ciuData.ciudades));

    let extHtml = '<span style="color:var(--tinta-suave);font-size:13px">cargando…</span>';
    if (_extData && _extData.candidatos) {
      const pv = _extData.candidatos.find((c) => /valencia/i.test(c.nombre));
      if (pv) extHtml =
        `<div class="pal__row"><span class="pal__rn">Total exterior</span><span class="pal__rp">${pct(pv.pct)}</span></div>` +
        `<div class="pal__row"><span class="pal__rn">Votos</span><span class="pal__rp">${fmt.format(pv.votos)}</span></div>`;
    }
    $("palExt").innerHTML = extHtml;
  }

  // ---- Evolución por boletín (línea de tiempo) ----
  function pintarSerie(serie) {
    const svg = $("serieSvg"), W = 560, H = 240, pad = 34;
    if (!serie || !serie.length) {
      $("serieSub").textContent = "registrando en vivo…";
      svg.innerHTML = "";
      $("serieNota").textContent =
        "El feed público no expone el histórico por candidato; esta línea se registra EN VIVO " +
        "desde que corre el tablero y capturará la evolución completa el 21 de junio.";
      return;
    }
    $("serieSub").textContent = serie.length + " boletín(es) registrado(s)";
    const allv = serie.flatMap((s) => [s.abelardo, s.cepeda, s.paloma]);
    let ymin = Math.max(0, Math.floor(Math.min(...allv) / 5) * 5 - 2);
    let ymax = Math.ceil(Math.max(...allv) / 5) * 5 + 2;
    const n = serie.length;
    const x = (i) => pad + (n <= 1 ? (W - pad - 8) / 2 : (i / (n - 1)) * (W - pad - 8));
    const y = (v) => pad + (1 - (v - ymin) / (ymax - ymin || 1)) * (H - pad * 2);
    const linea = (key, color) => {
      const pts = serie.map((s, i) => `${x(i).toFixed(1)},${y(s[key]).toFixed(1)}`).join(" ");
      const dots = serie.map((s, i) => `<circle cx="${x(i).toFixed(1)}" cy="${y(s[key]).toFixed(1)}" r="3" fill="${color}"/>`).join("");
      return `<polyline points="${pts}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linejoin="round"/>${dots}`;
    };
    let grid = "";
    for (let g = 0; g <= 4; g++) {
      const v = ymin + (ymax - ymin) * g / 4, yy = y(v).toFixed(1);
      grid += `<line x1="${pad}" y1="${yy}" x2="${W - 8}" y2="${yy}" stroke="#E3DFD3" stroke-width="1"/>`;
      grid += `<text x="4" y="${(+yy + 4)}" font-size="10" fill="#6B6557">${v.toFixed(0)}%</text>`;
    }
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.innerHTML = grid + linea("cepeda", "#8C378C") + linea("abelardo", "#CE742A") + linea("paloma", "#2980B9");
    $("serieNota").textContent = serie.length < 3
      ? "Registro en vivo: el feed público no trae el histórico por candidato, así que el tablero lo va guardando boletín a boletín. En la 2.ª vuelta (21 jun) capturará toda la noche."
      : "Evolución del porcentaje de cada candidato a lo largo de los boletines registrados.";
  }
  async function cargarSerie() {
    try { const r = await fetch("/api/serie", { cache: "no-store" }); if (!r.ok) return;
      pintarSerie((await r.json()).serie || []); } catch (e) { /* */ }
  }

  // ---- Exportar resultados a CSV ----
  function exportarCSV() {
    const esc = (v) => '"' + String(v == null ? "" : v).replace(/"/g, '""') + '"';
    const L = ["Elecciones Presidenciales Colombia 2026 - Primera vuelta"];
    if (_ultimo) {
      L.push("", `Nacional (boletin ${_ultimo.boletin}, mesas ${_ultimo.porcentaje_mesas}%, corte ${_ultimo.fecha_corte_txt || ""})`);
      L.push(["Candidato", "Partido", "Votos", "%"].map(esc).join(","));
      _ultimo.candidatos.forEach((c) => L.push([c.nombre, c.partido, c.votos, c.porcentaje].map(esc).join(",")));
    }
    if (_deptData && _deptData.departamentos) {
      L.push("", "Departamentos");
      L.push(["Departamento", "1o", "1o %", "1o votos", "2o", "2o %", "2o votos", "Valencia %", "Valencia votos", "Participacion %", "Mesas %"].map(esc).join(","));
      _deptData.departamentos.forEach((d) => L.push([d.nombre, d.primero.nombre, d.primero.pct, d.primero.votos, d.segundo.nombre, d.segundo.pct, d.segundo.votos, (d.paloma || {}).pct, (d.paloma || {}).votos, d.participacion_pct, d.mesas_pct].map(esc).join(",")));
    }
    if (_ciuData && _ciuData.ciudades) {
      L.push("", "Ciudades principales");
      L.push(["Ciudad", "1o", "1o %", "1o votos", "2o", "2o %", "2o votos", "Valencia %", "Participacion %", "Mesas %"].map(esc).join(","));
      _ciuData.ciudades.forEach((d) => L.push([d.nombre, d.primero.nombre, d.primero.pct, d.primero.votos, d.segundo.nombre, d.segundo.pct, d.segundo.votos, (d.paloma || {}).pct, d.participacion_pct, d.mesas_pct].map(esc).join(",")));
    }
    if (_extData && _extData.paises) {
      L.push("", "Exterior (por pais)");
      L.push(["Pais", "Lider", "% lider", "Votantes", "Mesas %"].map(esc).join(","));
      _extData.paises.forEach((p) => L.push([p.nombre, p.lider, p.lider_pct, p.votantes, p.mesas_pct].map(esc).join(",")));
    }
    const blob = new Blob(["﻿" + L.join("\n")], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "resultados_colombia_2026.csv";
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(a.href);
  }

  // ---- Cuenta regresiva 2.ª vuelta ----
  function tickR2() {
    const el = $("r2Count"); if (!el) return;
    const target = new Date("2026-06-21T08:00:00-05:00").getTime();
    const diff = target - Date.now();
    if (diff <= 0) { el.textContent = "¡Jornada en curso!"; return; }
    const d = Math.floor(diff / 86400000), h = Math.floor(diff % 86400000 / 3600000),
      m = Math.floor(diff % 3600000 / 60000), s = Math.floor(diff % 60000 / 1000);
    el.textContent = `${d}d ${String(h).padStart(2, "0")}h ${String(m).padStart(2, "0")}m ${String(s).padStart(2, "0")}s`;
  }

  // ====== Histórico 2022 + comparativo (swing) ======
  let _hist2022 = null;
  let _vuelta2022 = "r1";

  // clave canónica de departamento (empata 2022 <-> 2026 <-> geojson)
  function canonD(s) {
    const n = _norm(s);
    if (n.includes("BOGOTA")) return "BOGOTA";
    if (n.includes("SANANDRES") || n.includes("ARCHIPIE")) return "SANANDRES";
    if (n.startsWith("VALLE")) return "VALLE";
    if (n.startsWith("NORTEDESAN")) return "NORTEDESANTANDER";
    if (n.includes("GUAJIRA")) return "LAGUAJIRA";
    return n;
  }
  const signo = (x) => (x >= 0 ? "+" : "−") + pct(Math.abs(x));

  async function cargarHistorico2022() {
    if (!_hist2022) {
      try {
        const r = await fetch("/historico_2022_departamentos.json", { cache: "force-cache" });
        if (!r.ok) return;
        _hist2022 = await r.json();
      } catch (e) { return; }
    }
    pintar2022(_vuelta2022);
    pintarSwing();
  }

  // ---- Panel 1: 2022 por departamento ----
  function pintar2022(vuelta) {
    if (!_hist2022) return;
    _vuelta2022 = vuelta;
    const data = _hist2022[vuelta] || {};
    const deptos = Object.values(data).sort((a, b) => a.nombre.localeCompare(b.nombre));
    if (!deptos.length) { $("panel2022").style.display = "none"; return; }
    $("panel2022").style.display = "";
    document.querySelectorAll("#seg2022 .seg2022__b").forEach((b) =>
      b.classList.toggle("is-on", b.dataset.v === vuelta));
    $("head2022").innerHTML = vuelta === "r1"
      ? `<tr><th>Departamento</th><th class="num">Petro</th><th class="num">Rodolfo Hernández</th><th class="num">Fico Gutiérrez</th></tr>`
      : `<tr><th>Departamento</th><th class="num">Petro</th><th class="num">Rodolfo Hernández</th></tr>`;
    const cell = (c, color) => c
      ? `<td class="num"><div class="hrow__pct" style="color:${color}">${pct(c.p)}</div><div class="hrow__vot">${fmt.format(c.v)}</div></td>`
      : `<td class="num">—</td>`;
    const body = $("body2022");
    body.innerHTML = "";
    deptos.forEach((d) => {
      let cols = cell(d.petro, "#8C378C") + cell(d.rodolfo, "#C8932B");
      if (vuelta === "r1") cols += cell(d.fico, "#2980B9");
      const tr = document.createElement("tr");
      tr.innerHTML = `<td class="dept__nom">${d.nombre}</td>${cols}`;
      body.appendChild(tr);
    });
  }

  function _swColor(sw) {
    if (sw == null) return "#E3DFD3";
    if (sw > 6) return "#B85C28";
    if (sw > 1.5) return "#E0A36A";
    if (sw >= -1.5) return "#C9C2B2";
    if (sw >= -6) return "#B98FC0";
    return "#6E2A6E";
  }

  // ---- Panel 2: swing 2022 -> 2026 ----
  async function pintarSwing() {
    if (!_hist2022 || !_deptData || !(_deptData.departamentos || []).length || !_ultimo) return;
    const r1 = _hist2022.r1, r2 = _hist2022.r2;

    // Narrativa nacional
    const c = _ultimo.comparativo || {};
    const L26 = (c.cepeda || {}).pct || 0, R26 = (c.suma || {}).pct || 0;
    const L22 = 40.34, R22 = 52.11; // Petro R1 nac. ; (Rodolfo+Fico) R1 nac.
    const swNat = Math.round(((R26 - L26) - (R22 - L22)) * 100) / 100;
    const dir = swNat >= 0 ? "ensanchó" : "se redujo";
    $("swingNat").innerHTML = `
      <div class="swing__natbox"><h4>Bloque izquierda (1.ª vuelta)</h4>
        <div class="swing__row"><span>Petro 2022</span><b>${pct(L22)}</b></div>
        <div class="swing__row"><span>Cepeda 2026</span><b style="color:#8C378C">${pct(L26)}</b></div>
        <div class="swing__delta">${signo(L26 - L22)} vs 2022</div></div>
      <div class="swing__natbox"><h4>Bloque derecha (1.ª vuelta)</h4>
        <div class="swing__row"><span>Rodolfo + Fico 2022</span><b>${pct(R22)}</b></div>
        <div class="swing__row"><span>De la Espriella + Valencia 2026</span><b style="color:#CE742A">${pct(R26)}</b></div>
        <div class="swing__delta">${signo(R26 - R22)} vs 2022</div></div>
      <div class="swing__titular">La derecha sigue siendo mayoría como en 2022, pero su ventaja ${dir} <b>${pct(Math.abs(swNat))}</b>.
        La gran diferencia: en 2026 la derecha va <b>unificada</b> tras De la Espriella, mientras en 2022 estaba dividida (Rodolfo + Fico), lo que dejó a Petro de primero.</div>`;

    // swing + flips por departamento
    const swKey = {}, win22 = {}, lead26 = {};
    (_deptData.departamentos || []).forEach((d) => {
      const k = canonD(d.nombre), h1 = r1[k], h2 = r2[k];
      if (!h1) return;
      const cep = [d.primero, d.segundo].find((x) => /cepeda/i.test(x.nombre));
      const esp = [d.primero, d.segundo].find((x) => /espriella/i.test(x.nombre));
      const L = cep ? cep.pct : 0, R = (esp ? esp.pct : 0) + (d.paloma ? d.paloma.pct : 0);
      swKey[k] = Math.round(((R - L) - ((h1.rodolfo.p + h1.fico.p) - h1.petro.p)) * 100) / 100;
      if (h2) win22[k] = h2.petro.p >= h2.rodolfo.p ? "izq" : "der";
      lead26[k] = /espriella/i.test(d.primero.nombre) ? "der" : "izq";
    });

    // volteos
    let flipDer = 0, flipIzq = 0;
    Object.keys(win22).forEach((k) => {
      if (win22[k] === "izq" && lead26[k] === "der") flipDer++;
      else if (win22[k] === "der" && lead26[k] === "izq") flipIzq++;
    });
    $("swingFlips").innerHTML = `
      <div class="swing__flip"><div class="n" style="color:#CE742A">${flipDer}</div>
        <div class="l">deptos. que ganó <b>Petro</b> en 2022 y ahora lidera <b>De la Espriella</b></div></div>
      <div class="swing__flip"><div class="n" style="color:#8C378C">${flipIzq}</div>
        <div class="l">deptos. de la derecha en 2022 que ahora lidera <b>Cepeda</b></div></div>`;

    // mapa de giro
    try {
      const geo = await _ensureGeo();
      let minLon = 1e9, maxLon = -1e9, minLat = 1e9, maxLat = -1e9;
      const eachPt = (co, f) => { if (typeof co[0] === "number") f(co); else co.forEach((x) => eachPt(x, f)); };
      geo.features.forEach((ft) => eachPt(ft.geometry.coordinates, ([lo, la]) => {
        if (lo < minLon) minLon = lo; if (lo > maxLon) maxLon = lo;
        if (la < minLat) minLat = la; if (la > maxLat) maxLat = la;
      }));
      const W = 560, H = Math.round(W * (maxLat - minLat) / (maxLon - minLon));
      const sc = Math.min(W / (maxLon - minLon), H / (maxLat - minLat));
      const px = (lo) => ((lo - minLon) * sc).toFixed(1), py = (la) => ((maxLat - la) * sc).toFixed(1);
      const ring = (rg) => rg.map((p, i) => (i ? "L" : "M") + px(p[0]) + "," + py(p[1])).join("") + "Z";
      const path = (g) => (g.type === "Polygon" ? [g.coordinates] : g.coordinates).map((poly) => poly.map(ring).join("")).join("");
      const svg = $("mapaSwing");
      svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
      let html = "";
      geo.features.forEach((ft) => {
        const k = canonD(ft.properties.dpt);
        const sw = (k in swKey) ? swKey[k] : null;
        const tip = (k in swKey)
          ? `${ft.properties.dpt}: giro ${signo(sw)} (${sw >= 0 ? "derecha" : "izquierda"})`
          : ft.properties.dpt;
        html += `<path d="${path(ft.geometry)}" fill="${_swColor(sw)}" stroke="#FAF9F5" stroke-width="0.7" class="mapa__dpt" data-tip="${tip.replace(/"/g, "")}"/>`;
      });
      svg.innerHTML = html;
      const tipEl = $("swingTip");
      svg.querySelectorAll(".mapa__dpt").forEach((p) => {
        p.addEventListener("mousemove", (e) => {
          const rr = svg.parentElement.getBoundingClientRect();
          tipEl.style.display = "block"; tipEl.textContent = p.dataset.tip;
          tipEl.style.left = (e.clientX - rr.left + 14) + "px";
          tipEl.style.top = (e.clientY - rr.top + 14) + "px";
        });
        p.addEventListener("mouseleave", () => { tipEl.style.display = "none"; });
      });
    } catch (e) { /* mapa opcional */ }

    // tabla por departamento
    const rows = (_deptData.departamentos || []).map((d) => {
      const k = canonD(d.nombre), h2 = r2[k];
      if (!h2) return null;
      const w = h2.petro.p >= h2.rodolfo.p
        ? { n: "Petro", p: h2.petro.p, c: "#8C378C" }
        : { n: "Hernández", p: h2.rodolfo.p, c: "#C8932B" };
      return { nombre: d.nombre, w, lead: d.primero, sw: (k in swKey) ? swKey[k] : 0 };
    }).filter(Boolean).sort((a, b) => b.sw - a.sw);
    const body = $("swingBody");
    body.innerHTML = "";
    rows.forEach((rw) => {
      const tr = document.createElement("tr");
      const cls = rw.sw >= 0 ? "swing__giro--der" : "swing__giro--izq";
      tr.innerHTML = `
        <td class="dept__nom">${rw.nombre}</td>
        <td><div class="dept__lider"><span class="dept__dot" style="background:${rw.w.c}"></span><span>${rw.w.n} ${pct(rw.w.p)}</span></div></td>
        <td><div class="dept__lider"><span class="dept__dot" style="background:${rw.lead.color}"></span><span>${nombreCorto(rw.lead.nombre)} ${pct(rw.lead.pct)}</span></div></td>
        <td class="num ${cls}">${signo(rw.sw)}<div class="swing__dir">${rw.sw >= 0 ? "→ a la derecha" : "← a la izquierda"}</div></td>`;
      body.appendChild(tr);
    });
    $("panelSwing").style.display = "";
  }

  // ====== Explorador: selección múltiple de departamentos y ciudades ======
  const _explSel = { dept: new Set(), ciu: new Set() };
  let _explBuilt = false;

  function _explChips(contId, items, tipo) {
    const cont = $(contId);
    if (!cont) return;
    cont.innerHTML = "";
    items.forEach((name) => {
      const c = document.createElement("span");
      c.className = "expl__chip" + (_explSel[tipo].has(name) ? " is-on" : "");
      c.textContent = name;
      c.addEventListener("click", () => {
        if (_explSel[tipo].has(name)) _explSel[tipo].delete(name);
        else _explSel[tipo].add(name);
        c.classList.toggle("is-on");
        _explRender();
      });
      cont.appendChild(c);
    });
  }

  function pintarExplorar() {
    if (!_deptData || !_ciuData) return;
    const depts = (_deptData.departamentos || []).map((d) => d.nombre);
    const cities = (_ciuData.ciudades || []).map((c) => c.nombre);
    if (!depts.length || !cities.length) return;
    $("panelExplorar").style.display = "";
    if (!_explBuilt) {
      // Sin selección por defecto: el usuario elige los territorios que quiera.
      _explChips("explDeptChips", depts, "dept");
      _explChips("explCiuChips", cities, "ciu");
      document.querySelectorAll(".expl__act").forEach((b) => {
        b.addEventListener("click", () => {
          const t = b.dataset.t, arr = t === "dept" ? depts : cities;
          if (b.dataset.a === "all") arr.forEach((n) => _explSel[t].add(n));
          else _explSel[t].clear();
          _explChips(t === "dept" ? "explDeptChips" : "explCiuChips", arr, t);
          _explRender();
        });
      });
      _explBuilt = true;
    }
    _explRender();
  }

  function _explRender() {
    const body = $("explBody");
    if (!body) return;
    const dmap = {}, cmap = {};
    (_deptData.departamentos || []).forEach((d) => { dmap[d.nombre] = d; });
    (_ciuData.ciudades || []).forEach((c) => { cmap[c.nombre] = c; });
    const rows = [];
    _explSel.dept.forEach((n) => { if (dmap[n]) rows.push({ r: dmap[n], tipo: "Depto." }); });
    _explSel.ciu.forEach((n) => { if (cmap[n]) rows.push({ r: cmap[n], tipo: "Ciudad" }); });
    body.innerHTML = "";
    rows.forEach(({ r, tipo }) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="dept__nom">${r.nombre} <span style="font-size:11px;color:var(--tinta-suave);font-weight:400">${tipo}</span></td>
        <td class="plc">${placeCell(r.primero)}</td>
        <td class="plc">${placeCell(r.segundo)}</td>
        <td class="plc">${placeCell(r.paloma)}</td>
        <td class="num">${partCell(r)}</td>
        <td class="num">${pct(r.mesas_pct)}</td>`;
      body.appendChild(tr);
    });
    $("explNota").textContent = rows.length
      ? rows.length + " territorios seleccionados (" + _explSel.dept.size + " deptos. + " + _explSel.ciu.size + " ciudades)."
      : "Selecciona uno o varios departamentos y ciudades arriba para compararlos.";
  }

  async function cargar() {
    try {
      const r = await fetch("/api/resultados", { cache: "no-store" });
      if (!r.ok) throw new Error("HTTP " + r.status);
      const data = await r.json();
      pintarAviso(data);
      pintarMetricas(data);
      pintarVs(data);
      pintarParticipacion(data);
      pintarCandidatos(data);
      pintarPaloma();
      cargarDepartamentos();
      cargarCiudades();
      _ultimo = data;
      pintarComp(data);
      cargarHistorico2022();
      pintarProyeccion(data);
      pintarAnalisis(data);
      pintarEncuestas(data);
      cargarPolymarket();
      cargarExterior();
      cargarSerie();
    } catch (e) {
      $("avisoTexto").innerHTML =
        `<strong style="color:#B45F44">Sin conexión con el servidor</strong> · ${e.message}`;
    } finally {
      reiniciarCuenta();
    }
  }

  function reiniciarCuenta() {
    cuenta = REFRESCO_SEG;
    $("mCuenta").textContent = cuenta;
  }

  function iniciar() {
    tickReloj();
    setInterval(tickReloj, 1000);

    cargar();
    iniciarControles();

    timerCuenta = setInterval(() => {
      cuenta -= 1;
      if (cuenta <= 0) {
        cargar();
      } else {
        $("mCuenta").textContent = cuenta;
      }
    }, 1000);

    $("btnRefrescar").addEventListener("click", cargar);
  }

  document.addEventListener("DOMContentLoaded", iniciar);
})();
