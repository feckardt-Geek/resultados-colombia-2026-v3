# 🤖 Asistente IA por panel — cómo funciona y cómo activarlo

El dashboard tiene un **chat de IA al pie de cada panel** (Google Gemini) que
responde preguntas usando los datos visibles de ese panel. También un botón
**Compartir** en el encabezado.

La API key de Gemini **nunca** viaja al navegador: vive en un servidor.

| Dónde | Quién atiende el chat | Estado |
|---|---|---|
| **Local** (`python server.py`) | `server.py` con tu `.env` | ✅ listo |
| **Link público** (GitHub Pages) | Cloudflare Worker (`worker.js`) | requiere desplegar 1 vez |

---

## 1) Local — ya funciona

Crea un archivo `.env` en la carpeta del proyecto (NO se sube a GitHub):

```
GEMINI_API_KEY=tu_llave_de_google_ai_studio
GEMINI_MODEL=gemini-flash-latest
```

> Tu llave de Gemini se saca gratis en https://aistudio.google.com/apikey

Arranca el servidor y listo:

```powershell
python server.py        # http://localhost:8000
```

---

## 2) Link público — desplegar el Worker (gratis, ~5 min)

Las páginas de GitHub Pages son estáticas (sin servidor), así que el chat
necesita un mini-proxy. Usamos **Cloudflare Workers** (plan gratis: 100.000
peticiones/día).

1. Crea una cuenta gratis en **https://dash.cloudflare.com**
2. Menú **Workers & Pages → Create → Create Worker**. Ponle un nombre
   (ej. `elecciones-ia`) y **Deploy**.
3. **Edit code**: borra el ejemplo y pega el contenido de [`worker.js`](worker.js).
   **Deploy**.
4. **Settings → Variables and Secrets → Add**:
   - `GEMINI_API_KEY` = tu llave de Gemini → tipo **Secret** → Save
   - `GEMINI_MODEL` = `gemini-flash-latest` (opcional, tipo Text)
5. Copia la URL del Worker (algo como `https://elecciones-ia.TU-USUARIO.workers.dev`).

### Reconstruir las páginas con esa URL

```powershell
$env:IA_PROXY_URL = "https://elecciones-ia.TU-USUARIO.workers.dev"
python build_html.py        # base
python _build_ver3.py       # versión 3 (la más completa)
```

Luego publica como siempre (Git Bash):

```bash
./publicar3.sh
```

Desde ese momento el chat funciona también en el enlace que compartes por
WhatsApp. Si reconstruyes **sin** `IA_PROXY_URL`, el chat sigue en local pero en
público mostrará "falta conectar el proxy" (no rompe nada).

---

## Notas

- **Modelo gratis:** `gemini-flash-latest` siempre apunta al Gemini Flash vigente
  (evita que se rompa cuando Google cambia de versión).
- **Anti-abuso (opcional):** en `worker.js`, la constante `ORIGENES_PERMITIDOS`
  permite limitar qué webs pueden usar tu Worker. Ej.:
  `["https://feckardt-geek.github.io"]`.
- **Costo:** el tier gratis de Gemini + el de Cloudflare alcanzan de sobra para
  uso normal. Cero costo esperado.
