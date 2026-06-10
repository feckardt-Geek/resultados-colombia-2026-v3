#!/bin/bash
# Actualiza los datos y republica la pagina (GitHub Pages).
# Uso:  ./publicar.sh
set -e
cd "$(dirname "$0")"

echo "1/3  Consultando datos oficiales y regenerando el HTML..."
python3 build_html.py

echo "2/3  Copiando a la carpeta de publicacion..."
cp Resultados_Elecciones_Colombia_2026.html publicar/index.html

echo "3/3  Publicando en GitHub Pages..."
cd publicar
git add -A
git commit -q -m "Actualizar resultados $(date '+%Y-%m-%d %H:%M')" || { echo "Sin cambios nuevos."; exit 0; }
git push -q origin main
echo "Listo. La pagina se actualiza en internet en ~1 minuto."
