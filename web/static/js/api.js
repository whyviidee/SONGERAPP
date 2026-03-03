// web/static/js/api.js
const API = {
  async get(path) {
    const r = await fetch(path);
    if (!r.ok) throw new Error(`GET ${path} → ${r.status}`);
    return r.json();
  },
  async post(path, body) {
    const r = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(`POST ${path} → ${r.status}`);
    return r.json();
  },
  async del(path) {
    const r = await fetch(path, { method: "DELETE" });
    if (!r.ok) throw new Error(`DELETE ${path} → ${r.status}`);
    return r.json();
  },
};

function toast(msg, type = "info") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = msg;
  document.getElementById("toast-container").appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

function fmtDuration(ms) {
  if (!ms) return "—";
  const s = Math.floor(ms / 1000);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

// Cache of downloaded track IDs → file paths (refreshed per view)
let _downloadedMap = null;

async function _getDownloadedMap() {
  if (_downloadedMap !== null) return _downloadedMap;
  try { _downloadedMap = await API.get("/api/downloaded-ids"); }
  catch (e) { _downloadedMap = {}; }
  return _downloadedMap;
}

function _invalidateDownloadedCache() { _downloadedMap = null; }

// Build clickable artist HTML — splits "Artist1, Artist2" into individual links
function _artistHTML(artistStr, artistId) {
  if (!artistStr) return "";
  // If there's a single artist with an ID, make the whole thing clickable
  if (artistId && !artistStr.includes(",")) {
    return `<a class="artist-link" data-artist-id="${_escAttr(artistId)}">${_escHtml(artistStr)}</a>`;
  }
  // Multiple artists: split by comma, first one gets the ID if available
  const parts = artistStr.split(/,\s*/);
  return parts.map((name, i) => {
    if (i === 0 && artistId) {
      return `<a class="artist-link" data-artist-id="${_escAttr(artistId)}">${_escHtml(name)}</a>`;
    }
    return `<span class="artist-link artist-link--search" data-artist-name="${_escAttr(name)}">${_escHtml(name)}</span>`;
  }).join(", ");
}

function _escHtml(s) { return String(s ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
function _escAttr(s) { return String(s ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }

// ── Custom confirm/modal system (replaces browser confirm/prompt) ──
function showConfirm({ title = "Confirm", body = "", buttons = [] }) {
  return new Promise(resolve => {
    const overlay = document.getElementById("confirm-modal");
    document.getElementById("confirm-modal-title").textContent = title;
    document.getElementById("confirm-modal-body").innerHTML = body;
    const actions = document.getElementById("confirm-modal-actions");
    actions.innerHTML = "";
    buttons.forEach(btn => {
      const el = document.createElement("button");
      el.className = btn.primary ? "btn-primary" : "btn-ghost";
      el.textContent = btn.label;
      el.addEventListener("click", () => {
        overlay.classList.remove("open");
        resolve(btn.value);
      });
      actions.appendChild(el);
    });
    overlay.classList.add("open");
    // Close on overlay click
    overlay.onclick = e => {
      if (e.target === overlay) { overlay.classList.remove("open"); resolve(null); }
    };
  });
}

// ── Queue modal (Now Playing) ──
function _openQueueModal() {
  const overlay = document.getElementById("queue-modal");
  const list = document.getElementById("queue-modal-list");
  if (!window.PLAYER || !window.PLAYER._getPlaylist) {
    list.innerHTML = `<div class="empty-state" style="height:100px">No tracks in queue</div>`;
  } else {
    const { playlist, currentIdx, isPreview } = PLAYER._getPlaylist();
    if (!playlist.length) {
      list.innerHTML = `<div class="empty-state" style="height:100px">No tracks in queue</div>`;
    } else {
      list.innerHTML = playlist.map((t, i) => `
        <div class="track-row queue-modal-track ${i === currentIdx ? "queue-modal-active" : ""}" data-idx="${i}">
          ${t.cover ? `<img class="track-cover" src="${t.cover}" alt="" style="width:36px;height:36px">` : `<div class="track-cover" style="width:36px;height:36px;background:var(--surface-2)"></div>`}
          <div class="track-info">
            <div class="track-name" style="font-size:12px">${_escHtml(t.name || "")}</div>
            <div class="track-artist" style="font-size:10px">${_escHtml(t.artist || "")}</div>
          </div>
          ${isPreview ? `<span style="font-size:9px;color:var(--accent);font-weight:700">PREVIEW</span>` : ""}
        </div>
      `).join("");
      list.querySelectorAll(".queue-modal-track").forEach(row => {
        row.addEventListener("click", () => {
          const idx = parseInt(row.dataset.idx);
          if (isPreview) {
            PLAYER.setPreviewPlaylist(playlist, idx);
          } else {
            PLAYER.setPlaylist(playlist, idx);
          }
          _openQueueModal(); // refresh active state
        });
      });
    }
  }
  overlay.classList.add("open");
  lucide.createIcons();
}

// ── Download badge counter (instead of stacking toasts) ──
let _dlBadgeCount = 0;
function _incrementDownloadBadge() {
  _dlBadgeCount++;
  const badge = document.getElementById("queue-badge");
  if (badge) {
    badge.textContent = `+${_dlBadgeCount}`;
    badge.style.display = "";
  }
}
function _resetDownloadBadge() {
  _dlBadgeCount = 0;
  const badge = document.getElementById("queue-badge");
  if (badge) badge.style.display = "none";
}

// Wire artist link clicks → navigate to artist page
function _wireArtistLinks(container) {
  container.querySelectorAll(".artist-link[data-artist-id]").forEach(el => {
    el.addEventListener("click", e => {
      e.stopPropagation();
      APP.navigate("artist", { id: el.dataset.artistId });
    });
  });
  container.querySelectorAll(".artist-link--search[data-artist-name]").forEach(el => {
    el.addEventListener("click", e => {
      e.stopPropagation();
      APP.navigate("search", { q: el.dataset.artistName });
    });
  });
}

// Wire preview buttons + double-click to play downloaded tracks
function _wirePreview(container, tracks) {
  // Add preview button to tracks that have preview_url
  container.querySelectorAll(".track-row[data-preview-url]").forEach(row => {
    const url = row.dataset.previewUrl;
    if (!url) return;
    const dlBtn = row.querySelector(".btn-download");
    if (!dlBtn) return;
    const previewBtn = document.createElement("button");
    previewBtn.className = "btn-preview";
    previewBtn.title = "Preview 30s";
    previewBtn.innerHTML = `<i data-lucide="headphones" width="13" height="13"></i>`;
    dlBtn.parentNode.insertBefore(previewBtn, dlBtn);

    previewBtn.addEventListener("click", e => {
      e.stopPropagation();
      const info = {
        name: row.dataset.trackName || "",
        artist: row.dataset.trackArtist || "",
        album: row.dataset.trackAlbum || "",
        cover: row.dataset.trackCover || "",
        preview_url: url,
      };
      if (tracks && tracks.length) {
        const previewable = tracks.filter(t => t.preview_url);
        const idx = previewable.findIndex(t => t.id === row.dataset.id);
        PLAYER.setPreviewPlaylist(previewable, Math.max(idx, 0));
      } else {
        PLAYER.preview(url, info);
      }
    });
  });
  lucide.createIcons();

  // Double-click on track row → play local file if downloaded
  container.querySelectorAll(".track-row[data-id]").forEach(row => {
    row.addEventListener("dblclick", async e => {
      if (e.target.closest("button") || e.target.closest("a")) return;
      const trackId = row.dataset.id;
      if (!trackId) return;
      const map = await _getDownloadedMap();
      const filePath = map[trackId];
      if (filePath) {
        PLAYER.playFile(filePath, {
          name: row.dataset.trackName || "",
          artist: row.dataset.trackArtist || "",
          album: row.dataset.trackAlbum || "",
          cover: row.dataset.trackCover || "",
        });
      }
    });
  });
}

async function _wireDownloadButtons(container) {
  const downloaded = await _getDownloadedMap();

  container.querySelectorAll(".btn-download").forEach(btn => {
    const trackId = btn.dataset.id;
    const filePath = downloaded[trackId];

    if (filePath) {
      btn.innerHTML = `<i data-lucide="play" width="14" height="14"></i> Play`;
      btn.classList.add("done");
      lucide.createIcons();
      btn.addEventListener("click", e => {
        e.stopPropagation();
        PLAYER.playFile(filePath, {
          name: btn.dataset.name, artist: btn.dataset.artist,
          album: btn.dataset.album,
        });
      });
      return;
    }

    btn.addEventListener("click", async e => {
      e.stopPropagation();
      btn.innerHTML = `<i data-lucide="loader-2" width="14" height="14"></i> Adding...`;
      btn.classList.add("downloading");
      lucide.createIcons();
      try {
        await API.post("/api/download", {
          id: btn.dataset.id, name: btn.dataset.name,
          artist: btn.dataset.artist, album: btn.dataset.album,
          uri: btn.dataset.uri || "", cover: btn.dataset.cover || "",
        });
        btn.innerHTML = `<i data-lucide="check" width="14" height="14"></i> Queued`;
        btn.classList.remove("downloading");
        btn.classList.add("done");
        _invalidateDownloadedCache();
        lucide.createIcons();
        _incrementDownloadBadge();
      } catch (err) {
        btn.innerHTML = `<i data-lucide="download" width="14" height="14"></i> Download`;
        btn.classList.remove("downloading");
        lucide.createIcons();
        toast(`Error: ${err.message}`, "error");
      }
    });
  });
}
