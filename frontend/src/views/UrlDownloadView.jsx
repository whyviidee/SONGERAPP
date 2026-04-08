import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { IoLink, IoCloudDownload, IoMusicalNote, IoCheckmarkCircle, IoAlertCircle } from 'react-icons/io5'
import GlassCard from '../components/GlassCard'
import { api } from '../lib/api'

const PLATFORM_COLORS = {
  soundcloud: '#ff5500',
  bandcamp: '#1da0c3',
  mixcloud: '#52aad8',
  youtube: '#ff0000',
  web: '#8b5cf6',
}

const PLATFORM_LABELS = {
  soundcloud: 'SoundCloud',
  bandcamp: 'Bandcamp',
  mixcloud: 'Mixcloud',
  youtube: 'YouTube',
  web: 'Web',
}

function formatDuration(ms) {
  if (!ms) return ''
  const s = Math.floor(ms / 1000)
  const m = Math.floor(s / 60)
  const h = Math.floor(m / 60)
  if (h > 0) return `${h}:${String(m % 60).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
  return `${m}:${String(s % 60).padStart(2, '0')}`
}

export default function UrlDownloadView({ refreshDownloadedIds }) {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [track, setTrack] = useState(null)
  const [error, setError] = useState('')
  const [downloading, setDownloading] = useState(false)
  const [dlStatus, setDlStatus] = useState(null) // 'queued' | 'error'

  const fetchInfo = async () => {
    const trimmed = url.trim()
    if (!trimmed) return
    setLoading(true)
    setError('')
    setTrack(null)
    setDlStatus(null)
    try {
      const data = await api.urlInfo(trimmed)
      setTrack(data.track)
    } catch (e) {
      setError(e.message || 'Não foi possível extrair informação deste URL.')
    }
    setLoading(false)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') fetchInfo()
  }

  const handleDownload = async () => {
    if (!track) return
    setDownloading(true)
    setDlStatus(null)
    try {
      await api.downloadDirect(track)
      setDlStatus('queued')
      refreshDownloadedIds?.()
    } catch (e) {
      setDlStatus('error')
    }
    setDownloading(false)
  }

  const platform = track?.platform || 'web'
  const platformColor = PLATFORM_COLORS[platform] || PLATFORM_COLORS.web

  return (
    <div style={{ maxWidth: 700, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* Header */}
      <div>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: '#f0f0f5', margin: 0 }}>URL Directo</h1>
        <p style={{ color: 'rgba(240,240,245,0.45)', fontSize: 14, marginTop: 6 }}>
          Download de SoundCloud, Bandcamp, Mixcloud e qualquer site suportado.
        </p>
      </div>

      {/* URL Input */}
      <GlassCard style={{ padding: '18px 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <IoLink size={22} style={{ color: 'rgba(240,240,245,0.4)', flexShrink: 0 }} />
          <input
            type="url"
            value={url}
            onChange={e => { setUrl(e.target.value); setTrack(null); setError(''); setDlStatus(null) }}
            onKeyDown={handleKeyDown}
            placeholder="Cola aqui o URL  (ex: https://soundcloud.com/...)"
            autoFocus
            style={{
              flex: 1, background: 'none', border: 'none', outline: 'none',
              color: '#f0f0f5', fontSize: 16, fontFamily: 'inherit',
            }}
          />
          <motion.button
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.96 }}
            onClick={fetchInfo}
            disabled={loading || !url.trim()}
            style={{
              padding: '8px 20px', borderRadius: 20, border: 'none',
              background: 'linear-gradient(135deg, #8b5cf6, #06b6d4)',
              color: '#fff', fontWeight: 600, fontSize: 14, cursor: loading ? 'wait' : 'pointer',
              opacity: !url.trim() ? 0.4 : 1, flexShrink: 0,
            }}
          >
            {loading ? 'A pesquisar...' : 'Pesquisar'}
          </motion.button>
        </div>
      </GlassCard>

      {/* Spinner */}
      {loading && (
        <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 16 }}>
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            style={{ width: 28, height: 28, border: '3px solid #8b5cf6', borderTopColor: 'transparent', borderRadius: '50%' }}
          />
        </div>
      )}

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '14px 18px', borderRadius: 14,
              background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.25)', color: '#f87171', fontSize: 14 }}
          >
            <IoAlertCircle size={18} />
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Preview card */}
      <AnimatePresence>
        {track && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            <GlassCard style={{ padding: 20 }}>
              <div style={{ display: 'flex', gap: 18, alignItems: 'center' }}>

                {/* Cover */}
                <div style={{ position: 'relative', flexShrink: 0 }}>
                  {track.cover_url ? (
                    <img
                      src={track.cover_url}
                      alt="cover"
                      style={{ width: 88, height: 88, borderRadius: 10, objectFit: 'cover', display: 'block' }}
                    />
                  ) : (
                    <div style={{ width: 88, height: 88, borderRadius: 10, background: 'rgba(255,255,255,0.06)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <IoMusicalNote size={30} style={{ color: 'rgba(255,255,255,0.2)' }} />
                    </div>
                  )}
                  {/* Platform badge */}
                  <div style={{
                    position: 'absolute', bottom: -6, right: -6,
                    padding: '2px 7px', borderRadius: 8, fontSize: 10, fontWeight: 700,
                    background: platformColor, color: '#fff', letterSpacing: '0.3px',
                  }}>
                    {PLATFORM_LABELS[platform] || platform}
                  </div>
                </div>

                {/* Info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 18, fontWeight: 700, color: '#f0f0f5',
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {track.title}
                  </div>
                  <div style={{ fontSize: 14, color: 'rgba(240,240,245,0.55)', marginTop: 4 }}>
                    {track.artist}
                  </div>
                  <div style={{ fontSize: 12, color: 'rgba(240,240,245,0.3)', marginTop: 4, display: 'flex', gap: 8 }}>
                    {track.album && <span>{track.album}</span>}
                    {track.album && track.duration_ms && <span>·</span>}
                    {track.duration_ms > 0 && <span>{formatDuration(track.duration_ms)}</span>}
                  </div>
                </div>

                {/* Download button */}
                <div style={{ flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                  {dlStatus === 'queued' ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#4ade80', fontSize: 13, fontWeight: 600 }}>
                      <IoCheckmarkCircle size={20} /> Na fila
                    </div>
                  ) : (
                    <motion.button
                      whileHover={{ scale: 1.06 }}
                      whileTap={{ scale: 0.94 }}
                      onClick={handleDownload}
                      disabled={downloading}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 8,
                        padding: '10px 22px', borderRadius: 22, border: 'none',
                        background: 'linear-gradient(135deg, #8b5cf6, #06b6d4)',
                        color: '#fff', fontWeight: 600, fontSize: 14,
                        cursor: downloading ? 'wait' : 'pointer',
                        opacity: downloading ? 0.6 : 1,
                      }}
                    >
                      <IoCloudDownload size={18} />
                      {downloading ? 'A adicionar...' : 'Download'}
                    </motion.button>
                  )}
                  {dlStatus === 'error' && (
                    <span style={{ fontSize: 12, color: '#f87171' }}>Erro ao adicionar</span>
                  )}
                </div>
              </div>
            </GlassCard>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Hint */}
      {!track && !loading && !error && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginTop: 8 }}>
          {['SoundCloud', 'Bandcamp', 'Mixcloud', 'YouTube'].map(name => (
            <div key={name} style={{
              padding: '6px 14px', borderRadius: 20, fontSize: 12, fontWeight: 500,
              background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
              color: 'rgba(240,240,245,0.4)',
            }}>
              {name}
            </div>
          ))}
          <div style={{
            padding: '6px 14px', borderRadius: 20, fontSize: 12, fontWeight: 500,
            background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
            color: 'rgba(240,240,245,0.25)',
          }}>
            + 1000 sites
          </div>
        </div>
      )}
    </div>
  )
}
