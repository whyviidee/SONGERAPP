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

    <div id="recent-section" style="display:none">
      <div class="section-header">
        <span class="section-title">Recently Downloaded</span>
        <a class="section-link" data-view="history" href="#">View all →</a>
      </div>
    </div>

    <div class="album-grid" id="recent-grid" style="display:none"></div>
  `;

  lucide.createIcons();

  // Wire search
  document.getElementById("do-search").addEventListener("click", () => {
    const q = document.getElementById("search-input").value.trim();
    if (q) window.APP.navigate("search", { q });
  });
  document.getElementById("search-input").addEventListener("keydown", e => {
    if (e.key === "Enter") document.getElementById("do-search").click();
  });

  // Wire "View all"
  document.querySelectorAll("[data-view]").forEach(el => {
    if (el.closest("#sidebar")) return;
    el.addEventListener("click", e => {
      e.preventDefault();
      window.APP.navigate(el.dataset.view);
    });
  });

  // Load stats
  try {
    const stats = await API.get("/api/stats");
    document.getElementById("stat-0").textContent = stats.tracks.toLocaleString();
    document.getElementById("stat-1").textContent = stats.downloading;
    document.getElementById("stat-2").textContent = stats.playlists;
    document.getElementById("stat-3").textContent = `${stats.storage_gb} GB`;
  } catch (e) {}

  // Load recent history
  try {
    const history = await API.get("/api/history");
    const recent = history.slice(0, 5);
    if (recent.length === 0) return;

    const section = document.getElementById("recent-section");
    const grid = document.getElementById("recent-grid");
    section.style.display = "";
    grid.style.display = "";

    grid.innerHTML = recent.map(h => {
      const label = h.name || "Unknown";
      const sub = [h.format?.toUpperCase(), h.done_count > 1 ? `${h.done_count} tracks` : ""].filter(Boolean).join(" · ");
      return `
        <div class="album-card" title="${esc(label)}">
          <div class="album-thumb">
            ${h.cover
              ? `<img src="${esc(h.cover)}" alt="" class="album-thumb-img" onerror="this.remove()">`
              : `<div class="album-thumb-fallback"><i data-lucide="disc-3" width="28" height="28"></i></div>`
            }
          </div>
          <div class="album-card-body">
            <div class="album-name">${esc(label)}</div>
            <div class="album-artist">${esc(sub)}</div>
          </div>
        </div>`;
    }).join("");

    lucide.createIcons();
  } catch (e) {}
}

function esc(s) {
  return String(s ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}
