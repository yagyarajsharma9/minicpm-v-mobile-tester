# Architecture Overview

## Two-Part System

### 1. Python FastAPI Web Server (`app.py`)

A single-file FastAPI application that serves as the primary testing interface. It provides three LLM backend options:

| Provider | How It Works |
|---|---|
| `transformers` | Loads `openbmb/MiniCPM-V-4.6` directly via HuggingFace Transformers with GPU acceleration |
| `ollama` | Communicates with a local Ollama server via REST API |
| `openai` | Connects to any OpenAI-compatible server (vLLM, SGLang, transformers serve, llama.cpp server) |

**Key endpoints:**
- `GET /` — web UI
- `GET /mobile` — PWA mobile shell
- `GET /api/status` — checks Ollama availability and features
- `POST /api/chat` — main chat endpoint with attachments and options

**Web UI features:**
- Text chat with conversation history
- Single and multi-image upload
- Video frame sampling (browser-based)
- OCR prompt shortcut
- Tool-call demo with determinism helpers
- MiniCPM-V 4.6 style visual settings (16x/4x downsampling, slices, frames, stack, image IDs)
- Generation controls (temperature, top-p, top-k, max tokens)

### 2. Android App (`EDAP MINI AI`)

An Android application built with Kotlin and llama.cpp JNI for offline MiniCPM-V 4.6 inference.

**Architecture layers:**
1. **UI Layer** — Kotlin Activities and XML layouts (chat screen, model manager, message renderer)
2. **ViewModel Layer** — Kotlin classes managing chat state, model loading, message generation
3. **JNI Bridge** — `LlamaEngine.kt` connects Kotlin to native llama.cpp via JNI
4. **Native Layer** — `llama_jni.cpp` wraps llama.cpp API for model loading, generation, image prefill
5. **Web Search** — `WebSearchClient.kt` handles Tavily, TinyFish, Wikipedia, DuckDuckGo search
6. **Memory Management** — `ConversationMemoryManager.kt` implements compact memory for long conversations
7. **Prompt Policy** — `ResponsePromptPolicy.kt` enforces complete answers and formula readability
8. **Display** — `MathHtmlRenderer.kt` renders LaTeX formulas via bundled KaTeX WebView

**Key model settings:**
- Model folder: `minicpm-v-4_6-instruct`
- Visible name: `EMINI AI 2.6 (Q4_K_M)`
- Context window: 8192 tokens (mobile-safe)
- Default predict length: 1024 tokens
- Response range: 256–1536 tokens
- Arch: arm64-v8a only