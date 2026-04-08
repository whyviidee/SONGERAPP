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
import AlbumView from './views/AlbumView'
import ArtistView from './views/ArtistView'
import FaqView from './views/FaqView'
import UrlDownloadView from './views/UrlDownloadView'
import OnboardingView from './views/OnboardingView'
import { api } from './lib/api'

const VIEWS = {
  home: HomeView,
  search: SearchView,
  queue: QueueView,
  library: LibraryView,
  trending: TrendingView,
  settings: SettingsView,
  album: AlbumView,
  artist: ArtistView,
  faq: FaqView,
  url_download: UrlDownloadView,
}

const pageTransition = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
  transition: { duration: 0.15, ease: 'easeOut' },
}

export default function App() {
  const [nav, setNav] = useState({ id: 'home', params: {} })
  const [downloadedIds, setDownloadedIds] = useState(new Set())
  const [playingTrack, setPlayingTrack] = useState(null)
  const [showOnboarding, setShowOnboarding] = useState(null) // null=loading, true=show, false=skip
  const View = VIEWS[nav.id] || VIEWS.home

  const navigate = useCallback((id, params = {}) => setNav({ id, params }), [])

  const refreshDownloadedIds = useCallback(() => {
    api.downloadedIds().then((d) => setDownloadedIds(new Set(d.ids || []))).catch(() => {})
  }, [])

  useEffect(() => { refreshDownloadedIds() }, [refreshDownloadedIds])
  useEffect(() => { refreshDownloadedIds() }, [nav.id])

  // Check if onboarding is needed on startup
  useEffect(() => {
    fetch('/api/status')
      .then(r => r.json())
      .then(s => {
        const configured = s.spotify === 'ok' || s.tidal === 'ok'
        setShowOnboarding(!configured)
      })
      .catch(() => setShowOnboarding(false))
  }, [])

  if (showOnboarding === null) return null // loading

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
          <motion.div key={nav.id + JSON.stringify(nav.params)} {...pageTransition}>
            <View
              onNavigate={navigate}
              params={nav.params}
              downloadedIds={downloadedIds}
              refreshDownloadedIds={refreshDownloadedIds}
              onPlay={setPlayingTrack}
            />
          </motion.div>
        </AnimatePresence>
      </main>
      <MiniPlayer track={playingTrack} onClose={() => setPlayingTrack(null)} />
      <NavDock active={nav.id} onNavigate={navigate} />
      {showOnboarding && (
        <OnboardingView onComplete={() => setShowOnboarding(false)} />
      )}
    </div>
  )
}
