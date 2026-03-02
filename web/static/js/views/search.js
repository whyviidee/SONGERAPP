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
    const results = document.getElementById("search-results");
    results.innerHTML = `<div class="loading-spinner"><i data-lucide="loader-2" width="20" height="20"></i> Searching...</div>`;
    lucide.createIcons();
    try {
      const tracks = await API.get(`/api/search?q=${encodeURIComponent(q)}`);
      if (!tracks.length) {
        results.innerHTML = `<div class="empty-state"><i data-lucide="music-off" width="32" height="32"></i>No results found</div>`;
        lucide.createIcons();
        return;
      }
      results.innerHTML = `<div class="track-list">${tracks.map(t => `
        <div class="track-row" data-id="${t.id}" data-uri="${t.uri}">
          ${t.cover
            ? `<img class="track-cover" src="${t.cover}" alt="">`
            : `<div class="track-cover" style="display:flex;align-items:center;justify-content:center"><i data-lucide="music" width="16" height="16"></i></div>`}
          <div class="track-info">
            <div class="track-name">${t.name}</div>
            <div class="track-artist">${t.artist} · ${t.album}</div>
          </div>
          <div class="track-duration">${fmtDuration(t.duration_ms)}</div>
          <button class="btn-download" data-id="${t.id}" data-name="${t.name}" data-artist="${t.artist}" data-album="${t.album}" data-uri="${t.uri}">
            <i data-lucide="download" width="14" height="14"></i> Download
          </button>
        </div>`).join("")}</div>`;
      lucide.createIcons();

      // Wire download buttons
      results.querySelectorAll(".btn-download").forEach(btn => {
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
            // Toast with link to queue
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
      results.innerHTML = `<div class="empty-state" style="color:#ef4444"><i data-lucide="alert-circle" width="32" height="32"></i>${err.message}</div>`;
      lucide.createIcons();
    }
  };

  document.getElementById("do-search").addEventListener("click", doSearch);
  document.getElementById("search-input").addEventListener("keydown", e => {
    if (e.key === "Enter") doSearch();
  });

  if (params.q) doSearch();
}
