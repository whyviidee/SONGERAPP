# SONGER Liquid Redesign — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign completo do SONGER com UI "Liquid" — React + Vite + Tailwind, wrapped em PyWebView para .app nativo Mac. Abrir a app e ter tudo a funcionar (Flask backend auto-start).

**Architecture:** PyWebView lança o Flask server.py como thread background, depois abre uma janela nativa que carrega o React frontend (build estático servido pelo Flask). Zero processos separados — um único `python songer.py` faz tudo. O React frontend comunica com o Flask backend via fetch() para localhost:8888.

**Tech Stack:** React 19, Vite 6, Tailwind CSS v4, Framer Motion, PyWebView, Flask (existente), PyInstaller (build .app)

---

## Design System — "Liquid"

**Paleta:**
- `--bg-deep`: #0a0a0f (preto profundo azulado)
- `--bg-surface`: rgba(255,255,255,0.04) (glass panels)
- `--bg-surface-hover`: rgba(255,255,255,0.08)
- `--accent-primary`: #8b5cf6 (violeta)
- `--accent-secondary`: #06b6d4 (cyan)
- `--accent-gradient`: linear-gradient(135deg, #8b5cf6, #06b6d4)
- `--text-primary`: #f0f0f5
- `--text-secondary`: rgba(240,240,245,0.5)
- `--glass-blur`: blur(20px)
- `--glass-border`: rgba(255,255,255,0.08)

**Princípios:**
- Zero cantos retos — mínimo border-radius: 16px, cards 24px, botões 12px
- Tudo flutua — box-shadow com glow suave violeta/cyan
- Gradientes animados no background (slow orbit, 20s cycle)
- Cover art como hero element — grande, com blur backdrop
- Navegação: orbs flutuantes no fundo do ecrã (dock-style, não sidebar)
- Player bar: glass panel flutuante no fundo
- Transições: spring animations (framer motion)
- Tipografia: Inter (clean, moderna)

---

### Task 1: Scaffold React + Vite + Tailwind

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.jsx`
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/index.css`

**Step 1: Init Vite React project**

```bash
cd /Users/deejaydago/Documents/CLAUDECODEHOUSE/PROJECTOS/music-tools/SONGER
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install -D tailwindcss @tailwindcss/vite
npm install framer-motion react-icons
```

**Step 2: Configure Vite proxy to Flask backend**

`frontend/vite.config.js`:
```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8888',
      '/stream': 'http://127.0.0.1:8888',
      '/setup': 'http://127.0.0.1:8888',
      '/callback': 'http://127.0.0.1:8888',
      '/disconnect': 'http://127.0.0.1:8888',
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  }
})
```

**Step 3: Setup Tailwind with Liquid design tokens**

`frontend/src/index.css`:
```css
@import "tailwindcss";

@theme {
  --color-deep: #0a0a0f;
  --color-surface: rgba(255, 255, 255, 0.04);
  --color-surface-hover: rgba(255, 255, 255, 0.08);
  --color-violet: #8b5cf6;
  --color-cyan: #06b6d4;
  --color-text: #f0f0f5;
  --color-text-muted: rgba(240, 240, 245, 0.5);
  --color-glass-border: rgba(255, 255, 255, 0.08);
  --font-sans: 'Inter', system-ui, sans-serif;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background: var(--color-deep);
  color: var(--color-text);
  font-family: var(--font-sans);
  overflow: hidden;
  height: 100vh;
}

/* Animated gradient background */
.liquid-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  overflow: hidden;
}

.liquid-bg::before,
.liquid-bg::after {
  content: '';
  position: absolute;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  filter: blur(120px);
  opacity: 0.15;
  animation: float 20s ease-in-out infinite;
}

.liquid-bg::before {
  background: var(--color-violet);
  top: -200px;
  left: -100px;
}

.liquid-bg::after {
  background: var(--color-cyan);
  bottom: -200px;
  right: -100px;
  animation-delay: -10s;
  animation-direction: reverse;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(100px, 50px) scale(1.1); }
  50% { transform: translate(-50px, 100px) scale(0.9); }
  75% { transform: translate(80px, -30px) scale(1.05); }
}

/* Glass panel base */
.glass {
  background: var(--color-surface);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--color-glass-border);
  border-radius: 24px;
}

.glass-sm {
  background: var(--color-surface);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--color-glass-border);
  border-radius: 16px;
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}
```

**Step 4: Verify dev server runs**

```bash
cd frontend && npm run dev
```
Expected: Vite dev server on localhost:5173

**Step 5: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): scaffold React + Vite + Tailwind with Liquid design tokens"
```

---

### Task 2: Layout Shell + Animated Background + Navigation Dock

**Files:**
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/components/LiquidBackground.jsx`
- Create: `frontend/src/components/NavDock.jsx`
- Create: `frontend/src/components/PlayerBar.jsx`

