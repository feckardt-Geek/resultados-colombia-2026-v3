#!/bin/bash
# Actualiza y republica la v3.0 (con explorador de seleccion multiple).
# Uso:  ./publicar3.sh
set -e
cd "$(dirname "$0")"
echo "1/3  Regenerando HTML con datos frescos..."
python3 build_html.py
echo "2/3  Copiando a publicar3..."
cp Resultados_Elecciones_Colombia_2026.html publicar3/index.html
echo "3/3  Publicando v3.0..."
cd publicar3
git add -A
git commit -q -m "Actualizar v3.0 $(date '+%Y-%m-%d %H:%M')" || { echo "Sin cambios."; exit 0; }
git push -q origin main
echo "Listo: https://feckardt-geek.github.io/resultados-colombia-2026-v3/ (se actualiza en ~1 min)"
