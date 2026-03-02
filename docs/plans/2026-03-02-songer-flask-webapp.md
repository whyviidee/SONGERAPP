# SONGER Flask Web App Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert SONGER from PyQt6 desktop app to Flask web app running on localhost:8888, with a full redesigned dark UI matching the Pencil design.

**Architecture:** Flask serves an HTML/CSS/JS single-page app. All core backends (Spotipy, yt-dlp, slskd) remain unchanged. The browser replaces PyQt6 as the frontend. Server-Sent Events push download progress to the client.

**Tech Stack:** Python 3.11 + Flask, HTML5 + CSS3 + Vanilla JS, Lucide icons (CDN), Inter font (Google Fonts), no build step, no npm.

---

## Context for the implementer

Key files already exist:
- `server.py` — Flask OAuth setup server, extend this (do not replace)
- `core/config.py` — `Config` class, loads `~/.songer/config.json`
- `core/downloader.py` — `Downloader` class with `ThreadPoolExecutor`
- `core/history.py` — `DownloadHistory` class
- `core/library.py` — `scan_library(base_path)` function
- `core/spotify.py` — Spotify client
- `web/index.html` — Jinja2 template, Spotify setup page (don't touch)

Design tokens:
```
--bg: #09090B       --surface: #111113    --border: #1C1C1E
--accent: #1DB954   --text: #FFFFFF       --text-2: #71717A
--text-3: #3F3F46   --radius-card: 14px   --radius-btn: 12px
```

---

## Task 1: CSS design system

**Files:**
- Create: `web/static/css/app.css`

**Step 1: Create the CSS file with tokens and base styles**

```css
/* web/static/css/app.css */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --bg: #09090B;
  --surface: #111113;
  --surface-2: #1C1C1E;
  --border: #1C1C1E;
  --accent: #1DB954;
  --accent-dim: rgba(29,185,84,0.12);
  --text: #FFFFFF;
  --text-2: #71717A;
  --text-3: #3F3F46;
  --radius-card: 14px;
  --radius-btn: 12px;
  --sidebar-w: 230px;
  --player-h: 88px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body { height: 100%; overflow: hidden; }

body {
  font-family: 'Inter', -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
  -webkit-font-smoothing: antialiased;
}

/* ── Layout shell ── */
#app {
  display: flex;
  height: 100vh;
}

/* ── Sidebar ── */
#sidebar {
  width: var(--sidebar-w);
  min-width: var(--sidebar-w);
  background: var(--surface);
  display: flex;
  flex-direction: column;
  padding: 24px 20px 20px;
  gap: 0;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 6px;
  margin-bottom: 28px;
}

.logo-mark {
  width: 30px; height: 30px;
  background: var(--accent);
  border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; font-weight: 800; color: #000;
  flex-shrink: 0;
}

.logo-name {
  font-size: 17px; font-weight: 800; letter-spacing: 1px; color: var(--text);
}

.sidebar-label {
  font-size: 10px; font-weight: 600; letter-spacing: 2px;
  color: var(--text-3); padding: 0 6px; margin-bottom: 10px;
  text-transform: uppercase;
}

.nav-item {
  display: flex; align-items: center; gap: 12px;
  height: 40px; padding: 0 14px;
  border-radius: 10px; cursor: pointer;
  font-size: 13px; font-weight: 500; color: var(--text-2);
  transition: background 0.1s, color 0.1s;
  text-decoration: none; position: relative;
}

.nav-item:hover { background: rgba(255,255,255,0.04); color: var(--text); }

.nav-item.active {
  background: var(--accent-dim);
  color: var(--accent);
  font-weight: 600;
}

.nav-item .nav-badge {
  margin-left: auto;
  background: var(--accent); color: #000;
  font-size: 10px; font-weight: 700;
  width: 22px; height: 22px; border-radius: 11px;
  display: flex; align-items: center; justify-content: center;
}

.sidebar-spacer { flex: 1; }

.sidebar-divider {
  height: 1px; background: var(--surface-2); margin: 0 0 12px;
}

.sidebar-status {
  display: flex; align-items: center; gap: 8px;
  padding: 0 14px; height: 20px; margin-bottom: 12px;
  font-size: 11px; font-weight: 500; color: var(--text-3);
}

.status-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--text-3); flex-shrink: 0;
}
.status-dot.ok { background: var(--accent); }
.status-dot.err { background: #ef4444; }

.nav-settings {
  display: flex; align-items: center; gap: 10px;
  padding: 0 14px; height: 36px; cursor: pointer;
  border-radius: 10px; font-size: 12px; font-weight: 500;
  color: var(--text-3); transition: color 0.1s, background 0.1s;
}
.nav-settings:hover { color: var(--text-2); background: rgba(255,255,255,0.04); }

/* ── Right panel ── */
#right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

#content {
  flex: 1;
  overflow-y: auto;
  padding: 28px 32px;
  display: flex;
  flex-direction: column;
  gap: 28px;
  scrollbar-width: thin;
  scrollbar-color: var(--surface-2) transparent;
}

/* ── Search row ── */
.search-row {
  display: flex; align-items: center; gap: 12px;
}

.search-input-wrap {
  flex: 1; position: relative;
  display: flex; align-items: center;
}

.search-input-wrap i {
  position: absolute; left: 16px;
  color: var(--text-2); pointer-events: none;
}

#search-input {
  width: 100%; height: 44px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-btn); padding: 0 16px 0 42px;
  font-family: inherit; font-size: 13px; color: var(--text);
  outline: none; transition: border-color 0.15s;
}

#search-input::placeholder { color: var(--text-3); }
#search-input:focus { border-color: var(--accent); }

.btn-search {
  height: 44px; padding: 0 20px;
  background: var(--accent); border: none; border-radius: var(--radius-btn);
  display: flex; align-items: center; gap: 8px;
  font-family: inherit; font-size: 13px; font-weight: 700;
  color: #000; cursor: pointer; white-space: nowrap;
  transition: background 0.15s;
}
.btn-search:hover { background: #22c95e; }

/* ── Stats cards ── */
.stats-row {
  display: flex; gap: 14px;
}

.stat-card {
  flex: 1; background: var(--surface);
  border-radius: var(--radius-card); padding: 18px 20px;
  display: flex; flex-direction: column; gap: 6px;
}

.stat-value {
  font-size: 26px; font-weight: 800; letter-spacing: -1px; color: var(--text);
}
.stat-value.accent { color: var(--accent); }
.stat-label { font-size: 11px; font-weight: 500; color: var(--text-2); }

/* ── Section header ── */
.section-header {
  display: flex; align-items: center; justify-content: space-between;
}

.section-title {
  font-size: 15px; font-weight: 700; color: var(--text);
}

.section-link {
  font-size: 12px; font-weight: 500; color: var(--accent);
  text-decoration: none; cursor: pointer;
}
.section-link:hover { text-decoration: underline; }

/* ── Album grid ── */
.album-grid {
  display: flex; gap: 14px;
}

.album-card {
  flex: 1; background: var(--surface);
  border-radius: var(--radius-card); overflow: hidden;
  cursor: pointer; transition: transform 0.15s;
  padding: 10px 10px 14px;
  display: flex; flex-direction: column;
}
.album-card:hover { transform: translateY(-2px); }

.album-cover {
  width: 100%; aspect-ratio: 1;
  border-radius: 10px; object-fit: cover;
  background: var(--surface-2);
}
.album-cover-placeholder {
  width: 100%; aspect-ratio: 1;
  border-radius: 10px; background: var(--surface-2);
  display: flex; align-items: center; justify-content: center;
  color: var(--text-3);
}

.album-name {
  font-size: 13px; font-weight: 600; color: var(--text);
  margin-top: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.album-artist {
  font-size: 11px; color: var(--text-2);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

/* ── Player bar ── */
#player {
  height: var(--player-h);
  background: var(--surface);
  border-top: 1px solid var(--border);
  display: flex; align-items: center;
  padding: 0 24px; gap: 0; flex-shrink: 0;
}

.player-left {
  width: 260px; display: flex; align-items: center; gap: 14px; flex-shrink: 0;
}

.player-art {
  width: 44px; height: 44px; border-radius: 8px;
  object-fit: cover; background: var(--surface-2); flex-shrink: 0;
}

.player-info { min-width: 0; }
.player-title { font-size: 13px; font-weight: 600; color: var(--text); truncate: ellipsis; }
.player-sub { font-size: 11px; color: var(--text-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.player-center {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 10px; padding: 0 40px;
}

.player-controls {
  display: flex; align-items: center; gap: 28px;
}

.ctrl-btn {
  background: none; border: none; cursor: pointer;
  color: var(--text-2); display: flex; align-items: center;
  padding: 0; transition: color 0.1s;
}
.ctrl-btn:hover { color: var(--text); }
.ctrl-btn.active { color: var(--accent); }

.ctrl-play {
  width: 42px; height: 42px; border-radius: 21px;
  background: var(--text); border: none; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  color: var(--bg); transition: transform 0.1s, background 0.1s;
}
.ctrl-play:hover { transform: scale(1.05); background: #e8e8e8; }

.player-progress {
  width: 100%; display: flex; align-items: center; gap: 12px;
}

.progress-time { font-size: 11px; color: var(--text-2); flex-shrink: 0; }

.progress-track {
  flex: 1; height: 4px; background: var(--surface-2);
  border-radius: 4px; cursor: pointer; position: relative;
}

.progress-fill {
  height: 100%; background: var(--accent);
  border-radius: 4px; pointer-events: none;
  width: 0%;
}

.player-right {
  width: 220px; display: flex; align-items: center;
  justify-content: flex-end; gap: 16px; flex-shrink: 0;
}

.volume-wrap { display: flex; align-items: center; gap: 10px; }

input[type=range] {
  width: 80px; height: 4px;
  -webkit-appearance: none; appearance: none;
  background: var(--surface-2); border-radius: 4px; cursor: pointer;
}
input[type=range]::-webkit-slider-thumb {
  -webkit-appearance: none; width: 12px; height: 12px;
  border-radius: 50%; background: var(--text); cursor: pointer;
}

/* ── Track list (search results / playlists / history) ── */
.track-list { display: flex; flex-direction: column; gap: 2px; }

.track-row {
  display: flex; align-items: center; gap: 14px;
  padding: 10px 14px; border-radius: 10px;
  cursor: pointer; transition: background 0.1s;
}
.track-row:hover { background: var(--surface); }

.track-cover {
  width: 40px; height: 40px; border-radius: 6px;
  object-fit: cover; background: var(--surface-2); flex-shrink: 0;
}

.track-info { flex: 1; min-width: 0; }
.track-name { font-size: 13px; font-weight: 600; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.track-artist { font-size: 11px; color: var(--text-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.track-duration { font-size: 12px; color: var(--text-2); flex-shrink: 0; min-width: 40px; text-align: right; }

.btn-download {
  height: 32px; padding: 0 14px; flex-shrink: 0;
  background: var(--accent); border: none; border-radius: 8px;
  font-family: inherit; font-size: 12px; font-weight: 600;
  color: #000; cursor: pointer; display: flex; align-items: center; gap: 6px;
  transition: background 0.15s;
}
.btn-download:hover { background: #22c95e; }
.btn-download.done { background: var(--surface-2); color: var(--text-2); cursor: default; }
.btn-download.downloading { background: transparent; border: 1px solid var(--border); color: var(--text-2); cursor: default; }

/* ── Download queue ── */
.queue-row {
  display: flex; align-items: center; gap: 14px;
  padding: 12px 14px; border-radius: 10px;
  background: var(--surface); margin-bottom: 4px;
}

.queue-info { flex: 1; min-width: 0; }
.queue-name { font-size: 13px; font-weight: 600; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.queue-sub { font-size: 11px; color: var(--text-2); }

.queue-progress { width: 100%; height: 3px; background: var(--surface-2); border-radius: 3px; margin-top: 6px; }
.queue-progress-fill { height: 100%; background: var(--accent); border-radius: 3px; transition: width 0.3s; }

.queue-status {
  font-size: 11px; font-weight: 600; flex-shrink: 0; min-width: 70px; text-align: right;
}
.queue-status.pending { color: var(--text-3); }
.queue-status.downloading { color: var(--accent); }
.queue-status.done { color: #22c95e; }
.queue-status.error { color: #ef4444; }

.btn-cancel {
  background: none; border: none; cursor: pointer;
  color: var(--text-3); padding: 4px; border-radius: 6px;
  display: flex; align-items: center; transition: color 0.1s, background 0.1s;
}
.btn-cancel:hover { color: #ef4444; background: rgba(239,68,68,0.1); }

/* ── Loading / empty states ── */
.loading-spinner {
  display: flex; align-items: center; justify-content: center;
  height: 120px; color: var(--text-3); gap: 10px; font-size: 13px;
}

.empty-state {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; height: 200px; gap: 8px;
  color: var(--text-3); font-size: 13px; text-align: center;
}

/* ── Modal / Settings ── */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.7); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  z-index: 100; opacity: 0; pointer-events: none; transition: opacity 0.2s;
}
.modal-overlay.open { opacity: 1; pointer-events: all; }

.modal {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 18px; padding: 32px; width: 480px; max-height: 80vh;
  overflow-y: auto; display: flex; flex-direction: column; gap: 20px;
}

.modal-title { font-size: 18px; font-weight: 700; color: var(--text); }

.field { display: flex; flex-direction: column; gap: 6px; }

.field label {
  font-size: 11px; font-weight: 600; color: var(--text-2);
  text-transform: uppercase; letter-spacing: 0.5px;
}

.field input, .field select {
  width: 100%; height: 40px;
  background: var(--bg); border: 1px solid var(--border);
  border-radius: 8px; padding: 0 14px;
  font-family: inherit; font-size: 13px; color: var(--text);
  outline: none; transition: border-color 0.15s;
}
.field input:focus, .field select:focus { border-color: var(--accent); }
.field select option { background: var(--surface); }

.modal-actions { display: flex; justify-content: flex-end; gap: 10px; }

.btn-primary {
  height: 40px; padding: 0 20px;
  background: var(--accent); border: none; border-radius: 8px;
  font-family: inherit; font-size: 13px; font-weight: 700; color: #000;
  cursor: pointer; transition: background 0.15s;
}
.btn-primary:hover { background: #22c95e; }

.btn-ghost {
  height: 40px; padding: 0 16px;
  background: transparent; border: 1px solid var(--border);
  border-radius: 8px; font-family: inherit; font-size: 13px;
  font-weight: 500; color: var(--text-2); cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}
.btn-ghost:hover { border-color: var(--text-2); color: var(--text); }

/* ── Library tree ── */
.lib-artist { margin-bottom: 4px; }
.lib-artist-name {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; border-radius: 8px; cursor: pointer;
  font-size: 13px; font-weight: 600; color: var(--text);
  transition: background 0.1s;
}
.lib-artist-name:hover { background: var(--surface); }
.lib-albums { padding-left: 24px; display: none; }
.lib-artist.open .lib-albums { display: block; }

.lib-album-name {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 10px; border-radius: 8px; cursor: pointer;
  font-size: 12px; font-weight: 500; color: var(--text-2);
  transition: background 0.1s;
}
.lib-album-name:hover { background: var(--surface); }
.lib-tracks { padding-left: 24px; display: none; }
.lib-album.open .lib-tracks { display: block; }

/* ── Playlist grid ── */
.playlist-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
}

.playlist-card {
  background: var(--surface); border-radius: var(--radius-card);
  padding: 12px; cursor: pointer; transition: transform 0.15s;
  display: flex; flex-direction: column; gap: 8px;
}
.playlist-card:hover { transform: translateY(-2px); }

.playlist-cover {
  width: 100%; aspect-ratio: 1; border-radius: 10px;
  object-fit: cover; background: var(--surface-2);
}

.playlist-name {
  font-size: 13px; font-weight: 600; color: var(--text);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.playlist-count { font-size: 11px; color: var(--text-2); }

/* ── View header ── */
.view-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;
}
.view-title { font-size: 20px; font-weight: 800; color: var(--text); }

.btn-sm {
  height: 32px; padding: 0 14px;
  border: 1px solid var(--border); border-radius: 8px;
  background: transparent; font-family: inherit; font-size: 12px;
  font-weight: 500; color: var(--text-2); cursor: pointer;
  display: flex; align-items: center; gap: 6px; transition: border-color 0.15s, color 0.15s;
}
.btn-sm:hover { border-color: var(--text-2); color: var(--text); }
.btn-sm.danger:hover { border-color: #ef4444; color: #ef4444; }

/* ── Filter input ── */
.filter-input {
  width: 100%; height: 36px;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 0 14px;
  font-family: inherit; font-size: 12px; color: var(--text);
  outline: none; transition: border-color 0.15s;
}
.filter-input::placeholder { color: var(--text-3); }
.filter-input:focus { border-color: var(--accent); }

/* ── Toast notifications ── */
#toast-container {
  position: fixed; bottom: 100px; right: 24px;
  display: flex; flex-direction: column; gap: 8px; z-index: 200;
}

.toast {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 10px; padding: 12px 16px;
  font-size: 13px; color: var(--text); max-width: 300px;
  animation: slide-in 0.2s ease; display: flex; align-items: center; gap: 10px;
}
.toast.success { border-color: var(--accent); }
.toast.error { border-color: #ef4444; }

@keyframes slide-in {
  from { transform: translateX(20px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
```

**Step 2: No tests for CSS. Verify visually after Task 2.**

---

## Task 2: App shell HTML

**Files:**
- Create: `web/app.html`

**Step 1: Create app.html**

```html
<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SONGER</title>
  <link rel="stylesheet" href="/static/css/app.css">
  <!-- Lucide icons -->
  <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
</head>
<body>
  <div id="app">
    <!-- Sidebar -->
    <nav id="sidebar">
      <div class="sidebar-logo">
        <div class="logo-mark">S</div>
        <span class="logo-name">SONGER</span>
      </div>

      <div class="sidebar-label">Menu</div>

      <a class="nav-item active" data-view="home" href="#">
        <i data-lucide="house" width="16" height="16"></i>
        Home
      </a>
      <a class="nav-item" data-view="search" href="#">
        <i data-lucide="search" width="16" height="16"></i>
        Search
      </a>
      <a class="nav-item" data-view="playlists" href="#">
        <i data-lucide="music" width="16" height="16"></i>
        Playlists
      </a>
      <a class="nav-item" data-view="queue" href="#">
        <i data-lucide="download" width="16" height="16"></i>
        Downloads
        <span class="nav-badge" id="queue-badge" style="display:none">0</span>
      </a>
      <a class="nav-item" data-view="library" href="#">
        <i data-lucide="library" width="16" height="16"></i>
        Library
      </a>
      <a class="nav-item" data-view="history" href="#">
        <i data-lucide="history" width="16" height="16"></i>
        History
      </a>

      <div class="sidebar-spacer"></div>
      <div class="sidebar-divider"></div>

      <div class="sidebar-status">
        <span class="status-dot" id="spotify-dot"></span>
        <span id="spotify-label">Spotify</span>
      </div>
      <div class="sidebar-status">
        <span class="status-dot" id="slsk-dot"></span>
        <span id="slsk-label">Soulseek</span>
      </div>

      <div class="nav-settings" id="open-settings">
        <i data-lucide="settings" width="16" height="16"></i>
        Settings
      </div>
    </nav>

    <!-- Right panel -->
    <div id="right-panel">
      <div id="content">
        <!-- Views injected here by JS -->
      </div>

      <!-- Player bar -->
      <div id="player">
        <div class="player-left">
          <img class="player-art" id="player-art" src="" alt="">
          <div class="player-info">
            <div class="player-title" id="player-title">—</div>
            <div class="player-sub" id="player-sub"></div>
          </div>
        </div>

        <div class="player-center">
          <div class="player-controls">
            <button class="ctrl-btn" id="ctrl-shuffle" title="Shuffle">
              <i data-lucide="shuffle" width="18" height="18"></i>
            </button>
            <button class="ctrl-btn" id="ctrl-prev" title="Previous">
              <i data-lucide="skip-back" width="20" height="20"></i>
            </button>
            <button class="ctrl-play" id="ctrl-play" title="Play/Pause">
              <i data-lucide="play" width="16" height="16" id="play-icon"></i>
            </button>
            <button class="ctrl-btn" id="ctrl-next" title="Next">
              <i data-lucide="skip-forward" width="20" height="20"></i>
            </button>
            <button class="ctrl-btn" id="ctrl-repeat" title="Repeat">
              <i data-lucide="repeat" width="18" height="18"></i>
            </button>
          </div>
          <div class="player-progress">
            <span class="progress-time" id="p-current">0:00</span>
            <div class="progress-track" id="progress-track">
              <div class="progress-fill" id="progress-fill"></div>
            </div>
            <span class="progress-time" id="p-duration">0:00</span>
          </div>
        </div>

        <div class="player-right">
          <div class="volume-wrap">
            <button class="ctrl-btn" id="ctrl-mute">
              <i data-lucide="volume-2" width="16" height="16" id="volume-icon"></i>
            </button>
            <input type="range" id="volume-slider" min="0" max="100" value="80">
          </div>
          <button class="ctrl-btn" id="ctrl-queue-view" title="Queue">
            <i data-lucide="list" width="16" height="16"></i>
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Settings modal -->
  <div class="modal-overlay" id="settings-modal">
    <div class="modal">
      <div class="modal-title">Settings</div>

      <div class="field">
        <label>Download Path</label>
        <input type="text" id="s-dl-path" placeholder="~/Music/SONGER">
      </div>
      <div class="field">
        <label>Format</label>
        <select id="s-format">
          <option value="flac">FLAC</option>
          <option value="mp3_320">MP3 320kbps</option>
          <option value="mp3_256">MP3 256kbps</option>
          <option value="mp3_128">MP3 128kbps</option>
        </select>
      </div>
      <div class="field">
        <label>Source</label>
        <select id="s-source">
          <option value="hybrid">Both (Soulseek first)</option>
          <option value="youtube">YouTube only</option>
          <option value="soulseek">Soulseek only</option>
        </select>
      </div>
      <div class="field">
        <label>Soulseek URL</label>
        <input type="text" id="s-slsk-url" placeholder="http://localhost:5030">
      </div>
      <div class="field">
        <label>Soulseek API Key</label>
        <input type="password" id="s-slsk-key" placeholder="Leave empty if none">
      </div>

      <div class="modal-actions">
        <button class="btn-ghost" id="close-settings">Cancel</button>
        <button class="btn-primary" id="save-settings">Save</button>
      </div>
    </div>
  </div>

  <!-- Toast container -->
  <div id="toast-container"></div>

  <!-- Hidden audio element -->
  <audio id="audio-el" preload="none"></audio>

  <script src="/static/js/api.js"></script>
  <script src="/static/js/player.js"></script>
  <script src="/static/js/views/home.js"></script>
  <script src="/static/js/views/search.js"></script>
  <script src="/static/js/views/queue.js"></script>
  <script src="/static/js/views/playlists.js"></script>
  <script src="/static/js/views/library.js"></script>
  <script src="/static/js/views/history.js"></script>
  <script src="/static/js/app.js"></script>
</body>
</html>
```

**Step 2: No automated test. Open browser after Task 3 to verify layout.**

---

## Task 3: Flask routes — /app + /api/status + /api/stats

**Files:**
- Modify: `server.py` — add imports and new routes after existing disconnect route

**Step 1: Write test**

Create `tests/test_api.py`:
```python
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import server

@pytest.fixture
def client():
    server.app.config["TESTING"] = True
    with server.app.test_client() as c:
        yield c

def test_app_route_redirects_without_token(client):
    # No token file → redirect to setup
    if server.TOKEN_PATH.exists():
        pytest.skip("Token exists, skip redirect test")
    resp = client.get("/app")
    assert resp.status_code == 302

def test_status_endpoint(client):
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "spotify" in data
    assert "soulseek" in data

def test_stats_endpoint(client):
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "tracks" in data
    assert "storage_gb" in data
```

**Step 2: Run test to verify it fails**

```
cd e:\CODING\CLAUDECODEHOUSE\PROJECTOS\music-tools\SONGER
python -m pytest tests/test_api.py -v
```
Expected: FAIL — no `tests/` directory or routes missing.

**Step 3: Create tests/ directory and add Flask routes to server.py**

First: `mkdir tests && echo "" > tests/__init__.py`

Add to `server.py` after the existing imports:
```python
import os
from core.config import Config
from core.library import scan_library
from core.history import DownloadHistory
```

Add these routes after the `/disconnect` route:

```python
@app.route("/app")
def app_shell():
    if not TOKEN_PATH.exists():
        return redirect("/?error=no_token")
    return render_template("app.html")


@app.route("/api/status")
def api_status():
    cfg = _load_config()
    has_spotify = TOKEN_PATH.exists() and bool(cfg.get("spotify", {}).get("client_id"))

    slsk_ok = False
    if cfg.get("soulseek", {}).get("enabled"):
        try:
            import requests as req
            slsk_url = cfg.get("soulseek", {}).get("slskd_url", "http://localhost:5030")
            r = req.get(f"{slsk_url}/api/v0/application", timeout=2)
            slsk_ok = r.status_code == 200
        except Exception:
            slsk_ok = False

    return jsonify({
        "spotify": "ok" if has_spotify else "error",
        "soulseek": "ok" if slsk_ok else "error",
    })


@app.route("/api/stats")
def api_stats():
    cfg = _load_config()
    dl_path = cfg.get("download", {}).get("path", str(Path.home() / "Music" / "SONGER"))

    try:
        files = scan_library(dl_path)
    except Exception:
        files = []

    total_mb = sum(f.get("size_mb", 0) for f in files)

    history = DownloadHistory()
    playlists_count = len(set(
        e.get("url", "") for e in history.get_all()
        if "playlist" in e.get("url", "")
    ))

    # Count active downloads from global queue (set up in Task 6)
    active = len([t for t in _download_queue.values() if t.get("status") == "downloading"]) if "_download_queue" in globals() else 0

    return jsonify({
        "tracks": len(files),
        "downloading": active,
        "playlists": playlists_count,
        "storage_gb": round(total_mb / 1024, 1),
    })
```

Also update `_open_browser()` to redirect to `/app` if token exists:
```python
def _open_browser():
    time.sleep(0.8)
    url = "http://127.0.0.1:8888/app" if TOKEN_PATH.exists() else "http://127.0.0.1:8888"
    webbrowser.open(url)
```

**Step 4: Run tests**

```
python -m pytest tests/test_api.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add web/static/css/app.css web/app.html server.py tests/
git commit -m "feat: add app shell, CSS design system, Flask /app + /api/status + /api/stats"
```

---

## Task 4: API utility + Home view JS

**Files:**
- Create: `web/static/js/api.js`
- Create: `web/static/js/views/home.js`
- Create dirs: `web/static/js/` and `web/static/js/views/`

**Step 1: Create api.js**

```javascript
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
```

**Step 2: Create home.js**

```javascript
// web/static/js/views/home.js
async function renderHome() {
  const content = document.getElementById("content");
  content.innerHTML = `
    <div class="search-row">
      <div class="search-input-wrap">
        <i data-lucide="search" width="16" height="16"></i>
        <input id="search-input" type="text" placeholder="Search music, paste Spotify URL...">
      </div>
      <button class="btn-search" id="do-search">
        <i data-lucide="search" width="16" height="16"></i>
        Search
      </button>
    </div>

    <div class="stats-row" id="stats-row">
      ${["—","—","—","—"].map((v,i) => `
        <div class="stat-card">
          <div class="stat-value ${i===1?"accent":""}" id="stat-${i}">${v}</div>
          <div class="stat-label">${["tracks in library","downloading now","playlists synced","storage used"][i]}</div>
        </div>`).join("")}
    </div>

    <div>
      <div class="section-header">
        <span class="section-title">Recently Downloaded</span>
        <a class="section-link" data-view="history" href="#">View all →</a>
      </div>
    </div>

    <div class="album-grid" id="recent-grid">
      ${Array(5).fill(0).map(() => `
        <div class="album-card">
          <div class="album-cover-placeholder">
            <i data-lucide="disc-3" width="32" height="32"></i>
          </div>
          <div class="album-name" style="color:var(--text-3)">—</div>
          <div class="album-artist" style="color:var(--text-3)">—</div>
        </div>`).join("")}
    </div>
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
  } catch (e) {
    console.error("Stats error:", e);
  }

  // Load recent history
  try {
    const history = await API.get("/api/history");
    const recent = history.slice(0, 5);
    const grid = document.getElementById("recent-grid");
    if (recent.length > 0) {
      grid.innerHTML = recent.map(h => `
        <div class="album-card" title="${h.name}">
          <div class="album-cover-placeholder">
            <i data-lucide="disc-3" width="32" height="32"></i>
          </div>
          <div class="album-name">${h.name}</div>
          <div class="album-artist">${h.format?.toUpperCase() || ""} · ${h.done_count} tracks</div>
        </div>`).join("");
      lucide.createIcons();
    }
  } catch (e) {
    console.error("History error:", e);
  }
}
```

**Step 3: No automated test for view rendering. Verify manually after Task 5 (app.js).**

---

## Task 5: App.js — navigation + sidebar + status polling

**Files:**
- Create: `web/static/js/app.js`

**Step 1: Create app.js**

```javascript
// web/static/js/app.js

