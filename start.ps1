$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python -m pip install -r "backend\requirements.txt"
if (-not (Test-Path "frontend\node_modules")) {
  npm install --prefix frontend
}
npm run build --prefix frontend
python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8765
