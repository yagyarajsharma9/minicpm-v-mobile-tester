from __future__ import annotations

import json
import re
import asyncio
import base64
import time
from io import BytesIO
from datetime import datetime
from typing import Any, Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


DEFAULT_OLLAMA_ENDPOINT = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "openbmb/minicpm-v4.6"
DEFAULT_MODEL = "openbmb/MiniCPM-V-4.6"
_TRANSFORMERS_CACHE: dict[str, Any] = {"model_id": None, "processor": None, "model": None}


class Attachment(BaseModel):
    kind: Literal["image", "video_frame"]
    name: str
    mime: str = "image/jpeg"
    data: str = Field(description="Base64 payload without data URL prefix")


class ChatOptions(BaseModel):
    temperature: float = 0.2
    top_p: float = 0.9
    top_k: int = 40
    max_tokens: int = 512
    downsample_mode: Literal["16x", "4x"] = "16x"
    max_slice_nums: int = 36
    max_num_frames: int = 16
    stack_frames: int = 1
    use_image_id: bool = True
    tool_demo: bool = False


class Message(BaseModel):
    role: Literal["user", "assistant", "tool"]
    content: str


class ChatRequest(BaseModel):
    provider: Literal["transformers", "ollama", "openai"] = "transformers"
    endpoint: str = DEFAULT_OLLAMA_ENDPOINT
    model: str = DEFAULT_MODEL
    system: str = ""
    prompt: str
    history: list[Message] = []
    attachments: list[Attachment] = []
    options: ChatOptions = ChatOptions()


class ChatResponse(BaseModel):
    content: str
    provider: str
    model: str
    elapsed_ms: int
    tool_calls: list[dict[str, Any]] = []
    usage: dict[str, Any] | None = None


app = FastAPI(title="MiniCPM-V 4.6 Mobile Tester")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/mobile_app", StaticFiles(directory="mobile_app"), name="mobile_app")


@app.get("/")
def index() -> FileResponse:
    return FileResponse("static/index.html")


@app.get("/mobile")
def mobile_app() -> FileResponse:
    return FileResponse("mobile_app/index.html")


