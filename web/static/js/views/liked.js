// web/static/js/views/liked.js
let _likedCache = null;

async function renderLiked() {
  const content = document.getElementById("content");
  content.innerHTML = `
    <div class="view-header">
      <span class="view-title">Liked Songs</span>
      <div style="display:flex;gap:8px;align-items:center">
        <span id="liked-count" style="font-size:12px;color:var(--text-2)"></span>
        <button class="btn-sm" id="liked-refresh">
          <i data-lucide="refresh-cw" width="14" height="14"></i> Refresh
        </button>
        <button class="btn-primary" id="liked-dl-all" style="height:32px;font-size:12px;display:none">
          <i data-lucide="download" width="14" height="14"></i> Download all
        </button>
      </div>
    </div>
    <input class="filter-input" id="liked-filter" placeholder="Filter liked songs...">
    <div id="liked-list"><div class="loading-spinner"><i data-lucide="loader-2" width="20" height="20"></i> Loading liked songs...</div></div>
  `;
  lucide.createIcons();

  document.getElementById("liked-refresh").addEventListener("click", async () => {
    _likedCache = null;
    await _loadLiked();
  });

  await _loadLiked();
}

async function _loadLiked() {
  const list = document.getElementById("liked-list");
  if (!list) return;

  if (!_likedCache) {
    list.innerHTML = `<div class="loading-spinner"><i data-lucide="loader-2" width="20" height="20"></i> Loading liked songs...</div>`;
    lucide.createIcons();
    try {
      _likedCache = await API.get("/api/liked-songs");
    } catch (e) {
      list.innerHTML = `<div class="empty-state" style="color:#ef4444">${e.message || "Failed to load liked songs"}</div>`;
      return;
    }
  }

  const countEl = document.getElementById("liked-count");
  const dlAllBtn = document.getElementById("liked-dl-all");
  if (countEl) countEl.textContent = `${_likedCache.length} songs`;
  if (dlAllBtn) {
    dlAllBtn.style.display = "";
    dlAllBtn.onclick = async () => {
      for (const t of _likedCache) {
        await API.post("/api/download", t).catch(() => {});
      }
      toast(`Added ${_likedCache.length} tracks to queue`, "success");
      APP.navigate("queue");
    };
  }

  _renderLikedList(_likedCache);

  const filterInput = document.getElementById("liked-filter");
  if (filterInput) {
    filterInput.addEventListener("input", e => {
      const q = e.target.value.toLowerCase();
      const filtered = q
        ? _likedCache.filter(t => t.name.toLowerCase().includes(q) || t.artist.toLowerCase().includes(q))
        : _likedCache;
      _renderLikedList(filtered);
    });
  }
}

async function _renderLikedList(tracks) {
  const list = document.getElementById("liked-list");
  if (!list) return;

  if (tracks.length === 0) {
    list.innerHTML = `<div class="empty-state">No songs found</div>`;
    return;
  }

  list.innerHTML = `<div class="track-list">${tracks.map(t => `
    <div class="track-row">
      ${t.cover
        ? `<img class="track-cover" src="${_esc(t.cover)}" alt="" onerror="this.style.opacity='0'">`
        : `<div class="track-cover" style="background:var(--surface-2)"></div>`
      }
      <div class="track-info">
        <div class="track-name">${_esc(t.name)}</div>
        <div class="track-artist">${_esc(t.artist)}${t.album ? ` · ${_esc(t.album)}` : ""}</div>
      </div>
      <div class="track-duration">${fmtDuration(t.duration_ms)}</div>
      <button class="btn-download" data-id="${_esc(t.id)}" data-name="${_esc(t.name)}" data-artist="${_esc(t.artist)}" data-album="${_esc(t.album || "")}" data-cover="${_esc(t.cover || "")}">
        <i data-lucide="download" width="14" height="14"></i> Download
      </button>
    </div>`).join("")}</div>`;

  lucide.createIcons();
  await _wireDownloadButtons(list);
}

function _esc(s) {
  return String(s ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}
