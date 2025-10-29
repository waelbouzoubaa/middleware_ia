// ===========================================================
// Middleware IA Chat – version finale 2025
// ===========================================================
const qs = new URLSearchParams(location.search);
const $ = (s, r = document) => r.querySelector(s);
const API_BASE = (localStorage.getItem("API_BASE") || "http://127.0.0.1:8010").replace(/\/$/, "");

const MODELS = {
  openai: [
    { id: "openai:gpt-4o-mini", label: "GPT-4o-Mini" },
    { id: "openai:gpt-4o", label: "GPT-4o" },
    { id: "openai:gpt-4-turbo", label: "GPT-4-Turbo" },
    { id: "openai:gpt-3.5-turbo", label: "GPT-3.5-Turbo" },
  ],
  mistral: [
    { id: "mistral:open-mixtral-8x7b", label: "Mixtral 8×7B" },
    { id: "mistral:open-mistral-7b", label: "Mistral 7B" },
  ],
};

const state = {
  provider: qs.get("provider") || "openai",
  model: null,
  files: [],
  messages: [],
  sending: false,
};

document.addEventListener("DOMContentLoaded", () => {
  initApiConfig();
  initModelSelect();
  initChatEvents();
  $("#newChatBtn").addEventListener("click", resetChat);
});

// ===========================================================
// INIT
// ===========================================================
function initChatEvents() {
  $("#sendBtn").addEventListener("click", sendMessage);
  $("#chatInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  $("#fileUpload").addEventListener("change", handleFileSelect);
}

function initApiConfig() {
  const modal = $("#apiConfigModal");
  $("#apiConfigBtn").addEventListener("click", () => {
    $("#apiBaseInput").value = localStorage.getItem("API_BASE") || API_BASE;
    modal.classList.remove("hidden");
  });
  $("#cancelApiConfig").addEventListener("click", () => modal.classList.add("hidden"));
  $("#saveApiConfig").addEventListener("click", () => {
    const val = $("#apiBaseInput").value.trim();
    if (val) localStorage.setItem("API_BASE", val);
    modal.classList.add("hidden");
    alert("✅ URL API mise à jour !");
  });
}

function initModelSelect() {
  const select = $("#modelSelect");
  const models = MODELS[state.provider] || [];
  select.innerHTML = "";
  models.forEach((m) => {
    const o = document.createElement("option");
    o.value = m.id;
    o.textContent = m.label;
    select.appendChild(o);
  });
  state.model = models[0]?.id;
  select.addEventListener("change", (e) => (state.model = e.target.value));
}

// ===========================================================
// CHAT MANAGEMENT
// ===========================================================
function handleFileSelect(e) {
  state.files = Array.from(e.target.files);
  $("#attachments").innerHTML = state.files
    .map((f) => `<div>📎 ${f.name} (${(f.size / 1024).toFixed(1)} Ko)</div>`)
    .join("");
}

function resetChat() {
  state.messages = [];
  renderMessages();
  $("#usageStats").classList.add("hidden");
}

function addMessage(role, content, files = []) {
  const log = $("#chatLog");
  const msg = document.createElement("div");
  msg.className = `msg ${role}`;

  let fileHtml = "";
  if (files.length > 0) {
    fileHtml = `<div class="file-preview">${files
      .map((f) => `📎 <span>${f.name}</span>`)
      .join("<br>")}</div>`;
  }

  msg.innerHTML = `
    <span class="avatar">${role === "user" ? "🧠" : "🤖"}</span>
    <div class="bubble">${escapeHTML(content)}${fileHtml}</div>
  `;

  log.appendChild(msg);
  log.scrollTop = log.scrollHeight;
}

function renderMessages() {
  const log = $("#chatLog");
  log.innerHTML = "";
  for (const m of state.messages) addMessage(m.role, m.content);
}

function escapeHTML(s) {
  return (s || "").replace(/[&<>"']/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#039;" }[m]));
}

// ===========================================================
// LOADER (3 points animés)
// ===========================================================
function showLoader() {
  const log = $("#chatLog");
  const loader = document.createElement("div");
  loader.id = "loader";
  loader.className = "msg assistant";
  loader.innerHTML = `<span class="avatar">🤖</span>
    <div class="bubble loading">
      <span class="dot"></span><span class="dot"></span><span class="dot"></span>
    </div>`;
  log.appendChild(loader);
  log.scrollTop = log.scrollHeight;
}
function removeLoader() {
  $("#loader")?.remove();
}

// ===========================================================
// ENVOI MESSAGE
// ===========================================================
async function sendMessage() {
  if (state.sending || !state.model) return;
  const input = $("#chatInput");
  const text = input.value.trim();
  const hasFile = state.files.length > 0;
  if (!text && !hasFile) return;

  addMessage("user", text || "(fichier envoyé)", state.files);
  input.value = "";
  state.sending = true;
  $("#sendBtn").disabled = true;
  showLoader();

  try {
    let resp;
    if (hasFile) {
      const form = new FormData();
      form.append("model", state.model);
      form.append("messages", JSON.stringify(state.messages));
      state.files.forEach((f) => form.append("files", f));
      resp = await fetch(`${API_BASE}/chat/file-to-ai`, { method: "POST", body: form });
    } else {
      const body = {
        user_id: "webclient",
        model: state.model,
        messages: state.messages,
        stream: false,
      };
      resp = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    }

    if (!resp.ok) throw new Error(await resp.text());
    const data = await resp.json();
    removeLoader();
    addMessage("assistant", data?.content || "(Aucune réponse)");
    renderUsage(data);
  } catch (e) {
    removeLoader();
    addMessage("assistant", `⚠️ Erreur : ${e.message}`);
  } finally {
    state.sending = false;
    $("#sendBtn").disabled = false;
    state.files = [];
    $("#attachments").innerHTML = "";
  }
}

// ===========================================================
// STATISTIQUES
// ===========================================================
function renderUsage(r) {
  const u = r?.usage || {};
  const inT = u.input_tokens || 0,
    outT = u.output_tokens || 0;
  const cost = r?.cost_eur || 0;
  const co2 = r?.est_co2e_g || 0;

  $("#tokensPill").textContent = `🔹 ${inT + outT} tokens (${inT} in / ${outT} out)`;
  $("#costPill").textContent = `💰 ${cost.toFixed(5)} €`;
  $("#co2Pill").textContent = `🌍 ${co2.toFixed(2)} gCO₂e`;
  $("#usageStats").classList.remove("hidden");
}
