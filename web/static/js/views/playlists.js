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

    const tracks = await API.get(`/api/playlists/${params.playlist_id}/tracks`);
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

    document.getElementById("pl-tracks").innerHTML = `<div class="track-list">${tracks.map(t => `
      <div class="track-row">
        ${t.cover ? `<img class="track-cover" src="${t.cover}" alt="">` : `<div class="track-cover"></div>`}
        <div class="track-info">
          <div class="track-name">${t.name}</div>
          <div class="track-artist">${t.artist} · ${t.album}</div>
        </div>
        <div class="track-duration">${fmtDuration(t.duration_ms)}</div>
        <button class="btn-download" data-track='${JSON.stringify(t)}'>
          <i data-lucide="download" width="14" height="14"></i> Download
        </button>
      </div>`).join("")}</div>`;
    lucide.createIcons();

    document.querySelectorAll(".btn-download[data-track]").forEach(btn => {
      btn.addEventListener("click", async () => {
        const t = JSON.parse(btn.dataset.track);
        await API.post("/api/download", t);
        btn.classList.add("done");
        btn.innerHTML = `<i data-lucide="check" width="14" height="14"></i> Added`;
        lucide.createIcons();
      });
    });
    return;
  }

  // Playlist grid
  content.innerHTML = `
    <div class="view-header"><span class="view-title">Playlists</span></div>
    <input class="filter-input" id="pl-filter" placeholder="Filter playlists...">
    <div id="pl-grid"><div class="loading-spinner"><i data-lucide="loader-2" width="20" height="20"></i></div></div>
  `;
  lucide.createIcons();

  try {
    const playlists = await API.get("/api/playlists");

    function renderGrid(list) {
      document.getElementById("pl-grid").innerHTML = `<div class="playlist-grid">${list.map(p => `
        <div class="playlist-card" data-id="${p.id}" data-name="${p.name}">
          ${p.cover ? `<img class="playlist-cover" src="${p.cover}" alt="">` : `<div class="playlist-cover" style="display:flex;align-items:center;justify-content:center;background:var(--surface-2)"><i data-lucide="music" width="32" height="32"></i></div>`}
          <div class="playlist-name">${p.name}</div>
          <div class="playlist-count">${p.tracks_total} tracks</div>
        </div>`).join("")}</div>`;
      lucide.createIcons();
      document.querySelectorAll(".playlist-card").forEach(card => {
        card.addEventListener("click", () => renderPlaylists({ playlist_id: card.dataset.id, playlist_name: card.dataset.name }));
      });
    }

    renderGrid(playlists);

    document.getElementById("pl-filter").addEventListener("input", e => {
      const q = e.target.value.toLowerCase();
      renderGrid(q ? playlists.filter(p => p.name.toLowerCase().includes(q)) : playlists);
    });
  } catch (e) {
    document.getElementById("pl-grid").innerHTML = `<div class="empty-state" style="color:#ef4444">${e.message}</div>`;
  }
}
