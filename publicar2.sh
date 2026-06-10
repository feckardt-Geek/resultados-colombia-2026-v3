#!/bin/bash
# Actualiza y republica la v2.0 (con comparativo 2022 vs 2026).
# Uso:  ./publicar2.sh
set -e
cd "$(dirname "$0")"
echo "1/3  Regenerando HTML con datos frescos..."
python3 build_html.py
echo "2/3  Copiando a publicar2..."
cp Resultados_Elecciones_Colombia_2026.html publicar2/index.html
echo "3/3  Publicando v2.0..."
cd publicar2
git add -A
git commit -q -m "Actualizar v2.0 $(date '+%Y-%m-%d %H:%M')" || { echo "Sin cambios."; exit 0; }
git push -q origin main
echo "Listo: https://feckardt-geek.github.io/resultados-colombia-2026-v2/ (se actualiza en ~1 min)"
