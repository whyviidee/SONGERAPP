import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { IoCloudDownload, IoArrowBack, IoDisc } from 'react-icons/io5'
import TrackRow from '../components/TrackRow'
import GlassCard from '../components/GlassCard'
import { api } from '../lib/api'

export default function AlbumView({ params = {}, onNavigate, downloadedIds, refreshDownloadedIds }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!params.id) return
    setLoading(true)
    setData(null)
    api.album(params.id)
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [params.id])

  const handleDownload = async (track) => {
    try { await api.download(track); refreshDownloadedIds() } catch (e) { console.error(e) }
  }

  const handleDownloadAll = async () => {
    if (!tracks.length) return
    try { await api.download(tracks); refreshDownloadedIds() } catch (e) { console.error(e) }
  }

  const goBack = () => onNavigate(params._backView || 'search', params._backParams || {})

  if (!params.id) return null

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 80 }}>
      <motion.div animate={{ rotate: 360 }} transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
        style={{ width: 36, height: 36, border: '2px solid #8b5cf6', borderTopColor: 'transparent', borderRadius: '50%' }} />
    </div>
  )

  if (error) return (
    <div style={{ textAlign: 'center', color: '#ef4444', paddingTop: 80 }}>{error}</div>
  )

  const album = data?.album || data
  const tracks = data?.tracks || []
  const cover = album?.images?.[0]?.url || album?.cover

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Back */}
      <motion.button whileTap={{ scale: 0.95 }} onClick={goBack}
        style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'none', border: 'none', color: 'rgba(240,240,245,0.4)', cursor: 'pointer', fontSize: 13, fontFamily: 'inherit', alignSelf: 'flex-start' }}>
        <IoArrowBack size={16} /> Back
      </motion.button>

      {/* Header */}
      <div style={{ display: 'flex', gap: 28, alignItems: 'flex-end' }}>
        {cover ? (
          <img src={api.coverUrl(cover)} alt=""
            style={{ width: 180, height: 180, borderRadius: 20, objectFit: 'cover', boxShadow: '0 16px 48px rgba(0,0,0,0.5)', flexShrink: 0 }} />
        ) : (
          <div style={{ width: 180, height: 180, borderRadius: 20, background: 'rgba(255,255,255,0.04)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <IoDisc size={48} style={{ color: 'rgba(240,240,245,0.2)' }} />
          </div>
        )}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1px', color: 'rgba(240,240,245,0.4)', marginBottom: 8 }}>Album</div>
          <h1 style={{ fontSize: 32, fontWeight: 800, color: '#f0f0f5', margin: 0, lineHeight: 1.1 }}>{album?.name}</h1>
          <p style={{ fontSize: 14, color: 'rgba(240,240,245,0.5)', margin: '10px 0 4px' }}>
            {album?.artists?.map(a => a.name).join(', ')}
            {album?.release_date && ` · ${album.release_date.split('-')[0]}`}
          </p>
          <p style={{ fontSize: 13, color: 'rgba(240,240,245,0.3)', margin: 0 }}>{tracks.length} tracks</p>
          {tracks.length > 0 && (
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={handleDownloadAll}
              style={{ marginTop: 16, background: 'linear-gradient(135deg, #8b5cf6, #06b6d4)', border: 'none', borderRadius: 14, padding: '10px 24px', color: '#fff', cursor: 'pointer', fontSize: 14, fontWeight: 600, fontFamily: 'inherit', display: 'flex', alignItems: 'center', gap: 8 }}>
              <IoCloudDownload size={16} /> Download All
            </motion.button>
          )}
        </div>
      </div>

      {/* Tracklist */}
      {tracks.length > 0 && (
        <GlassCard hover={false} style={{ padding: 8 }}>
          {tracks.map((track, i) => (
            <TrackRow key={track.id || i} track={track} index={i} onDownload={handleDownload} isDownloaded={downloadedIds?.has(track.id)} />
          ))}
        </GlassCard>
      )}
    </div>
  )
}
