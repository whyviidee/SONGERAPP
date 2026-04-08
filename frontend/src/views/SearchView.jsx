import { useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { IoSearch, IoMusicalNotes, IoDisc, IoPerson, IoArchive } from 'react-icons/io5'
import TrackRow from '../components/TrackRow'
import GlassCard from '../components/GlassCard'
import { api } from '../lib/api'

function ZipButton({ playlistId, playlistName }) {
  const [status, setStatus] = useState('idle')
  const [progress, setProgress] = useState(0)

  const handleZip = async () => {
    setStatus('zipping')
    setProgress(0)
    try {
      const r = await fetch(`/api/playlists/${playlistId}/zip`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: playlistName }),
      })
      const data = await r.json()
      if (!data.job_id) { setStatus('error'); return }
      const poll = setInterval(async () => {
        try {
          const s = await fetch(`/api/zip/${data.job_id}/status`).then(r => r.json())
          setProgress(s.progress || 0)
          if (s.status === 'done') { clearInterval(poll); setStatus('done'); setTimeout(() => setStatus('idle'), 3000) }
          else if (s.status === 'error') { clearInterval(poll); setStatus('error'); setTimeout(() => setStatus('idle'), 3000) }
        } catch { clearInterval(poll); setStatus('error') }
      }, 1500)
    } catch { setStatus('error') }
  }

  const label = status === 'zipping' ? `${progress}%` : status === 'done' ? 'Saved!' : status === 'error' ? 'Failed' : 'Download ZIP'
  const bg = status === 'done' ? 'rgba(6,182,212,0.15)' : status === 'error' ? 'rgba(248,113,113,0.15)' : 'rgba(139,92,246,0.15)'
  const color = status === 'done' ? '#06b6d4' : status === 'error' ? '#f87171' : '#c4b5fd'

  return (
    <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
      onClick={handleZip} disabled={status === 'zipping'}
      style={{ background: bg, border: '1px solid rgba(139,92,246,0.3)', borderRadius: 14, padding: '10px 18px', color, cursor: status === 'zipping' ? 'wait' : 'pointer', fontSize: 13, fontWeight: 600, fontFamily: 'inherit', display: 'flex', alignItems: 'center', gap: 7 }}>
      <IoArchive size={15} /> {label}
    </motion.button>
  )
}

