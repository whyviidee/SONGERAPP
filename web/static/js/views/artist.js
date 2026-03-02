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
              <div class="track-row" data-id="${t.id}">
                <div class="track-number">${i + 1}</div>
                ${t.cover
                  ? `<img class="track-cover" src="${t.cover}" alt="">`
                  : `<div class="track-cover" style="display:flex;align-items:center;justify-content:center"><i data-lucide="music" width="16" height="16"></i></div>`}
                <div class="track-info">
                  <div class="track-name">${t.name}</div>
                  <div class="track-artist">${t.artist} · ${t.album}</div>
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

    // Wire download buttons
    await _wireDownloadButtons(content);
  } catch (err) {
    content.innerHTML = `<div class="empty-state" style="color:#ef4444"><i data-lucide="alert-circle" width="32" height="32"></i>${err.message}</div>`;
    lucide.createIcons();
  }
}
