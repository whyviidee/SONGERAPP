// web/static/js/api.js
const API = {
  async get(path) {
    const r = await fetch(path);
    if (!r.ok) throw new Error(`GET ${path} → ${r.status}`);
    return r.json();
  },
  async post(path, body) {
    const r = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(`POST ${path} → ${r.status}`);
    return r.json();
  },
  async del(path) {
    const r = await fetch(path, { method: "DELETE" });
    if (!r.ok) throw new Error(`DELETE ${path} → ${r.status}`);
    return r.json();
  },
};

function toast(msg, type = "info") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = msg;
  document.getElementById("toast-container").appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

function fmtDuration(ms) {
  if (!ms) return "—";
  const s = Math.floor(ms / 1000);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

// Cache of downloaded track IDs → file paths (refreshed per view)
let _downloadedMap = null;

async function _getDownloadedMap() {
  if (_downloadedMap !== null) return _downloadedMap;
  try { _downloadedMap = await API.get("/api/downloaded-ids"); }
  catch (e) { _downloadedMap = {}; }
  return _downloadedMap;
}

function _invalidateDownloadedCache() { _downloadedMap = null; }

async function _wireDownloadButtons(container) {
  const downloaded = await _getDownloadedMap();

  container.querySelectorAll(".btn-download").forEach(btn => {
    const trackId = btn.dataset.id;
    const filePath = downloaded[trackId];

    if (filePath) {
      btn.innerHTML = `<i data-lucide="play" width="14" height="14"></i> Play`;
      btn.classList.add("done");
      lucide.createIcons();
      btn.addEventListener("click", e => {
        e.stopPropagation();
        PLAYER.playFile(filePath, {
          name: btn.dataset.name, artist: btn.dataset.artist,
          album: btn.dataset.album,
        });
      });
      return;
    }

    btn.addEventListener("click", async e => {
      e.stopPropagation();
      btn.innerHTML = `<i data-lucide="loader-2" width="14" height="14"></i> Adding...`;
      btn.classList.add("downloading");
      lucide.createIcons();
      try {
        await API.post("/api/download", {
          id: btn.dataset.id, name: btn.dataset.name,
          artist: btn.dataset.artist, album: btn.dataset.album,
          uri: btn.dataset.uri || "", cover: btn.dataset.cover || "",
        });
        btn.innerHTML = `<i data-lucide="check" width="14" height="14"></i> Queued`;
        btn.classList.remove("downloading");
        btn.classList.add("done");
        _invalidateDownloadedCache();
        lucide.createIcons();
        const toastEl = document.createElement("div");
        toastEl.className = "toast success";
        toastEl.innerHTML = `↓ <strong>${btn.dataset.name}</strong> added &nbsp;<a href="#" class="go-queue" style="color:var(--accent);text-decoration:underline;white-space:nowrap">View Downloads →</a>`;
        document.getElementById("toast-container").appendChild(toastEl);
        toastEl.querySelector(".go-queue").addEventListener("click", ev => {
          ev.preventDefault(); toastEl.remove(); APP.navigate("queue");
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
}
