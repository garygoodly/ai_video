Set-Location (Join-Path $PSScriptRoot "..")
& .\.venv\Scripts\Activate.ps1
python .\main.py *>> .\workspace\daily.log