**Step 1: Build LiquidBackground component**

`frontend/src/components/LiquidBackground.jsx`:
```jsx
import { motion } from 'framer-motion'

export default function LiquidBackground() {
  return (
    <div className="liquid-bg" aria-hidden>
      <motion.div
        className="absolute w-[500px] h-[500px] rounded-full opacity-10"
        style={{
          background: 'radial-gradient(circle, var(--color-violet), transparent 70%)',
          filter: 'blur(80px)',
        }}
        animate={{
          x: [0, 120, -60, 80, 0],
          y: [0, 60, 120, -40, 0],
          scale: [1, 1.15, 0.9, 1.08, 1],
        }}
        transition={{ duration: 25, repeat: Infinity, ease: 'easeInOut' }}
      />
      <motion.div
        className="absolute right-0 bottom-0 w-[400px] h-[400px] rounded-full opacity-10"
        style={{
          background: 'radial-gradient(circle, var(--color-cyan), transparent 70%)',
          filter: 'blur(80px)',
        }}
        animate={{
          x: [0, -80, 50, -30, 0],
          y: [0, -50, -100, 40, 0],
          scale: [1, 0.9, 1.1, 0.95, 1],
        }}
        transition={{ duration: 20, repeat: Infinity, ease: 'easeInOut' }}
      />
    </div>
  )
}
```

**Step 2: Build NavDock — floating orbs at bottom**

`frontend/src/components/NavDock.jsx`:
```jsx
import { motion } from 'framer-motion'
import { IoHome, IoSearch, IoCloudDownload, IoMusicalNotes, IoTime } from 'react-icons/io5'

const NAV_ITEMS = [
  { id: 'home', icon: IoHome, label: 'Home' },
  { id: 'search', icon: IoSearch, label: 'Search' },
  { id: 'queue', icon: IoCloudDownload, label: 'Queue' },
  { id: 'library', icon: IoMusicalNotes, label: 'Library' },
  { id: 'history', icon: IoTime, label: 'History' },
]

export default function NavDock({ active, onNavigate }) {
  return (
    <motion.nav
      initial={{ y: 100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 200, damping: 25 }}
      className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50"
    >
      <div className="glass flex items-center gap-2 px-3 py-2">
        {NAV_ITEMS.map(({ id, icon: Icon, label }) => {
          const isActive = active === id
          return (
            <motion.button
              key={id}
              onClick={() => onNavigate(id)}
              whileHover={{ scale: 1.15 }}
              whileTap={{ scale: 0.9 }}
              className={`relative flex flex-col items-center gap-1 px-4 py-2 rounded-2xl transition-colors ${
                isActive ? 'text-violet' : 'text-text-muted hover:text-text'
              }`}
            >
              {isActive && (
                <motion.div
                  layoutId="nav-glow"
                  className="absolute inset-0 rounded-2xl"
                  style={{
                    background: 'linear-gradient(135deg, rgba(139,92,246,0.2), rgba(6,182,212,0.2))',
                    boxShadow: '0 0 20px rgba(139,92,246,0.3)',
                  }}
                  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                />
              )}
              <Icon size={22} className="relative z-10" />
              <span className="relative z-10 text-[10px] font-medium">{label}</span>
            </motion.button>
          )
        })}
      </div>
    </motion.nav>
  )
}
```

**Step 3: Build App shell with routing**

`frontend/src/App.jsx`:
```jsx
import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import LiquidBackground from './components/LiquidBackground'
import NavDock from './components/NavDock'
import HomeView from './views/HomeView'
import SearchView from './views/SearchView'
import QueueView from './views/QueueView'
import LibraryView from './views/LibraryView'
import HistoryView from './views/HistoryView'

const VIEWS = {
  home: HomeView,
  search: SearchView,
  queue: QueueView,
  library: LibraryView,
  history: HistoryView,
}

const pageTransition = {
  initial: { opacity: 0, y: 20, scale: 0.98 },
  animate: { opacity: 1, y: 0, scale: 1 },
  exit: { opacity: 0, y: -20, scale: 0.98 },
  transition: { type: 'spring', stiffness: 300, damping: 30 },
}

export default function App() {
  const [view, setView] = useState('home')
  const View = VIEWS[view]

  return (
    <div className="h-screen w-screen overflow-hidden relative">
      <LiquidBackground />
      <main className="relative z-10 h-full overflow-y-auto pb-28 pt-6 px-6">
        <AnimatePresence mode="wait">
          <motion.div key={view} {...pageTransition}>
            <View onNavigate={setView} />
          </motion.div>
        </AnimatePresence>
      </main>
      <NavDock active={view} onNavigate={setView} />
    </div>
  )
}
```

**Step 4: Create placeholder views**

