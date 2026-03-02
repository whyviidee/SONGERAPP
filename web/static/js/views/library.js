// web/static/js/views/library.js
async function renderLibrary() {
  const content = document.getElementById("content");
  content.innerHTML = `
    <div class="view-header">
      <span class="view-title">Library</span>
      <div style="display:flex;gap:8px">
        <button class="btn-sm" id="open-folder-btn">
          <i data-lucide="folder-open" width="14" height="14"></i> Open Folder
        </button>
        <button class="btn-sm" id="refresh-lib">
          <i data-lucide="refresh-cw" width="14" height="14"></i> Refresh
        </button>
      </div>
    </div>
    <input class="filter-input" id="lib-filter" placeholder="Filter by artist or track name...">
    <div id="lib-tree"><div class="loading-spinner"><i data-lucide="loader-2" width="20" height="20"></i></div></div>
  `;
  lucide.createIcons();

  document.getElementById("open-folder-btn").addEventListener("click", async () => {
    try {
      const r = await API.get("/api/open-folder");
      toast(`Opened: ${r.path}`, "success");
    } catch (e) {
      toast("Could not open folder", "error");
    }
  });

  let allFiles = [];

  async function loadLib() {
    document.getElementById("lib-tree").innerHTML = `<div class="loading-spinner"><i data-lucide="loader-2" width="20" height="20"></i></div>`;
    lucide.createIcons();
    allFiles = await API.get("/api/library");
    renderTree(allFiles);
  }

  function renderTree(files) {
    const q = document.getElementById("lib-filter")?.value?.toLowerCase() || "";
    const filtered = q ? files.filter(f => f.artist.toLowerCase().includes(q) || f.name.toLowerCase().includes(q)) : files;

    // Group by artist → album
    const tree = {};
    for (const f of filtered) {
      const artist = f.artist || "Unknown Artist";
      const album = f.album || "Unknown Album";
      if (!tree[artist]) tree[artist] = {};
      if (!tree[artist][album]) tree[artist][album] = [];
      tree[artist][album].push(f);
    }

    const libTree = document.getElementById("lib-tree");
    if (!Object.keys(tree).length) {
      libTree.innerHTML = `<div class="empty-state"><i data-lucide="inbox" width="32" height="32"></i>No tracks found</div>`;
      lucide.createIcons();
      return;
    }

    const esc = s => s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");

    libTree.innerHTML = Object.entries(tree).sort(([a],[b]) => a.localeCompare(b)).map(([artist, albums]) => {
      const albumCount = Object.keys(albums).length;
      const trackCount = Object.values(albums).flat().length;
      const initial = artist.trim()[0]?.toUpperCase() || "?";
      const firstPath = Object.values(albums)[0]?.[0]?.path || "";
      const firstAlbum = Object.keys(albums)[0] || "";
      const coverUrl = firstPath
        ? `/api/cover?path=${encodeURIComponent(firstPath)}&artist=${encodeURIComponent(artist)}&album=${encodeURIComponent(firstAlbum)}`
        : "";
      return `
      <div class="lib-artist">
        <div class="lib-artist-header">
          <div class="lib-artist-avatar">
            ${coverUrl ? `<img class="lib-av-img" src="${esc(coverUrl)}" alt="" onerror="this.style.opacity='0'">` : ""}
            ${esc(initial)}
          </div>
          <div class="lib-artist-info">
            <div class="lib-artist-name-text">${esc(artist)}</div>
            <div class="lib-artist-meta">${albumCount} album${albumCount !== 1 ? "s" : ""} · ${trackCount} track${trackCount !== 1 ? "s" : ""}</div>
          </div>
          <i data-lucide="chevron-right" width="16" height="16" class="lib-artist-chevron"></i>
        </div>
        <div class="lib-artist-body">
          ${Object.entries(albums).sort(([a],[b]) => a.localeCompare(b)).map(([album, tracks]) => `
            <div class="lib-album">
              <div class="lib-album-header">
                <i data-lucide="disc-3" width="12" height="12" style="color:var(--text-3);flex-shrink:0"></i>
                <span class="lib-album-name-text">${esc(album)}</span>
                <span class="lib-album-count">${tracks.length} track${tracks.length !== 1 ? "s" : ""}</span>
                <i data-lucide="chevron-right" width="12" height="12" class="lib-album-chevron"></i>
              </div>
              <div class="lib-album-tracks">
                ${tracks.map((t, i) => `
                  <div class="lib-track-row">
                    <span class="lib-track-num">${i + 1}</span>
                    <div class="lib-track-name">${esc(t.name)}</div>
                    <span class="lib-track-tag">${esc(t.ext.toUpperCase())}</span>
                    <span class="lib-track-size">${t.size_mb} MB</span>
                    <button class="ctrl-btn play-lib" data-path="${esc(t.path)}" title="Play">
                      <i data-lucide="play" width="14" height="14"></i>
                    </button>
                    <button class="ctrl-btn reveal-lib" data-path="${esc(t.path)}" title="Reveal in Explorer">
                      <i data-lucide="folder" width="13" height="13"></i>
                    </button>
                  </div>`).join("")}
              </div>
            </div>`).join("")}
        </div>
      </div>`;
    }).join("");
    lucide.createIcons();

    // Toggle artists
    document.querySelectorAll(".lib-artist-header").forEach(el => {
      el.addEventListener("click", () => el.closest(".lib-artist").classList.toggle("open"));
    });
    // Toggle albums
    document.querySelectorAll(".lib-album-header").forEach(el => {
      el.addEventListener("click", () => el.closest(".lib-album").classList.toggle("open"));
    });

    // Play buttons
    document.querySelectorAll(".play-lib").forEach(btn => {
      btn.addEventListener("click", e => {
        e.stopPropagation();
        window.PLAYER?.playFile(btn.dataset.path);
      });
    });

    // Double-click track row to play
    document.querySelectorAll(".lib-track-row").forEach(row => {
      row.addEventListener("dblclick", () => {
        const btn = row.querySelector(".play-lib");
        if (btn) window.PLAYER?.playFile(btn.dataset.path);
      });
    });

    // Reveal in Explorer buttons
    document.querySelectorAll(".reveal-lib").forEach(btn => {
      btn.addEventListener("click", async e => {
        e.stopPropagation();
        try {
          await API.post("/api/open-file", { path: btn.dataset.path, action: "reveal" });
        } catch (err) {
          toast("Could not open file location", "error");
        }
      });
    });
  }

  document.getElementById("refresh-lib").addEventListener("click", loadLib);
  document.getElementById("lib-filter").addEventListener("input", () => renderTree(allFiles));

  loadLib();
}
