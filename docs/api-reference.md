# API Reference

## Web Server API (`app.py`)

### `GET /api/status`
Returns the server status, detected Ollama availability, and supported features.

**Response:**
```json
{
  "default_model": "openbmb/MiniCPM-V-4.6",
  "ollama_model": "openbmb/minicpm-v4.6",
  "ollama": {
    "ok": true,
    "models": ["openbmb/minicpm-v4.6"],
    "error": ""
  },
  "features": [
    "Text chat",
    "Single-image understanding",
    "Multi-image reasoning",
    "OCR prompts",
    "Video frame sampling",
    "Tool-call demo",
    "Mobile efficiency controls"
  ]
}
```

### `POST /api/chat`
Main chat endpoint. Accepts text prompts, image/video attachments, and configurable generation options.

**Request Body (`ChatRequest`):**
| Field | Type | Default | Description |
|---|---|---|---|
| `provider` | `"transformers"`, `"ollama"`, `"openai"` | `"transformers"` | LLM backend |
| `endpoint` | `string` | `"http://localhost:11434"` | Provider API endpoint |
| `model` | `string` | `"openbmb/MiniCPM-V-4.6"` | Model identifier |
| `system` | `string` | `""` | System prompt |
| `prompt` | `string` | — | User message |
| `history` | `list[Message]` | `[]` | Chat history (last 8–12 turns used) |
| `attachments` | `list[Attachment]` | `[]` | Images or video frames |
| `options` | `ChatOptions` | default options | Generation settings |

**`ChatOptions`:**
| Field | Type | Default | Description |
|---|---|---|---|
| `temperature` | float | 0.2 | Sampling temperature |
| `top_p` | float | 0.9 | Nucleus sampling |
| `top_k` | int | 40 | Top-k sampling |
| `max_tokens` | int | 512 | Max output tokens |
| `downsample_mode` | `"16x"` or `"4x"` | `"16x"` | Visual token compression |
| `max_slice_nums` | int | 36 | Max image slices |
| `max_num_frames` | int | 16 | Max video frames to sample |
| `stack_frames` | int | 1 | Stack frame count |
| `use_image_id` | bool | true | Enable image ID tokens |
| `tool_demo` | bool | false | Enable tool-call demo |

**Response (`ChatResponse`):**
| Field | Type | Description |
|---|---|---|
| `content` | string | Model response text |
| `provider` | string | Provider used |
| `model` | string | Model name |
| `elapsed_ms` | int | Response time in milliseconds |
| `tool_calls` | list[dict] | Detected tool calls |
| `usage` | dict or null | Token usage info |

### `GET /`
Serves the web UI (`static/index.html`).

### `GET /mobile`
Serves the PWA mobile shell (`mobile_app/index.html`).

### `GET /static/*`
Serves static web assets from the `static/` directory.

### `GET /mobile_app/*`
Serves PWA shell assets from the `mobile_app/` directory.