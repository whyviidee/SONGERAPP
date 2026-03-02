// web/static/js/views/home.js
async function renderHome() {
  const content = document.getElementById("content");
  content.innerHTML = `
    <div class="search-row">
      <div class="search-input-wrap">
        <input id="search-input" type="text" placeholder="Search music, paste Spotify URL...">
      </div>
      <button class="btn-search" id="do-search">
        <i data-lucide="search" width="16" height="16"></i>
        Search
      </button>
    </div>

    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon"><i data-lucide="music-2" width="15" height="15"></i></div>
        <div class="stat-value" id="stat-0">—</div>
        <div class="stat-label">tracks in library</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon accent"><i data-lucide="download" width="15" height="15"></i></div>
        <div class="stat-value accent" id="stat-1">—</div>
        <div class="stat-label">downloading now</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon"><i data-lucide="list-music" width="15" height="15"></i></div>
        <div class="stat-value" id="stat-2">—</div>
        <div class="stat-label">playlists synced</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon"><i data-lucide="hard-drive" width="15" height="15"></i></div>
        <div class="stat-value" id="stat-3">—</div>
        <div class="stat-label">storage used</div>
      </div>
    </div>

    <div class="quick-actions" id="quick-actions"></div>

    <div id="recent-section" style="display:none">
      <div class="section-header">
        <span class="section-title">Recently Downloaded</span>
        <div style="display:flex;gap:8px;align-items:center">
          <a class="section-link" id="clear-recent" href="#" style="color:var(--text-3);font-size:11px">Clear</a>
          <a class="section-link" data-view="history" href="#">View all →</a>
        </div>
      </div>
      <div class="album-grid" id="recent-grid"></div>
    </div>

    <div id="top-artists-section" style="display:none">
      <div class="section-header">
        <span class="section-title">Your Top Artists</span>
        <a class="section-link" data-view="library" href="#">Library →</a>
      </div>
      <div class="artist-grid" id="top-artists-grid"></div>
    </div>

    <div id="recommendations-section" style="display:none">
      <div class="section-header">
        <span class="section-title"><i data-lucide="sparkles" width="14" height="14" style="display:inline"></i> Recommended for You</span>
      </div>
      <div class="track-list" id="recommendations-list"></div>
    </div>
  `;

  lucide.createIcons();

  // Wire search
  document.getElementById("do-search").addEventListener("click", () => {
    const q = document.getElementById("search-input").value.trim();
    if (q) APP.navigate("search", { q });
  });
  document.getElementById("search-input").addEventListener("keydown", e => {
    if (e.key === "Enter") document.getElementById("do-search").click();
  });

  // Wire section links
  content.querySelectorAll("[data-view]").forEach(el => {
    if (el.closest("#sidebar")) return;
    el.addEventListener("click", e => {
      e.preventDefault();
      APP.navigate(el.dataset.view);
    });
  });

  // Load stats + build quick actions
  let stats = null;
  try {
    stats = await API.get("/api/stats");
    document.getElementById("stat-0").textContent = stats.tracks.toLocaleString();
    document.getElementById("stat-1").textContent = stats.downloading;
    document.getElementById("stat-2").textContent = stats.playlists;
    document.getElementById("stat-3").textContent = `${stats.storage_gb} GB`;
  } catch (e) {}

  // Quick actions
  _buildQuickActions(stats);

  // Load recent history, top artists, recommendations in parallel
  _loadRecent();
  _loadTopArtists(stats);
  _loadRecommendations();
}

function _buildQuickActions(stats) {
  const actions = [];

  if (stats && stats.pending > 0) {
    actions.push({
      icon: "play", label: `${stats.pending} downloads in progress`,
      action: () => APP.navigate("queue"),
    });
  }

  actions.push({
    icon: "heart", label: "Sync liked songs",
    action: () => APP.navigate("liked"),
  });

  actions.push({
    icon: "link", label: "Import Spotify URL",
    action: () => {
      const url = prompt("Paste a Spotify URL (playlist, album, or track):");
      if (url && url.trim()) APP.navigate("search", { q: url.trim() });
    },
  });

  actions.push({
    icon: "folder-open", label: "Open library folder",
    action: async () => {
      try { await API.get("/api/open-folder"); }
      catch (e) { toast("Could not open folder", "error"); }
    },
  });

  const container = document.getElementById("quick-actions");
  container.innerHTML = actions.map(a => `
    <button class="quick-action-btn">
      <i data-lucide="${a.icon}" width="16" height="16"></i>
      <span>${a.label}</span>
    </button>
  `).join("");
  lucide.createIcons();

  container.querySelectorAll(".quick-action-btn").forEach((btn, i) => {
    btn.addEventListener("click", actions[i].action);
  });
}

