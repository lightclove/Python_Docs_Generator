# Пакетная конвертация MD в PDF

$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot
pip install reportlab -q 2>$null
python scripts/batch_md_to_pdf.py
