const state = {
  history: [],
  image: null,
  busy: false,
};

const els = {
  status: document.querySelector("#status"),
  settingsBtn: document.querySelector("#settingsBtn"),
  settings: document.querySelector("#settings"),
  engine: document.querySelector("#engine"),
  endpoint: document.querySelector("#endpoint"),
  model: document.querySelector("#model"),
  maxTokens: document.querySelector("#maxTokens"),
  messages: document.querySelector("#messages"),
  composer: document.querySelector("#composer"),
  prompt: document.querySelector("#prompt"),
  imageInput: document.querySelector("#imageInput"),
  sendBtn: document.querySelector("#sendBtn"),
};

function saveSettings() {
  const settings = {
    engine: els.engine.value,
    endpoint: els.endpoint.value,
    model: els.model.value,
    maxTokens: els.maxTokens.value,
  };
  localStorage.setItem("minicpm-mobile-settings", JSON.stringify(settings));
}

function loadSettings() {
  const raw = localStorage.getItem("minicpm-mobile-settings");
  if (!raw) return;
  try {
    const settings = JSON.parse(raw);
    els.engine.value = settings.engine || els.engine.value;
    els.endpoint.value = settings.endpoint || els.endpoint.value;
    els.model.value = settings.model || els.model.value;
    els.maxTokens.value = settings.maxTokens || els.maxTokens.value;
  } catch {
    localStorage.removeItem("minicpm-mobile-settings");
  }
}

function addMessage(role, text, imageUrl = null) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${role}`;
  bubble.textContent = text;
  if (imageUrl) {
    const image = document.createElement("img");
    image.src = imageUrl;
    image.alt = "Attached image";
    bubble.appendChild(image);
  }
  els.messages.appendChild(bubble);
  els.messages.scrollTop = els.messages.scrollHeight;
}

function setBusy(value) {
  state.busy = value;
  els.sendBtn.disabled = value;
  els.sendBtn.textContent = value ? "..." : "Send";
}

function dataUrlParts(dataUrl) {
  const [meta, data] = dataUrl.split(",");
  const mime = /data:(.*?);base64/.exec(meta)?.[1] || "image/jpeg";
  return { mime, data };
}

function readFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

async function sendToServer(prompt) {
  const attachments = [];
  if (state.image) {
    const { mime, data } = dataUrlParts(state.image.dataUrl);
    attachments.push({ kind: "image", name: state.image.name, mime, data });
  }

  const body = {
    provider: "transformers",
    endpoint: "",
    model: els.model.value,
    system: "You are MiniCPM-V running for a mobile assistant. Keep answers short and useful.",
    prompt,
    history: state.history.slice(-8),
    attachments,
    options: {
      temperature: 0.2,
      top_p: 0.9,
      top_k: 40,
      max_tokens: Number(els.maxTokens.value) || 256,
      downsample_mode: "16x",
      max_slice_nums: 36,
      max_num_frames: 8,
      stack_frames: 1,
      use_image_id: true,
      tool_demo: false,
    },
  };

  const response = await fetch(els.endpoint.value, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Server request failed");
  return data.content;
}

async function sendOffline(prompt) {
  if (window.MiniCPMNative?.generate) {
    return window.MiniCPMNative.generate({
      prompt,
      image: state.image?.dataUrl || null,
      model: els.model.value,
      maxTokens: Number(els.maxTokens.value) || 256,
    });
  }
  throw new Error("Offline native llama.cpp bridge is not installed in this PWA build yet.");
}

async function onSubmit(event) {
  event.preventDefault();
  if (state.busy) return;

  const prompt = els.prompt.value.trim();
  if (!prompt && !state.image) return;

  const imageUrl = state.image?.dataUrl || null;
  addMessage("user", prompt || "[image]", imageUrl);
  els.prompt.value = "";
  setBusy(true);

  try {
    const answer = els.engine.value === "offline" ? await sendOffline(prompt) : await sendToServer(prompt);
    addMessage("assistant", answer);
    state.history.push({ role: "user", content: prompt || "[image]" });
    state.history.push({ role: "assistant", content: answer });
    state.image = null;
  } catch (error) {
    addMessage("meta", error.message);
  } finally {
    setBusy(false);
  }
}

els.settingsBtn.addEventListener("click", () => {
  els.settings.hidden = !els.settings.hidden;
});

[els.engine, els.endpoint, els.model, els.maxTokens].forEach((input) => {
  input.addEventListener("change", saveSettings);
});

els.imageInput.addEventListener("change", async (event) => {
  const [file] = event.target.files;
  if (!file) return;
  const dataUrl = await readFile(file);
  state.image = { name: file.name, dataUrl };
  addMessage("meta", `Image attached: ${file.name}`);
});

els.composer.addEventListener("submit", onSubmit);

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/mobile_app/sw.js").catch(() => {});
}

loadSettings();
els.status.textContent = navigator.onLine ? "Ready for server or offline bridge" : "Offline shell ready";
