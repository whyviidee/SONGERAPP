import { useState, useEffect, useCallback } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import LiquidBackground from './components/LiquidBackground'
import NavDock from './components/NavDock'
import MiniPlayer from './components/MiniPlayer'
import HomeView from './views/HomeView'
import SearchView from './views/SearchView'
import QueueView from './views/QueueView'
import LibraryView from './views/LibraryView'
import TrendingView from './views/TrendingView'
import SettingsView from './views/SettingsView'
import { api } from './lib/api'

const VIEWS = {
  home: HomeView,
  search: SearchView,
  queue: QueueView,
  library: LibraryView,
  trending: TrendingView,
  settings: SettingsView,
}

const pageTransition = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
  transition: { duration: 0.15, ease: 'easeOut' },
}

export default function App() {
  const [view, setView] = useState('home')
  const [downloadedIds, setDownloadedIds] = useState(new Set())
  const [playingTrack, setPlayingTrack] = useState(null)
  const View = VIEWS[view]

  const refreshDownloadedIds = useCallback(() => {
    api.downloadedIds().then((d) => setDownloadedIds(new Set(d.ids || []))).catch(() => {})
  }, [])

  useEffect(() => { refreshDownloadedIds() }, [refreshDownloadedIds])

  return (
    <div style={{ height: '100vh', width: '100vw', overflow: 'hidden', position: 'relative' }}>
      <LiquidBackground />
      <main style={{
        position: 'relative',
        zIndex: 10,
        height: '100%',
        overflowY: 'auto',
        paddingBottom: playingTrack ? 160 : 120,
        paddingTop: 32,
        paddingLeft: 32,
        paddingRight: 32,
      }}>
        <AnimatePresence mode="wait">
          <motion.div key={view} {...pageTransition}>
            <View
              onNavigate={setView}
              downloadedIds={downloadedIds}
              refreshDownloadedIds={refreshDownloadedIds}
              onPlay={setPlayingTrack}
            />
          </motion.div>
        </AnimatePresence>
      </main>
      <MiniPlayer track={playingTrack} onClose={() => setPlayingTrack(null)} />
      <NavDock active={view} onNavigate={setView} />
    </div>
  )
}
