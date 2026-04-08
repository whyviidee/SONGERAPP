import { motion } from 'framer-motion'
import { IoHome, IoSearch, IoCloudDownload, IoLibrary, IoFlame, IoSettings, IoHelpCircle, IoLink } from 'react-icons/io5'
import { useDownloadQueue } from '../hooks/useDownloadQueue'

const NAV_ITEMS = [
  { id: 'home', icon: IoHome, label: 'Home' },
  { id: 'search', icon: IoSearch, label: 'Search' },
  { id: 'url_download', icon: IoLink, label: 'URL' },
  { id: 'queue', icon: IoCloudDownload, label: 'Downloads' },
  { id: 'library', icon: IoLibrary, label: 'My Music' },
  { id: 'trending', icon: IoFlame, label: 'Trending' },
  { id: 'faq', icon: IoHelpCircle, label: 'Help' },
  { id: 'settings', icon: IoSettings, label: 'Settings' },
]

export default function NavDock({ active, onNavigate }) {
  const { jobs } = useDownloadQueue()
  const activeCount = jobs.filter(j => j.status === 'downloading' || j.status === 'pending').length

  return (
    <motion.nav
      initial={{ y: 100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.2, delay: 0.1 }}
      style={{
        position: 'fixed',
        bottom: 20,
        left: 0,
        right: 0,
        display: 'flex',
        justifyContent: 'center',
        zIndex: 50,
        pointerEvents: 'none',
      }}
    >
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 4,
        padding: '10px 14px',
        pointerEvents: 'auto',
        background: 'rgba(255,255,255,0.06)',
        backdropFilter: 'blur(24px)',
        WebkitBackdropFilter: 'blur(24px)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 28,
        boxShadow: '0 8px 40px rgba(0,0,0,0.5), 0 0 60px rgba(139,92,246,0.08)',
      }}>
        {NAV_ITEMS.map(({ id, icon: Icon, label }) => {
          const isActive = active === id
          const showBadge = id === 'queue' && activeCount > 0
          return (
            <motion.button
              key={id}
              onClick={() => onNavigate(id)}
              whileHover={{ scale: 1.12 }}
              whileTap={{ scale: 0.9 }}
              style={{
                position: 'relative',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 4,
                padding: '8px 16px',
                borderRadius: 20,
                border: 'none',
                background: isActive ? 'linear-gradient(135deg, rgba(139,92,246,0.2), rgba(6,182,212,0.2))' : 'transparent',
                boxShadow: isActive ? '0 0 25px rgba(139,92,246,0.25)' : 'none',
                color: isActive ? '#8b5cf6' : 'rgba(240,240,245,0.4)',
                cursor: 'pointer',
                transition: 'color 0.2s',
              }}
            >
              <Icon size={20} />
              <span style={{ fontSize: 10, fontWeight: 500, letterSpacing: '0.5px' }}>{label}</span>
              {showBadge && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  style={{
                    position: 'absolute', top: 2, right: 8,
                    width: 16, height: 16, borderRadius: 8,
                    background: 'linear-gradient(135deg, #8b5cf6, #06b6d4)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 9, fontWeight: 700, color: '#fff',
                  }}>
                  {activeCount}
                </motion.div>
              )}
            </motion.button>
          )
        })}
      </div>
    </motion.nav>
  )
}
