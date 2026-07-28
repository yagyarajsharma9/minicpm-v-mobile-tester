# MiniCPM-V 4.6 Mobile Tester

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub Repo stars](https://img.shields.io/github/stars/yagyarajsharma9/minicpm-v-mobile-tester.svg)](https://github.com/yagyarajsharma9/minicpm-v-mobile-tester/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/yagyarajsharma9/minicpm-v-mobile-tester.svg)](https://github.com/yagyarajsharma9/minicpm-v-mobile-tester/issues)
[![GitHub forks](https://img.shields.io/github/forks/yagyarajsharma9/minicpm-v-mobile-tester.svg)](https://github.com/yagyarajsharma9/minicpm-v-mobile-tester/network/members)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![Kotlin](https://img.shields.io/badge/Kotlin-Android-brightgreen.svg)](https://kotlinlang.org)
[![Model](https://img.shields.io/badge/Model-MiniCPM--V%204.6-orange.svg)](https://huggingface.co/openbmb/MiniCPM-V-4.6)
[![Windows Only](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](README.md)

> Local testing toolkit for OpenBMB MiniCPM-V 4.6 — a FastAPI web UI and Android APK build research project. Lightweight, open-source, and built to explore what's possible running vision-language models locally and on mobile.

---

## Table of Contents

- [What This Project Is](#what-this-project-is)
- [Quick Start](#quick-start)
- [Features](#features)
- [What We Researched](#what-we-researched)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

---

## What This Project Is

A local testing toolkit for [OpenBMB MiniCPM-V 4.6](https://huggingface.co/openbmb/MiniCPM-V-4.6) with:

- **Python FastAPI web server** — chat, image understanding, video frame sampling, OCR, tool-call demo, and mobile efficiency controls at `http://127.0.0.1:7860`
- **Android app research** — documentation and build scripts for an offline mobile app with llama.cpp JNI, web search, voice input, and image understanding

This is a **research showcase**. The Android source code and APK are not included — anyone can clone, install dependencies, and build their own.

---

## Quick Start

### Prerequisites

- Windows 10/11
- PowerShell 7+
- Python 3.12+ (auto-configured by the setup script)
- Ollama (optional for local model serving)

### Web Server (Recommended)

```powershell
.\run.ps1
```

Then open **http://127.0.0.1:7860**. The mobile PWA is at **http://127.0.0.1:7860/mobile**.

The script will:
1. Create a Python virtual environment at `.venv/` (first run only)
2. Install all Python dependencies from `requirements.txt`
3. Start Ollama automatically if not already running
4. Launch the FastAPI server on `127.0.0.1:7860`

### Android Build (Documentation Only)

The build script and Android project are documented for reference. To build the APK, see the [Android Development Guide](docs/android-development.md).

---

## Features

| Feature | Web Server | Android App |
|---|:---:|:---:|
| Text chat | | |
| Single-image understanding | | |
| Multi-image comparison | | |
| Video frame sampling | | |
| OCR prompt shortcut | | |
| Tool-call demo | | |
| Voice input | | |
| Web search (Tavily, TinyFish) | | |
| Math formula rendering | | KaTeX |
| Compact memory for long chats | | |
| Mobile efficiency controls (16x/4x, slices, frames) | | |
| Multiple image selection with preview | | |
| Image prefill before generation | | |

---

## What We Researched

This project documents key findings while deploying MiniCPM-V 4.6 in resource-constrained environments:

### Context Window
- **8192 tokens** is the sweet spot for mobile — safe increase from the default 4096, while staying well below the full server-side capability
- Do not push above 8192 without real device RAM testing

### Generation Quality
- Default `predict_length` of 192 caused "half answers" — increased to **1024**
- Response token range: **256–1536** tokens

### Math Formula Rendering
- Android ICU regex is stricter than desktop JVM regex — unescaped brackets cause crashes
- KaTeX WebView must be created lazily (only when math is detected)
- Formula normalization converts LaTeX to readable Android text

### Web Search
- Hybrid approach: Tavily (primary) + TinyFish (page content) + Wikipedia/DuckDuckGo (fallback)
- Search context injected into model prompt with source citation support

---

## Project Structure

```
minicpm-v-mobile-tester/
├── README.md                  # This file
├── AGENTS.md                  # Agent instructions
├── LICENSE                    # MIT License
├── CONTRIBUTING.md            # How to contribute
├── SECURITY.md                # Security policy
├── app.py                     # FastAPI web server (single file)
├── requirements.txt           # Python dependencies
├── .gitignore                 # Excludes APK, vendor, .venv, logs
├── run.ps1                    # Start web server
├── run_controller.py          # Desktop vibration controller
├── run_controller.ps1         # Controller helper script
├── build_android.ps1          # Android build script (documentation)
├── test_response_quality.ps1  # Android quality self-test
├── test_memory_compaction.ps1 # Android memory self-test
├── mobile_app/                # PWA mobile shell
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   ├── manifest.webmanifest
│   ├── sw.js
│   └── icon.svg
├── static/                    # Web UI assets
│   ├── index.html
│   ├── app.js
│   └── styles.css
└── docs/                      # Research and documentation
    ├── architecture.md
    ├── android-development.md
    ├── research-findings.md
    └── api-reference.md
```

---

## API Reference

### `POST /api/chat`
Main chat endpoint with text prompts, image/video attachments, and generation options.

**Request:**
```json
{
  "provider": "transformers",
  "model": "openbmb/MiniCPM-V-4.6",
  "prompt": "Describe this image.",
  "attachments": [],
  "options": {
    "temperature": 0.2,
    "top_p": 0.9,
    "max_tokens": 512,
    "downsample_mode": "16x",
    "max_slice_nums": 36,
    "max_num_frames": 16
  }
}
```

**Response:**
```json
{
  "content": "The image shows...",
  "provider": "transformers",
  "model": "openbmb/MiniCPM-V-4.6",
  "elapsed_ms": 3420,
  "tool_calls": [],
  "usage": null
}
```

Full API details: [docs/api-reference.md](docs/api-reference.md).

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Areas for Contribution
- Additional LLM provider support
- Mobile UI improvements
- New self-test scripts
- Android feature expansion
- Documentation and examples

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Important Notes

- **No APK in this repo** — the debug APK with bundled model files is ~1.6 GB and excluded to keep this repo lightweight
- **No API keys** — web search API keys are configured locally via `local.properties`, not in source code
- **Windows only** — builds and scripts require PowerShell on Windows
- **Research showcase** — this repo demonstrates what was researched and built, not a distributable application