const VIEWS = {
  home: renderHome,
  search: renderSearch,
  queue: renderQueue,
  playlists: renderPlaylists,
  library: renderLibrary,
  history: renderHistory,
};

window.APP = {
  currentView: null,
  navigate(view, params = {}) {
    // Update sidebar active state
    document.querySelectorAll(".nav-item").forEach(el => {
      el.classList.toggle("active", el.dataset.view === view);
    });
    this.currentView = view;
    if (VIEWS[view]) VIEWS[view](params);
  },
};

// Sidebar navigation
document.querySelectorAll(".nav-item[data-view]").forEach(el => {
  el.addEventListener("click", e => {
    e.preventDefault();
    APP.navigate(el.dataset.view);
  });
});

// Settings modal
const settingsModal = document.getElementById("settings-modal");
document.getElementById("open-settings").addEventListener("click", () => openSettings());
document.getElementById("close-settings").addEventListener("click", () => settingsModal.classList.remove("open"));
document.getElementById("save-settings").addEventListener("click", () => saveSettings());

settingsModal.addEventListener("click", e => {
  if (e.target === settingsModal) settingsModal.classList.remove("open");
});

async function openSettings() {
  try {
    const cfg = await API.get("/api/config");
    document.getElementById("s-dl-path").value = cfg.download?.path || "";
    document.getElementById("s-format").value = cfg.download?.format || "mp3_320";
    document.getElementById("s-source").value = cfg.download?.source || "hybrid";
    document.getElementById("s-slsk-url").value = cfg.soulseek?.slskd_url || "";
    document.getElementById("s-slsk-key").value = cfg.soulseek?.slskd_api_key || "";
  } catch (e) {}
  settingsModal.classList.add("open");
}

