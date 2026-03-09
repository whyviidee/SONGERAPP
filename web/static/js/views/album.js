// web/static/js/views/album.js
async function renderAlbum(params = {}) {
  const content = document.getElementById("content");
  if (!params.id) {
    content.innerHTML = `<div class="empty-state">No album selected</div>`;
    return;
  }

  content.innerHTML = `<div class="loading-spinner"><i data-lucide="loader-2" width="20" height="20"></i> Loading album...</div>`;
  lucide.createIcons();

  try {
    const data = await API.get(`/api/album/${params.id}`);
    const album = data.album;
    const tracks = data.tracks || [];

    content.innerHTML = `
      <div class="detail-back" id="album-back">
        <i data-lucide="arrow-left" width="16" height="16"></i> Back
      </div>

      <div class="album-header">
        ${album.cover
          ? `<img class="album-header-cover" src="${album.cover}" alt="">`
          : `<div class="album-header-cover album-header-cover--empty"><i data-lucide="disc" width="48" height="48"></i></div>`}
        <div class="album-header-info">
          <div class="album-header-type">Album</div>
          <div class="album-header-name">${album.name}</div>
          <div class="album-header-meta">
            <span class="album-header-artist" ${album.artist_id ? `data-artist-id="${album.artist_id}" style="cursor:pointer;text-decoration:underline"` : ""}>${album.artist}</span>
            ${album.year ? ` · ${album.year}` : ""}
            ${album.total_tracks ? ` · ${album.total_tracks} tracks` : ""}
          </div>
          <div style="display:flex;gap:8px;margin-top:12px">
            <button class="btn-primary" id="album-download-all">
              <i data-lucide="download" width="14" height="14"></i> Download All
            </button>
            <button class="btn-sm" id="album-download-zip" style="height:36px;font-size:12px">
              <i data-lucide="archive" width="14" height="14"></i> Download ZIP
            </button>
          </div>
        </div>
      </div>

      <div class="track-list" id="album-tracks">
        ${tracks.map((t, i) => `
          <div class="track-row" data-id="${t.id}" data-preview-url="${t.preview_url || ""}" data-track-name="${t.name}" data-track-artist="${t.artist}" data-track-album="${t.album}" data-track-cover="${t.cover || ""}">
            <div class="track-number">${i + 1}</div>
            ${t.cover
              ? `<img class="track-cover" src="${t.cover}" alt="">`
              : `<div class="track-cover" style="display:flex;align-items:center;justify-content:center"><i data-lucide="music" width="16" height="16"></i></div>`}
            <div class="track-info">
              <div class="track-name">${t.name}</div>
              <div class="track-artist">${_artistHTML(t.artist, t.artist_id)}</div>
            </div>
            <div class="track-duration">${fmtDuration(t.duration_ms)}</div>
            <button class="btn-download" data-id="${t.id}" data-name="${t.name}" data-artist="${t.artist}" data-album="${t.album}" data-cover="${t.cover || ""}">
              <i data-lucide="download" width="14" height="14"></i> Download
            </button>
          </div>
        `).join("")}
      </div>
    `;
    lucide.createIcons();

    // Back button
    document.getElementById("album-back").addEventListener("click", () => {
      if (params._from === "artist" && params._fromId) {
        APP.navigate("artist", { id: params._fromId });
      } else {
        APP.navigate("search", { q: params._q || "" });
      }
    });

    // Artist name click → navigate to artist
    const artistEl = content.querySelector(".album-header-artist[data-artist-id]");
    if (artistEl) {
      artistEl.addEventListener("click", () => {
        APP.navigate("artist", { id: artistEl.dataset.artistId });
      });
    }

    // Download All
    document.getElementById("album-download-all").addEventListener("click", async () => {
      const btn = document.getElementById("album-download-all");
      btn.innerHTML = `<i data-lucide="loader-2" width="14" height="14"></i> Adding all...`;
      btn.disabled = true;
      lucide.createIcons();
      let added = 0;
      for (const t of tracks) {
        try {
          await API.post("/api/download", {
            id: t.id, name: t.name, artist: t.artist, album: t.album, cover: t.cover || "", uri: "",
          });
          added++;
        } catch (e) {}
      }
      btn.innerHTML = `<i data-lucide="check" width="14" height="14"></i> ${added} queued`;
      lucide.createIcons();
      toast(`${added} tracks added to queue`, "success");
    });

    // Download ZIP
    document.getElementById("album-download-zip").addEventListener("click", () => {
      zipFlow(
        document.getElementById("album-download-zip"),
        tracks.map(t => ({ id: t.id, name: t.name, artist: t.artist, album: t.album, cover: t.cover || "" })),
        album.name,
      );
    });

    // Individual download buttons + artist links + preview
    await _wireDownloadButtons(content);
    _wireArtistLinks(content);
    _wirePreview(content, tracks);
  } catch (err) {
    content.innerHTML = `<div class="empty-state" style="color:#ef4444"><i data-lucide="alert-circle" width="32" height="32"></i>${err.message}</div>`;
    lucide.createIcons();
  }
}