export default function SearchView({ downloadedIds, refreshDownloadedIds, onNavigate }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('tracks')
  const timerRef = useRef(null)

  const doSearch = useCallback(async (q) => {
    if (!q.trim()) { setResults(null); return }
    setLoading(true)
    try {
      const data = await api.search(q)
      setResults(data)
      const tracks = data?.tracks?.items || data?.tracks || []
      const albums = data?.albums?.items || data?.albums || []
      const artists = data?.artists?.items || data?.artists || []
      if (tracks.length > 0) setActiveTab('tracks')
      else if (albums.length > 0) setActiveTab('albums')
      else if (artists.length > 0) setActiveTab('artists')
    } catch (e) { console.error(e) }
    setLoading(false)
  }, [])

  const handleInput = (e) => {
    const val = e.target.value
    setQuery(val)
    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => doSearch(val), 400)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') { clearTimeout(timerRef.current); doSearch(query) }
  }

  const handleDownload = async (track) => {
    try { await api.download(track); refreshDownloadedIds() } catch (e) { console.error(e) }
  }

  const tracks = results?.tracks?.items || results?.tracks || []
  const albums = results?.albums?.items || results?.albums || []
  const artists = results?.artists?.items || results?.artists || []

  const tabs = [
    { id: 'tracks', label: 'Tracks', count: tracks.length, icon: IoMusicalNotes },
    { id: 'albums', label: 'Albums', count: albums.length, icon: IoDisc },
    { id: 'artists', label: 'Artists', count: artists.length, icon: IoPerson },
  ]

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Search Bar */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 14, padding: '18px 24px',
        background: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)',
        border: '1px solid rgba(255,255,255,0.1)', borderRadius: 28,
        boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
      }}>
        <IoSearch size={22} style={{ color: 'rgba(240,240,245,0.4)', flexShrink: 0 }} />
        <input
          type="text" value={query} onChange={handleInput} onKeyDown={handleKeyDown}
          placeholder="Song, artist, album, or Spotify URL..."
          autoFocus
          style={{
            flex: 1, background: 'none', border: 'none', outline: 'none',
            color: '#f0f0f5', fontSize: 18, fontFamily: 'inherit',
          }}
        />
        {loading && (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            style={{ width: 22, height: 22, border: '2px solid #8b5cf6', borderTopColor: 'transparent', borderRadius: '50%', flexShrink: 0 }}
          />
        )}
      </div>

      {/* Result tabs */}
      {results && (tracks.length > 0 || albums.length > 0 || artists.length > 0) && (
        <div style={{ display: 'flex', gap: 8 }}>
          {tabs.filter(t => t.count > 0).map(({ id, label, count, icon: Icon }) => (
            <motion.button key={id} whileTap={{ scale: 0.95 }}
              onClick={() => setActiveTab(id)}
              style={{
                display: 'flex', alignItems: 'center', gap: 6, padding: '8px 16px', borderRadius: 14,
                border: 'none', cursor: 'pointer', fontFamily: 'inherit', fontSize: 13, fontWeight: 500,
                background: activeTab === id ? 'rgba(139,92,246,0.2)' : 'rgba(255,255,255,0.04)',
                color: activeTab === id ? '#c4b5fd' : 'rgba(240,240,245,0.5)',
              }}>
              <Icon size={14} /> {label} <span style={{ opacity: 0.5 }}>{count}</span>
            </motion.button>
          ))}
        </div>
      )}

      {/* Playlist header + ZIP button */}
      {results?.playlist_id && tracks.length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 4px' }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#f0f0f5' }}>{results.playlist_name}</div>
            <div style={{ fontSize: 12, color: 'rgba(240,240,245,0.4)', marginTop: 2 }}>{tracks.length} tracks</div>
          </div>
          <ZipButton playlistId={results.playlist_id} playlistName={results.playlist_name} />
        </div>
      )}

      <AnimatePresence mode="wait">
        {/* Tracks */}
        {activeTab === 'tracks' && tracks.length > 0 && (
          <motion.div key="tracks" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <GlassCard hover={false} style={{ padding: 8 }}>
              {tracks.map((track, i) => (
                <TrackRow key={track.id || i} track={track} index={i} onDownload={handleDownload} isDownloaded={downloadedIds?.has(track.id)} />
              ))}
            </GlassCard>
          </motion.div>
        )}

        {/* Albums */}
        {activeTab === 'albums' && albums.length > 0 && (
          <motion.div key="albums" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 16 }}>
              {albums.map((album, i) => {
                const cover = album.images?.[0]?.url || album.cover
                return (
                  <motion.div key={album.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
                    <GlassCard onClick={() => onNavigate('album', { id: album.id, _backView: 'search' })} style={{ padding: 12 }}>
                      {cover && (
                        <img src={api.coverUrl(cover)} alt=""
                          style={{ width: '100%', aspectRatio: '1', borderRadius: 16, objectFit: 'cover', marginBottom: 12, boxShadow: '0 8px 24px rgba(0,0,0,0.3)' }} />
                      )}
                      <div style={{ fontSize: 14, fontWeight: 600, color: '#f0f0f5', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{album.name}</div>
                      <div style={{ fontSize: 12, color: 'rgba(240,240,245,0.4)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: 4 }}>
                        {album.artists?.map(a => a.name).join(', ')}
                        {album.release_date && ` · ${album.release_date.split('-')[0]}`}
                      </div>
                    </GlassCard>
                  </motion.div>
                )
              })}
            </div>
          </motion.div>
        )}

        {/* Artists */}
        {activeTab === 'artists' && artists.length > 0 && (
          <motion.div key="artists" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 16 }}>
              {artists.map((artist, i) => {
                const img = artist.images?.[0]?.url || artist.cover
                return (
                  <motion.div key={artist.id} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.05 }}>
                    <GlassCard
                      onClick={() => onNavigate('artist', { id: artist.id, _backView: 'search' })}
                      style={{ padding: 16, display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
                      {img ? (
                        <img src={api.coverUrl(img)} alt=""
                          style={{ width: 80, height: 80, borderRadius: '50%', objectFit: 'cover', marginBottom: 12, boxShadow: '0 4px 16px rgba(0,0,0,0.3)' }} />
                      ) : (
                        <div style={{ width: 80, height: 80, borderRadius: '50%', background: 'rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 12 }}>
                          <IoPerson size={28} style={{ color: 'rgba(240,240,245,0.3)' }} />
                        </div>
                      )}
                      <div style={{ fontSize: 14, fontWeight: 500, color: '#f0f0f5', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', width: '100%' }}>{artist.name}</div>
                      {artist.genres?.length > 0 && (
                        <div style={{ fontSize: 11, color: 'rgba(240,240,245,0.4)', marginTop: 4 }}>{artist.genres.slice(0, 2).join(', ')}</div>
                      )}
                    </GlassCard>
                  </motion.div>
                )
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Empty states */}
      {!results && !loading && (
        <div style={{ textAlign: 'center', paddingTop: 60 }}>
          <div style={{ width: 80, height: 80, borderRadius: '50%', background: 'rgba(139,92,246,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
            <IoSearch size={32} style={{ color: 'rgba(139,92,246,0.4)' }} />
          </div>
          <p style={{ color: 'rgba(240,240,245,0.5)', fontSize: 16 }}>Search for any song, artist, or album</p>
          <p style={{ color: 'rgba(240,240,245,0.3)', fontSize: 13, marginTop: 6 }}>You can also paste a Spotify URL</p>
        </div>
      )}
      {results && tracks.length === 0 && albums.length === 0 && artists.length === 0 && (
        <div style={{ textAlign: 'center', color: 'rgba(240,240,245,0.4)', paddingTop: 48 }}>No results found</div>
      )}
    </div>
  )
}