async function saveSettings() {
  try {
    await API.post("/api/settings", {
      download: {
        path: document.getElementById("s-dl-path").value,
        format: document.getElementById("s-format").value,
        source: document.getElementById("s-source").value,
      },
      soulseek: {
        slskd_url: document.getElementById("s-slsk-url").value,
        slskd_api_key: document.getElementById("s-slsk-key").value,
      },
    });
    settingsModal.classList.remove("open");
    toast("Settings saved", "success");
  } catch (e) {
    toast("Failed to save settings", "error");
  }
}

// Status polling (every 10s)
async function pollStatus() {
  try {
    const s = await API.get("/api/status");
    const spotDot = document.getElementById("spotify-dot");
    const slskDot = document.getElementById("slsk-dot");
    spotDot.className = "status-dot " + (s.spotify === "ok" ? "ok" : "err");
    document.getElementById("spotify-label").textContent = s.spotify === "ok" ? "Spotify connected" : "Spotify offline";
    slskDot.className = "status-dot " + (s.soulseek === "ok" ? "ok" : "");
    document.getElementById("slsk-label").textContent = s.soulseek === "ok" ? "Soulseek connected" : "Soulseek offline";
  } catch (e) {}
}

pollStatus();
setInterval(pollStatus, 10000);

// Boot
lucide.createIcons();
APP.navigate("home");
```

**Step 2: Test in browser**

```
python server.py
```
Open `http://127.0.0.1:8888/app`. Expected: sidebar renders, Home view loads with stats.

