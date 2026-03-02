// web/static/js/views/queue.js
let _queueSSE = null;

async function renderQueue() {
  const content = document.getElementById("content");
  content.innerHTML = `
    <div class="view-header">
      <span class="view-title">Downloads</span>
      <button class="btn-sm danger" id="cancel-all">
        <i data-lucide="x" width="14" height="14"></i> Cancel all
      </button>
    </div>
    <div class="track-list" id="queue-list">
      <div class="loading-spinner"><i data-lucide="loader-2" width="20" height="20"></i> Loading...</div>
    </div>
  `;
  lucide.createIcons();

  document.getElementById("cancel-all").addEventListener("click", async () => {
    await API.del("/api/queue");
    loadQueue();
  });

  async function loadQueue() {
    try {
      const jobs = await API.get("/api/queue");
      renderQueueList(jobs);
    } catch (e) {
      console.error(e);
    }
  }

  function renderQueueList(jobs) {
    const list = document.getElementById("queue-list");
    if (!list) return;
    const badge = document.getElementById("queue-badge");
    const active = jobs.filter(j => j.status === "downloading" || j.status === "pending").length;
    if (badge) {
      badge.textContent = active;
      badge.style.display = active > 0 ? "flex" : "none";
    }
    if (!jobs.length) {
      list.innerHTML = `<div class="empty-state"><i data-lucide="inbox" width="32" height="32"></i>Queue is empty</div>`;
      lucide.createIcons();
      return;
    }
    list.innerHTML = jobs.map(j => `
      <div class="queue-row" id="qr-${j.id}">
        <div class="queue-info">
          <div class="queue-name">${j.name}</div>
          <div class="queue-sub">${j.artist}${j.album ? " · " + j.album : ""}</div>
          <div class="queue-progress">
            <div class="queue-progress-fill" style="width:${j.progress || 0}%"></div>
          </div>
        </div>
        <span class="queue-status ${j.status}">${
          j.status === "downloading" ? `${Math.round(j.progress || 0)}%`
          : j.status === "done" ? "✓ done"
          : j.status === "error" ? "✗ error"
          : j.status
        }</span>
        ${j.status === "done"
          ? `<button class="ctrl-btn open-file-btn" data-id="${j.id}" data-path="${j.path||""}" title="Open folder" style="color:var(--text-3)"><i data-lucide="folder" width="15" height="15"></i></button>`
          : j.status !== "cancelled" && j.status !== "error"
          ? `<button class="btn-cancel" data-id="${j.id}" title="Cancel"><i data-lucide="x" width="14" height="14"></i></button>`
          : ""}
      </div>`).join("");
    lucide.createIcons();

    list.querySelectorAll(".btn-cancel").forEach(btn => {
      btn.addEventListener("click", async () => {
        await API.del(`/api/queue/${btn.dataset.id}`);
        loadQueue();
      });
    });

    list.querySelectorAll(".open-file-btn").forEach(btn => {
      btn.addEventListener("click", async e => {
        e.stopPropagation();
        if (btn.dataset.path) {
          try { await API.post("/api/open-file", { path: btn.dataset.path, action: "reveal" }); }
          catch { toast("Could not open file location", "error"); }
        } else {
          try { await API.get("/api/open-folder"); }
          catch { toast("Could not open folder", "error"); }
        }
      });
    });

    // Auto-scroll to first downloading item
    const downloading = list.querySelector(".queue-status.downloading");
    if (downloading) downloading.closest(".queue-row")?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  loadQueue();

  // SSE for live updates
  if (_queueSSE) _queueSSE.close();
  _queueSSE = new EventSource("/api/events");
  _queueSSE.onmessage = e => {
    const data = JSON.parse(e.data);
    if (data.type === "queue_update") loadQueue();
  };
}
