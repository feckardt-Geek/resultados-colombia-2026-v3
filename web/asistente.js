/* Asistente IA + Compartir — Dashboard Elecciones Colombia 2026
   Módulo independiente: NO toca la lógica de app.js.
   - Botón "Compartir" (menú nativo en celular, copiar enlace en PC).
   - Chat con IA (Google Gemini) inyectado al pie de cada panel, con el
     contexto de los datos visibles en ese panel.
   El endpoint se resuelve solo:
     · localhost           -> /api/chat   (lo atiende server.py)
     · link público/file   -> window.IA_PROXY_URL (Cloudflare Worker) */
(function () {
  "use strict";

  // ---- Endpoint de la IA --------------------------------------------------
  var ES_LOCAL = /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname);
  var IA_URL = ES_LOCAL ? "/api/chat" : (window.IA_PROXY_URL || "");

  var $ = function (id) { return document.getElementById(id); };

  // ---- Toast (aviso flotante) ---------------------------------------------
  function toast(msg) {
    var t = document.createElement("div");
    t.className = "ia-toast";
    t.textContent = msg;
    document.body.appendChild(t);
    requestAnimationFrame(function () { t.classList.add("ia-toast--on"); });
    setTimeout(function () {
      t.classList.remove("ia-toast--on");
      setTimeout(function () { t.remove(); }, 300);
    }, 2200);
  }

  // ---- Compartir ----------------------------------------------------------
  function compartir() {
    var datos = {
      title: document.title,
      text: "Resultados Elecciones Presidenciales · Colombia 2026",
      url: location.href
    };
    if (navigator.share) {
      navigator.share(datos).catch(function () {});
      return;
    }
    var url = location.href;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(
        function () { toast("Enlace copiado ✓"); },
        function () { prompt("Copia el enlace:", url); }
      );
    } else {
      prompt("Copia el enlace:", url);
    }
  }

  function montarCompartir() {
    var btn = $("btnCompartir");
    if (btn) { btn.addEventListener("click", compartir); }
  }

  // ---- Botón Actualizar (reusa el refresco del tablero) -------------------
  function montarActualizar() {
    var btn = $("btnActualizarTop");
    if (!btn) return;
    btn.addEventListener("click", function () {
      btn.classList.add("is-loading");
      var refr = $("btnRefrescar");            // botón de refresco de app.js
      if (refr) { refr.click(); }
      toast("Actualizando datos…");
      setTimeout(function () { btn.classList.remove("is-loading"); }, 1800);
    });
  }

  // ---- Contexto que se le manda a la IA -----------------------------------
  function resumenGlobal() {
    function g(id) { var e = $(id); return e ? e.textContent.trim() : ""; }
    return "Boletín " + g("boletinNum") +
      " · Mesas informadas: " + g("mMesasPct") +
      " · Votos: " + g("mVotos") +
      " · Líder: " + g("mLider") + " (" + g("mLiderPct") + ").";
  }

  function contextoPanel(panel) {
    var partes = [];
    var hijos = panel.children;
    for (var i = 0; i < hijos.length; i++) {
      var el = hijos[i];
      if (el.classList && el.classList.contains("ia-box")) continue;
      var txt = (el.innerText || "").trim();
      if (txt) partes.push(txt);
    }
    return partes.join("\n").replace(/\n{3,}/g, "\n\n").trim().slice(0, 3500);
  }

  function tituloPanel(panel) {
    var h = panel.querySelector("h2");
    return h ? h.textContent.trim() : "Panel";
  }

  // ---- Llamada a la IA ----------------------------------------------------
  function preguntar(panel, pregunta) {
    var cuerpo = {
      question: pregunta,
      panel: tituloPanel(panel),
      context: "RESUMEN NACIONAL: " + resumenGlobal() +
               "\n\nDATOS DE ESTE PANEL:\n" + contextoPanel(panel)
    };
    return fetch(IA_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cuerpo)
    }).then(function (r) { return r.json(); });
  }

  // ---- Caja de chat por panel ---------------------------------------------
  function nuevaBurbuja(log, quien, texto) {
    var b = document.createElement("div");
    b.className = "ia-msg ia-msg--" + quien;
    b.textContent = texto;
    log.appendChild(b);
    log.scrollTop = log.scrollHeight;
    return b;
  }

  function montarCajaIA(panel) {
    if (panel.querySelector(".ia-box")) return;       // evita duplicados

    var box = document.createElement("div");
    box.className = "ia-box";

    var toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "ia-toggle";
    toggle.innerHTML = '<span class="ia-toggle__ico">✦</span> Preguntar a la IA sobre este panel';

    var panelIA = document.createElement("div");
    panelIA.className = "ia-panel";
    panelIA.hidden = true;

    var log = document.createElement("div");
    log.className = "ia-log";

    var form = document.createElement("form");
    form.className = "ia-form";
    var input = document.createElement("input");
    input.className = "ia-input";
    input.type = "text";
    input.placeholder = "Escribe tu pregunta sobre estos datos…";
    input.autocomplete = "off";
    var send = document.createElement("button");
    send.className = "ia-send";
    send.type = "submit";
    send.textContent = "Enviar";
    form.appendChild(input);
    form.appendChild(send);

    // Sugerencias rápidas
    var sug = document.createElement("div");
    sug.className = "ia-sug";
    ["Explícame este panel en palabras simples",
     "¿Qué significa esto para la segunda vuelta?"].forEach(function (s) {
      var chip = document.createElement("button");
      chip.type = "button";
      chip.className = "ia-chip";
      chip.textContent = s;
      chip.addEventListener("click", function () { enviar(s); });
      sug.appendChild(chip);
    });

    panelIA.appendChild(log);
    panelIA.appendChild(form);
    panelIA.appendChild(sug);
    box.appendChild(toggle);
    box.appendChild(panelIA);
    panel.appendChild(box);

    var ocupado = false;
    function enviar(texto) {
      texto = (texto || input.value || "").trim();
      if (!texto || ocupado) return;
      if (!IA_URL) {
        nuevaBurbuja(log, "ia", "El asistente todavía no está configurado en esta versión. " +
          (ES_LOCAL ? "Define GEMINI_API_KEY y reinicia el servidor." :
                      "Falta conectar el proxy de IA (window.IA_PROXY_URL)."));
        return;
      }
      ocupado = true;
      input.value = "";
      nuevaBurbuja(log, "yo", texto);
      var pensando = nuevaBurbuja(log, "ia", "Pensando…");
      pensando.classList.add("ia-msg--load");
      preguntar(panel, texto).then(function (res) {
        pensando.remove();
        if (res && res.ok && res.answer) {
          nuevaBurbuja(log, "ia", res.answer);
        } else {
          nuevaBurbuja(log, "ia", "No pude responder ahora mismo" +
            (res && res.error ? " (" + res.error + ")" : "") + ".");
        }
      }).catch(function () {
        pensando.remove();
        nuevaBurbuja(log, "ia", "No se pudo conectar con la IA. Revisa la conexión e inténtalo de nuevo.");
      }).then(function () { ocupado = false; input.focus(); });
    }

    toggle.addEventListener("click", function () {
      var abrir = panelIA.hidden;
      panelIA.hidden = !abrir;
      toggle.classList.toggle("ia-toggle--on", abrir);
      if (abrir) {
        if (!log.childElementCount) {
          nuevaBurbuja(log, "ia", "Hola 👋 Pregúntame lo que quieras sobre «" +
            tituloPanel(panel) + "». Respondo con los datos de este panel.");
        }
        input.focus();
      }
    });
    form.addEventListener("submit", function (e) { e.preventDefault(); enviar(); });
  }

  function montarCajasIA() {
    var paneles = document.querySelectorAll("section.panel");
    for (var i = 0; i < paneles.length; i++) montarCajaIA(paneles[i]);
  }

  function iniciar() {
    montarCompartir();
    montarActualizar();
    // app.js arma su contenido en DOMContentLoaded; montamos al final de la cola.
    setTimeout(montarCajasIA, 0);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
