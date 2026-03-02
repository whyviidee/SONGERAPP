// web/static/js/views/history.js
async function renderHistory() {
  const content = document.getElementById("content");
  content.innerHTML = `
    <div class="view-header">
      <span class="view-title">History</span>
      <button class="btn-sm danger" id="clear-history"><i data-lucide="trash-2" width="14" height="14"></i> Clear all</button>
    </div>
    <div id="history-list"><div class="loading-spinner"><i data-lucide="loader-2" width="20" height="20"></i></div></div>
  `;
  lucide.createIcons();

  document.getElementById("clear-history").addEventListener("click", async () => {
    await API.del("/api/history");
    loadHistory();
    toast("History cleared");
  });

  async function loadHistory() {
    const entries = await API.get("/api/history");
    const list = document.getElementById("history-list");
    if (!entries.length) {
      list.innerHTML = `<div class="empty-state"><i data-lucide="clock" width="32" height="32"></i>No history yet</div>`;
      lucide.createIcons();
      return;
    }
    list.innerHTML = `<div class="track-list">${entries.map(h => `
      <div class="track-row">
        <div class="track-cover" style="display:flex;align-items:center;justify-content:center;background:var(--surface-2)">
          <i data-lucide="disc-3" width="16" height="16"></i>
        </div>
        <div class="track-info">
          <div class="track-name">${h.name}</div>
          <div class="track-artist">${h.date?.slice(0,10)} · ${h.done_count}/${h.tracks_count} tracks · ${h.format}</div>
        </div>
        <button class="btn-download re-dl" data-url="${h.url}" data-name="${h.name}">
          <i data-lucide="download" width="14" height="14"></i> Re-download
        </button>
      </div>`).join("")}</div>`;
    lucide.createIcons();

    list.querySelectorAll(".re-dl").forEach(btn => {
      btn.addEventListener("click", async () => {
        await API.post("/api/download", { uri: btn.dataset.url, name: btn.dataset.name });
        toast(`Re-queued: ${btn.dataset.name}`, "success");
        APP.navigate("queue");
      });
    });
  }

  loadHistory();
}
