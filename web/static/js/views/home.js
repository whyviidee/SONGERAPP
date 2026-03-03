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
    action: async () => {
      // Read from clipboard if available, otherwise let user type in search
      try {
        const clip = await navigator.clipboard.readText();
        if (clip && clip.includes("spotify.com")) {
          APP.navigate("search", { q: clip.trim() });
          return;
        }
      } catch (e) {}
      // Fallback: focus search and let user paste
      APP.navigate("search");
      setTimeout(() => {
        const input = document.getElementById("search-input");
        if (input) { input.focus(); input.placeholder = "Paste Spotify URL here..."; }
      }, 100);
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

let _currentPlayingCard = null;

async function _loadRecent() {
  try {
    const history = await API.get("/api/history");
    const downloadedMap = await _getDownloadedMap();
    const recent = history.slice(0, 6);
    if (recent.length === 0) return;

    document.getElementById("recent-section").style.display = "";

    document.getElementById("recent-grid").innerHTML = recent.map(h => {
      const label = h.name || "Unknown";
      const sub = [h.format?.toUpperCase(), h.done_count > 1 ? `${h.done_count} tracks` : ""].filter(Boolean).join(" · ");
      // Try to find the file path from downloaded map
      const parts = label.split(" – ");
      return `
        <div class="album-card recent-playable" title="${_homeEsc(label)}" data-name="${_homeEsc(label)}" data-cover="${_homeEsc(h.cover || "")}">
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

    // Click to play/pause recently downloaded
    document.querySelectorAll(".recent-playable").forEach(card => {
      card.addEventListener("click", async () => {
        const name = card.dataset.name || "";
        const cover = card.dataset.cover || "";
        // Find matching file in downloaded map
        const map = await _getDownloadedMap();
        let filePath = null;
        for (const [id, path] of Object.entries(map)) {
          if (path && name && (path.includes(name.split(" – ").pop()?.trim()) || name.includes(path.split(/[\\/]/).pop()?.replace(/\.[^.]+$/, "")))) {
            filePath = path;
            break;
          }
        }
        if (!filePath) {
          // Fallback: try library scan
          try {
            const lib = await API.get("/api/library");
            const parts = name.split(" – ");
            const trackName = parts.length > 1 ? parts[1].trim() : parts[0].trim();
            const match = lib.find(f => f.name.toLowerCase().includes(trackName.toLowerCase()));
            if (match) filePath = match.path;
          } catch (e) {}
        }

        if (!filePath) {
          toast("File not found in library", "error");
          return;
        }

        const audioEl = document.getElementById("audio-el");
        // Toggle play/pause if same card
        if (_currentPlayingCard === card && !audioEl.paused) {
          audioEl.pause();
          card.classList.remove("playing");
          document.getElementById("play-icon").setAttribute("data-lucide", "play");
          lucide.createIcons();
          return;
        }
        // Remove playing state from previous
        if (_currentPlayingCard) _currentPlayingCard.classList.remove("playing");
        _currentPlayingCard = card;
        card.classList.add("playing");

        const parts = name.split(" – ");
        PLAYER.playFile(filePath, {
          name: parts.length > 1 ? parts[1].trim() : name,
          artist: parts.length > 1 ? parts[0].trim() : "",
          cover: cover,
        });
      });
    });

    // Listen for audio pause to update card state
    document.getElementById("audio-el").addEventListener("pause", () => {
      if (_currentPlayingCard) _currentPlayingCard.classList.remove("playing");
    });
    document.getElementById("audio-el").addEventListener("play", () => {
      if (_currentPlayingCard) _currentPlayingCard.classList.add("playing");
    });

    document.getElementById("clear-recent").addEventListener("click", async e => {
      e.preventDefault();
      const answer = await showConfirm({
        title: "Clear History",
        body: "This will clear your download history. Your files won't be deleted.",
        buttons: [
          { label: "Cancel", value: false },
          { label: "Clear", value: true, primary: true },
        ],
      });
      if (!answer) return;
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

  // Click top artist → search for artist to find their Spotify page
  document.querySelectorAll("#top-artists-grid .artist-card").forEach(card => {
    card.addEventListener("click", async () => {
      const name = card.dataset.name;
      // Try to find artist ID via search API, then navigate directly
      try {
        const data = await API.get(`/api/search?q=${encodeURIComponent(name)}`);
        const artists = data.artists || [];
        const match = artists.find(a => a.name.toLowerCase() === name.toLowerCase());
        if (match) {
          APP.navigate("artist", { id: match.id });
          return;
        }
      } catch (e) {}
      // Fallback: plain search
      APP.navigate("search", { q: name });
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
