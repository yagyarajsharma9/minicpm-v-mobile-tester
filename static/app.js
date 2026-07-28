const state = {
  history: [],
  attachments: [],
  busy: false,
};

const els = {
  statusLine: document.querySelector("#statusLine"),
  chatLog: document.querySelector("#chatLog"),
  chatForm: document.querySelector("#chatForm"),
  prompt: document.querySelector("#prompt"),
  imageInput: document.querySelector("#imageInput"),
  videoInput: document.querySelector("#videoInput"),
  previewStrip: document.querySelector("#previewStrip"),
  clearBtn: document.querySelector("#clearBtn"),
  sendBtn: document.querySelector("#sendBtn"),
  provider: document.querySelector("#provider"),
  endpoint: document.querySelector("#endpoint"),
  model: document.querySelector("#model"),
  systemPrompt: document.querySelector("#systemPrompt"),
  toolDemo: document.querySelector("#toolDemo"),
  downsample: document.querySelector("#downsample"),
  maxSliceNums: document.querySelector("#maxSliceNums"),
  maxNumFrames: document.querySelector("#maxNumFrames"),
  stackFrames: document.querySelector("#stackFrames"),
  useImageId: document.querySelector("#useImageId"),
  temperature: document.querySelector("#temperature"),
  temperatureOut: document.querySelector("#temperatureOut"),
  topP: document.querySelector("#topP"),
  topPOut: document.querySelector("#topPOut"),
  topK: document.querySelector("#topK"),
  maxTokens: document.querySelector("#maxTokens"),
};

const presets = {
  describe: "Describe the attached media. Include the important objects, text, layout, and any visible relationships.",
  ocr: "Extract all readable text from the attached image or frames. Preserve line breaks and mention uncertain text.",
  compare: "Compare the attached images. List similarities, differences, and any likely sequence or causal relationship.",
  video: "Describe this video from the sampled frames. Follow the timeline and focus on scene changes, on-screen text, and main actions.",
};

function addMessage(role, content) {
  const item = document.createElement("div");
  item.className = `message ${role}`;
  item.textContent = content;
  els.chatLog.appendChild(item);
  els.chatLog.scrollTop = els.chatLog.scrollHeight;
}

function setBusy(value) {
  state.busy = value;
  els.sendBtn.disabled = value;
  els.sendBtn.textContent = value ? "Running" : "Send";
}

function syncOutputs() {
  els.temperatureOut.value = els.temperature.value;
  els.topPOut.value = els.topP.value;
}

function dataUrlParts(dataUrl) {
  const [meta, data] = dataUrl.split(",");
  const mime = /data:(.*?);base64/.exec(meta)?.[1] || "image/jpeg";
  return { mime, data };
}

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

async function addImageFiles(files) {
  for (const file of files) {
    const dataUrl = await readFileAsDataUrl(file);
    const { mime, data } = dataUrlParts(dataUrl);
    state.attachments.push({ kind: "image", name: file.name, mime, data, preview: dataUrl });
  }
  renderPreviews();
}

async function addVideoFile(file) {
  const maxFrames = Number(els.maxNumFrames.value) || 16;
  addMessage("meta", `Sampling up to ${maxFrames} video frames from ${file.name}...`);
  const frames = await sampleVideoFrames(file, maxFrames);
  for (const [index, frame] of frames.entries()) {
    const { mime, data } = dataUrlParts(frame);
    state.attachments.push({
      kind: "video_frame",
      name: `${file.name} frame ${index + 1}`,
      mime,
      data,
      preview: frame,
    });
  }
  renderPreviews();
}

function sampleVideoFrames(file, maxFrames) {
  return new Promise((resolve, reject) => {
    const video = document.createElement("video");
    const url = URL.createObjectURL(file);
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");
    const frames = [];
    let targets = [];
    let current = 0;

    video.muted = true;
    video.preload = "metadata";
    video.src = url;

    video.onloadedmetadata = () => {
      const duration = Number.isFinite(video.duration) && video.duration > 0 ? video.duration : maxFrames;
      const count = Math.max(1, Math.min(maxFrames, Math.ceil(duration)));
      targets = Array.from({ length: count }, (_, index) => ((index + 0.5) * duration) / count);
      canvas.width = Math.min(960, video.videoWidth || 960);
      canvas.height = Math.max(1, Math.round(canvas.width * ((video.videoHeight || 540) / (video.videoWidth || 960))));
      video.currentTime = Math.min(targets[0], Math.max(0, duration - 0.05));
    };

    video.onseeked = () => {
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      frames.push(canvas.toDataURL("image/jpeg", 0.82));
      current += 1;
      if (current >= targets.length) {
        URL.revokeObjectURL(url);
        resolve(frames);
        return;
      }
      video.currentTime = targets[current];
    };

    video.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Could not decode video in the browser."));
    };
  });
}

