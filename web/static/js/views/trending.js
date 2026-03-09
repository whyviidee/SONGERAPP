// web/static/js/views/trending.js
// Hidden view — accessible via Ctrl+Shift+T only

function _trendingTrackId(t) {
  // Spotify: extract track ID from URL
  if (t.source === "Spotify") {
    const m = t.url.match(/track\/([A-Za-z0-9]+)/);
    if (m) return m[1];
  }
  // SoundCloud / fallback: use a stable slug from artist+title
  return "sc_" + (t.artist + "_" + t.title).toLowerCase().replace(/[^a-z0-9]+/g, "_").slice(0, 60);
}

async function renderTrending() {
  const content = document.getElementById("content");

  content.innerHTML = `
    <div style="padding:28px 28px 0">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
        <div>
          <h2 style="font-size:22px;font-weight:700;margin:0">⚡ Trending</h2>
          <p style="color:var(--text-3);font-size:12px;margin:4px 0 0">só para ti · Ctrl+Shift+T</p>
        </div>
        <div style="display:flex;align-items:center;gap:10px">
          <select id="trending-cat" style="background:var(--surface-2);color:var(--text);border:1px solid #3f3f46;border-radius:8px;padding:7px 14px;font-size:13px;cursor:pointer;outline:none;font-family:inherit"></select>
          <input id="trending-genre" type="text" placeholder="Gravar Género" style="background:var(--surface-2);color:var(--text);border:1px solid #3f3f46;border-radius:8px;padding:7px 12px;font-size:13px;outline:none;font-family:inherit;width:190px" />
          <button class="btn-primary" id="trending-dl-all" style="height:36px;font-size:12px;white-space:nowrap">
            <i data-lucide="download" width="14" height="14"></i> Download All
          </button>
          <button class="btn-sm" id="trending-dl-zip" style="height:36px;font-size:12px;white-space:nowrap">
            <i data-lucide="archive" width="14" height="14"></i> ZIP
          </button>
          <button class="btn-sm" id="trending-refresh" style="height:36px;font-size:12px;white-space:nowrap" title="Actualizar esta categoria">
            <i data-lucide="refresh-cw" width="14" height="14"></i>
          </button>
        </div>
      </div>
      <div id="trending-list"></div>
    </div>
  `;
  lucide.createIcons();

  let categories = [];
  try {
    categories = await API.get("/api/trending");
  } catch (e) {
    document.getElementById("trending-list").innerHTML =
      `<p style="color:var(--text-3)">Erro ao carregar trending.</p>`;
    return;
  }

  if (!categories.length) {
    document.getElementById("trending-list").innerHTML =
      `<p style="color:var(--text-3)">Sem ficheiros trending encontrados.</p>`;
    return;
  }

  // Populate select
  const sel = document.getElementById("trending-cat");
  categories.forEach((cat, i) => {
    const opt = document.createElement("option");
    opt.value = i;
    opt.textContent = cat.label;
    sel.appendChild(opt);
  });

  // Download All + ZIP + Refresh handlers
  const dlAllBtn = document.getElementById("trending-dl-all");
  const dlZipBtn = document.getElementById("trending-dl-zip");
  const refreshBtn = document.getElementById("trending-refresh");
  const genreInput = document.getElementById("trending-genre");

  dlZipBtn.addEventListener("click", () => {
    const cat = categories[parseInt(sel.value)];
    if (!cat || !cat.tracks.length) return;
    const genre = genreInput.value.trim();
    zipFlow(
      dlZipBtn,
      cat.tracks.map(t => ({ id: _trendingTrackId(t), name: t.title, artist: t.artist, album: "", cover: "", genre })),
      cat.label,
    );
  });
  async function downloadAll(cat) {
    if (!cat || !cat.tracks.length) return;
    const genre = genreInput.value.trim();
    dlAllBtn.disabled = true;
    dlAllBtn.innerHTML = `<i data-lucide="loader-2" width="14" height="14"></i> A adicionar...`;
    lucide.createIcons();
    let added = 0;
    for (const t of cat.tracks) {
      try {
        await API.post("/api/download", {
          id: _trendingTrackId(t),
          name: t.title,
          artist: t.artist,
          album: "",
          cover: "",
          genre,
        });
        added++;
      } catch (e) {}
    }
    dlAllBtn.disabled = false;
    dlAllBtn.innerHTML = `<i data-lucide="check" width="14" height="14"></i> ${added} na fila`;
    lucide.createIcons();
    toast(`${added} tracks adicionadas à fila`, "success");
    setTimeout(() => {
      dlAllBtn.innerHTML = `<i data-lucide="download" width="14" height="14"></i> Download All`;
      lucide.createIcons();
    }, 3000);
  }

  dlAllBtn.addEventListener("click", () => {
    downloadAll(categories[parseInt(sel.value)]);
  });

  refreshBtn.addEventListener("click", async () => {
    const idx = parseInt(sel.value);
    const cat = categories[idx];
    if (!cat) return;
    refreshBtn.disabled = true;
    refreshBtn.innerHTML = `<i data-lucide="loader-2" width="14" height="14"></i>`;
    lucide.createIcons();
    try {
      const r = await API.post(`/api/trending/${cat.key}/refresh`, {});
      categories[idx].tracks = r.tracks;
      renderTracks(categories[idx]);
      toast(`${cat.label} actualizado — ${r.count} tracks`, "success");
    } catch (e) {
      toast("Erro ao actualizar trending", "error");
    }
    refreshBtn.disabled = false;
    refreshBtn.innerHTML = `<i data-lucide="refresh-cw" width="14" height="14"></i>`;
    lucide.createIcons();
  });

  function renderTracks(cat) {
    const list = document.getElementById("trending-list");
    if (!cat || !cat.tracks.length) {
      list.innerHTML = `<p style="color:var(--text-3)">Sem tracks.</p>`;
      return;
    }
    list.innerHTML = cat.tracks.map((t, i) => `
      <div class="trending-row" data-url="${t.url}" data-source="${t.source}" data-artist="${encodeURIComponent(t.artist)}" data-title="${encodeURIComponent(t.title)}">
        <span class="trending-num">${i + 1}</span>
        <div class="trending-info">
          <span class="trending-artist">${escHtml(t.artist)}</span>
          <span class="trending-sep"> — </span>
          <span class="trending-title">${escHtml(t.title)}</span>
        </div>
        <span class="trending-src ${t.source.toLowerCase()}">${t.source}</span>
        <a href="${t.url}" target="_blank" rel="noopener" class="btn-sm trending-open-btn" title="Ouvir no ${t.source}" style="color:${t.source === 'Spotify' ? '#1DB954' : '#f26f23'};display:inline-flex;align-items:center;gap:4px;text-decoration:none">
          <i data-lucide="external-link" width="13" height="13"></i>
        </a>
        <button class="btn-sm trending-search-btn" title="Buscar no Spotify">
          <i data-lucide="search" width="13" height="13"></i> Buscar
        </button>
        <button class="btn-sm trending-dl-btn" title="Download">
          <i data-lucide="download" width="13" height="13"></i>
        </button>
      </div>
    `).join("");
    lucide.createIcons();

    list.querySelectorAll(".trending-search-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const row = btn.closest(".trending-row");
        const url = row.dataset.url;
        const source = row.dataset.source;
        const artist = decodeURIComponent(row.dataset.artist);
        const title = decodeURIComponent(row.dataset.title);
        const query = source === "Spotify" ? url : `${artist} ${title}`;
        APP.navigate("search", { q: query });
      });
    });

    list.querySelectorAll(".trending-dl-btn").forEach((btn, idx) => {
      btn.addEventListener("click", async () => {
        const t = cat.tracks[idx];
        const genre = genreInput.value.trim();
        btn.disabled = true;
        btn.innerHTML = `<i data-lucide="loader-2" width="13" height="13"></i>`;
        lucide.createIcons();
        try {
          await API.post("/api/download", {
            id: _trendingTrackId(t),
            name: t.title,
            artist: t.artist,
            album: "",
            cover: "",
            genre,
          });
          btn.innerHTML = `<i data-lucide="check" width="13" height="13"></i>`;
          lucide.createIcons();
          toast(`${t.artist} — ${t.title} adicionado`, "success");
        } catch (e) {
          btn.disabled = false;
          btn.innerHTML = `<i data-lucide="download" width="13" height="13"></i>`;
          lucide.createIcons();
          toast("Erro ao adicionar download", "error");
        }
      });
    });
  }

  sel.addEventListener("change", () => {
    renderTracks(categories[parseInt(sel.value)]);
  });

  renderTracks(categories[0]);
}

function escHtml(s) {
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}
