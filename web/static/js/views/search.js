// web/static/js/views/search.js
async function renderSearch(params = {}) {
  const content = document.getElementById("content");
  content.innerHTML = `
    <div class="search-row">
      <div class="search-input-wrap">
        <input id="search-input" type="text" placeholder="Search music, paste Spotify URL..." value="${params.q || ""}">
      </div>
      <button class="btn-search" id="do-search">
        <i data-lucide="search" width="16" height="16"></i>
        Search
      </button>
    </div>
    <div id="search-results"></div>
  `;
  lucide.createIcons();

  const doSearch = async () => {
    const q = document.getElementById("search-input").value.trim();
    if (!q) return;
    const container = document.getElementById("search-results");
    container.innerHTML = `<div class="loading-spinner"><i data-lucide="loader-2" width="20" height="20"></i> Searching...</div>`;
    lucide.createIcons();
    try {
      const data = await API.get(`/api/search?q=${encodeURIComponent(q)}`);

      // Support both old format (array) and new format ({tracks, albums, artists})
      const tracks = Array.isArray(data) ? data : (data.tracks || []);
      const albums = Array.isArray(data) ? [] : (data.albums || []);
      const artists = Array.isArray(data) ? [] : (data.artists || []);

      if (!tracks.length && !albums.length && !artists.length) {
        container.innerHTML = `<div class="empty-state"><i data-lucide="music-off" width="32" height="32"></i>No results found</div>`;
        lucide.createIcons();
        return;
      }

      let html = "";

      // Artists section
      if (artists.length) {
        html += `
          <div class="search-section">
            <div class="search-section-header">
              <span class="search-section-title"><i data-lucide="mic-2" width="16" height="16"></i> Artists</span>
              ${artists.length > 3 ? `<button class="btn-see-more" data-target="artists-list">See all</button>` : ""}
            </div>
            <div class="artist-grid" id="artists-list">
              ${artists.map((a, i) => `
                <div class="artist-card ${i >= 3 ? "hidden-item" : ""}" data-id="${a.id}" data-name="${a.name}">
                  ${a.cover
                    ? `<img class="artist-avatar" src="${a.cover}" alt="">`
                    : `<div class="artist-avatar"><i data-lucide="user" width="24" height="24"></i></div>`}
                  <div class="artist-card-info">
                    <div class="artist-card-name">${a.name}</div>
                    <div class="artist-card-genres">${a.genres.length ? a.genres.join(", ") : "Artist"}</div>
                  </div>
                </div>
              `).join("")}
            </div>
          </div>`;
      }

      // Albums section
      if (albums.length) {
        html += `
          <div class="search-section">
            <div class="search-section-header">
              <span class="search-section-title"><i data-lucide="disc-3" width="16" height="16"></i> Albums</span>
              ${albums.length > 3 ? `<button class="btn-see-more" data-target="albums-list">See all</button>` : ""}
            </div>
            <div class="album-grid" id="albums-list">
              ${albums.map((a, i) => `
                <div class="album-card ${i >= 3 ? "hidden-item" : ""}" data-id="${a.id}" data-name="${a.name}">
                  ${a.cover
                    ? `<img class="album-card-cover" src="${a.cover}" alt="">`
                    : `<div class="album-card-cover"><i data-lucide="disc" width="20" height="20"></i></div>`}
                  <div class="album-card-info">
                    <div class="album-card-name">${a.name}</div>
                    <div class="album-card-meta">${a.artist}${a.year ? ` · ${a.year}` : ""}${a.total_tracks ? ` · ${a.total_tracks} tracks` : ""}</div>
                  </div>
                </div>
              `).join("")}
            </div>
          </div>`;
      }

      // Tracks section
      if (tracks.length) {
        html += `
          <div class="search-section">
            <div class="search-section-header">
              <span class="search-section-title"><i data-lucide="music" width="16" height="16"></i> Tracks</span>
              ${tracks.length > 5 ? `<button class="btn-see-more" data-target="tracks-list">See all</button>` : ""}
            </div>
            <div class="track-list" id="tracks-list">
              ${tracks.map((t, i) => `
                <div class="track-row ${i >= 5 ? "hidden-item" : ""}" data-id="${t.id}" data-uri="${t.uri || ""}">
                  ${t.cover
                    ? `<img class="track-cover" src="${t.cover}" alt="">`
                    : `<div class="track-cover" style="display:flex;align-items:center;justify-content:center"><i data-lucide="music" width="16" height="16"></i></div>`}
                  <div class="track-info">
                    <div class="track-name">${t.name}</div>
                    <div class="track-artist">${t.artist} · ${t.album}</div>
                  </div>
                  <div class="track-duration">${fmtDuration(t.duration_ms)}</div>
                  <button class="btn-download" data-id="${t.id}" data-name="${t.name}" data-artist="${t.artist}" data-album="${t.album}" data-uri="${t.uri || ""}">
                    <i data-lucide="download" width="14" height="14"></i> Download
                  </button>
                </div>
              `).join("")}
            </div>
          </div>`;
      }

      container.innerHTML = html;
      lucide.createIcons();

      // "See all" toggle buttons
      container.querySelectorAll(".btn-see-more").forEach(btn => {
        btn.addEventListener("click", () => {
          const target = document.getElementById(btn.dataset.target);
          if (!target) return;
          const hidden = target.querySelectorAll(".hidden-item");
          const isShowing = btn.textContent === "Show less";
          hidden.forEach(el => el.style.display = isShowing ? "none" : "");
          btn.textContent = isShowing ? "See all" : "Show less";
        });
      });

      // Artist card click → search artist name
      container.querySelectorAll(".artist-card").forEach(card => {
        card.addEventListener("click", () => {
          document.getElementById("search-input").value = card.dataset.name;
          doSearch();
        });
      });

      // Album card click → search "artist album" to find tracks
      container.querySelectorAll(".album-card").forEach(card => {
        card.addEventListener("click", () => {
          document.getElementById("search-input").value = card.dataset.name;
          doSearch();
        });
      });

      // Wire download buttons
      container.querySelectorAll(".btn-download").forEach(btn => {
        btn.addEventListener("click", async e => {
          e.stopPropagation();
          btn.innerHTML = `<i data-lucide="loader-2" width="14" height="14"></i> Adding...`;
          btn.classList.add("downloading");
          lucide.createIcons();
          try {
            await API.post("/api/download", {
              id: btn.dataset.id,
              name: btn.dataset.name,
              artist: btn.dataset.artist,
              album: btn.dataset.album,
              uri: btn.dataset.uri,
            });
            btn.innerHTML = `<i data-lucide="check" width="14" height="14"></i> Queued`;
            btn.classList.remove("downloading");
            btn.classList.add("done");
            lucide.createIcons();
            const toastEl = document.createElement("div");
            toastEl.className = "toast success";
            toastEl.innerHTML = `↓ <strong>${btn.dataset.name}</strong> added &nbsp;<a href="#" class="go-queue" style="color:var(--accent);text-decoration:underline;white-space:nowrap">View Downloads →</a>`;
            document.getElementById("toast-container").appendChild(toastEl);
            toastEl.querySelector(".go-queue").addEventListener("click", e => {
              e.preventDefault();
              toastEl.remove();
              APP.navigate("queue");
            });
            setTimeout(() => toastEl.remove(), 6000);
          } catch (err) {
            btn.innerHTML = `<i data-lucide="download" width="14" height="14"></i> Download`;
            btn.classList.remove("downloading");
            lucide.createIcons();
            toast(`Error: ${err.message}`, "error");
          }
        });
      });
    } catch (err) {
      container.innerHTML = `<div class="empty-state" style="color:#ef4444"><i data-lucide="alert-circle" width="32" height="32"></i>${err.message}</div>`;
      lucide.createIcons();
    }
  };

  document.getElementById("do-search").addEventListener("click", doSearch);
  document.getElementById("search-input").addEventListener("keydown", e => {
    if (e.key === "Enter") doSearch();
  });

  if (params.q) doSearch();
}
