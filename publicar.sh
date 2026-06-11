#!/usr/bin/env bash
# ============================================================================
#  Actualiza el dashboard con los datos mas recientes de la Registraduria
#  y lo publica en GitHub Pages.
#
#  Uso (Mac / Linux):   ./publicar.sh        (requiere python3 y git)
#  En Windows usa el equivalente:            .\publicar.ps1
# ============================================================================
set -e
cd "$(dirname "$0")"

# URL del proxy de IA (Cloudflare Worker): necesaria para que el chat funcione
# en la version publica. Es una URL publica, NO es un secreto.
: "${IA_PROXY_URL:=https://elecciones-ia.federicoeckardt.workers.dev}"
export IA_PROXY_URL

echo "1/3  Generando el dashboard con datos frescos de la Registraduria..."
python3 build_html.py

echo "2/3  Publicando como index.html..."
cp Resultados_Elecciones_Colombia_2026.html index.html

echo "3/3  Subiendo a GitHub..."
git add -A
if git diff --cached --quiet; then
  echo "Sin cambios (el boletin no cambio)."
else
  git commit -m "Actualizar boletin $(date '+%Y-%m-%d %H:%M')"
  git push origin main
  echo "Listo. La pagina se actualiza en ~1 min:"
  echo "  https://feckardt-geek.github.io/resultados-colombia-2026-v3/"
fi
