import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { IoArrowBack, IoPerson, IoTrendingUp, IoDisc } from 'react-icons/io5'
import TrackRow from '../components/TrackRow'
import GlassCard from '../components/GlassCard'
import { api } from '../lib/api'

function fmtFollowers(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
  return String(n)
}

export default function ArtistView({ params = {}, onNavigate, downloadedIds, refreshDownloadedIds }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!params.id) return
    setLoading(true)
    setData(null)
    api.artist(params.id)
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [params.id])

  const handleDownload = async (track) => {
    try { await api.download(track); refreshDownloadedIds() } catch (e) { console.error(e) }
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

  const artist = data?.artist || data
  const topTracks = data?.top_tracks || []
  const albums = data?.albums || []
  const cover = artist?.images?.[0]?.url || artist?.cover

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 28 }}>
      {/* Back */}
      <motion.button whileTap={{ scale: 0.95 }} onClick={goBack}
        style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'none', border: 'none', color: 'rgba(240,240,245,0.4)', cursor: 'pointer', fontSize: 13, fontFamily: 'inherit', alignSelf: 'flex-start' }}>
        <IoArrowBack size={16} /> Back
      </motion.button>

      {/* Header */}
      <div style={{ display: 'flex', gap: 28, alignItems: 'center' }}>
        {cover ? (
          <img src={api.coverUrl(cover)} alt=""
            style={{ width: 160, height: 160, borderRadius: '50%', objectFit: 'cover', boxShadow: '0 12px 40px rgba(0,0,0,0.5)', flexShrink: 0 }} />
        ) : (
          <div style={{ width: 160, height: 160, borderRadius: '50%', background: 'rgba(255,255,255,0.04)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <IoPerson size={48} style={{ color: 'rgba(240,240,245,0.2)' }} />
          </div>
        )}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1px', color: 'rgba(240,240,245,0.4)', marginBottom: 8 }}>Artist</div>
          <h1 style={{ fontSize: 36, fontWeight: 800, color: '#f0f0f5', margin: 0, lineHeight: 1.1 }}>{artist?.name}</h1>
          {(artist?.genres?.length > 0 || artist?.followers) && (
            <p style={{ fontSize: 14, color: 'rgba(240,240,245,0.4)', margin: '10px 0 0' }}>
              {artist.genres?.slice(0, 3).join(', ')}
              {artist.genres?.length > 0 && artist.followers ? ' · ' : ''}
              {artist.followers ? `${fmtFollowers(artist.followers)} followers` : ''}
            </p>
          )}
        </div>
      </div>

      {/* Top Tracks */}
      {topTracks.length > 0 && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <IoTrendingUp size={16} style={{ color: '#8b5cf6' }} />
            <span style={{ fontSize: 13, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.8px', color: 'rgba(240,240,245,0.5)' }}>Popular</span>
          </div>
          <GlassCard hover={false} style={{ padding: 8 }}>
            {topTracks.map((track, i) => (
              <TrackRow key={track.id || i} track={track} index={i} onDownload={handleDownload} isDownloaded={downloadedIds?.has(track.id)} />
            ))}
          </GlassCard>
        </div>
      )}

      {/* Discography */}
      {albums.length > 0 && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <IoDisc size={16} style={{ color: '#06b6d4' }} />
            <span style={{ fontSize: 13, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.8px', color: 'rgba(240,240,245,0.5)' }}>Discography</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 16 }}>
            {albums.map((album, i) => {
              const albumCover = album.images?.[0]?.url || album.cover
              return (
                <motion.div key={album.id} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}>
                  <GlassCard
                    onClick={() => onNavigate('album', { id: album.id, _backView: 'artist', _backParams: params })}
                    style={{ padding: 12 }}>
                    {albumCover ? (
                      <img src={api.coverUrl(albumCover)} alt=""
                        style={{ width: '100%', aspectRatio: '1', borderRadius: 14, objectFit: 'cover', marginBottom: 10, boxShadow: '0 6px 20px rgba(0,0,0,0.3)' }} />
                    ) : (
                      <div style={{ width: '100%', aspectRatio: '1', borderRadius: 14, background: 'rgba(255,255,255,0.04)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 10 }}>
                        <IoDisc size={28} style={{ color: 'rgba(240,240,245,0.2)' }} />
                      </div>
                    )}
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#f0f0f5', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{album.name}</div>
                    <div style={{ fontSize: 11, color: 'rgba(240,240,245,0.4)', marginTop: 4 }}>
                      {album.year || (album.release_date && album.release_date.split('-')[0])}
                      {album.total_tracks ? ` · ${album.total_tracks} tracks` : ''}
                    </div>
                  </GlassCard>
                </motion.div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
