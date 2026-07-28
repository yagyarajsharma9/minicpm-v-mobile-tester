$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
  if (Test-Path "$env:APPDATA\uv\python\cpython-3.12.12-windows-x86_64-none\python.exe") {
    & "$env:APPDATA\uv\python\cpython-3.12.12-windows-x86_64-none\python.exe" -m venv .venv
  } else {
    python -m venv .venv
  }
}

.\.venv\Scripts\python.exe -m pip install -r requirements.txt

try {
  Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 | Out-Null
} catch {
  Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
  Start-Sleep -Seconds 3
}

.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 7860