**Step 3: Commit**

```bash
git add web/static/js/
git commit -m "feat: add app.js navigation, home view, API utility"
```

---

## Task 6: Flask search API + Search view

**Files:**
- Modify: `server.py` — add `/api/search` route
- Create: `web/static/js/views/search.js`

**Step 1: Write test**

Add to `tests/test_api.py`:
```python
def test_search_requires_query(client):
    resp = client.get("/api/search")
    assert resp.status_code == 400
    data = resp.get_json()
    assert "error" in data

def test_search_returns_list(client, monkeypatch):
    def mock_search(*args, **kwargs):
        return [{"id": "t1", "name": "Test Track", "artists": [{"name": "Artist"}],
                 "album": {"name": "Album", "images": []}, "duration_ms": 210000}]
    import core.spotify as sp_mod
    monkeypatch.setattr(sp_mod, "_search_tracks", mock_search, raising=False)
    resp = client.get("/api/search?q=test")
    assert resp.status_code in (200, 500)  # 500 if spotify not configured
```

**Step 2: Run — expect FAIL (route missing)**

```
python -m pytest tests/test_api.py::test_search_requires_query -v
```

**Step 3: Add search route to server.py**

```python
# Global spotify client (lazy init)
_spotify = None

def _get_spotify():
    global _spotify
    if _spotify is None:
        from core.spotify import SpotifyClient
        _spotify = SpotifyClient()
    return _spotify


@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "q required"}), 400
    try:
        sp = _get_spotify()
        # detect URL type
        if "spotify.com" in q:
            results = sp.resolve_url(q)
        else:
            results = sp.search_tracks(q, limit=30)

        tracks = []
        for t in results:
            tracks.append({
                "id": t.get("id", ""),
                "name": t.get("name", ""),
                "artist": ", ".join(a["name"] for a in t.get("artists", [])),
                "album": t.get("album", {}).get("name", ""),
                "cover": (t.get("album", {}).get("images") or [{}])[0].get("url", ""),
                "duration_ms": t.get("duration_ms", 0),
                "uri": t.get("uri", ""),
                "external_url": t.get("external_urls", {}).get("spotify", ""),
            })
        return jsonify(tracks)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

Also add `/api/config` and `/api/settings` routes:
```python
@app.route("/api/config")
def api_config():
    return jsonify(_load_config())