function renderPreviews() {
  els.previewStrip.replaceChildren();
  for (const [index, attachment] of state.attachments.entries()) {
    const preview = document.createElement("button");
    preview.className = "preview";
    preview.type = "button";
    preview.title = "Remove attachment";
    preview.onclick = () => {
      state.attachments.splice(index, 1);
      renderPreviews();
    };

    const image = document.createElement("img");
    image.alt = attachment.name;
    image.src = attachment.preview;
    const label = document.createElement("span");
    label.textContent = attachment.kind === "video_frame" ? "frame" : attachment.name;
    preview.append(image, label);
    els.previewStrip.appendChild(preview);
  }
}

function payload(prompt) {
  return {
    provider: els.provider.value,
    endpoint: els.endpoint.value,
    model: els.model.value,
    system: els.systemPrompt.value,
    prompt,
    history: state.history.slice(-10),
    attachments: state.attachments.map(({ preview, ...rest }) => rest),
    options: {
      temperature: Number(els.temperature.value),
      top_p: Number(els.topP.value),
      top_k: Number(els.topK.value),
      max_tokens: Number(els.maxTokens.value),
      downsample_mode: els.downsample.value,
      max_slice_nums: Number(els.maxSliceNums.value),
      max_num_frames: Number(els.maxNumFrames.value),
      stack_frames: Number(els.stackFrames.value),
      use_image_id: els.useImageId.checked,
      tool_demo: els.toolDemo.checked,
    },
  };
}

async function sendPrompt(event) {
  event.preventDefault();
  if (state.busy) return;

  const prompt = els.prompt.value.trim();
  if (!prompt && state.attachments.length === 0) return;

  setBusy(true);
  addMessage("user", prompt || "[media only]");
  els.prompt.value = "";

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload(prompt)),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Request failed");
    }
    addMessage("assistant", `${data.content}\n\n[${data.model} via ${data.provider}, ${data.elapsed_ms} ms]`);
    state.history.push({ role: "user", content: prompt || "[media only]" });
    state.history.push({ role: "assistant", content: data.content });
    state.attachments = [];
    renderPreviews();
  } catch (error) {
    addMessage("meta", error.message);
  } finally {
    setBusy(false);
  }
}

async function loadStatus() {
  try {
    const response = await fetch("/api/status");
    const data = await response.json();
    const hasModel = data.ollama.models.some((name) => name === data.ollama_model || name.startsWith(`${data.ollama_model}:`));
    els.statusLine.textContent = hasModel
      ? "Transformers backend ready; Ollama model is installed but may require fork support"
      : "Transformers backend ready; Ollama model is not listed";
  } catch {
    els.statusLine.textContent = "Start Ollama, then reload this page";
  }
}

document.querySelectorAll("[data-preset]").forEach((button) => {
  button.addEventListener("click", () => {
    els.prompt.value = presets[button.dataset.preset];
    els.prompt.focus();
  });
});

els.provider.addEventListener("change", () => {
  if (els.provider.value === "ollama") {
    els.endpoint.value = "http://localhost:11434";
    els.model.value = "openbmb/minicpm-v4.6";
  } else if (els.provider.value === "transformers") {
    els.endpoint.value = "";
    els.model.value = "openbmb/MiniCPM-V-4.6";
  } else {
    els.endpoint.value = "http://localhost:8000";
    els.model.value = "openbmb/MiniCPM-V-4.6";
  }
});
els.temperature.addEventListener("input", syncOutputs);
els.topP.addEventListener("input", syncOutputs);
els.chatForm.addEventListener("submit", sendPrompt);
els.imageInput.addEventListener("change", (event) => addImageFiles(event.target.files));
els.videoInput.addEventListener("change", (event) => {
  const [file] = event.target.files;
  if (file) addVideoFile(file);
});
els.clearBtn.addEventListener("click", () => {
  state.history = [];
  state.attachments = [];
  els.chatLog.replaceChildren();
  renderPreviews();
});

syncOutputs();
loadStatus();
