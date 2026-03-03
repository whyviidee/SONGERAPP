// web/static/js/player.js
const audioEl = document.getElementById("audio-el");
let _playlist = [];
let _currentIdx = -1;
let _shuffle = false;
let _repeat = false;
let _isPreview = false; // true when playing a 30s Spotify preview

window.PLAYER = {
  playFile(path, info = {}) {
    _isPreview = false;
    audioEl.src = `/stream/${encodeURIComponent(path)}`;
    audioEl.play();
    _updatePlayerUI(info, path);
  },
  setPlaylist(files, startIdx = 0) {
    _playlist = files;
    _currentIdx = startIdx;
    if (files[startIdx]) this.playFile(files[startIdx].path, files[startIdx]);
  },
  preview(url, info = {}) {
    if (!url) { toast("No preview available for this track", "error"); return; }
    _isPreview = true;
    audioEl.src = url;
    audioEl.play();
    _updatePlayerUI(info);
    document.getElementById("player").classList.add("preview-mode");
  },
  setPreviewPlaylist(tracks, startIdx = 0) {
    _playlist = tracks;
    _currentIdx = startIdx;
    if (tracks[startIdx]) this.preview(tracks[startIdx].preview_url, tracks[startIdx]);
  },
  _getPlaylist() {
    return { playlist: _playlist, currentIdx: _currentIdx, isPreview: _isPreview };
  },
};

function _updatePlayerUI(info, path) {
  const name = info.name || (path ? path.split(/[\\/]/).pop().replace(/\.[^.]+$/, "") : "Preview");
  document.getElementById("player-title").textContent = name;
  document.getElementById("player-sub").textContent = [info.artist, info.album].filter(Boolean).join(" · ");
  document.getElementById("player-art").src = info.cover || "";
  document.getElementById("play-icon").setAttribute("data-lucide", "pause");
  if (_isPreview) {
    document.getElementById("player").classList.add("preview-mode");
  } else {
    document.getElementById("player").classList.remove("preview-mode");
  }
  lucide.createIcons();
}

// Play/pause
document.getElementById("ctrl-play").addEventListener("click", () => {
  if (audioEl.paused) {
    audioEl.play();
    document.getElementById("play-icon").setAttribute("data-lucide", "pause");
  } else {
    audioEl.pause();
    document.getElementById("play-icon").setAttribute("data-lucide", "play");
  }
  lucide.createIcons();
});

// Progress bar
audioEl.addEventListener("timeupdate", () => {
  if (!audioEl.duration) return;
  const pct = (audioEl.currentTime / audioEl.duration) * 100;
  document.getElementById("progress-fill").style.width = `${pct}%`;
  document.getElementById("p-current").textContent = fmtSeconds(audioEl.currentTime);
  document.getElementById("p-duration").textContent = fmtSeconds(audioEl.duration);
});

document.getElementById("progress-track").addEventListener("click", e => {
  if (!audioEl.duration) return;
  const rect = e.currentTarget.getBoundingClientRect();
  audioEl.currentTime = ((e.clientX - rect.left) / rect.width) * audioEl.duration;
});

// Volume
const volSlider = document.getElementById("volume-slider");
volSlider.addEventListener("input", () => { audioEl.volume = volSlider.value / 100; });
audioEl.volume = 0.8;

document.getElementById("ctrl-mute").addEventListener("click", () => {
  audioEl.muted = !audioEl.muted;
  document.getElementById("volume-icon").setAttribute("data-lucide", audioEl.muted ? "volume-x" : "volume-2");
  lucide.createIcons();
});

// Next / Prev
function playNext() {
  if (!_playlist.length) return;
  _currentIdx = _shuffle
    ? Math.floor(Math.random() * _playlist.length)
    : (_currentIdx + 1) % _playlist.length;
  const t = _playlist[_currentIdx];
  if (_isPreview) {
    PLAYER.preview(t.preview_url, t);
  } else {
    PLAYER.playFile(t.path, t);
  }
}

function playPrev() {
  if (!_playlist.length) return;
  _currentIdx = (_currentIdx - 1 + _playlist.length) % _playlist.length;
  const t = _playlist[_currentIdx];
  if (_isPreview) {
    PLAYER.preview(t.preview_url, t);
  } else {
    PLAYER.playFile(t.path, t);
  }
}

document.getElementById("ctrl-next").addEventListener("click", playNext);
document.getElementById("ctrl-prev").addEventListener("click", playPrev);
audioEl.addEventListener("ended", () => { if (_repeat) audioEl.play(); else playNext(); });

// Shuffle / Repeat
document.getElementById("ctrl-shuffle").addEventListener("click", e => {
  _shuffle = !_shuffle;
  e.currentTarget.classList.toggle("active", _shuffle);
});
document.getElementById("ctrl-repeat").addEventListener("click", e => {
  _repeat = !_repeat;
  e.currentTarget.classList.toggle("active", _repeat);
});

// Queue view btn → opens now playing modal
document.getElementById("ctrl-queue-view").addEventListener("click", () => _openQueueModal());

function fmtSeconds(s) {
  if (isNaN(s)) return "0:00";
  return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
}
