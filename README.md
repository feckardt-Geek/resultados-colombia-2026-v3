# Resultados Elecciones Presidenciales · Colombia 2026

Dashboard de la **primera vuelta presidencial de Colombia 2026** (De la Espriella vs. Cepeda):
resultados por departamento, ciudad y exterior, con explorador de selección múltiple,
mapa de giro, comparativo histórico **2022 → 2026**, panel **escrutinio vs. preconteo**
y un asistente IA por panel.

**Demo (GitHub Pages):** `https://feckardt-geek.github.io/resultados-colombia-2026-v3/`
*(si Pages está habilitado en Settings → Pages, sirviendo `index.html` desde la raíz).*

> ℹ️ **Repo unificado (Opción A).** Este repositorio reúne el proyecto completo:
> el **código fuente** (generador + servidor local + datos) y el **dashboard publicado**
> (`index.html`). Antes el proyecto estaba dividido en dos repos:
> - `elecciones-colombia-2026` (privado) → la fuente: scripts, datos y análisis.
> - `resultados-colombia-2026-v3` (público) → la salida: solo `index.html`.
>
> La integración del código fuente se hace con los pasos de la sección
> [**Fusión de los dos repos**](#fusión-de-los-dos-repos-opción-a).

---

## Arquitectura

El mismo `index.html` funciona en **dos modos**, que se resuelven solos según dónde se abra:

| | Local (desarrollo) | Público (GitHub Pages / archivo) |
|---|---|---|
| **Datos** | `fetch('/api/resultados')` en vivo, servido por `server.py` | datos incrustados en `window.__SNAP__` por `build_html.py` |
| **Asistente IA** | `/api/chat` → `server.py` (usa `GEMINI_API_KEY`) | Cloudflare Worker (`window.IA_PROXY_URL`) |

- **Fuente de datos:** preconteo oficial de la Registraduría Nacional del Estado Civil.
- **Análisis:** comparativo histórico **2022 → 2026** y proyección a segunda vuelta.
- **Seguridad:** la clave de Gemini vive en el Worker / variable de entorno local;
  **nunca** se incrusta en el `index.html` publicado.

## Estructura (objetivo tras la fusión)

> Los archivos de código provienen del repo `elecciones-colombia-2026`; los nombres
> exactos pueden variar ligeramente. Lo confirmado por el propio `index.html` está marcado ✅.

```
.
├── index.html        ✅ Dashboard autónomo PUBLICADO (lo sirve GitHub Pages). Generado por build_html.py
├── build_html.py     ✅ Genera index.html incrustando el snapshot de datos (window.__SNAP__)
├── server.py         ✅ Servidor local: /api/resultados (preconteo en vivo) y /api/chat (Gemini)
├── app.js            ✅ Lógica del tablero (se inlinea en index.html al construir)
├── data/                Boletines de la Registraduría + datos 2022 para el comparativo
├── requirements.txt     Dependencias de Python
├── .gitignore           Protege secretos (.env, *.key) y artefactos de Python
└── README.md
```

## Uso

**Ver el dashboard publicado:** abre la demo de GitHub Pages, o el `index.html` directamente.

**Desarrollo local** (datos en vivo + IA):

```bash
export GEMINI_API_KEY="tu_clave"   # necesaria para /api/chat
python3 server.py                  # levanta el servidor local
# abre http://localhost:<puerto>   (ver el puerto que imprime server.py)
```

**Regenerar el HTML publicado tras un nuevo boletín:**

```bash
python3 build_html.py              # reescribe index.html con el snapshot actual
git add index.html
git commit -m "Actualizar boletín"
git push                           # GitHub Pages redepliega solo
```

## Despliegue (GitHub Pages)

GitHub Pages sirve **`index.html` desde la raíz** de la rama de publicación.
**No muevas `index.html` de la raíz** o se rompe la URL publicada. En público, el
asistente IA pasa por el Cloudflare Worker (`IA_PROXY_URL`); la clave de Gemini no
viaja al navegador.

## Fusión de los dos repos (Opción A)

Este repo (público) es la **base**. Falta traerle el código fuente que vive en
`elecciones-colombia-2026` (privado). Como el `index.html` ya se generaba **junto a**
`build_html.py`, la fusión se hace en la **raíz**, sin reorganizar carpetas.

Los comandos exactos (que preservan el historial del repo privado) se entregaron en el
hilo de trabajo; en resumen: añadir el repo privado como remoto, hacer
`git merge --allow-unrelated-histories`, conservar **este** `README.md`/`index.html`
ante conflictos, y volver a publicar. Una vez integrado, el repo privado puede
archivarse.
