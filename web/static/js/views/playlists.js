// web/static/js/views/playlists.js
async function renderPlaylists(params = {}) {
  const content = document.getElementById("content");

  if (params.playlist_id) {
    // Show playlist tracks
    content.innerHTML = `
      <div class="view-header">
        <button class="btn-sm" id="back-playlists"><i data-lucide="arrow-left" width="14" height="14"></i> Back</button>
        <span class="view-title" id="pl-title">Playlist</span>
        <div style="display:flex;gap:8px">
          <button class="btn-sm" id="dl-zip" style="height:32px;font-size:12px">
            <i data-lucide="archive" width="14" height="14"></i> Download ZIP
          </button>
          <button class="btn-primary" id="dl-all" style="height:32px;font-size:12px">
            <i data-lucide="download" width="14" height="14"></i> Download all
          </button>
        </div>
      </div>
      <div id="pl-tracks"><div class="loading-spinner"><i data-lucide="loader-2" width="20" height="20"></i></div></div>
    `;
    lucide.createIcons();
    document.getElementById("back-playlists").addEventListener("click", () => renderPlaylists());

    console.log(`[SONGER] Loading playlist tracks: ${params.playlist_id} (${params.playlist_name})`);
    let tracks;
    try {
      tracks = await API.get(`/api/playlists/${params.playlist_id}/tracks`);
      console.log(`[SONGER] Playlist tracks loaded: ${tracks.length} tracks`, tracks);
    } catch (err) {
      console.error(`[SONGER] Playlist tracks FAILED:`, err);
      document.getElementById("pl-tracks").innerHTML = `<div class="empty-state" style="color:#ef4444"><i data-lucide="alert-circle" width="32" height="32"></i> Failed to load tracks: ${err.message}</div>`;
      lucide.createIcons();
      return;
    }
    if (!tracks.length) {
      console.warn(`[SONGER] Playlist returned 0 tracks`);
      document.getElementById("pl-tracks").innerHTML = `<div class="empty-state"><i data-lucide="music-off" width="32" height="32"></i> No tracks found in this playlist</div>`;
      lucide.createIcons();
      return;
    }
    document.getElementById("pl-title").textContent = params.playlist_name || "Playlist";
    document.getElementById("dl-all").addEventListener("click", async () => {
      for (const t of tracks) {
        await API.post("/api/download", t).catch(() => {});
      }
      toast(`Added ${tracks.length} tracks`, "success");
      APP.navigate("queue");
    });

    document.getElementById("dl-zip").addEventListener("click", async () => {
      const btn = document.getElementById("dl-zip");
      btn.disabled = true;
      btn.innerHTML = `<i data-lucide="loader-2" width="14" height="14"></i> Starting...`;
      lucide.createIcons();
      try {
        const r = await API.post(`/api/playlists/${params.playlist_id}/zip`, { name: params.playlist_name || "playlist" });
        const jobId = r.job_id;
        toast(`ZIP started — ${tracks.length} tracks...`, "info");
        const poll = setInterval(async () => {
          try {
            const s = await API.get(`/api/zip/${jobId}/status`);
            if (s.status === "done") {
              clearInterval(poll);
              btn.disabled = false;
              btn.innerHTML = `<i data-lucide="archive" width="14" height="14"></i> Download ZIP`;
              lucide.createIcons();
              toast(`ZIP ready! ${s.done}/${s.total} tracks`, "success");
              const a = document.createElement("a");
              a.href = `/api/zip/${jobId}`;
              a.click();
            } else if (s.status === "error") {
              clearInterval(poll);
              btn.disabled = false;
              btn.innerHTML = `<i data-lucide="archive" width="14" height="14"></i> Download ZIP`;
              lucide.createIcons();
              toast(`ZIP failed: ${s.error}`, "error");
            } else {
              btn.innerHTML = `<i data-lucide="loader-2" width="14" height="14"></i> ${s.done}/${s.total}`;
              lucide.createIcons();
            }
          } catch (e) {}
        }, 3000);
      } catch (e) {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="archive" width="14" height="14"></i> Download ZIP`;
        lucide.createIcons();
        toast("Failed to start ZIP", "error");
      }
    });

    const plTracksEl = document.getElementById("pl-tracks");
    plTracksEl.innerHTML = `<div class="track-list">${tracks.map(t => `
      <div class="track-row" data-id="${t.id || ""}" data-preview-url="${(t.preview_url || "").replace(/"/g, "&quot;")}" data-track-name="${(t.name || "").replace(/"/g, "&quot;")}" data-track-artist="${(t.artist || "").replace(/"/g, "&quot;")}" data-track-album="${(t.album || "").replace(/"/g, "&quot;")}" data-track-cover="${(t.cover || "").replace(/"/g, "&quot;")}">
        ${t.cover ? `<img class="track-cover" src="${t.cover}" alt="">` : `<div class="track-cover"></div>`}
        <div class="track-info">
          <div class="track-name">${t.name}</div>
          <div class="track-artist">${_artistHTML(t.artist, t.artist_id)}${t.album ? ` · ${t.album}` : ""}</div>
        </div>
        <div class="track-duration">${fmtDuration(t.duration_ms)}</div>
        <button class="btn-download" data-id="${t.id || ""}" data-name="${(t.name || "").replace(/"/g, "&quot;")}" data-artist="${(t.artist || "").replace(/"/g, "&quot;")}" data-album="${(t.album || "").replace(/"/g, "&quot;")}" data-cover="${(t.cover || "").replace(/"/g, "&quot;")}">
          <i data-lucide="download" width="14" height="14"></i> Download
        </button>
      </div>`).join("")}</div>`;
    lucide.createIcons();
    await _wireDownloadButtons(plTracksEl);
    _wireArtistLinks(plTracksEl);
    _wirePreview(plTracksEl, tracks);
    return;
  }

  // Playlist grid
  content.innerHTML = `
    <div class="view-header">
      <span class="view-title">Playlists</span>
      <button class="btn-sm" id="pl-refresh" style="height:32px;font-size:12px">
        <i data-lucide="refresh-cw" width="14" height="14"></i> Refresh
      </button>
    </div>
    <input class="filter-input" id="pl-filter" placeholder="Filter playlists...">
    <div id="pl-grid"><div class="loading-spinner"><i data-lucide="loader-2" width="20" height="20"></i></div></div>
  `;
  lucide.createIcons();

  try {
    console.log(`[SONGER] Loading playlists...`);
    const playlists = await API.get("/api/playlists");
    console.log(`[SONGER] Playlists loaded: ${playlists.length}`, playlists.map(p => ({id: p.id, name: p.name, tracks: p.tracks_total, cover: !!p.cover})));

    function renderGrid(list) {
      document.getElementById("pl-grid").innerHTML = `<div class="playlist-grid">${list.map(p => `
        <div class="playlist-card" data-id="${p.id}" data-name="${p.name}">
          ${p.cover ? `<img class="playlist-cover" src="${p.cover}" alt="">` : `<div class="playlist-cover" style="display:flex;align-items:center;justify-content:center;background:var(--surface-2)"><i data-lucide="music" width="32" height="32"></i></div>`}
          <div class="playlist-name">${p.name}</div>
          <div class="playlist-count" data-pl-id="${p.id}">${p.tracks_total || '...'} tracks</div>
        </div>`).join("")}</div>`;
      lucide.createIcons();
      document.querySelectorAll(".playlist-card").forEach(card => {
        card.addEventListener("click", () => renderPlaylists({ playlist_id: card.dataset.id, playlist_name: card.dataset.name }));
      });

      // Lazy-fetch real counts for playlists showing 0 (batch, update once)
      const zeroPl = list.filter(p => !p.tracks_total);
      if (zeroPl.length) {
        Promise.allSettled(zeroPl.map(p =>
          API.get(`/api/playlists/${p.id}/count`).then(r => ({ id: p.id, count: r.count }))
        )).then(results => {
          results.forEach(r => {
            if (r.status !== 'fulfilled') return;
            const { id, count } = r.value;
            const el = document.querySelector(`.playlist-count[data-pl-id="${id}"]`);
            if (!el) return;
            el.textContent = count ? `${count} tracks` : '— tracks';
            const pl = list.find(p => p.id === id);
            if (pl && count) pl.tracks_total = count;
          });
        });
      }
    }

    renderGrid(playlists);

    document.getElementById("pl-filter").addEventListener("input", e => {
      const q = e.target.value.toLowerCase();
      renderGrid(q ? playlists.filter(p => p.name.toLowerCase().includes(q)) : playlists);
    });
  } catch (e) {
    document.getElementById("pl-grid").innerHTML = `<div class="empty-state" style="color:#ef4444"><i data-lucide="alert-circle" width="32" height="32"></i>${e.message}</div>`;
    lucide.createIcons();
  }

  document.getElementById("pl-refresh").addEventListener("click", () => renderPlaylists());
}
