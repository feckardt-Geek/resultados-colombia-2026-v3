# ============================================================================
#  Actualiza el dashboard con los datos mas recientes de la Registraduria
#  y lo publica en GitHub Pages.
#
#  Uso:   .\publicar.ps1     (en PowerShell, dentro de la carpeta del repo)
#  Requiere: web/index.html presente y Python instalado (comando 'python').
# ============================================================================
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# URL del proxy de IA (Cloudflare Worker): necesaria para que el chat funcione
# en la version publica. Es una URL publica, NO es un secreto.
if (-not $env:IA_PROXY_URL) {
    $env:IA_PROXY_URL = "https://elecciones-ia.federicoeckardt.workers.dev"
}

Write-Host "1/3  Generando el dashboard con datos frescos de la Registraduria..." -ForegroundColor Cyan
python build_html.py

Write-Host "2/3  Publicando como index.html..." -ForegroundColor Cyan
Copy-Item -Force "Resultados_Elecciones_Colombia_2026.html" "index.html"

Write-Host "3/3  Subiendo a GitHub..." -ForegroundColor Cyan
git add -A
if (git status --porcelain) {
    git commit -m "Actualizar boletin $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    git push origin main
    Write-Host "Listo. La pagina se actualiza en ~1 min:" -ForegroundColor Green
    Write-Host "  https://feckardt-geek.github.io/resultados-colombia-2026-v3/"
} else {
    Write-Host "Sin cambios (el boletin no cambio)." -ForegroundColor Yellow
}