async function _loadRecent() {
  try {
    const history = await API.get("/api/history");
    const recent = history.slice(0, 6);
    if (recent.length === 0) return;

    document.getElementById("recent-section").style.display = "";

    document.getElementById("recent-grid").innerHTML = recent.map(h => {
      const label = h.name || "Unknown";
      const sub = [h.format?.toUpperCase(), h.done_count > 1 ? `${h.done_count} tracks` : ""].filter(Boolean).join(" · ");
      return `
        <div class="album-card" title="${_homeEsc(label)}">
          ${h.cover
            ? `<img class="album-card-cover" src="${_homeEsc(h.cover)}" alt="" onerror="this.style.opacity='0'">`
            : `<div class="album-card-cover"><i data-lucide="disc-3" width="28" height="28"></i></div>`}
          <div class="album-card-info">
            <div class="album-card-name">${_homeEsc(label)}</div>
            <div class="album-card-meta">${_homeEsc(sub)}</div>
          </div>
        </div>`;
    }).join("");
    lucide.createIcons();

    document.getElementById("clear-recent").addEventListener("click", async e => {
      e.preventDefault();
      if (!confirm("Clear download history?")) return;
      try {
        await API.del("/api/history");
        document.getElementById("recent-section").style.display = "none";
        toast("History cleared", "success");
      } catch (err) { toast("Failed to clear", "error"); }
    });
  } catch (e) {}
}

function _loadTopArtists(stats) {
  if (!stats || !stats.top_artists || stats.top_artists.length === 0) return;

  document.getElementById("top-artists-section").style.display = "";
  document.getElementById("top-artists-grid").innerHTML = stats.top_artists.map(a => `
    <div class="artist-card" data-name="${_homeEsc(a.name)}">
      ${a.cover
        ? `<img class="artist-avatar" src="${_homeEsc(a.cover)}" alt="" style="object-fit:cover">`
        : `<div class="artist-avatar"><i data-lucide="user" width="24" height="24"></i></div>`}
      <div class="artist-card-info">
        <div class="artist-card-name">${_homeEsc(a.name)}</div>
        <div class="artist-card-genres">${a.count} tracks</div>
      </div>
    </div>
  `).join("");
  lucide.createIcons();

  document.querySelectorAll("#top-artists-grid .artist-card").forEach(card => {
    card.addEventListener("click", () => {
      APP.navigate("search", { q: card.dataset.name });
    });
  });
}

async function _loadRecommendations() {
  try {
    const tracks = await API.get("/api/recommendations");
    if (!tracks || tracks.length === 0) return;

    document.getElementById("recommendations-section").style.display = "";
    document.getElementById("recommendations-list").innerHTML = tracks.map(t => `
      <div class="track-row" data-id="${t.id}">
        ${t.cover
          ? `<img class="track-cover" src="${t.cover}" alt="">`
          : `<div class="track-cover" style="display:flex;align-items:center;justify-content:center"><i data-lucide="music" width="16" height="16"></i></div>`}
        <div class="track-info">
          <div class="track-name">${t.name}</div>
          <div class="track-artist">${t.artist} · ${t.album}</div>
        </div>
        <div class="track-duration">${fmtDuration(t.duration_ms)}</div>
        <button class="btn-download" data-id="${t.id}" data-name="${_homeEsc(t.name)}" data-artist="${_homeEsc(t.artist)}" data-album="${_homeEsc(t.album)}" data-cover="${_homeEsc(t.cover || "")}">
          <i data-lucide="download" width="14" height="14"></i> Download
        </button>
      </div>
    `).join("");
    lucide.createIcons();
    await _wireDownloadButtons(document.getElementById("recommendations-list"));
  } catch (e) {}
}

function _homeEsc(s) {
  return String(s ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}
