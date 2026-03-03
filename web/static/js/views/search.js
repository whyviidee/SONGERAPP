// web/static/js/views/search.js
async function renderSearch(params = {}) {
  const content = document.getElementById("content");

  // If params.type is set, render paginated single-type results
  if (params.type && params.q) {
    return _renderSearchType(content, params.type, params.q);
  }

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

  const MAX_PER_SECTION = 9;

  const doSearch = async () => {
    const q = document.getElementById("search-input").value.trim();
    if (!q) return;
    const container = document.getElementById("search-results");
    container.innerHTML = `<div class="loading-spinner"><i data-lucide="loader-2" width="20" height="20"></i> Searching...</div>`;
    lucide.createIcons();
    try {
      const data = await API.get(`/api/search?q=${encodeURIComponent(q)}`);

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
              ${artists.length > MAX_PER_SECTION ? `<button class="btn-see-more" data-type="artists" data-q="${q}">See all</button>` : ""}
            </div>
            <div class="artist-grid" id="artists-list">
              ${artists.slice(0, MAX_PER_SECTION).map(a => `
                <div class="artist-card" data-id="${a.id}" data-name="${a.name}">
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
              ${albums.length > MAX_PER_SECTION ? `<button class="btn-see-more" data-type="albums" data-q="${q}">See all</button>` : ""}
            </div>
            <div class="album-grid" id="albums-list">
              ${albums.slice(0, MAX_PER_SECTION).map(a => `
                <div class="album-card" data-id="${a.id}" data-name="${a.name}">
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
              ${tracks.length > MAX_PER_SECTION ? `<button class="btn-see-more" data-type="tracks" data-q="${q}">See all</button>` : ""}
            </div>
            <div class="track-list" id="tracks-list">
              ${tracks.slice(0, MAX_PER_SECTION).map(t => `
                <div class="track-row" data-id="${t.id}" data-uri="${t.uri || ""}" data-preview-url="${t.preview_url || ""}" data-track-name="${t.name}" data-track-artist="${t.artist}" data-track-album="${t.album}" data-track-cover="${t.cover || ""}">
                  ${t.cover
                    ? `<img class="track-cover" src="${t.cover}" alt="">`
                    : `<div class="track-cover" style="display:flex;align-items:center;justify-content:center"><i data-lucide="music" width="16" height="16"></i></div>`}
                  <div class="track-info">
                    <div class="track-name">${t.name}</div>
                    <div class="track-artist">${_artistHTML(t.artist, t.artist_id)}${t.album ? ` · ${t.album}` : ""}</div>
                  </div>
                  <div class="track-duration">${fmtDuration(t.duration_ms)}</div>
                  <button class="btn-download" data-id="${t.id}" data-name="${t.name}" data-artist="${t.artist}" data-album="${t.album}" data-cover="${t.cover || ""}" data-uri="${t.uri || ""}">
                    <i data-lucide="download" width="14" height="14"></i> Download
                  </button>
                </div>
              `).join("")}
            </div>
          </div>`;
      }

      container.innerHTML = html;
      lucide.createIcons();

      // "See all" → navigate to paginated type view
      container.querySelectorAll(".btn-see-more").forEach(btn => {
        btn.addEventListener("click", () => {
          APP.navigate("search", { type: btn.dataset.type, q: btn.dataset.q });
        });
      });

      // Artist card click → artist detail
      container.querySelectorAll(".artist-card").forEach(card => {
        card.addEventListener("click", () => {
          APP.navigate("artist", { id: card.dataset.id, _q: q });
        });
      });

      // Album card click → album detail
      container.querySelectorAll(".album-card").forEach(card => {
        card.addEventListener("click", () => {
          APP.navigate("album", { id: card.dataset.id, _q: q });
        });
      });

      // Wire download buttons, artist links, double-click preview
      _wireDownloadButtons(container);
      _wireArtistLinks(container);
      _wirePreview(container, tracks);
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

// Paginated single-type search results
async function _renderSearchType(content, type, q) {
  const typeLabels = { tracks: "Tracks", albums: "Albums", artists: "Artists" };
  const typeIcons = { tracks: "music", albums: "disc-3", artists: "mic-2" };
  const label = typeLabels[type] || type;
  const icon = typeIcons[type] || "search";

  content.innerHTML = `
    <div class="detail-back" id="search-type-back">
      <i data-lucide="arrow-left" width="16" height="16"></i> Back to search
    </div>
    <div class="view-header">
      <span class="view-title"><i data-lucide="${icon}" width="20" height="20"></i> ${label} for "${q}"</span>
    </div>
    <div id="search-type-results"></div>
    <div id="search-type-loader" style="display:none" class="loading-spinner">
      <i data-lucide="loader-2" width="20" height="20"></i> Loading more...
    </div>
    <button class="btn-ghost" id="search-type-more" style="display:none;margin:16px auto">Load more</button>
  `;
  lucide.createIcons();

  document.getElementById("search-type-back").addEventListener("click", () => {
    APP.navigate("search", { q });
  });

  let currentOffset = 0;
  let hasMore = true;

  const loadMore = async () => {
    if (!hasMore) return;
    const loader = document.getElementById("search-type-loader");
    const moreBtn = document.getElementById("search-type-more");
    loader.style.display = "";
    moreBtn.style.display = "none";
    lucide.createIcons();

    try {
      const data = await API.get(`/api/search/${type}?q=${encodeURIComponent(q)}&offset=${currentOffset}`);
      const container = document.getElementById("search-type-results");
      hasMore = data.has_more;
      currentOffset = data.offset + data.items.length;

      let html = "";
      if (type === "tracks") {
        html = data.items.map(t => `
          <div class="track-row" data-id="${t.id}" data-preview-url="${t.preview_url || ""}" data-track-name="${t.name}" data-track-artist="${t.artist}" data-track-album="${t.album}" data-track-cover="${t.cover || ""}">
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
        `).join("");
      } else if (type === "albums") {
        html = data.items.map(a => `
          <div class="album-card" data-id="${a.id}">
            ${a.cover
              ? `<img class="album-card-cover" src="${a.cover}" alt="">`
              : `<div class="album-card-cover"><i data-lucide="disc" width="20" height="20"></i></div>`}
            <div class="album-card-info">
              <div class="album-card-name">${a.name}</div>
              <div class="album-card-meta">${a.artist || ""}${a.year ? ` · ${a.year}` : ""}${a.total_tracks ? ` · ${a.total_tracks} tracks` : ""}</div>
            </div>
          </div>
        `).join("");
      } else if (type === "artists") {
        html = data.items.map(a => `
          <div class="artist-card" data-id="${a.id}">
            ${a.cover
              ? `<img class="artist-avatar" src="${a.cover}" alt="">`
              : `<div class="artist-avatar"><i data-lucide="user" width="24" height="24"></i></div>`}
            <div class="artist-card-info">
              <div class="artist-card-name">${a.name}</div>
              <div class="artist-card-genres">${(a.genres || []).join(", ") || "Artist"}</div>
            </div>
          </div>
        `).join("");
      }

      // Wrap in correct container if first load
      if (currentOffset <= data.items.length) {
        if (type === "tracks") container.innerHTML = `<div class="track-list">${html}</div>`;
        else if (type === "albums") container.innerHTML = `<div class="album-grid">${html}</div>`;
        else container.innerHTML = `<div class="artist-grid">${html}</div>`;
      } else {
        // Append to existing container
        const inner = container.firstElementChild;
        if (inner) inner.insertAdjacentHTML("beforeend", html);
      }

      lucide.createIcons();

      // Wire clicks
      container.querySelectorAll(".artist-card").forEach(card => {
        card.addEventListener("click", () => APP.navigate("artist", { id: card.dataset.id, _q: q }));
      });
      container.querySelectorAll(".album-card").forEach(card => {
        card.addEventListener("click", () => APP.navigate("album", { id: card.dataset.id, _q: q }));
      });
      _wireDownloadButtons(container);
      _wireArtistLinks(container);
      if (type === "tracks") _wirePreview(container, data.items);

      loader.style.display = "none";
      if (hasMore) moreBtn.style.display = "";
    } catch (err) {
      document.getElementById("search-type-loader").style.display = "none";
      toast(`Error: ${err.message}`, "error");
    }
  };

  document.getElementById("search-type-more").addEventListener("click", loadMore);
  loadMore();
}
