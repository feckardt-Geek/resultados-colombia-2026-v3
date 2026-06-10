/* ============================================================================
   Cloudflare Worker — Proxy a Google Gemini para el asistente del dashboard.

   ¿Para qué? Las versiones publicadas en GitHub Pages son HTML estático (sin
   servidor), así que no pueden guardar la API key de Gemini. Este Worker la
   guarda como SECRETO y responde a las preguntas del chat. El HTML público lo
   llama vía window.IA_PROXY_URL.

   CÓMO DESPLEGARLO (gratis, ~5 min) — ver IA_SETUP.md para el paso a paso:
     1. Cuenta gratis en https://dash.cloudflare.com  → Workers & Pages → Create
     2. Pega este archivo como código del Worker.
     3. Settings → Variables and Secrets:
          GEMINI_API_KEY = (tu llave de Google AI Studio)   [tipo: Secret]
          GEMINI_MODEL   = gemini-flash-latest               [opcional]
     4. Deploy. Copia la URL (https://<algo>.workers.dev) y pásala al build:
          IA_PROXY_URL="https://<algo>.workers.dev" python build_html.py
   ============================================================================ */

const SYSTEM = (
  "Eres un asistente experto que ayuda a entender el tablero de resultados de " +
  "las elecciones presidenciales de Colombia 2026. Responde SIEMPRE en español, " +
  "de forma breve, clara y neutral. Básate ÚNICAMENTE en los datos del CONTEXTO " +
  "que se te entrega (son datos reales del tablero). Si la respuesta no está en " +
  "el contexto, dilo con honestidad y no inventes cifras. No des recomendaciones " +
  "de voto ni opiniones partidistas; limítate a explicar los datos."
);

// Limita qué webs pueden usar tu Worker (anti-abuso). Vacío = cualquiera.
const ORIGENES_PERMITIDOS = ["https://feckardt-geek.github.io"];

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const permitido = ORIGENES_PERMITIDOS.length === 0 ||
                      ORIGENES_PERMITIDOS.some((o) => origin.startsWith(o));
    const cors = {
      "Access-Control-Allow-Origin": permitido && origin ? origin : "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    };

    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    if (request.method !== "POST") return j({ ok: false, error: "Usa POST" }, 405, cors);
    if (!permitido) return j({ ok: false, error: "Origen no permitido" }, 403, cors);

    let body;
    try { body = await request.json(); }
    catch { return j({ ok: false, error: "JSON inválido" }, 400, cors); }

    const pregunta = String(body.question || "").slice(0, 600).trim();
    const panel = String(body.panel || "Panel").slice(0, 120);
    const contexto = String(body.context || "").slice(0, 6000);
    if (!pregunta) return j({ ok: false, error: "Pregunta vacía" }, 400, cors);
    if (!env.GEMINI_API_KEY) return j({ ok: false, error: "Falta GEMINI_API_KEY en el Worker" }, 500, cors);

    const model = env.GEMINI_MODEL || "gemini-flash-latest";
    const url = "https://generativelanguage.googleapis.com/v1beta/models/" +
                model + ":generateContent?key=" + env.GEMINI_API_KEY;
    const payload = {
      systemInstruction: { parts: [{ text: SYSTEM }] },
      contents: [{ role: "user", parts: [{
        text: "PANEL: " + panel + "\n\n" + contexto + "\n\nPREGUNTA DEL USUARIO: " + pregunta
      }] }],
      // thinkingBudget:0 desactiva el "razonamiento" del modelo: si no, esos
      // tokens consumen el presupuesto y la respuesta sale truncada (MAX_TOKENS).
      generationConfig: { temperature: 0.3, maxOutputTokens: 1200, thinkingConfig: { thinkingBudget: 0 } },
    };

    try {
      const r = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await r.json();
      if (!r.ok) {
        const msg = (data && data.error && data.error.message) || ("HTTP " + r.status);
        return j({ ok: false, error: "Gemini " + r.status + ": " + msg }, 502, cors);
      }
      const cand = (data.candidates && data.candidates[0]) || {};
      const partes = (cand.content && cand.content.parts) || [];
      const texto = partes.map((p) => p.text || "").join("").trim();
      if (!texto) return j({ ok: false, error: "Respuesta vacía del modelo" }, 502, cors);
      return j({ ok: true, answer: texto }, 200, cors);
    } catch (e) {
      return j({ ok: false, error: String(e) }, 502, cors);
    }
  },
};

function j(obj, status, cors) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: Object.assign({ "Content-Type": "application/json; charset=utf-8" }, cors),
  });
}
