$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
  python -m venv .venv
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}

.\.venv\Scripts\python.exe -m pip show pyserial *> $null
if ($LASTEXITCODE -ne 0) {
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}

.\.venv\Scripts\python.exe .\run_controller.py @args
exit $LASTEXITCODE