Create `frontend/src/views/HomeView.jsx`, `SearchView.jsx`, `QueueView.jsx`, `LibraryView.jsx`, `HistoryView.jsx` — all with placeholder glass panels showing the view name.

**Step 5: Verify layout renders correctly**

```bash
cd frontend && npm run dev
```
Expected: Dark background with floating violet/cyan blobs, glass nav dock at bottom with 5 orbs, page transitions working.

**Step 6: Commit**

```bash
git add frontend/src/
git commit -m "feat(frontend): liquid layout shell with animated bg, nav dock, page transitions"
```

---

### Task 3: API Layer + Hooks

**Files:**
- Create: `frontend/src/lib/api.js`
- Create: `frontend/src/hooks/useSpotifyStatus.js`
- Create: `frontend/src/hooks/useDownloadQueue.js`
- Create: `frontend/src/hooks/useSSE.js`

**Step 1: API client**

`frontend/src/lib/api.js`:
```js
const BASE = ''  // proxy handles /api → Flask

async function get(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

async function del(path) {
  const res = await fetch(`${BASE}${path}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export const api = {
  // Status
  status: () => get('/api/status'),
  stats: () => get('/api/stats'),
  config: () => get('/api/config'),

  // Search
  search: (q) => get(`/api/search?q=${encodeURIComponent(q)}`),
  artist: (id) => get(`/api/artist/${id}`),
  album: (id) => get(`/api/album/${id}`),

  // Playlists
  playlists: () => get('/api/playlists'),
  playlistTracks: (id) => get(`/api/playlists/${id}/tracks`),

  // Liked songs
  likedSongs: (offset = 0, limit = 50) => get(`/api/liked-songs?offset=${offset}&limit=${limit}`),

  // Download
  download: (tracks, format, source) => post('/api/download', { tracks, format, source }),
  queue: () => get('/api/queue'),
  cancelJob: (id) => del(`/api/queue/${id}`),
  cancelAll: () => del('/api/queue'),
  downloadedIds: () => get('/api/downloaded-ids'),

  // Library
  library: () => get('/api/library'),

  // History
  history: () => get('/api/history'),
  clearHistory: () => del('/api/history'),

  // Trending
  trending: () => get('/api/trending'),

  // Cover art proxy
  coverUrl: (url) => `/api/cover?url=${encodeURIComponent(url)}`,

  // Audio stream
  streamUrl: (path) => `/stream/${encodeURIComponent(path)}`,
}
```

**Step 2: SSE hook for real-time download updates**

`frontend/src/hooks/useSSE.js`:
```js
import { useEffect, useRef } from 'react'

export function useSSE(onEvent) {
  const cbRef = useRef(onEvent)
  cbRef.current = onEvent

  useEffect(() => {
    const source = new EventSource('/api/events')
    source.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        cbRef.current(data)
      } catch {}
    }
    return () => source.close()
  }, [])
}
```

**Step 3: Status and queue hooks**

`frontend/src/hooks/useSpotifyStatus.js`:
```js
import { useState, useEffect } from 'react'
import { api } from '../lib/api'

export function useSpotifyStatus() {
  const [status, setStatus] = useState({ spotify: false, soulseek: false })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.status().then(setStatus).catch(() => {}).finally(() => setLoading(false))
  }, [])

  return { ...status, loading }
}
```

`frontend/src/hooks/useDownloadQueue.js`:
```js
import { useState, useEffect, useCallback } from 'react'
import { api } from '../lib/api'
import { useSSE } from './useSSE'

export function useDownloadQueue() {
  const [jobs, setJobs] = useState([])

  const refresh = useCallback(() => {
    api.queue().then(data => setJobs(data.queue || []))
  }, [])

  useEffect(() => { refresh() }, [refresh])

  useSSE((event) => {
    if (event.type === 'progress' || event.type === 'done' || event.type === 'error') {
      refresh()
    }
  })

  return { jobs, refresh }
}
```

**Step 4: Commit**

```bash
git add frontend/src/lib/ frontend/src/hooks/
git commit -m "feat(frontend): API client + SSE/status/queue hooks"
```

---

### Task 4: Home View — Dashboard

**Files:**
- Create: `frontend/src/views/HomeView.jsx`
- Create: `frontend/src/components/StatCard.jsx`
- Create: `frontend/src/components/GlassCard.jsx`

**Step 1: GlassCard reusable component**

`frontend/src/components/GlassCard.jsx`:
```jsx
import { motion } from 'framer-motion'

export default function GlassCard({ children, className = '', onClick, hover = true }) {
  return (
    <motion.div
      whileHover={hover ? { scale: 1.02, y: -2 } : {}}
      whileTap={onClick ? { scale: 0.98 } : {}}
      onClick={onClick}
      className={`glass p-5 cursor-${onClick ? 'pointer' : 'default'} ${className}`}
      style={{
        boxShadow: '0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05)',
      }}
    >
      {children}
    </motion.div>
  )
}
```

**Step 2: Home view with stats, quick actions, recent downloads**

`frontend/src/views/HomeView.jsx`:
```jsx
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { IoSearch, IoMusicalNotes, IoCloudDownload, IoSparkles } from 'react-icons/io5'
import GlassCard from '../components/GlassCard'
import { api } from '../lib/api'

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08 } },
}
const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
}

