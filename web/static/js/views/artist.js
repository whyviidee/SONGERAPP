// web/static/js/views/artist.js
async function renderArtist(params = {}) {
  const content = document.getElementById("content");
  if (!params.id) {
    content.innerHTML = `<div class="empty-state">No artist selected</div>`;
    return;
  }

  content.innerHTML = `<div class="loading-spinner"><i data-lucide="loader-2" width="20" height="20"></i> Loading artist...</div>`;
  lucide.createIcons();

  try {
    const data = await API.get(`/api/artist/${params.id}`);
    const artist = data.artist;
    const topTracks = data.top_tracks || [];
    const albums = data.albums || [];

    const fmtFollowers = (n) => {
      if (n >= 1000000) return (n / 1000000).toFixed(1) + "M";
      if (n >= 1000) return (n / 1000).toFixed(1) + "K";
      return String(n);
    };

    content.innerHTML = `
      <div class="detail-back" id="artist-back">
        <i data-lucide="arrow-left" width="16" height="16"></i> Back
      </div>

      <div class="artist-header">
        ${artist.cover
          ? `<img class="artist-header-img" src="${artist.cover}" alt="">`
          : `<div class="artist-header-img artist-header-img--empty"><i data-lucide="user" width="48" height="48"></i></div>`}
        <div class="artist-header-info">
          <div class="artist-header-type">Artist</div>
          <div class="artist-header-name">${artist.name}</div>
          <div class="artist-header-meta">
            ${artist.genres.length ? artist.genres.join(", ") : ""}
            ${artist.followers ? ` · ${fmtFollowers(artist.followers)} followers` : ""}
          </div>
        </div>
      </div>

      ${topTracks.length ? `
        <div class="search-section">
          <div class="search-section-header">
            <span class="search-section-title"><i data-lucide="trending-up" width="16" height="16"></i> Popular</span>
          </div>
          <div class="track-list" id="artist-top-tracks">
            ${topTracks.map((t, i) => `
              <div class="track-row" data-id="${t.id}" data-preview-url="${t.preview_url || ""}" data-track-name="${t.name}" data-track-artist="${t.artist}" data-track-album="${t.album}" data-track-cover="${t.cover || ""}">
                <div class="track-number">${i + 1}</div>
                ${t.cover
                  ? `<img class="track-cover" src="${t.cover}" alt="">`
                  : `<div class="track-cover" style="display:flex;align-items:center;justify-content:center"><i data-lucide="music" width="16" height="16"></i></div>`}
                <div class="track-info">
                  <div class="track-name">${t.name}</div>
                  <div class="track-artist">${_artistHTML(t.artist, t.artist_id)}${t.album ? ` · ${t.album}` : ""}</div>
                </div>
                <div class="track-duration">${fmtDuration(t.duration_ms)}</div>
                <button class="btn-download" data-id="${t.id}" data-name="${t.name}" data-artist="${t.artist}" data-album="${t.album}" data-cover="${t.cover || ""}">
                  <i data-lucide="download" width="14" height="14"></i> Download
                </button>
              </div>
            `).join("")}
          </div>
        </div>
      ` : ""}

      ${albums.length ? `
        <div class="search-section">
          <div class="search-section-header">
            <span class="search-section-title"><i data-lucide="disc-3" width="16" height="16"></i> Discography</span>
          </div>
          <div class="album-grid" id="artist-albums">
            ${albums.map(a => `
              <div class="album-card" data-id="${a.id}">
                ${a.cover
                  ? `<img class="album-card-cover" src="${a.cover}" alt="">`
                  : `<div class="album-card-cover"><i data-lucide="disc" width="20" height="20"></i></div>`}
                <div class="album-card-info">
                  <div class="album-card-name">${a.name}</div>
                  <div class="album-card-meta">${a.year || ""}${a.total_tracks ? ` · ${a.total_tracks} tracks` : ""}</div>
                </div>
              </div>
            `).join("")}
          </div>
        </div>
      ` : ""}
    `;
    lucide.createIcons();

    // Back button
    document.getElementById("artist-back").addEventListener("click", () => {
      APP.navigate("search", { q: params._q || artist.name });
    });

    // Album cards → album detail
    content.querySelectorAll(".album-card").forEach(card => {
      card.addEventListener("click", () => {
        APP.navigate("album", { id: card.dataset.id, _from: "artist", _fromId: params.id, _q: params._q });
      });
    });

    // Wire download buttons + artist links + preview
    await _wireDownloadButtons(content);
    _wireArtistLinks(content);
    _wirePreview(content, topTracks);

    // Load user's owned tracks for this artist from library
    try {
      const lib = await API.get("/api/library");
      const artistName = artist.name.toLowerCase();
      const owned = lib.filter(f => f.artist.toLowerCase() === artistName);
      if (owned.length) {
        const esc = s => String(s ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
        const section = document.createElement("div");
        section.className = "search-section";
        section.innerHTML = `
          <div class="search-section-header">
            <span class="search-section-title"><i data-lucide="hard-drive" width="16" height="16"></i> In Your Library</span>
            <span style="font-size:11px;color:var(--text-3)">${owned.length} track${owned.length !== 1 ? "s" : ""}</span>
          </div>
          <div class="track-list">
            ${owned.map((t, i) => `
              <div class="track-row lib-owned-track" data-path="${esc(t.path)}">
                <div class="track-number">${i + 1}</div>
                <div class="track-info">
                  <div class="track-name">${esc(t.name)}</div>
                  <div class="track-artist">${esc(t.album || "")}</div>
                </div>
                <span class="lib-track-tag">${esc(t.ext.toUpperCase())}</span>
                <span style="font-size:11px;color:var(--text-3)">${t.size_mb} MB</span>
                <button class="ctrl-btn play-owned" data-path="${esc(t.path)}" title="Play">
                  <i data-lucide="play" width="14" height="14"></i>
                </button>
              </div>
            `).join("")}
          </div>`;
        content.appendChild(section);
        lucide.createIcons();

        // Wire play buttons
        section.querySelectorAll(".play-owned").forEach(btn => {
          btn.addEventListener("click", e => {
            e.stopPropagation();
            PLAYER.playFile(btn.dataset.path, { name: btn.closest(".track-row").querySelector(".track-name").textContent, artist: artist.name });
          });
        });
        // Double-click row to play
        section.querySelectorAll(".lib-owned-track").forEach(row => {
          row.addEventListener("dblclick", () => {
            const btn = row.querySelector(".play-owned");
            if (btn) PLAYER.playFile(btn.dataset.path, { name: row.querySelector(".track-name").textContent, artist: artist.name });
          });
        });
      }
    } catch (e) {}

  } catch (err) {
    content.innerHTML = `<div class="empty-state" style="color:#ef4444"><i data-lucide="alert-circle" width="32" height="32"></i>${err.message}</div>`;
    lucide.createIcons();
  }
}
