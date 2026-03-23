import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { IoSearch, IoMusicalNotes, IoCloudDownload, IoFlame, IoFolder, IoPlay, IoTrash } from 'react-icons/io5'
import GlassCard from '../components/GlassCard'
import { api } from '../lib/api'

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.04 } },
}
const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
}

const ACTIONS = [
  { icon: IoSearch, label: 'Search', desc: 'Find any song', view: 'search', color: '#8b5cf6' },
  { icon: IoCloudDownload, label: 'Downloads', desc: 'Queue & history', view: 'queue', color: '#06b6d4' },
  { icon: IoMusicalNotes, label: 'Library', desc: 'Songs, playlists, liked', view: 'library', color: '#a78bfa' },
  { icon: IoFlame, label: 'Trending', desc: 'Hot tracks now', view: 'trending', color: '#22d3ee' },
]

export default function HomeView({ onNavigate, onPlay }) {
  const [stats, setStats] = useState(null)
  const [history, setHistory] = useState([])
  const [library, setLibrary] = useState([])

  useEffect(() => {
    api.stats().then(setStats).catch(() => {})
    api.history().then((d) => setHistory((d.history || []).slice(0, 6))).catch(() => {})
    api.library().then((d) => setLibrary(d.tracks || d.library || d || [])).catch(() => {})
  }, [])

  return (
    <motion.div variants={container} initial="hidden" animate="show" style={{ maxWidth: 900, margin: '0 auto' }}>
      <motion.div variants={item} style={{ marginBottom: 40 }}>
        <h1 style={{
          fontSize: 56, fontWeight: 800, lineHeight: 1.1, margin: 0,
          background: 'linear-gradient(135deg, #8b5cf6, #06b6d4)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        }}>
          SONGER
        </h1>
        <p style={{ color: 'rgba(240,240,245,0.5)', marginTop: 10, fontSize: 18 }}>
          What are we downloading today?
        </p>
      </motion.div>

      <motion.div variants={item} style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 16, marginBottom: 36 }}>
        {ACTIONS.map(({ icon: Icon, label, desc, view, color }) => (
          <GlassCard key={label} onClick={() => onNavigate(view)}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ background: `${color}20`, borderRadius: 16, padding: 16, flexShrink: 0 }}>
                <Icon size={26} style={{ color }} />
              </div>
              <div>
                <div style={{ fontWeight: 600, color: '#f0f0f5', fontSize: 16 }}>{label}</div>
                <div style={{ fontSize: 13, color: 'rgba(240,240,245,0.4)', marginTop: 2 }}>{desc}</div>
              </div>
            </div>
          </GlassCard>
        ))}
      </motion.div>

      {stats && (
        <motion.div variants={item} style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 16, marginBottom: 36 }}>
          {[
            { label: 'Tracks', value: stats.tracks || stats.total_tracks || 0 },
            { label: 'Artists', value: stats.top_artists?.length || stats.total_artists || 0 },
            { label: 'Storage', value: stats.storage_mb != null ? (stats.storage_mb >= 1024 ? `${(stats.storage_mb / 1024).toFixed(1)} GB` : `${Math.round(stats.storage_mb)} MB`) : '0 MB' },
          ].map(({ label, value }) => (
            <GlassCard key={label} hover={false}>
              <div style={{
                fontSize: 32, fontWeight: 700,
                background: 'linear-gradient(135deg, #8b5cf6, #06b6d4)',
                WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
              }}>
                {value}
              </div>
              <div style={{ color: 'rgba(240,240,245,0.5)', fontSize: 13, marginTop: 4 }}>{label}</div>
            </GlassCard>
          ))}
        </motion.div>
      )}

      {/* Your Music (downloaded) */}
      {library.length > 0 && (
        <motion.div variants={item} style={{ marginBottom: 36 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
            <IoFolder size={20} style={{ color: '#8b5cf6' }} />
            <h2 style={{ fontSize: 18, fontWeight: 600, color: '#f0f0f5', margin: 0 }}>Your Music</h2>
            <span style={{ fontSize: 13, color: 'rgba(240,240,245,0.4)' }}>{library.length} tracks</span>
          </div>
          <GlassCard hover={false} style={{ padding: 8 }}>
            {library.slice(0, 10).map((track, i) => (
              <div key={i} className="group" style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '10px 12px', borderRadius: 14, transition: 'background 0.2s' }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.06)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
                <motion.button whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.85 }}
                  onClick={() => onPlay && onPlay(track)}
                  style={{ width: 44, height: 44, borderRadius: 12, flexShrink: 0, border: 'none', cursor: 'pointer', padding: 0, position: 'relative', overflow: 'hidden', background: 'linear-gradient(135deg, rgba(139,92,246,0.15), rgba(6,182,212,0.15))', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#a78bfa' }}>
                  {track.path && <img src={api.trackCoverUrl(track.path)} alt="" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', borderRadius: 12 }} onError={(e) => e.target.style.display = 'none'} />}
                  <IoPlay size={16} style={{ position: 'relative', zIndex: 1, filter: 'drop-shadow(0 1px 3px rgba(0,0,0,0.5))' }} />
                </motion.button>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 14, fontWeight: 500, color: '#f0f0f5', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{track.name}</div>
                  <div style={{ fontSize: 12, color: 'rgba(240,240,245,0.4)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{track.artist}{track.album ? ` · ${track.album}` : ''}</div>
                </div>
                {track.size_mb && <span style={{ fontSize: 11, color: 'rgba(240,240,245,0.4)' }}>{track.size_mb} MB</span>}
                <motion.button whileHover={{ scale: 1.15 }} whileTap={{ scale: 0.85 }}
                  onClick={async () => {
                    if (!confirm(`Delete "${track.name}"?`)) return
                    try {
                      await fetch('/api/delete-track', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path: track.path }) })
                      setLibrary(prev => prev.filter(t => t.path !== track.path))
                    } catch (e) { console.error(e) }
                  }}
                  style={{ background: 'none', border: 'none', color: 'rgba(240,240,245,0.2)', cursor: 'pointer', padding: 4, flexShrink: 0 }}
                  onMouseEnter={(e) => e.currentTarget.style.color = '#f87171'}
                  onMouseLeave={(e) => e.currentTarget.style.color = 'rgba(240,240,245,0.2)'}>
                  <IoTrash size={14} />
                </motion.button>
              </div>
            ))}
            {library.length > 10 && (
              <div style={{ textAlign: 'center', padding: '8px 0' }}>
                <motion.button whileTap={{ scale: 0.95 }} onClick={() => onNavigate('library')}
                  style={{ background: 'none', border: 'none', color: '#8b5cf6', cursor: 'pointer', fontSize: 13, fontFamily: 'inherit' }}>
                  View all {library.length} tracks →
                </motion.button>
              </div>
            )}
          </GlassCard>
        </motion.div>
      )}

      {history.length > 0 && (
        <motion.div variants={item}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: '#f0f0f5', marginBottom: 16 }}>Recent Downloads</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 12 }}>
            {history.map((h, i) => (
              <GlassCard key={i} style={{ padding: 14 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  {h.cover ? (
                    <img src={api.coverUrl(h.cover)} alt="" style={{ width: 40, height: 40, borderRadius: 10, objectFit: 'cover' }} />
                  ) : (
                    <div style={{ width: 40, height: 40, borderRadius: 10, background: 'rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <IoMusicalNotes size={16} style={{ color: 'rgba(240,240,245,0.3)' }} />
                    </div>
                  )}
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 500, color: '#f0f0f5', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{h.name}</div>
                    <div style={{ fontSize: 11, color: 'rgba(240,240,245,0.4)' }}>{h.tracks_count} tracks</div>
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