export default function HomeView({ onNavigate }) {
  const [stats, setStats] = useState(null)
  const [history, setHistory] = useState([])

  useEffect(() => {
    api.stats().then(setStats).catch(() => {})
    api.history().then(data => setHistory((data.history || []).slice(0, 6))).catch(() => {})
  }, [])

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <motion.div variants={item}>
        <h1 className="text-4xl font-bold bg-gradient-to-r from-violet to-cyan bg-clip-text text-transparent">
          SONGER
        </h1>
        <p className="text-text-muted mt-1">What are we downloading today?</p>
      </motion.div>

      {/* Quick Actions */}
      <motion.div variants={item} className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { icon: IoSearch, label: 'Search', view: 'search', gradient: 'from-violet/20 to-violet/5' },
          { icon: IoCloudDownload, label: 'Queue', view: 'queue', gradient: 'from-cyan/20 to-cyan/5' },
          { icon: IoMusicalNotes, label: 'Library', view: 'library', gradient: 'from-violet/20 to-cyan/5' },
          { icon: IoSparkles, label: 'Trending', view: 'search', gradient: 'from-cyan/20 to-violet/5' },
        ].map(({ icon: Icon, label, view, gradient }) => (
          <GlassCard key={label} onClick={() => onNavigate(view)}>
            <div className={`bg-gradient-to-br ${gradient} rounded-2xl p-4 mb-3 w-fit`}>
              <Icon size={24} className="text-text" />
            </div>
            <span className="font-semibold">{label}</span>
          </GlassCard>
        ))}
      </motion.div>

      {/* Stats */}
      {stats && (
        <motion.div variants={item} className="grid grid-cols-3 gap-4">
          {[
            { label: 'Tracks', value: stats.total_tracks || 0 },
            { label: 'Artists', value: stats.total_artists || 0 },
            { label: 'Storage', value: stats.storage || '0 MB' },
          ].map(({ label, value }) => (
            <GlassCard key={label} hover={false}>
              <div className="text-2xl font-bold bg-gradient-to-r from-violet to-cyan bg-clip-text text-transparent">
                {value}
              </div>
              <div className="text-text-muted text-sm mt-1">{label}</div>
            </GlassCard>
          ))}
        </motion.div>
      )}

      {/* Recent Downloads */}
      {history.length > 0 && (
        <motion.div variants={item}>
          <h2 className="text-lg font-semibold mb-4">Recent</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {history.map((h, i) => (
              <GlassCard key={i} hover={true} className="!p-3">
                <div className="flex items-center gap-3">
                  {h.cover && (
                    <img
                      src={api.coverUrl(h.cover)}
                      alt=""
                      className="w-10 h-10 rounded-xl object-cover"
                    />
                  )}
                  <div className="min-w-0">
                    <div className="text-sm font-medium truncate">{h.name}</div>
                    <div className="text-xs text-text-muted">{h.tracks_count} tracks</div>
                  </div>
                </div>
              </GlassCard>
            ))}
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}
```

**Step 3: Commit**

```bash
git add frontend/src/views/HomeView.jsx frontend/src/components/
git commit -m "feat(frontend): home view with stats, quick actions, recent downloads"
```

---

### Task 5: Search View

**Files:**
- Create: `frontend/src/views/SearchView.jsx`
- Create: `frontend/src/components/TrackRow.jsx`
- Create: `frontend/src/components/DownloadButton.jsx`

**Step 1: TrackRow component — liquid style track display**

`frontend/src/components/TrackRow.jsx`:
```jsx
import { motion } from 'framer-motion'
import { api } from '../lib/api'
import DownloadButton from './DownloadButton'

export default function TrackRow({ track, index, onDownload, isDownloaded }) {
  const cover = track.album?.images?.[0]?.url || track.cover

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.03 }}
      className="group flex items-center gap-4 p-3 rounded-2xl hover:bg-surface-hover transition-all"
    >
      {cover && (
        <img
          src={api.coverUrl(cover)}
          alt=""
          className="w-12 h-12 rounded-xl object-cover shadow-lg"
        />
      )}
      <div className="flex-1 min-w-0">
        <div className="font-medium truncate">{track.name}</div>
        <div className="text-sm text-text-muted truncate">
          {track.artists?.map(a => a.name).join(', ') || track.artist}
        </div>
      </div>
      <div className="text-xs text-text-muted">
        {track.duration_ms ? `${Math.floor(track.duration_ms / 60000)}:${String(Math.floor((track.duration_ms % 60000) / 1000)).padStart(2, '0')}` : ''}
      </div>
      <DownloadButton
        track={track}
        onDownload={onDownload}
        isDownloaded={isDownloaded}
      />
    </motion.div>
  )
}
```

**Step 2: DownloadButton with liquid animation**

`frontend/src/components/DownloadButton.jsx`:
```jsx
import { useState } from 'react'
import { motion } from 'framer-motion'
import { IoCloudDownload, IoCheckmarkCircle } from 'react-icons/io5'

