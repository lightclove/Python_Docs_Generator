# Запуск перевода документации Python в отдельном терминале
# Не блокирует основную разработку

$ProjectRoot = $PSScriptRoot
$cmd = "cd '$ProjectRoot'; pip install deep-translator -q 2>`$null; python scripts/translate_python_docs.py; pause"

Write-Host "Запуск перевода в новом окне..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd
