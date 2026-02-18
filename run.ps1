# Полный цикл: загрузка + перевод + PDF
# Запуск: .\run.ps1

$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

pip install beautifulsoup4 reportlab deep-translator -q 2>$null

Write-Host "=== 1. Загрузка с docs.python.org ===" -ForegroundColor Cyan
python fetch_python_docs.py
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host ""
Write-Host "=== 2. Перевод EN -> RU ===" -ForegroundColor Cyan
python translate_python_docs.py
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host ""
Write-Host "=== 3. Конвертация MD -> PDF ===" -ForegroundColor Cyan
python batch_md_to_pdf.py
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host ""
Write-Host "Done." -ForegroundColor Green