export default function DownloadButton({ track, onDownload, isDownloaded }) {
  const [loading, setLoading] = useState(false)

  if (isDownloaded) {
    return <IoCheckmarkCircle size={20} className="text-cyan" />
  }

  return (
    <motion.button
      whileHover={{ scale: 1.2 }}
      whileTap={{ scale: 0.8 }}
      disabled={loading}
      onClick={async () => {
        setLoading(true)
        await onDownload(track)
        setLoading(false)
      }}
      className="text-text-muted hover:text-violet transition-colors opacity-0 group-hover:opacity-100"
    >
      {loading ? (
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        >
          <IoCloudDownload size={20} />
        </motion.div>
      ) : (
        <IoCloudDownload size={20} />
      )}
    </motion.button>
  )
}
```

**Step 3: Search view with live search + results**

`frontend/src/views/SearchView.jsx`:
```jsx
import { useState, useCallback, useRef } from 'react'
import { motion } from 'framer-motion'
import { IoSearch } from 'react-icons/io5'
import TrackRow from '../components/TrackRow'
import GlassCard from '../components/GlassCard'
import { api } from '../lib/api'

export default function SearchView() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [downloadedIds, setDownloadedIds] = useState(new Set())
  const timerRef = useRef(null)

  const doSearch = useCallback(async (q) => {
    if (!q.trim()) { setResults(null); return }
    setLoading(true)
    try {
      const [data, dlIds] = await Promise.all([
        api.search(q),
        api.downloadedIds(),
      ])
      setResults(data)
      setDownloadedIds(new Set(dlIds.ids || []))
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }, [])

  const handleInput = (e) => {
    const val = e.target.value
    setQuery(val)
    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => doSearch(val), 400)
  }

  const handleDownload = async (track) => {
    try {
      await api.download([track], 'mp3_320', 'hybrid')
    } catch (e) {
      console.error(e)
    }
  }

  const tracks = results?.tracks?.items || results?.tracks || []
  const albums = results?.albums?.items || []
  const artists = results?.artists?.items || []

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Search input */}
      <div className="glass flex items-center gap-3 px-5 py-4">
        <IoSearch size={20} className="text-text-muted" />
        <input
          type="text"
          value={query}
          onChange={handleInput}
          placeholder="Song, artist, album, or Spotify URL..."
          autoFocus
          className="flex-1 bg-transparent outline-none text-text placeholder:text-text-muted"
        />
        {loading && (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            className="w-5 h-5 border-2 border-violet border-t-transparent rounded-full"
          />
        )}
      </div>

      {/* Tracks */}
      {tracks.length > 0 && (
        <GlassCard hover={false} className="!p-2">
          <h3 className="text-sm font-semibold text-text-muted px-3 py-2">Tracks</h3>
          {tracks.map((track, i) => (
            <TrackRow
              key={track.id || i}
              track={track}
              index={i}
              onDownload={handleDownload}
              isDownloaded={downloadedIds.has(track.id)}
            />
          ))}
        </GlassCard>
      )}

      {/* Albums */}
      {albums.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-text-muted mb-3">Albums</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {albums.map((album) => (
              <GlassCard key={album.id} className="!p-3">
                {album.images?.[0] && (
                  <img
                    src={api.coverUrl(album.images[0].url)}
                    alt=""
                    className="w-full aspect-square rounded-2xl object-cover mb-3"
                  />
                )}
                <div className="text-sm font-medium truncate">{album.name}</div>
                <div className="text-xs text-text-muted truncate">
                  {album.artists?.map(a => a.name).join(', ')}
                </div>
              </GlassCard>
            ))}
          </div>
        </div>
      )}

      {/* No results */}
      {results && tracks.length === 0 && albums.length === 0 && (
        <div className="text-center text-text-muted py-12">No results found</div>
      )}
    </div>
  )
}
```

**Step 4: Commit**

```bash
git add frontend/src/views/SearchView.jsx frontend/src/components/TrackRow.jsx frontend/src/components/DownloadButton.jsx
git commit -m "feat(frontend): search view with live search, track rows, download buttons"
```

---

### Task 6: Queue View (real-time downloads)

**Files:**
- Create: `frontend/src/views/QueueView.jsx`

**Step 1: Queue view with SSE progress**

`frontend/src/views/QueueView.jsx`:
```jsx
import { motion } from 'framer-motion'
import { IoClose, IoTrash, IoCheckmarkCircle, IoAlertCircle } from 'react-icons/io5'
import GlassCard from '../components/GlassCard'
import { useDownloadQueue } from '../hooks/useDownloadQueue'
import { api } from '../lib/api'