@app.get("/api/status")
async def status() -> dict[str, Any]:
    ollama = {"ok": False, "models": []}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{DEFAULT_OLLAMA_ENDPOINT}/api/tags")
            response.raise_for_status()
            payload = response.json()
            ollama = {
                "ok": True,
                "models": [item.get("name") for item in payload.get("models", [])],
            }
    except Exception as exc:  # pragma: no cover - status endpoint should stay helpful.
        ollama["error"] = str(exc)
    return {
        "default_model": DEFAULT_MODEL,
        "ollama_model": DEFAULT_OLLAMA_MODEL,
        "ollama": ollama,
        "features": [
            "Text chat",
            "Single-image understanding",
            "Multi-image reasoning",
            "OCR prompts",
            "Video frame sampling",
            "Tool-call demo",
            "Mobile efficiency controls",
        ],
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    start = time.perf_counter()
    if not request.prompt.strip() and not request.attachments:
        raise HTTPException(status_code=400, detail="Prompt or media is required.")

    if request.provider == "ollama":
        first = await call_ollama(request)
        content = first["content"]
        tool_calls = extract_tool_calls(content)

        if request.options.tool_demo and tool_calls:
            tool_messages = [run_demo_tool(call) for call in tool_calls]
            second_request = request.model_copy(deep=True)
            second_request.history = [
                *request.history,
                Message(role="user", content=request.prompt),
                Message(role="assistant", content=content),
                *[Message(role="tool", content=json.dumps(msg)) for msg in tool_messages],
            ]
            second_request.prompt = "Use the tool result above to answer the user clearly."
            second_request.attachments = []
            second = await call_ollama(second_request)
            content = f"{content}\n\nTool result:\n{json.dumps(tool_messages, indent=2)}\n\nFinal answer:\n{second['content']}"

        return ChatResponse(
            content=normalize_response_text(content),
            provider=request.provider,
            model=request.model,
            elapsed_ms=int((time.perf_counter() - start) * 1000),
            tool_calls=tool_calls,
            usage=first.get("usage"),
        )

    if request.provider == "transformers":
        result = await asyncio.to_thread(call_transformers_sync, request)
        return ChatResponse(
            content=normalize_response_text(result["content"]),
            provider=request.provider,
            model=request.model,
            elapsed_ms=int((time.perf_counter() - start) * 1000),
            tool_calls=extract_tool_calls(result["content"]),
            usage=result.get("usage"),
        )

    result = await call_openai_compatible(request)
    return ChatResponse(
        content=normalize_response_text(result["content"]),
        provider=request.provider,
        model=request.model,
        elapsed_ms=int((time.perf_counter() - start) * 1000),
        tool_calls=extract_tool_calls(result["content"]),
        usage=result.get("usage"),
    )


async def call_ollama(request: ChatRequest) -> dict[str, Any]:
    endpoint = request.endpoint.rstrip("/") or DEFAULT_OLLAMA_ENDPOINT
    payload: dict[str, Any] = {
        "model": request.model,
        "stream": False,
        "messages": build_ollama_messages(request),
        "options": {
            "temperature": request.options.temperature,
            "top_p": request.options.top_p,
            "top_k": request.options.top_k,
            "num_predict": request.options.max_tokens,
        },
    }
    if request.options.tool_demo:
        payload["tools"] = demo_tools_schema()

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(f"{endpoint}/api/chat", json=payload)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        raise HTTPException(status_code=502, detail=f"Ollama error: {detail}") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach Ollama at {endpoint}: {exc}") from exc

    data = response.json()
    message = data.get("message", {})
    content = message.get("content", "")
    tool_calls = message.get("tool_calls")
    if tool_calls:
        content = f"{content}\n\n{json.dumps({'tool_calls': tool_calls}, indent=2)}"
    return {
        "content": content,
        "usage": {
            "prompt_eval_count": data.get("prompt_eval_count"),
            "eval_count": data.get("eval_count"),
            "total_duration": data.get("total_duration"),
        },
    }


def call_transformers_sync(request: ChatRequest) -> dict[str, Any]:
    try:
        import torch
        from PIL import Image
        from transformers import AutoModelForImageTextToText, AutoProcessor
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Transformers backend is not installed in the virtualenv: {exc}",
        ) from exc

    model_id = request.model or DEFAULT_MODEL
    if _TRANSFORMERS_CACHE["model_id"] != model_id:
        processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
        model = AutoModelForImageTextToText.from_pretrained(
            model_id,
            torch_dtype="auto",
            device_map="auto",
            trust_remote_code=True,
        )
        model.eval()
        _TRANSFORMERS_CACHE.update({"model_id": model_id, "processor": processor, "model": model})

    processor = _TRANSFORMERS_CACHE["processor"]
    model = _TRANSFORMERS_CACHE["model"]

    content: list[dict[str, Any]] = []
    for attachment in request.attachments:
        image_bytes = base64.b64decode(attachment.data)
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        content.append({"type": "image", "image": image})
    content.append({"type": "text", "text": enrich_prompt(request)})

    messages: list[dict[str, Any]] = []
    if request.system.strip():
        messages.append({"role": "system", "content": request.system.strip()})
    for item in request.history[-8:]:
        messages.append({"role": item.role, "content": item.content})
    messages.append({"role": "user", "content": content})

    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
        downsample_mode=request.options.downsample_mode,
        max_slice_nums=request.options.max_slice_nums,
        use_image_id=request.options.use_image_id,
    )
    target_device = getattr(model, "device", None) or next(model.parameters()).device
    inputs = inputs.to(target_device)

    with torch.inference_mode():
        generated_ids = model.generate(
            **inputs,
            downsample_mode=request.options.downsample_mode,
            max_new_tokens=request.options.max_tokens,
            temperature=request.options.temperature,
            top_p=request.options.top_p,
            top_k=request.options.top_k,
            do_sample=request.options.temperature > 0,
        )

    generated_ids_trimmed = [
        out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = processor.batch_decode(
        generated_ids_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )
    return {"content": output_text[0] if output_text else "", "usage": None}


def build_ollama_messages(request: ChatRequest) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    if request.system.strip():
        messages.append({"role": "system", "content": request.system.strip()})

    for item in request.history[-12:]:
        role = "user" if item.role == "tool" else item.role
        messages.append({"role": role, "content": item.content})

    prompt = enrich_prompt(request)
    user_message: dict[str, Any] = {"role": "user", "content": prompt}
    media_images = [att.data for att in request.attachments if att.kind in {"image", "video_frame"}]
    if media_images:
        user_message["images"] = media_images
    messages.append(user_message)
    return messages


async def call_openai_compatible(request: ChatRequest) -> dict[str, Any]:
    endpoint = request.endpoint.rstrip("/")
    if not endpoint:
        raise HTTPException(status_code=400, detail="OpenAI-compatible endpoint is required.")

    content: list[dict[str, Any]] = []
    for att in request.attachments:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{att.mime};base64,{att.data}"},
            }
        )
    content.append({"type": "text", "text": enrich_prompt(request)})

    messages: list[dict[str, Any]] = []
    if request.system.strip():
        messages.append({"role": "system", "content": request.system.strip()})
    for item in request.history[-12:]:
        messages.append({"role": item.role, "content": item.content})
    messages.append({"role": "user", "content": content})

    payload: dict[str, Any] = {
        "model": request.model,
        "messages": messages,
        "temperature": request.options.temperature,
        "top_p": request.options.top_p,
        "max_tokens": request.options.max_tokens,
    }
    if request.options.tool_demo:
        payload["tools"] = demo_tools_schema()

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(f"{endpoint}/v1/chat/completions", json=payload)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        raise HTTPException(status_code=502, detail=f"OpenAI-compatible server error: {detail}") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach {endpoint}: {exc}") from exc

    data = response.json()
    choice = data.get("choices", [{}])[0]
    message = choice.get("message", {})
    return {"content": message.get("content", ""), "usage": data.get("usage")}


