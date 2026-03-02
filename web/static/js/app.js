// web/static/js/app.js

const VIEWS = {
  home: renderHome,
  search: renderSearch,
  queue: renderQueue,
  playlists: renderPlaylists,
  liked: renderLiked,
  library: renderLibrary,
  history: renderHistory,
  faq: renderFaq,
};

window.APP = {
  currentView: null,
  navigate(view, params = {}) {
    // Update sidebar active state
    document.querySelectorAll(".nav-item").forEach(el => {
      el.classList.toggle("active", el.dataset.view === view);
    });
    this.currentView = view;
    if (VIEWS[view]) VIEWS[view](params);
  },
};

// Sidebar navigation
document.querySelectorAll(".nav-item[data-view]").forEach(el => {
  el.addEventListener("click", e => {
    e.preventDefault();
    APP.navigate(el.dataset.view);
  });
});

// Settings modal
const settingsModal = document.getElementById("settings-modal");
document.getElementById("open-settings").addEventListener("click", () => openSettings());
document.getElementById("close-settings").addEventListener("click", () => settingsModal.classList.remove("open"));
document.getElementById("save-settings").addEventListener("click", () => saveSettings());

settingsModal.addEventListener("click", e => {
  if (e.target === settingsModal) settingsModal.classList.remove("open");
});

document.getElementById("browse-dl-path").addEventListener("click", async () => {
  try {
    const r = await API.get("/api/browse-folder");
    if (r && r.path) document.getElementById("s-dl-path").value = r.path;
  } catch (e) {}
});

document.getElementById("disconnect-spotify").addEventListener("click", async () => {
  if (!confirm("Disconnect Spotify? You'll need to re-authenticate.")) return;
  try {
    await fetch("/disconnect", { method: "POST" });
    toast("Spotify disconnected. Redirecting...", "info");
    setTimeout(() => { window.location.href = "/"; }, 1000);
  } catch (e) {
    toast("Failed to disconnect", "error");
  }
});

async function openSettings() {
  try {
    const cfg = await API.get("/api/config");
    document.getElementById("s-dl-path").value = cfg.download?.path || "";
    document.getElementById("s-format").value = cfg.download?.format || "mp3_320";
    document.getElementById("s-source").value = cfg.download?.source || "hybrid";
    document.getElementById("s-slsk-url").value = cfg.soulseek?.slskd_url || "";
    document.getElementById("s-slsk-key").value = cfg.soulseek?.slskd_api_key || "";
  } catch (e) {}
  _updateFlacWarning("s-format", "s-source", "s-flac-warning");
  settingsModal.classList.add("open");
  lucide.createIcons();
}

function _updateFlacWarning(formatId, sourceId, warningId) {
  const fmt = document.getElementById(formatId);
  const src = document.getElementById(sourceId);
  const warn = document.getElementById(warningId);
  if (!fmt || !warn) return;
  const isFlac = fmt.value === "flac";
  const isYT = !src || src.value !== "soulseek";
  warn.style.display = (isFlac && isYT) ? "" : "none";
  if (isFlac && isYT) lucide.createIcons();
}

document.getElementById("s-format").addEventListener("change", () =>
  _updateFlacWarning("s-format", "s-source", "s-flac-warning"));
document.getElementById("s-source").addEventListener("change", () =>
  _updateFlacWarning("s-format", "s-source", "s-flac-warning"));

async function saveSettings() {
  try {
    await API.post("/api/settings", {
      download: {
        path: document.getElementById("s-dl-path").value,
        format: document.getElementById("s-format").value,
        source: document.getElementById("s-source").value,
      },
      soulseek: {
        slskd_url: document.getElementById("s-slsk-url").value,
        slskd_api_key: document.getElementById("s-slsk-key").value,
      },
    });
    settingsModal.classList.remove("open");
    toast("Settings saved", "success");
  } catch (e) {
    toast("Failed to save settings", "error");
  }
}

// Status polling (every 10s)
async function pollStatus() {
  try {
    const s = await API.get("/api/status");
    const spotDot = document.getElementById("spotify-dot");
    const slskDot = document.getElementById("slsk-dot");
    spotDot.className = "status-dot " + (s.spotify === "ok" ? "ok" : "err");
    document.getElementById("spotify-label").textContent = s.spotify === "ok" ? "Spotify connected" : "Spotify offline";
    slskDot.className = "status-dot " + (s.soulseek === "ok" ? "ok" : "");
    document.getElementById("slsk-label").textContent = s.soulseek === "ok" ? "Soulseek connected" : "Soulseek offline";
  } catch (e) {}
}

pollStatus();
setInterval(pollStatus, 10000);

// Onboarding
async function checkOnboarding() {
  try {
    const cfg = await API.get("/api/config");
    const hasPath = cfg.download?.path;
    const hasFormat = cfg.download?.format;
    if (!hasPath || !hasFormat) {
      document.getElementById("onboarding-modal").classList.add("open");
    }
  } catch (e) {}
}

document.getElementById("ob-format").addEventListener("change", () =>
  _updateFlacWarning("ob-format", "ob-source", "ob-flac-warning"));
document.getElementById("ob-source").addEventListener("change", () =>
  _updateFlacWarning("ob-format", "ob-source", "ob-flac-warning"));

document.getElementById("ob-save").addEventListener("click", async () => {
  const path = document.getElementById("ob-dl-path").value.trim();
  const format = document.getElementById("ob-format").value;
  const source = document.getElementById("ob-source").value;
  try {
    await API.post("/api/settings", {
      download: { path: path || "", format, source },
    });
    document.getElementById("onboarding-modal").classList.remove("open");
    toast("Setup complete! You're ready to download music.", "success");
  } catch (e) {
    toast("Could not save settings", "error");
  }
});

// Boot
lucide.createIcons();
APP.navigate("home");
checkOnboarding();