export default function QueueView() {
  const { jobs, refresh } = useDownloadQueue()

  const active = jobs.filter(j => j.status === 'downloading' || j.status === 'pending')
  const done = jobs.filter(j => j.status === 'done')
  const failed = jobs.filter(j => j.status === 'error')

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Queue</h1>
        {jobs.length > 0 && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={async () => { await api.cancelAll(); refresh() }}
            className="glass-sm px-4 py-2 text-sm text-text-muted hover:text-red-400 transition-colors"
          >
            <IoTrash className="inline mr-1" /> Clear all
          </motion.button>
        )}
      </div>

      {/* Active downloads */}
      {active.length > 0 && (
        <GlassCard hover={false} className="!p-3 space-y-1">
          <h3 className="text-sm font-semibold text-text-muted px-2 pb-2">Downloading</h3>
          {active.map((job) => (
            <div key={job.id} className="flex items-center gap-3 p-3 rounded-2xl hover:bg-surface-hover">
              {job.cover && (
                <img src={api.coverUrl(job.cover)} alt="" className="w-10 h-10 rounded-xl object-cover" />
              )}
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{job.name}</div>
                <div className="text-xs text-text-muted truncate">{job.artist}</div>
                {/* Progress bar */}
                <div className="mt-2 h-1 rounded-full bg-surface overflow-hidden">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ background: 'linear-gradient(90deg, var(--color-violet), var(--color-cyan))' }}
                    initial={{ width: 0 }}
                    animate={{ width: `${job.progress || 0}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
              </div>
              <motion.button
                whileHover={{ scale: 1.2 }}
                whileTap={{ scale: 0.8 }}
                onClick={async () => { await api.cancelJob(job.id); refresh() }}
                className="text-text-muted hover:text-red-400"
              >
                <IoClose size={18} />
              </motion.button>
            </div>
          ))}
        </GlassCard>
      )}

      {/* Completed */}
      {done.length > 0 && (
        <GlassCard hover={false} className="!p-3 space-y-1">
          <h3 className="text-sm font-semibold text-text-muted px-2 pb-2">Completed</h3>
          {done.map((job) => (
            <div key={job.id} className="flex items-center gap-3 p-3 rounded-2xl">
              {job.cover && (
                <img src={api.coverUrl(job.cover)} alt="" className="w-10 h-10 rounded-xl object-cover" />
              )}
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{job.name}</div>
                <div className="text-xs text-text-muted truncate">{job.artist}</div>
              </div>
              <IoCheckmarkCircle size={18} className="text-cyan" />
            </div>
          ))}
        </GlassCard>
      )}

      {/* Failed */}
      {failed.length > 0 && (
        <GlassCard hover={false} className="!p-3 space-y-1">
          <h3 className="text-sm font-semibold text-text-muted px-2 pb-2">Failed</h3>
          {failed.map((job) => (
            <div key={job.id} className="flex items-center gap-3 p-3 rounded-2xl">
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{job.name}</div>
                <div className="text-xs text-red-400 truncate">{job.error}</div>
              </div>
              <IoAlertCircle size={18} className="text-red-400" />
            </div>
          ))}
        </GlassCard>
      )}

      {/* Empty state */}
      {jobs.length === 0 && (
        <div className="text-center text-text-muted py-16">
          <IoCloudDownload size={48} className="mx-auto mb-4 opacity-30" />
          <p>No downloads in queue</p>
        </div>
      )}
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add frontend/src/views/QueueView.jsx
git commit -m "feat(frontend): queue view with real-time progress bars and SSE"
```

---

### Task 7: Library View

**Files:**
- Create: `frontend/src/views/LibraryView.jsx`

**Step 1: Library view with search/filter**

`frontend/src/views/LibraryView.jsx`:
```jsx
import { useState, useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'
import { IoMusicalNotes, IoSearch, IoFolder } from 'react-icons/io5'
import GlassCard from '../components/GlassCard'
import { api } from '../lib/api'

export default function LibraryView() {
  const [library, setLibrary] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    api.library()
      .then(data => setLibrary(data.tracks || data.library || []))
      .finally(() => setLoading(false))
  }, [])

  const filtered = useMemo(() => {
    if (!filter) return library
    const q = filter.toLowerCase()
    return library.filter(t =>
      t.name?.toLowerCase().includes(q) ||
      t.artist?.toLowerCase().includes(q) ||
      t.album?.toLowerCase().includes(q)
    )
  }, [library, filter])

  // Group by artist
  const grouped = useMemo(() => {
    const map = {}
    filtered.forEach(t => {
      const key = t.artist || 'Unknown'
      if (!map[key]) map[key] = []
      map[key].push(t)
    })
    return Object.entries(map).sort(([a], [b]) => a.localeCompare(b))
  }, [filtered])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
          className="w-8 h-8 border-2 border-violet border-t-transparent rounded-full"
        />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Library</h1>
        <span className="text-text-muted text-sm">{library.length} tracks</span>
      </div>

      {/* Filter */}
      <div className="glass-sm flex items-center gap-3 px-4 py-3">
        <IoSearch size={16} className="text-text-muted" />
        <input
          type="text"
          value={filter}
          onChange={e => setFilter(e.target.value)}
          placeholder="Filter library..."
          className="flex-1 bg-transparent outline-none text-sm text-text placeholder:text-text-muted"
        />
      </div>

      {/* Artists */}
      {grouped.map(([artist, tracks], i) => (
        <motion.div
          key={artist}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.02 }}
        >
          <GlassCard hover={false} className="!p-3">
            <div className="flex items-center gap-2 px-2 pb-2">
              <IoFolder size={14} className="text-violet" />
              <h3 className="text-sm font-semibold">{artist}</h3>
              <span className="text-xs text-text-muted">{tracks.length}</span>
            </div>
            {tracks.map((track, j) => (
              <div key={j} className="flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-surface-hover transition-colors">
                <IoMusicalNotes size={14} className="text-text-muted" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm truncate">{track.name}</div>
                  {track.album && <div className="text-xs text-text-muted truncate">{track.album}</div>}
                </div>
                {track.size_mb && (
                  <span className="text-xs text-text-muted">{track.size_mb} MB</span>
                )}
              </div>
            ))}
          </GlassCard>
        </motion.div>
      ))}

      {library.length === 0 && (
        <div className="text-center text-text-muted py-16">
          <IoMusicalNotes size={48} className="mx-auto mb-4 opacity-30" />
          <p>Library is empty — download some tracks first</p>
        </div>
      )}
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add frontend/src/views/LibraryView.jsx
git commit -m "feat(frontend): library view with artist grouping and filter"
```

---

### Task 8: History View

**Files:**
- Create: `frontend/src/views/HistoryView.jsx`

**Step 1: History view**

`frontend/src/views/HistoryView.jsx`:
```jsx
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { IoTime, IoTrash, IoMusicalNotes } from 'react-icons/io5'
import GlassCard from '../components/GlassCard'
import { api } from '../lib/api'

export default function HistoryView() {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    api.history()
      .then(data => setHistory(data.history || []))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">History</h1>
        {history.length > 0 && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={async () => { await api.clearHistory(); load() }}
            className="glass-sm px-4 py-2 text-sm text-text-muted hover:text-red-400 transition-colors"
          >
            <IoTrash className="inline mr-1" /> Clear
          </motion.button>
        )}
      </div>

      <GlassCard hover={false} className="!p-3 space-y-1">
        {history.map((h, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.03 }}
            className="flex items-center gap-3 p-3 rounded-2xl hover:bg-surface-hover transition-colors"
          >
            {h.cover ? (
              <img src={api.coverUrl(h.cover)} alt="" className="w-10 h-10 rounded-xl object-cover" />
            ) : (
              <div className="w-10 h-10 rounded-xl bg-surface flex items-center justify-center">
                <IoMusicalNotes size={16} className="text-text-muted" />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium truncate">{h.name}</div>
              <div className="text-xs text-text-muted">
                {h.done_count}/{h.tracks_count} tracks · {h.format} · {h.date}
              </div>
            </div>
            {h.fail_count > 0 && (
              <span className="text-xs text-red-400">{h.fail_count} failed</span>
            )}
          </motion.div>
        ))}
      </GlassCard>

      {!loading && history.length === 0 && (
        <div className="text-center text-text-muted py-16">
          <IoTime size={48} className="mx-auto mb-4 opacity-30" />
          <p>No download history yet</p>
        </div>
      )}
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add frontend/src/views/HistoryView.jsx
git commit -m "feat(frontend): history view with clear functionality"
```

---

### Task 9: Flask serves React build + PyWebView launcher

**Files:**
- Modify: `server.py` — add route to serve React build
- Create: `songer.py` — single entry point: starts Flask + opens PyWebView

**Step 1: Add React static serving to server.py**

Add at the bottom of server.py, before `if __name__`:
```python
# Serve React frontend build
import os as _os
_FRONTEND_DIST = _os.path.join(_os.path.dirname(__file__), 'frontend', 'dist')

@app.route('/app')
@app.route('/app/<path:path>')
def serve_react_app(path=''):
    if path and _os.path.exists(_os.path.join(_FRONTEND_DIST, path)):
        return send_file(_os.path.join(_FRONTEND_DIST, path))
    return send_file(_os.path.join(_FRONTEND_DIST, 'index.html'))

# Serve static assets from React build
@app.route('/assets/<path:path>')
def serve_react_assets(path):
    return send_file(_os.path.join(_FRONTEND_DIST, 'assets', path))
```

**Step 2: Create unified launcher**

`songer.py`:
```python
#!/usr/bin/env python3
"""SONGER — Single entry point for macOS app.
Starts Flask backend + opens PyWebView native window.
"""
import threading
import sys
import os

# Ensure we're running from the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def start_flask():
    from server import app
    app.run(host='127.0.0.1', port=8888, debug=False, use_reloader=False)

if __name__ == '__main__':
    # Start Flask in background thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    # Give Flask a moment to start
    import time
    time.sleep(1)

    # Open native window with PyWebView
    try:
        import webview
        window = webview.create_window(
            'SONGER',
            'http://127.0.0.1:8888/app',
            width=1100,
            height=750,
            min_size=(900, 600),
            background_color='#0a0a0f',
            frameless=False,
        )
        webview.start()
    except ImportError:
        # Fallback: open in browser
        import webbrowser
        webbrowser.open('http://127.0.0.1:8888/app')
        print('SONGER running at http://127.0.0.1:8888/app')
        print('Press Ctrl+C to quit')
        try:
            flask_thread.join()
        except KeyboardInterrupt:
            pass
```

**Step 3: Update requirements**

Add to requirements.txt:
```
pywebview>=5.0.0
```

**Step 4: Build React and test**

```bash
cd frontend && npm run build
cd .. && python3 songer.py
```
Expected: Native Mac window opens with Liquid SONGER UI

**Step 5: Commit**

```bash
git add songer.py server.py requirements.txt
git commit -m "feat: unified launcher with Flask + PyWebView, serves React build"
```

---

### Task 10: PyInstaller Mac Build

**Files:**
- Modify: `songer_mac.spec` — update for new architecture
- Modify: `build_mac.sh` — update build script

**Step 1: Update spec file**

Replace `songer_mac.spec` to use `songer.py` entry point and bundle `frontend/dist/`:
```python
# PyInstaller spec — macOS (Liquid Redesign)
import os
block_cipher = None

a = Analysis(
    ['songer.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('frontend/dist', 'frontend/dist'),
        ('web', 'web'),
        ('assets/logo.png', 'assets') if os.path.exists('assets/logo.png') else ('.', '.'),
    ],
    hiddenimports=[
        'flask', 'webview',
        'spotipy', 'spotipy.oauth2',
        'mutagen', 'mutagen.id3', 'mutagen.flac', 'mutagen.mp3',
        'yt_dlp', 'imageio_ffmpeg', 'requests',
        'core.config', 'core.spotify', 'core.youtube',
        'core.soulseek', 'core.downloader', 'core.metadata',
        'core.matcher', 'core.library', 'core.history',
        'core.ffmpeg_manager', 'core.logger', 'core.app_state',
    ],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'PyQt6', 'winotify'],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='SONGER',
    debug=False,
    strip=False,
    upx=True,
    console=False,
    target_arch='arm64',
)

coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=True, name='SONGER')

app = BUNDLE(
    coll,
    name='SONGER.app',
    bundle_identifier='com.songer.app',
    info_plist={
        'NSHighResolutionCapable': True,
        'CFBundleShortVersionString': '2.0.0',
    },
)
```

**Step 2: Update build script**

```bash
#!/bin/bash
set -e
echo "=== SONGER 2.0 — Build macOS ==="

# Build React frontend
echo "→ Building frontend..."
cd frontend && npm run build && cd ..

# Build Mac app
echo "→ Building .app..."
python3 -m PyInstaller songer_mac.spec --clean --noconfirm

echo "=== Done: dist/SONGER.app ==="
echo "open dist/SONGER.app"
```

**Step 3: Commit**

```bash
git add songer_mac.spec build_mac.sh
git commit -m "feat: update mac build for Liquid redesign (PyWebView + React)"
```

---

## Summary of deliverables

| Task | What it builds |
|------|---------------|
| 1 | React + Vite + Tailwind scaffold with Liquid design tokens |
| 2 | App shell: animated background, nav dock, page transitions |
| 3 | API layer + SSE/status/queue hooks |
| 4 | Home view: stats, quick actions, recent downloads |
| 5 | Search view: live search, track rows, download buttons |
| 6 | Queue view: real-time progress bars with SSE |
| 7 | Library view: artist grouping, filter |
| 8 | History view: download history with clear |
| 9 | Flask serves React build + PyWebView launcher (songer.py) |
| 10 | PyInstaller Mac build updated |

**Total: 10 tasks, ~20 files, zero new backend code needed.**
