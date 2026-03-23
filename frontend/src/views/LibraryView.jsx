import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { IoSearch, IoHeart, IoList, IoArrowBack, IoCloudDownload, IoArchive } from 'react-icons/io5'
import GlassCard from '../components/GlassCard'
import TrackRow from '../components/TrackRow'
import { api } from '../lib/api'

const TABS = [
  { id: 'playlists', label: 'Playlists', icon: IoList },
  { id: 'liked', label: 'Liked Songs', icon: IoHeart },
]

function ZipButton({ playlistId, playlistName }) {
  const [status, setStatus] = useState('idle') // idle, zipping, done, error
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
          if (s.status === 'done') {
            clearInterval(poll)
            setStatus('done')
            setTimeout(() => setStatus('idle'), 3000)
          } else if (s.status === 'error') {
            clearInterval(poll)
            setStatus('error')
            setTimeout(() => setStatus('idle'), 3000)
          }
        } catch { clearInterval(poll); setStatus('error') }
      }, 1500)
    } catch { setStatus('error') }
  }

  const label = status === 'zipping' ? `${progress}%` : status === 'done' ? 'Saved!' : status === 'error' ? 'Failed' : 'ZIP'
  const bg = status === 'done' ? 'rgba(6,182,212,0.15)' : status === 'error' ? 'rgba(248,113,113,0.15)' : 'rgba(255,255,255,0.06)'
  const color = status === 'done' ? '#06b6d4' : status === 'error' ? '#f87171' : '#f0f0f5'

  return (
    <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
      onClick={handleZip} disabled={status === 'zipping'}
      style={{ background: bg, border: '1px solid rgba(255,255,255,0.1)', borderRadius: 14, padding: '10px 16px', color, cursor: status === 'zipping' ? 'wait' : 'pointer', fontSize: 12, fontWeight: 600, fontFamily: 'inherit', display: 'flex', alignItems: 'center', gap: 6, minWidth: 80, justifyContent: 'center' }}>
      <IoArchive size={15} /> {label}
    </motion.button>
  )
}

