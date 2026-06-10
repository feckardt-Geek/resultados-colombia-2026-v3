#!/bin/bash
# Publicacion INICIAL en GitHub Pages (ejecutar UNA vez, despues de 'gh auth login').
set -e
cd "$(dirname "$0")/publicar"

USER=$(gh api user --jq .login)
REPO="resultados-colombia-2026"
echo "Usuario GitHub: $USER"

git branch -M main
# Crear el repositorio publico y subir el contenido
gh repo create "$REPO" --public --source=. --remote=origin --push

# Habilitar GitHub Pages (rama main, carpeta raiz)
echo '{"source":{"branch":"main","path":"/"}}' | gh api -X POST "repos/$USER/$REPO/pages" --input - \
  || echo '{"source":{"branch":"main","path":"/"}}' | gh api -X PUT "repos/$USER/$REPO/pages" --input - \
  || true

echo ""
echo "============================================================"
echo "  Pagina publicada. Enlace para tus amigos (en ~1-2 min):"
echo "  https://$USER.github.io/$REPO/"
echo "============================================================"
