@echo off
cd /d "%~dp0"
python -m pip install -r backend\requirements.txt
if not exist frontend\node_modules call npm install --prefix frontend
call npm run build --prefix frontend
python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8765
