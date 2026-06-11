# Resultados Elecciones Presidenciales · Colombia 2026

Dashboard de la **primera vuelta presidencial de Colombia 2026** (De la Espriella vs. Cepeda):
resultados por departamento, ciudad y exterior, con explorador de selección múltiple,
mapa de giro, comparativo histórico **2022 → 2026**, panel **escrutinio vs. preconteo**
y un asistente IA por panel.

**Demo (GitHub Pages):** https://feckardt-geek.github.io/resultados-colombia-2026-v3/

Este repositorio reúne **todo el proyecto**: el código fuente (generador + servidor
local + datos) y el dashboard publicado (`index.html`).

## Arquitectura

El mismo dashboard funciona en **dos modos**, que se resuelven solos según dónde se abra:

| | Local (desarrollo) | Público (GitHub Pages) |
|---|---|---|
| **Datos** | `fetch('/api/...')` en vivo, servido por `server.py` | datos incrustados por `build_html.py` (`window.__SNAP__`) |
| **Asistente IA** | `/api/chat` → `server.py` (lee `GEMINI_API_KEY` del `.env`) | Cloudflare Worker (`worker.js`, vía `IA_PROXY_URL`) |

- **Fuente de datos:** preconteo oficial de la Registraduría Nacional del Estado Civil.
- **La clave de Gemini nunca se versiona:** vive en `.env` (local) o como *Secret* del Worker.

## Estructura

```
.
├── index.html        Dashboard PUBLICADO (lo sirve GitHub Pages). Generado por build_html.py.
├── build_html.py     Genera el dashboard incrustando los datos (lee de web/).
├── server.py         Servidor local: sirve web/ + /api/resultados, /api/chat (Gemini), etc.
├── publicar.ps1      Atajo para publicar en Windows (PowerShell).
├── publicar.sh       Atajo para publicar en Mac / Linux (bash/zsh).
├── make_pdf.py       Genera el informe PDF (marca EDFO).
├── make_swing_img.py Genera la imagen del mapa de giro 2022→2026.
├── worker.js         Cloudflare Worker: proxy a Gemini para el chat en la web pública.
├── web/              Fuente del tablero: index.html, styles.css, app.js, asistente.*, escrutinio.js, geojson.
├── data/             Histórico 2022 + serie de boletines.
├── IA_SETUP.md       Cómo activar el asistente IA (local y público).
└── ENLACES_Y_VERSIONES.txt   Enlaces, versiones y registro de cambios.
```

## Actualizar el dashboard (p. ej. la 2.ª vuelta del 21 de junio)

**Forma rápida** (consulta el feed oficial, regenera `index.html` y lo sube; Pages
se actualiza en ~1 min y el enlace no cambia):
- **Mac / Linux:** `./publicar.sh`
- **Windows (PowerShell):** `.\publicar.ps1`

**Manual / multiplataforma:**
```bash
export IA_PROXY_URL="https://elecciones-ia.federicoeckardt.workers.dev"   # Windows: $env:IA_PROXY_URL="..."
python build_html.py
cp Resultados_Elecciones_Colombia_2026.html index.html                   # Windows: Copy-Item -Force ...
git add -A && git commit -m "Actualizar boletín" && git push origin main
```

## Desarrollo local (datos en vivo + IA)

```bash
# Crea un .env con GEMINI_API_KEY=tu_clave   (no se sube; está en .gitignore)
python server.py        # http://localhost:8000
```
Ver `IA_SETUP.md` para el detalle del asistente IA y el despliegue del Worker.

## Despliegue (GitHub Pages)

GitHub Pages sirve **`index.html` desde la raíz** — no lo muevas de ahí o se rompe la
URL publicada. En público, el chat pasa por el Cloudflare Worker; la clave de Gemini
no viaja al navegador.
