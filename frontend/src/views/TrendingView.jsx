import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { IoFlame, IoRefresh, IoCloudDownload } from 'react-icons/io5'
import GlassCard from '../components/GlassCard'
import TrackRow from '../components/TrackRow'
import { api } from '../lib/api'

export default function TrendingView({ downloadedIds, refreshDownloadedIds }) {
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(null)
  const [expanded, setExpanded] = useState(null)

  useEffect(() => {
    api.trending()
      .then((data) => setCategories(data || []))
      .catch(() => {}).finally(() => setLoading(false))
  }, [])

  const handleRefresh = async (key) => {
    setRefreshing(key)
    try {
      const r = await api.trendingRefresh(key)
      if (r.ok) setCategories((prev) => prev.map((c) => (c.key === key ? { ...c, tracks: r.tracks } : c)))
    } catch (e) { console.error(e) }
    setRefreshing(null)
  }

  const handleDownload = async (track) => {
    try { await api.download(track); refreshDownloadedIds() } catch (e) { console.error(e) }
  }

  const handleDownloadAll = async (tracks) => {
    try { await api.download(tracks); refreshDownloadedIds() } catch (e) { console.error(e) }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 256 }}>
        <motion.div animate={{ rotate: 360 }} transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
          style={{ width: 32, height: 32, border: '2px solid #8b5cf6', borderTopColor: 'transparent', borderRadius: '50%' }} />
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: '#f0f0f5' }}>Trending</h1>
        <IoFlame size={24} style={{ color: '#8b5cf6' }} />
      </div>

      {categories.length === 0 && (
        <div style={{ textAlign: 'center', color: 'rgba(240,240,245,0.4)', paddingTop: 80 }}>
          <IoFlame size={48} style={{ opacity: 0.2, marginBottom: 16 }} />
          <p>No trending data available</p>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 16 }}>
        {categories.map((cat) => (
          <GlassCard key={cat.key} onClick={() => setExpanded(expanded === cat.key ? null : cat.key)} style={{ padding: 16, minWidth: 0, overflow: 'hidden' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <h3 style={{ fontWeight: 600, fontSize: 14, color: '#f0f0f5', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{cat.label}</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 12, color: 'rgba(240,240,245,0.4)' }}>{cat.tracks?.length || 0}</span>
                <motion.button whileHover={{ scale: 1.2 }} whileTap={{ scale: 0.8 }}
                  onClick={(e) => { e.stopPropagation(); handleRefresh(cat.key) }}
                  style={{ background: 'none', border: 'none', color: 'rgba(240,240,245,0.4)', cursor: 'pointer', padding: 2 }}>
                  <motion.div animate={refreshing === cat.key ? { rotate: 360 } : {}} transition={{ duration: 1, repeat: refreshing === cat.key ? Infinity : 0, ease: 'linear' }}>
                    <IoRefresh size={16} />
                  </motion.div>
                </motion.button>
              </div>
            </div>
            {cat.tracks?.slice(0, 3).map((t, i) => (
              <div key={i} style={{ fontSize: 12, color: 'rgba(240,240,245,0.5)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', padding: '2px 0' }}>
                {i + 1}. {t.artist} — {t.title}
              </div>
            ))}
            {(cat.tracks?.length || 0) > 3 && (
              <div style={{ fontSize: 12, color: '#8b5cf6', marginTop: 4 }}>+{cat.tracks.length - 3} more</div>
            )}
          </GlassCard>
        ))}
      </div>

      {expanded && (() => {
        const cat = categories.find((c) => c.key === expanded)
        if (!cat) return null
        return (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <GlassCard hover={false} style={{ padding: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '4px 12px 12px' }}>
                <h3 style={{ fontWeight: 600, color: '#f0f0f5' }}>{cat.label}</h3>
                <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                  onClick={() => handleDownloadAll(cat.tracks)}
                  style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, padding: '6px 12px', color: '#06b6d4', cursor: 'pointer', fontSize: 12, fontFamily: 'inherit', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <IoCloudDownload size={14} /> Download All
                </motion.button>
              </div>
              {cat.tracks?.map((track, i) => (
                <TrackRow key={i} track={{ name: track.title, artists: [{ name: track.artist }], id: track.url, ...track }} index={i} onDownload={handleDownload} isDownloaded={downloadedIds?.has(track.url)} />
              ))}
            </GlassCard>
          </motion.div>
        )
      })()}
    </div>
  )
}