def enrich_prompt(request: ChatRequest) -> str:
    media_count = len(request.attachments)
    frame_count = len([att for att in request.attachments if att.kind == "video_frame"])
    image_count = media_count - frame_count
    notes = [
        "MiniCPM-V 4.6 test settings:",
        f"- visual token compression: {request.options.downsample_mode}",
        f"- max image slices: {request.options.max_slice_nums}",
        f"- sampled video frames: {frame_count}/{request.options.max_num_frames}",
        f"- stack frames: {request.options.stack_frames}",
        f"- image ids enabled: {request.options.use_image_id}",
    ]
    if image_count or frame_count:
        notes.append(f"- attached images: {image_count}; video-derived frames: {frame_count}")
    return f"{request.prompt.strip()}\n\n" + "\n".join(notes)


def demo_tools_schema() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "get_current_time",
                "description": "Get the current local server time.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get demo weather for a city. This tester returns a deterministic sample result.",
                "parameters": {
                    "type": "object",
                    "properties": {"location": {"type": "string", "description": "City name"}},
                    "required": ["location"],
                },
            },
        },
    ]


TOOL_XML_RE = re.compile(
    r"<function=(?P<name>[^>]+)>(?P<body>.*?)</function>",
    re.DOTALL | re.IGNORECASE,
)
PARAM_RE = re.compile(
    r"<parameter=(?P<name>[^>]+)>(?P<value>.*?)</parameter>",
    re.DOTALL | re.IGNORECASE,
)


def extract_tool_calls(content: str) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for match in TOOL_XML_RE.finditer(content or ""):
        args = {
            param.group("name").strip(): param.group("value").strip()
            for param in PARAM_RE.finditer(match.group("body"))
        }
        calls.append({"name": match.group("name").strip(), "arguments": args})

    try:
        parsed = json.loads(content)
        for item in parsed.get("tool_calls", []):
            function = item.get("function", {})
            calls.append(
                {
                    "name": function.get("name", item.get("name", "")),
                    "arguments": function.get("arguments", item.get("arguments", {})),
                }
            )
    except Exception:
        pass
    return calls


def run_demo_tool(call: dict[str, Any]) -> dict[str, Any]:
    name = call.get("name")
    arguments = call.get("arguments") or {}
    if name == "get_current_time":
        return {"tool": name, "result": datetime.now().isoformat(timespec="seconds")}
    if name == "get_weather":
        location = arguments.get("location", "Unknown")
        return {
            "tool": name,
            "location": location,
            "result": "Demo weather: 24 C, partly cloudy, light wind.",
        }
    return {"tool": name, "error": "Unknown demo tool"}


NORMALIZE_RE = re.compile(
    r"(```[\s\S]*?```|`[^`]+`|\$\$[\s\S]*?\$\$|\$[^$]+\$|\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\])"
    r"|(?<!\\)(?:\\r\\n|\\[nr])"
)


def normalize_response_text(text: str) -> str:
    if not isinstance(text, str) or "\\" not in text:
        return text
    return NORMALIZE_RE.sub(lambda match: match.group(1) or "\n", text)