export default function LibraryView({ downloadedIds, refreshDownloadedIds }) {
  const [tab, setTab] = useState('playlists')
  const [playlists, setPlaylists] = useState([])
  const [likedSongs, setLikedSongs] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const [openPlaylist, setOpenPlaylist] = useState(null)
  const [playlistTracks, setPlaylistTracks] = useState([])
  const [loadingPl, setLoadingPl] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [allPlaylists, setAllPlaylists] = useState([])
  const [hasMorePl, setHasMorePl] = useState(true)
  const [hasMoreLiked, setHasMoreLiked] = useState(true)

  const PAGE_SIZE = 30

  useEffect(() => {
    Promise.all([
      api.playlists().then((d) => {
        const p = Array.isArray(d) ? d : (d.playlists || [])
        setAllPlaylists(p)
        setPlaylists(p.slice(0, PAGE_SIZE))
        setHasMorePl(p.length > PAGE_SIZE)
      }).catch(() => {}),
      api.likedSongs(0, PAGE_SIZE).then((d) => {
        const t = Array.isArray(d) ? d : (d.tracks || [])
        setLikedSongs(t)
        setHasMoreLiked(t.length >= PAGE_SIZE)
      }).catch(() => {}),
    ]).finally(() => setLoading(false))
  }, [])

  const handleDownload = async (track) => {
    try { await api.download(track); refreshDownloadedIds() } catch (e) { console.error(e) }
  }

  const handleDownloadAll = async (tracks) => {
    try { await api.download(tracks); refreshDownloadedIds() } catch (e) { console.error(e) }
  }

  const handleOpenPlaylist = async (pl) => {
    setOpenPlaylist(pl)
    setLoadingPl(true)
    try {
      const data = await api.playlistTracks(pl.id)
      setPlaylistTracks(Array.isArray(data) ? data : (data.tracks || []))
    } catch (e) { console.error(e) }
    setLoadingPl(false)
  }

  const loadMorePlaylists = () => {
    const next = allPlaylists.slice(0, playlists.length + PAGE_SIZE)
    setPlaylists(next)
    setHasMorePl(next.length < allPlaylists.length)
  }

  const loadMoreLiked = async () => {
    setLoadingMore(true)
    try {
      const d = await api.likedSongs(likedSongs.length, PAGE_SIZE)
      const t = Array.isArray(d) ? d : (d.tracks || [])
      setLikedSongs([...likedSongs, ...t])
      setHasMoreLiked(t.length >= PAGE_SIZE)
    } catch (e) { console.error(e) }
    setLoadingMore(false)
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 256 }}>
        <motion.div animate={{ rotate: 360 }} transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
          style={{ width: 32, height: 32, border: '2px solid #8b5cf6', borderTopColor: 'transparent', borderRadius: '50%' }} />
      </div>
    )
  }

  // Playlist detail
  if (openPlaylist) {
    return (
      <div style={{ maxWidth: 900, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <motion.button whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}
            onClick={() => { setOpenPlaylist(null); setPlaylistTracks([]) }}
            style={{ background: 'rgba(255,255,255,0.06)', border: 'none', borderRadius: 12, padding: 10, color: '#f0f0f5', cursor: 'pointer' }}>
            <IoArrowBack size={20} />
          </motion.button>
          {openPlaylist.cover && (
            <img src={api.coverUrl(openPlaylist.cover)} alt="" style={{ width: 56, height: 56, borderRadius: 14, objectFit: 'cover' }} />
          )}
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 700, color: '#f0f0f5', margin: 0 }}>{openPlaylist.name}</h1>
            <p style={{ fontSize: 13, color: 'rgba(240,240,245,0.5)', margin: 0 }}>{openPlaylist.tracks_total || playlistTracks.length} tracks</p>
          </div>
          {playlistTracks.length > 0 && (
            <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
              <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                onClick={() => { handleDownloadAll(playlistTracks); refreshDownloadedIds() }}
                style={{ background: 'linear-gradient(135deg, #8b5cf6, #06b6d4)', border: 'none', borderRadius: 14, padding: '10px 16px', color: '#fff', cursor: 'pointer', fontSize: 12, fontWeight: 600, fontFamily: 'inherit', display: 'flex', alignItems: 'center', gap: 6 }}>
                <IoCloudDownload size={15} /> Download
              </motion.button>
              <ZipButton playlistId={openPlaylist.id} playlistName={openPlaylist.name} />
            </div>
          )}
        </div>
        {loadingPl ? (
          <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 40 }}>
            <motion.div animate={{ rotate: 360 }} transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
              style={{ width: 32, height: 32, border: '2px solid #8b5cf6', borderTopColor: 'transparent', borderRadius: '50%' }} />
          </div>
        ) : (
          <GlassCard hover={false} style={{ padding: 8 }}>
            {playlistTracks.map((track, i) => (
              <TrackRow key={track.id || i} track={track} index={i} onDownload={handleDownload} isDownloaded={downloadedIds.has(track.id)} />
            ))}
            {playlistTracks.length === 0 && (
              <div style={{ textAlign: 'center', color: 'rgba(240,240,245,0.4)', padding: 32 }}>No tracks</div>
            )}
          </GlassCard>
        )}
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, color: '#f0f0f5' }}>Library</h1>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 8 }}>
        {TABS.map(({ id, label, icon: Icon }) => (
          <motion.button key={id} whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
            onClick={() => { setTab(id); setFilter('') }}
            style={{
              flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              padding: '12px 16px', borderRadius: 16, border: 'none', cursor: 'pointer', fontFamily: 'inherit', fontSize: 14, fontWeight: 500,
              background: tab === id ? 'linear-gradient(135deg, rgba(139,92,246,0.2), rgba(6,182,212,0.2))' : 'rgba(255,255,255,0.04)',
              color: tab === id ? '#f0f0f5' : 'rgba(240,240,245,0.5)',
              boxShadow: tab === id ? '0 0 20px rgba(139,92,246,0.15)' : 'none',
            }}>
            <Icon size={16} /> {label}
            <span style={{ fontSize: 11, opacity: 0.6 }}>
              {id === 'playlists' ? allPlaylists.length : likedSongs.length}
            </span>
          </motion.button>
        ))}
      </div>

      {/* Playlists tab */}
      {tab === 'playlists' && (() => {
        const q = filter.toLowerCase()
        const filteredPl = q ? allPlaylists.filter(p => p.name?.toLowerCase().includes(q)) : playlists
        return (
          <>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px',
              background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16,
            }}>
              <IoSearch size={16} style={{ color: 'rgba(240,240,245,0.4)' }} />
              <input type="text" value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Search playlists..."
                style={{ flex: 1, background: 'none', border: 'none', outline: 'none', color: '#f0f0f5', fontSize: 14, fontFamily: 'inherit' }} />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 12 }}>
              {filteredPl.map((pl) => (
                <GlassCard key={pl.id} onClick={() => handleOpenPlaylist(pl)} style={{ padding: 14 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    {pl.cover ? (
                      <img src={api.coverUrl(pl.cover)} alt="" style={{ width: 44, height: 44, borderRadius: 10, objectFit: 'cover' }} />
                    ) : (
                      <div style={{ width: 44, height: 44, borderRadius: 10, background: 'rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <IoList size={18} style={{ color: 'rgba(240,240,245,0.3)' }} />
                      </div>
                    )}
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontSize: 14, fontWeight: 500, color: '#f0f0f5', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{pl.name}</div>
                      <div style={{ fontSize: 12, color: 'rgba(240,240,245,0.4)' }}>{pl.tracks_total || 0} tracks</div>
                    </div>
                  </div>
                </GlassCard>
              ))}
            </div>
            {!filter && hasMorePl && (
              <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }} onClick={loadMorePlaylists}
                style={{ width: '100%', padding: '14px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16, color: '#8b5cf6', cursor: 'pointer', fontSize: 14, fontWeight: 500, fontFamily: 'inherit' }}>
                Load more playlists ({allPlaylists.length - playlists.length} remaining)
              </motion.button>
            )}
          </>
        )
      })()}

      {/* Liked Songs tab */}
      {tab === 'liked' && (() => {
        const q = filter.toLowerCase()
        const filteredLiked = q ? likedSongs.filter(t => t.name?.toLowerCase().includes(q) || t.artist?.toLowerCase().includes(q)) : likedSongs
        return (
          <>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px',
              background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16,
            }}>
              <IoSearch size={16} style={{ color: 'rgba(240,240,245,0.4)' }} />
              <input type="text" value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Search liked songs..."
                style={{ flex: 1, background: 'none', border: 'none', outline: 'none', color: '#f0f0f5', fontSize: 14, fontFamily: 'inherit' }} />
            </div>
            {filteredLiked.length > 0 && !q && (
              <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                onClick={() => handleDownloadAll(filteredLiked)}
                style={{ width: '100%', padding: '14px', background: 'linear-gradient(135deg, rgba(139,92,246,0.15), rgba(6,182,212,0.15))', border: '1px solid rgba(139,92,246,0.2)', borderRadius: 16, color: '#c4b5fd', cursor: 'pointer', fontSize: 14, fontWeight: 500, fontFamily: 'inherit', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                <IoCloudDownload size={16} /> Download All ({filteredLiked.length} tracks)
              </motion.button>
            )}
            <GlassCard hover={false} style={{ padding: 8 }}>
              {filteredLiked.map((track, i) => (
                <TrackRow key={track.id || i} track={track} index={i} onDownload={handleDownload} isDownloaded={downloadedIds?.has(track.id)} />
              ))}
              {filteredLiked.length === 0 && (
                <div style={{ textAlign: 'center', color: 'rgba(240,240,245,0.4)', padding: 32 }}>
                  {q ? 'No matches' : 'No liked songs found'}
                </div>
              )}
            </GlassCard>
            {!filter && hasMoreLiked && (
              <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }} onClick={loadMoreLiked} disabled={loadingMore}
                style={{ width: '100%', padding: '14px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16, color: '#8b5cf6', cursor: loadingMore ? 'wait' : 'pointer', fontSize: 14, fontWeight: 500, fontFamily: 'inherit' }}>
                {loadingMore ? 'Loading...' : 'Load more liked songs'}
              </motion.button>
            )}
          </>
        )
      })()}
    </div>
  )
}
