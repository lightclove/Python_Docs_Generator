# Загрузка документации Python с docs.python.org

$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot
pip install beautifulsoup4 -q 2>$null
python scripts/fetch_python_docs.py
