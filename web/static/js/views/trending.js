// web/static/js/views/trending.js
// Hidden view — accessible via Ctrl+Shift+T only

async function renderTrending() {
  const content = document.getElementById("content");

  content.innerHTML = `
    <div style="padding:28px 28px 0">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
        <div>
          <h2 style="font-size:22px;font-weight:700;margin:0">⚡ Trending</h2>
          <p style="color:var(--text-3);font-size:12px;margin:4px 0 0">só para ti · Ctrl+Shift+T</p>
        </div>
        <select id="trending-cat" style="background:var(--surface-2);color:var(--text);border:1px solid #3f3f46;border-radius:8px;padding:7px 14px;font-size:13px;cursor:pointer;outline:none;font-family:inherit"></select>
      </div>
      <div id="trending-list"></div>
    </div>
  `;

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
        <button class="btn-sm trending-search-btn" title="Buscar no Spotify">
          <i data-lucide="search" width="13" height="13"></i> Buscar
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
  }

  sel.addEventListener("change", () => {
    renderTracks(categories[parseInt(sel.value)]);
  });

  renderTracks(categories[0]);
}

function escHtml(s) {
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}
