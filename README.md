# MiniCPM-V 4.6 Mobile Tester

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub Repo stars](https://img.shields.io/github/stars/yagyarajsharma9/minicpm-v-mobile-tester.svg)](https://github.com/yagyarajsharma9/minicpm-v-mobile-tester/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/yagyarajsharma9/minicpm-v-mobile-tester.svg)](https://github.com/yagyarajsharma9/minicpm-v-mobile-tester/issues)
[![GitHub forks](https://img.shields.io/github/forks/yagyarajsharma9/minicpm-v-mobile-tester.svg)](https://github.com/yagyarajsharma9/minicpm-v-mobile-tester/network/members)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![Model](https://img.shields.io/badge/Model-MiniCPM--V%204.6-orange.svg)](https://huggingface.co/openbmb/MiniCPM-V-4.6)
[![Windows Only](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](README.md)

> A lightweight, open-source toolkit for testing OpenBMB MiniCPM-V 4.6 locally and on mobile devices. Built to prove what's possible running a vision-language model on a laptop and as a standalone Android APK.

---

## Table of Contents

- [What This Project Is](#what-this-project-is)
- [Does It Run on a Client Laptop?](#does-it-run-on-a-client-laptop)
- [Is It Worth Publishing?](#is-it-worth-publishing)
- [Key Innovations](#key-innovations)
- [Quick Start](#quick-start)
- [Features](#features)
- [What We Researched](#what-we-researched)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

---

## What This Project Is

A complete toolkit for testing [MiniCPM-V 4.6](https://huggingface.co/openbmb/MiniCPM-V-4.6), OpenBMB's vision-language model, in two deployment targets:

- **Python FastAPI web server** — a local chat UI with image/video input, tool-call demo, OCR shortcut, and mobile efficiency controls. Runs at http://127.0.0.1:7860.
- **Android APK build** — an offline mobile app using llama.cpp JNI with web search, voice input, math formula rendering, and compact chat memory. Build scripts and documented architecture are included.

This repo is a **public reference** — the web server and all tools are ready to use. The Android source exists in the original repo but is excluded here to keep this showcase lightweight.

---

## Does It Run on a Client Laptop?

**Yes.** The web server runs on any Windows laptop:

`powershell
.\run.ps1
`

Requirements: Windows 10/11, PowerShell 7+, Python 3.12+, 8+ GB RAM (16 GB recommended for Transformers model). Ollama installed optionally for the Ollama backend.

The server auto-starts Ollama if needed, installs dependencies into a local venv, and launches the UI at http://127.0.0.1:7860. All processing is local — no data leaves the machine.

---

## Is It Worth Publishing?

**Yes.** This project demonstrates concrete verifiable results:

1. MiniCPM-V 4.6 running fully offline on a local machine with three different backends (Transformers, Ollama, OpenAI-compatible)
2. A mobile-focused deployment strategy (8192 context, 1024 predict length, arm64-v8a APK)
3. Practical workarounds for real problems (half answers, formula crashes, context overflow)
4. Self-testing scripts that verify model configuration correctness
5. A PWA mobile shell that works as a phone-installed app

---

## Key Innovations

| Innovation | Description |
|---|---|
| **Multi-backend testing** | Single UI to switch between Transformers, Ollama, and any OpenAI-compatible server without code changes |
| **Context window research** | Proved 8192 tokens is the mobile sweet spot — tested against 4096 (too small) and higher values (RAM-unsafe) |
| **Predict length fix** | Fixed the "half answer" bug by increasing DEFAULT_PREDICT_LENGTH from 192 to 1024 |
| **Formula crash fix** | Resolved Android ICU regex crash (PatternSyntaxException) by escaping unescaped brackets in math detection |
| **Lazy KaTeX rendering** | WebView only loads when math is detected — normal chat uses fast TextView rendering, no startup delay |
| **Formula normalization** | Converts raw LaTeX to readable text for Android TextView fallback display |
| **Compact memory for mobile** | Summarizes old chat turns to keep conversations within 8192 token budget |
| **Self-testing scripts** | Automated verification that model config and prompt policy rules are correct, integrates with Gradle tests |
| **Desktop vibration controller** | XInput and serial controller integration for device interaction testing |
| **Hybrid web search** | Tavily + TinyFish Fetch + Wikipedia/DuckDuckGo fallback with source citation in prompts |

---

## Quick Start

### Prerequisites

- Windows 10/11
- PowerShell 7+
- Python 3.12+
- Ollama (optional, auto-started if needed)

### Start the Web Server

`powershell
.\run.ps1
`

Then open **http://127.0.0.1:7860**. The PWA mobile shell is at **http://127.0.0.1:7860/mobile**.

What happens automatically:
1. Creates .venv/ if missing
2. Installs dependencies from equirements.txt
3. Starts Ollama if not detected on port 11434
4. Launches FastAPI on 127.0.0.1:7860

---

## Features

### Web Server

| Feature | Details |
|---|---|
| Text chat | Multi-turn conversation with history (last 12 turns to API, last 8 to Transformers) |
| Single-image understanding | Upload one image with text prompt |
| Multi-image comparison | Upload multiple images for comparative questions |
| Video frame sampling | Browser captures video frames as images |
| OCR prompt shortcut | Quick prompt to extract text from images |
| Tool-call demo | Built-in deterministic get_current_time and get_weather tools |
| Mobile efficiency controls | 16x/4x downsampling, max slices (36), max frames (16), stack frames, image IDs toggle |
| Generation controls | Temperature, top-p, top-k, max tokens |
| Three LLM backends | 	ransformers (local), ollama, openai-compatible |

### Android App (Documented)

| Feature | Details |
|---|---|
| Offline chat | No internet needed after model loaded |
| Voice input | Android system speech-to-text |
| Web search | Tavily + TinyFish with Wikipedia/DuckDuckGo fallback |
| Image understanding | Vision model processes attached images |
| Math formula rendering | KaTeX WebView (lazy-loaded) + formula normalization fallback |
| Compact memory | Summarizes old chat for long conversations |
| Response quality | Configurable token range (256-1536), min predict length 1024 |

---

## What We Researched

### Context Window
- **8192 tokens** is the mobile safe zone — 4x increase from the default 4096

### Generation Quality
- DEFAULT_PREDICT_LENGTH = 1024 fixes half-answer problem
- Configurable response range: **256-1536 tokens**

### Math Rendering on Android
- Android ICU regex is stricter than desktop JVM — unescaped brackets cause instant crash
- KaTeX WebView must be lazy-created to avoid slow app launches
- Formula normalization bridges LaTeX to readable Unicode for TextView fallback

### Web Search
- Tavily provides structured results; TinyFish fetches clean page content from result URLs
- Search context injected into model prompt with citation instructions

### Image Processing on Mobile
- Large images resized before processing to prevent OOM crashes
- Image context overflow guarded to reduce native crashes

---

## Project Structure

`
minicpm-v-mobile-tester/
├── README.md                      # This file
├── AGENTS.md                      # Agent instructions
├── LICENSE                        # MIT License
├── CONTRIBUTING.md                # How to contribute
├── SECURITY.md                    # Security policy
├── CODE_OF_CONDUCT.md             # Code of conduct
├── app.py                         # FastAPI web server (single file, 450+ lines)
├── requirements.txt               # Python dependencies
├── .gitignore                     # Excludes APK, vendor, .venv, logs
├── run.ps1                        # Start web server
├── run_controller.py              # Desktop vibration controller
├── run_controller.ps1             # Controller helper script
├── build_android.ps1              # Android build script
├── test_response_quality.ps1     # Android quality self-test
├── test_memory_compaction.ps1    # Android memory self-test
├── mobile_app/                    # PWA mobile shell
│   ├── index.html, app.js, styles.css, manifest.webmanifest, sw.js, icon.svg
├── static/                        # Web UI assets
│   ├── index.html, app.js, styles.css
└── docs/                          # Research documentation
    ├── architecture.md
    ├── android-development.md
    ├── research-findings.md
    └── api-reference.md
`

---

## API Reference

### POST /api/chat
Main chat endpoint with text prompts, image/video attachments, and generation options.

**Request:**
`json
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
`

**Response:**
`json
{
  "content": "The image shows...",
  "provider": "transformers",
  "model": "openbmb/MiniCPM-V-4.6",
  "elapsed_ms": 3420,
  "tool_calls": [],
  "usage": null
}
`

Full API details: [docs/api-reference.md](docs/api-reference.md).

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Areas for Contribution
- Additional LLM provider support (vLLM, SGLang configuration presets)
- Mobile UI improvements for the PWA shell
- New self-test scripts for Android build validation
- Android feature expansion (multi-language support, export chat history)
- Documentation and usage examples

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Important Notes

- **No APK in this repo** - the debug APK with bundled model files is ~1.6 GB and excluded to keep this repo lightweight
- **No API keys** - web search API keys are configured locally via local.properties, not in source code
- **Windows only** - builds and scripts require PowerShell on Windows
- **Public reference** - this repo demonstrates what was researched and built, not a distributable application