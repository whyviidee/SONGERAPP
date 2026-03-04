// web/static/js/app.js

const VIEWS = {
  home: renderHome,
  search: renderSearch,
  artist: renderArtist,
  album: renderAlbum,
  queue: renderQueue,
  playlists: renderPlaylists,
  liked: renderLiked,
  library: renderLibrary,
  history: renderHistory,
  faq: renderFaq,
  trending: renderTrending,
};

window.APP = {
  currentView: null,
  navigate(view, params = {}) {
    // Update sidebar active state
    document.querySelectorAll(".nav-item").forEach(el => {
      el.classList.toggle("active", el.dataset.view === view);
    });
    this.currentView = view;
    _invalidateDownloadedCache();
    if (VIEWS[view]) {
      // Show soundwave loader immediately
      const content = document.getElementById("content");
      content.innerHTML = `<div class="soundwave-loader"><div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div></div>`;
      // Run view (may be async)
      Promise.resolve(VIEWS[view](params)).catch(() => {});
    }
  },
};

// Sidebar navigation
document.querySelectorAll(".nav-item[data-view]").forEach(el => {
  el.addEventListener("click", e => {
    e.preventDefault();
    if (el.dataset.view === "queue") _resetDownloadBadge();
    APP.navigate(el.dataset.view);
  });
});

// Queue modal close
document.getElementById("close-queue-modal").addEventListener("click", () => {
  document.getElementById("queue-modal").classList.remove("open");
});
document.getElementById("queue-modal").addEventListener("click", e => {
  if (e.target.id === "queue-modal") e.target.classList.remove("open");
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
    const options = await API.get("/api/folder-options");
    const buttons = options.map((o, i) => ({
      label: o.label, value: o.path, primary: i === 0,
    }));
    buttons.push({ label: "Cancel", value: null });
    const pick = await showConfirm({
      title: "Choose Download Folder",
      body: "Select a location or type a custom path directly in the field.",
      buttons,
    });
    if (pick) document.getElementById("s-dl-path").value = pick;
  } catch (e) {
    toast("Could not load folder options", "error");
  }
});

document.getElementById("reset-download-db").addEventListener("click", async () => {
  const answer = await showConfirm({
    title: "Reset Download Database",
    body: "This will clear the record of downloaded tracks so everything shows \"Download\" again. Your music files won't be deleted.",
    buttons: [
      { label: "Cancel", value: false },
      { label: "Reset", value: true, primary: true },
    ],
  });
  if (!answer) return;
  try {
    await API.del("/api/downloaded-ids");
    _invalidateDownloadedCache();
    toast("Download database cleared", "success");
  } catch (e) {
    toast("Failed to reset", "error");
  }
});

document.getElementById("disconnect-spotify").addEventListener("click", async () => {
  const answer = await showConfirm({
    title: "Disconnect Spotify",
    body: "This will remove your saved token. You'll need to re-authenticate to use SONGER.",
    buttons: [
      { label: "Cancel", value: false },
      { label: "Disconnect", value: true, primary: true },
    ],
  });
  if (!answer) return;
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
  const newPath = document.getElementById("s-dl-path").value.trim();

  // Check if download path changed — warn about library impact
  try {
    const cfg = await API.get("/api/config");
    const oldPath = (cfg.download?.path || "").trim();
    if (newPath && oldPath && newPath !== oldPath) {
      const choice = await showConfirm({
        title: "Download Path Changed",
        body: `<p>You're changing from:</p>
          <p style="color:var(--text);font-weight:600;font-size:12px;padding:6px 10px;background:var(--surface-2);border-radius:6px;margin:4px 0">${oldPath}</p>
          <p>to:</p>
          <p style="color:var(--text);font-weight:600;font-size:12px;padding:6px 10px;background:var(--surface-2);border-radius:6px;margin:4px 0">${newPath}</p>
          <p style="margin-top:8px">Your existing music files in the old folder won't be moved. Choose how to handle this:</p>`,
        buttons: [
          { label: "Keep both (recommended)", value: "keep", primary: true },
          { label: "Only use new path", value: "new" },
          { label: "Cancel", value: null },
        ],
      });
      if (choice === null) return;
      if (choice === "keep") {
        // Save old path as secondary library source
        await API.post("/api/settings", {
          download: {
            path: newPath,
            format: document.getElementById("s-format").value,
            source: document.getElementById("s-source").value,
            legacy_paths: [...new Set([...(cfg.download?.legacy_paths || []), oldPath])],
          },
          soulseek: {
            slskd_url: document.getElementById("s-slsk-url").value,
            slskd_api_key: document.getElementById("s-slsk-key").value,
          },
        });
        settingsModal.classList.remove("open");
        toast("Settings saved. Old library preserved.", "success");
        return;
      }
      // "new" → just save normally, old files stay but won't show in library
    }
  } catch (e) {}

  try {
    await API.post("/api/settings", {
      download: {
        path: newPath,
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

// Ctrl+Shift+T → Trending (hidden)
document.addEventListener("keydown", e => {
  if (e.ctrlKey && e.shiftKey && e.key === "T") {
    e.preventDefault();
    APP.navigate("trending");
  }
});

// Boot
lucide.createIcons();
APP.navigate("home");
checkOnboarding();
