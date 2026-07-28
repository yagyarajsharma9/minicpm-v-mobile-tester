# AGENTS.md

## Project

This is a lightweight showcase of the MiniCPM-V 4.6 Mobile Tester research and implementation.

- **Python FastAPI web server** (`app.py`) — local UI at http://127.0.0.1:7860, chat, image/video understanding, tool-call demo, mobile PWA shell.
- **Android APK build** — defined in `build_android.ps1`, but Android source code and the APK are not included in this repo. Anyone can regenerate them.

## Quick Start (Python Web Server)

```powershell
.\run.ps1          # creates .venv, installs deps, starts Ollama if needed, runs uvicorn on :7860
```
Open http://127.0.0.1:7860. The mobile PWA is at http://127.0.0.1:7860/mobile.
- Web server code: `app.py` — single file, FastAPI backend.
- Static files served from `static/` (web) and `mobile_app/` (PWA shell).
- Three LLM providers: `transformers` (default, local), `ollama`, `openai`-compatible.

## Android Build (not included in this showcase)

The Android build script (`build_android.ps1`) uses `subst M:` drive mapping and sets `JAVA_HOME`/`ANDROID_HOME`/`GRADLE_USER_HOME` for Windows PowerShell. The full Android source (Kotlin + llama.cpp JNI) lives in the original repository under `vendor/MiniCPM-V-Apps/MiniCPM-V-demo-Android/`.

To build the APK, clone the original repository and run `.\build_android.ps1` from its root.

## Key File Locations (this showcase repo)

| Purpose | Path |
|---|---|
| Web server | `app.py` |
| Web UI | `static/` (index.html, app.js, styles.css) |
| Mobile PWA shell | `mobile_app/` (index.html, app.js, styles.css, manifest, sw.js) |
| Build script | `build_android.ps1` |
| Start script | `run.ps1` |
| Controller tool | `run_controller.py` + `run_controller.ps1` |
| Self-tests | `test_response_quality.ps1`, `test_memory_compaction.ps1` |
| Dependencies | `requirements.txt` |
| Documentation | `docs/` (architecture, android-development, research-findings, api-reference) |

## Environment & Toolchain

- **Windows only** — PowerShell, COM serial ports, XInput, `subst` drive mapping.
- Python venv auto-created at `.venv/` by `run.ps1`/`run_controller.ps1`.
- Model: `openbmb/MiniCPM-V-4.6` (GGUF Q4_K_M), 8192 context tokens for mobile.
- Ollama runs outside the venv; `run.ps1` auto-starts it if not detected on port 11434.
- The Android project under `vendor/` has its own `AGENTS.md` in `vendor/MiniCPM-V-Apps/llama.cpp/` with upstream contribution policy.

## What This Project Is Not

- No CI, lint, typecheck, or formatter configured.
- No `opencode.json` at the repo root.
- The Python side (`app.py`) is a tester/prototype — the Android project is where active mobile development happens.