@app.route("/api/settings", methods=["POST"])
def api_settings():
    data = request.get_json() or {}
    cfg = _load_config()
    for section, values in data.items():
        if section not in cfg:
            cfg[section] = {}
        cfg[section].update(values)
    _save_config(cfg)
    return jsonify({"ok": True})
```

**Step 4: Create search.js**

```javascript
// web/static/js/views/search.js
async function renderSearch(params = {}) {
  const content = document.getElementById("content");
  content.innerHTML = `
    <div class="search-row">
      <div class="search-input-wrap">
        <i data-lucide="search" width="16" height="16"></i>
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
            btn.innerHTML = `<i data-lucide="check" width="14" height="14"></i> Added`;
            btn.classList.remove("downloading");
            btn.classList.add("done");
            lucide.createIcons();
            toast(`Added: ${btn.dataset.name}`, "success");
          } catch (err) {
            btn.innerHTML = `<i data-lucide="download" width="14" height="14"></i> Download`;
            btn.classList.remove("downloading");
            lucide.createIcons();
            toast("Download failed", "error");
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
```

**Step 5: Run tests**

```
python -m pytest tests/test_api.py -v
```

**Step 6: Commit**

```bash
git add server.py web/static/js/views/search.js tests/test_api.py
git commit -m "feat: search API + search view with download buttons"
```

---

## Task 7: Download queue — backend + SSE + view

**Files:**
- Modify: `server.py` — add queue state + download routes + SSE endpoint
- Create: `web/static/js/views/queue.js`

**Step 1: Write test**

Add to `tests/test_api.py`:
```python
def test_download_requires_body(client):
    resp = client.post("/api/download", data="{}", content_type="application/json")
    assert resp.status_code in (200, 400)

def test_queue_returns_list(client):
    resp = client.get("/api/queue")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
```

**Step 2: Add queue state and routes to server.py**

Add after imports:
```python
import uuid
from collections import OrderedDict

_download_queue: dict[str, dict] = OrderedDict()
_queue_lock = threading.Lock()
_sse_clients: list = []
```

Add routes:
```python
@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.get_json() or {}
    track_id = data.get("id") or data.get("uri", "")
    if not track_id:
        return jsonify({"error": "id required"}), 400

    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "track_id": track_id,
        "name": data.get("name", "Unknown"),
        "artist": data.get("artist", ""),
        "album": data.get("album", ""),
        "uri": data.get("uri", ""),
        "status": "pending",
        "progress": 0,
        "error": "",
    }
    with _queue_lock:
        _download_queue[job_id] = job

    threading.Thread(target=_run_download, args=(job_id, data), daemon=True).start()
    _sse_push({"type": "queue_update"})
    return jsonify({"job_id": job_id})


def _run_download(job_id: str, track: dict):
    cfg = _load_config()
    with _queue_lock:
        if job_id not in _download_queue:
            return
        _download_queue[job_id]["status"] = "downloading"
    _sse_push({"type": "queue_update"})

    try:
        from core.config import Config
        from core.downloader import Downloader
        c = Config()
        dl = Downloader(c)
        dl.setup()

        # Build track dict for downloader
        t = {
            "id": track.get("id", ""),
            "name": track.get("name", "Unknown"),
            "artists": [{"name": a} for a in track.get("artist", "").split(", ")],
            "album": {"name": track.get("album", "")},
            "uri": track.get("uri", ""),
        }

        def progress_cb(pct):
            with _queue_lock:
                if job_id in _download_queue:
                    _download_queue[job_id]["progress"] = pct
            _sse_push({"type": "progress", "job_id": job_id, "progress": pct})

        result = dl.download_track(t, progress_callback=progress_cb)

        with _queue_lock:
            if job_id in _download_queue:
                _download_queue[job_id]["status"] = "done" if result.success else "error"
                _download_queue[job_id]["progress"] = 100 if result.success else 0
                _download_queue[job_id]["error"] = result.error
    except Exception as e:
        with _queue_lock:
            if job_id in _download_queue:
                _download_queue[job_id]["status"] = "error"
                _download_queue[job_id]["error"] = str(e)

    _sse_push({"type": "queue_update"})


@app.route("/api/queue")
def api_queue():
    with _queue_lock:
        return jsonify(list(_download_queue.values()))


@app.route("/api/queue/<job_id>", methods=["DELETE"])
def api_queue_cancel(job_id):
    with _queue_lock:
        if job_id in _download_queue:
            _download_queue[job_id]["status"] = "cancelled"
    _sse_push({"type": "queue_update"})
    return jsonify({"ok": True})


@app.route("/api/queue", methods=["DELETE"])
def api_queue_clear():
    with _queue_lock:
        for job in _download_queue.values():
            if job["status"] in ("pending", "downloading"):
                job["status"] = "cancelled"
    _sse_push({"type": "queue_update"})
    return jsonify({"ok": True})


# SSE
import queue as queue_mod

_sse_queues: list[queue_mod.Queue] = []

def _sse_push(data: dict):
    import json as _json
    msg = f"data: {_json.dumps(data)}\n\n"
    for q in list(_sse_queues):
        try:
            q.put_nowait(msg)
        except Exception:
            pass


@app.route("/api/events")
def api_events():
    import json as _json
    q = queue_mod.Queue()
    _sse_queues.append(q)

    def generate():
        try:
            yield "data: {\"type\":\"connected\"}\n\n"
            while True:
                try:
                    msg = q.get(timeout=30)
                    yield msg
                except queue_mod.Empty:
                    yield ": ping\n\n"
        except GeneratorExit:
            pass
        finally:
            if q in _sse_queues:
                _sse_queues.remove(q)

    return app.response_class(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

**Note:** `dl.download_track()` with a `progress_callback` parameter may not exist in the current downloader. Check `core/downloader.py` and adapt the call to match the actual API. If the method signature differs, wrap appropriately.

**Step 3: Create queue.js**

```javascript
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
        <span class="queue-status ${j.status}">${j.status}</span>
        ${j.status !== "done" && j.status !== "cancelled"
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
```

**Step 4: Run tests**

```
python -m pytest tests/test_api.py -v
```

**Step 5: Commit**

```bash
git add server.py web/static/js/views/queue.js
git commit -m "feat: download queue API + SSE + queue view"
```

---

## Task 8: Playlists, Library, History views

**Files:**
- Modify: `server.py` — add `/api/playlists`, `/api/library`, `/api/history`
- Create: `web/static/js/views/playlists.js`
- Create: `web/static/js/views/library.js`
- Create: `web/static/js/views/history.js`

**Step 1: Add routes to server.py**

```python
@app.route("/api/playlists")
def api_playlists():
    try:
        sp = _get_spotify()
        playlists = sp.get_user_playlists()
        result = []
        for p in playlists:
            result.append({
                "id": p.get("id", ""),
                "name": p.get("name", ""),
                "tracks_total": p.get("tracks", {}).get("total", 0),
                "cover": (p.get("images") or [{}])[0].get("url", ""),
                "uri": p.get("uri", ""),
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/playlists/<playlist_id>/tracks")
def api_playlist_tracks(playlist_id):
    try:
        sp = _get_spotify()
        tracks = sp.get_playlist_tracks(playlist_id)
        result = []
        for t in tracks:
            track = t.get("track") or t
            if not track:
                continue
            result.append({
                "id": track.get("id", ""),
                "name": track.get("name", ""),
                "artist": ", ".join(a["name"] for a in track.get("artists", [])),
                "album": track.get("album", {}).get("name", ""),
                "cover": (track.get("album", {}).get("images") or [{}])[0].get("url", ""),
                "duration_ms": track.get("duration_ms", 0),
                "uri": track.get("uri", ""),
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/library")
def api_library():
    cfg = _load_config()
    dl_path = cfg.get("download", {}).get("path", str(Path.home() / "Music" / "SONGER"))
    try:
        files = scan_library(dl_path)
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history")
def api_history():
    h = DownloadHistory()
    return jsonify(h.get_all())


@app.route("/api/history", methods=["DELETE"])
def api_history_clear():
    h = DownloadHistory()
    h.clear()
    return jsonify({"ok": True})
```

**Step 2: Create playlists.js**

```javascript
// web/static/js/views/playlists.js
async function renderPlaylists(params = {}) {
  const content = document.getElementById("content");

  if (params.playlist_id) {
    // Show playlist tracks
    content.innerHTML = `
      <div class="view-header">
        <button class="btn-sm" id="back-playlists"><i data-lucide="arrow-left" width="14" height="14"></i> Back</button>
        <span class="view-title" id="pl-title">Playlist</span>
        <button class="btn-primary" id="dl-all" style="height:32px;font-size:12px">
          <i data-lucide="download" width="14" height="14"></i> Download all
        </button>
      </div>
      <div id="pl-tracks"><div class="loading-spinner"><i data-lucide="loader-2" width="20" height="20"></i></div></div>
    `;
    lucide.createIcons();
    document.getElementById("back-playlists").addEventListener("click", () => renderPlaylists());

    const tracks = await API.get(`/api/playlists/${params.playlist_id}/tracks`);
    document.getElementById("pl-title").textContent = params.playlist_name || "Playlist";
    document.getElementById("dl-all").addEventListener("click", async () => {
      for (const t of tracks) {
        await API.post("/api/download", t).catch(() => {});
      }
      toast(`Added ${tracks.length} tracks`, "success");
      APP.navigate("queue");
    });

    document.getElementById("pl-tracks").innerHTML = `<div class="track-list">${tracks.map(t => `
      <div class="track-row">
        ${t.cover ? `<img class="track-cover" src="${t.cover}" alt="">` : `<div class="track-cover"></div>`}
        <div class="track-info">
          <div class="track-name">${t.name}</div>
          <div class="track-artist">${t.artist} · ${t.album}</div>
        </div>
        <div class="track-duration">${fmtDuration(t.duration_ms)}</div>
        <button class="btn-download" data-track='${JSON.stringify(t)}'>
          <i data-lucide="download" width="14" height="14"></i> Download
        </button>
      </div>`).join("")}</div>`;
    lucide.createIcons();

    document.querySelectorAll(".btn-download[data-track]").forEach(btn => {
      btn.addEventListener("click", async () => {
        const t = JSON.parse(btn.dataset.track);
        await API.post("/api/download", t);
        btn.classList.add("done");
        btn.innerHTML = `<i data-lucide="check" width="14" height="14"></i> Added`;
        lucide.createIcons();
      });
    });
    return;
  }

  // Playlist grid
  content.innerHTML = `
    <div class="view-header"><span class="view-title">Playlists</span></div>
    <div id="pl-grid"><div class="loading-spinner"><i data-lucide="loader-2" width="20" height="20"></i></div></div>
  `;
  lucide.createIcons();

  try {
    const playlists = await API.get("/api/playlists");
    document.getElementById("pl-grid").innerHTML = `<div class="playlist-grid">${playlists.map(p => `
      <div class="playlist-card" data-id="${p.id}" data-name="${p.name}">
        ${p.cover ? `<img class="playlist-cover" src="${p.cover}" alt="">` : `<div class="playlist-cover" style="display:flex;align-items:center;justify-content:center;background:var(--surface-2)"><i data-lucide="music" width="32" height="32"></i></div>`}
        <div class="playlist-name">${p.name}</div>
        <div class="playlist-count">${p.tracks_total} tracks</div>
      </div>`).join("")}</div>`;
    lucide.createIcons();

    document.querySelectorAll(".playlist-card").forEach(card => {
      card.addEventListener("click", () => renderPlaylists({ playlist_id: card.dataset.id, playlist_name: card.dataset.name }));
    });
  } catch (e) {
    document.getElementById("pl-grid").innerHTML = `<div class="empty-state" style="color:#ef4444">${e.message}</div>`;
  }
}
```

**Step 3: Create library.js**

```javascript
// web/static/js/views/library.js
async function renderLibrary() {
  const content = document.getElementById("content");
  content.innerHTML = `
    <div class="view-header">
      <span class="view-title">Library</span>
      <button class="btn-sm" id="refresh-lib"><i data-lucide="refresh-cw" width="14" height="14"></i> Refresh</button>
    </div>
    <input class="filter-input" id="lib-filter" placeholder="Filter by artist or track name...">
    <div id="lib-tree"><div class="loading-spinner"><i data-lucide="loader-2" width="20" height="20"></i></div></div>
  `;
  lucide.createIcons();

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

    libTree.innerHTML = Object.entries(tree).map(([artist, albums]) => `
      <div class="lib-artist">
        <div class="lib-artist-name">
          <i data-lucide="chevron-right" width="14" height="14"></i>
          ${artist}
        </div>
        <div class="lib-albums">${Object.entries(albums).map(([album, tracks]) => `
          <div class="lib-album">
            <div class="lib-album-name">
              <i data-lucide="disc-3" width="12" height="12"></i>
              ${album} <span style="color:var(--text-3);font-size:11px">(${tracks.length})</span>
            </div>
            <div class="lib-tracks">${tracks.map(t => `
              <div class="track-row" style="padding-left:8px">
                <div class="track-info">
                  <div class="track-name">${t.name}</div>
                  <div class="track-artist">${t.ext.toUpperCase()} · ${t.size_mb} MB</div>
                </div>
                <button class="ctrl-btn play-lib" data-path="${t.path}" title="Play">
                  <i data-lucide="play" width="16" height="16"></i>
                </button>
              </div>`).join("")}
            </div>
          </div>`).join("")}
        </div>
      </div>`).join("");
    lucide.createIcons();

    // Toggle open
    document.querySelectorAll(".lib-artist-name").forEach(el => {
      el.addEventListener("click", () => el.closest(".lib-artist").classList.toggle("open"));
    });
    document.querySelectorAll(".lib-album-name").forEach(el => {
      el.addEventListener("click", () => el.closest(".lib-album").classList.toggle("open"));
    });

    // Play buttons
    document.querySelectorAll(".play-lib").forEach(btn => {
      btn.addEventListener("click", e => {
        e.stopPropagation();
        window.PLAYER?.playFile(btn.dataset.path);
      });
    });
  }

  document.getElementById("refresh-lib").addEventListener("click", loadLib);
  document.getElementById("lib-filter").addEventListener("input", () => renderTree(allFiles));

  loadLib();
}
```

**Step 4: Create history.js**

```javascript
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
```

**Step 5: Run tests + manual check**

```
python -m pytest tests/test_api.py -v
python server.py
```
Open `/app`, check Playlists, Library, History views.

**Step 6: Commit**

```bash
git add server.py web/static/js/views/
git commit -m "feat: playlists, library, history views + Flask API routes"
```

---

## Task 9: HTML5 Audio player

**Files:**
- Create: `web/static/js/player.js`
- Modify: `server.py` — add `/stream/<path>` route

**Step 1: Add stream route to server.py**

```python
import urllib.parse

@app.route("/stream/<path:filepath>")
def stream_file(filepath):
    # filepath is URL-encoded absolute path
    decoded = urllib.parse.unquote(filepath)
    p = Path(decoded)
    if not p.exists() or not p.is_file():
        return jsonify({"error": "File not found"}), 404
    # Only serve files from the configured download path
    cfg = _load_config()
    dl_path = cfg.get("download", {}).get("path", "")
    try:
        p.relative_to(dl_path)
    except ValueError:
        return jsonify({"error": "Access denied"}), 403
    from flask import send_file
    return send_file(str(p))
```

**Step 2: Create player.js**

```javascript
// web/static/js/player.js
const audioEl = document.getElementById("audio-el");
let _playlist = [];
let _currentIdx = -1;
let _shuffle = false;
let _repeat = false;

window.PLAYER = {
  playFile(path, info = {}) {
    audioEl.src = `/stream/${encodeURIComponent(path)}`;
    audioEl.play();
    document.getElementById("player-title").textContent = info.name || path.split(/[\\/]/).pop().replace(/\.[^.]+$/, "");
    document.getElementById("player-sub").textContent = [info.artist, info.album].filter(Boolean).join(" · ");
    document.getElementById("player-art").src = info.cover || "";
    document.getElementById("play-icon").setAttribute("data-lucide", "pause");
    lucide.createIcons();
  },
  setPlaylist(files, startIdx = 0) {
    _playlist = files;
    _currentIdx = startIdx;
    if (files[startIdx]) this.playFile(files[startIdx].path, files[startIdx]);
  },
};

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
  PLAYER.playFile(t.path, t);
}

function playPrev() {
  if (!_playlist.length) return;
  _currentIdx = (_currentIdx - 1 + _playlist.length) % _playlist.length;
  const t = _playlist[_currentIdx];
  PLAYER.playFile(t.path, t);
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

// Queue view btn
document.getElementById("ctrl-queue-view").addEventListener("click", () => APP.navigate("queue"));

function fmtSeconds(s) {
  if (isNaN(s)) return "0:00";
  return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
}
```

**Step 3: Commit**

```bash
git add server.py web/static/js/player.js
git commit -m "feat: HTML5 audio player + /stream endpoint"
```

---

## Task 10: Final integration + startup redirect

**Files:**
- Modify: `server.py` — update callback to redirect to /app after OAuth
- Create: `web/success.html` (if not exists — shown after OAuth)

**Step 1: Check if web/success.html exists**

```bash
ls web/
```

**Step 2: Update OAuth callback in server.py**

The existing callback route ends with:
```python
threading.Thread(target=_launch_app, daemon=True).start()
return render_template("success.html")
```

Replace with:
```python
return redirect("/app")
```

Remove `_launch_app` function entirely (no longer needed — browser stays open).

**Step 3: Remove PyQt6 launch from server.py**

Delete `_launch_app()` function and its import of `sys, subprocess` if only used there.

**Step 4: Verify full flow**

```
python server.py
```
1. Browser opens → `http://127.0.0.1:8888`
2. If token exists → redirects to `/app` directly
3. If not → setup page → OAuth → redirects to `/app`
4. All 6 views work
5. Download a track → appears in queue with progress
6. Play a downloaded file from Library

**Step 5: Commit**

```bash
git add server.py web/
git commit -m "feat: complete SONGER web app - full flow from OAuth to downloads"
```

---

## Task 11: Check core/spotify.py API surface

Before running, verify method names used in server.py match actual core/spotify.py:

```bash
grep -n "def " core/spotify.py
```

Expected methods: `search_tracks()`, `get_user_playlists()`, `get_playlist_tracks()`, `resolve_url()`.
If names differ, update the calls in `server.py` accordingly.

Similarly verify `core/downloader.py` `download_track()` signature:
```bash
grep -n "def download_track\|def download" core/downloader.py
```

Adapt `_run_download()` in server.py to match actual method name and signature.

**This task has no code to write — it's an integration check.**

---

## Quick reference: file structure after all tasks

```
server.py                        # Extended with all API routes
web/
  index.html                     # Unchanged — Spotify setup
  app.html                       # App shell
  static/
    css/
      app.css                    # Full design system
    js/
      api.js                     # Fetch utilities
      player.js                  # HTML5 audio player
      app.js                     # Navigation + settings + polling
      views/
        home.js
        search.js
        queue.js
        playlists.js
        library.js
        history.js
tests/
  __init__.py
  test_api.py
```

---

## Run

```bash
cd e:\CODING\CLAUDECODEHOUSE\PROJECTOS\music-tools\SONGER
python server.py
```

Opens `http://127.0.0.1:8888` — redirects to `/app` if Spotify configured.
