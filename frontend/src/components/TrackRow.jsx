import { motion } from 'framer-motion'
import { api } from '../lib/api'
import DownloadButton from './DownloadButton'

export default function TrackRow({ track, index, onDownload, isDownloaded }) {
  const cover = track.cover || track.album?.images?.[0]?.url

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.1, delay: Math.min(index * 0.02, 0.3) }}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 16,
        padding: 12,
        borderRadius: 16,
        transition: 'background 0.2s',
      }}
      className="track-row"
      onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.06)'}
      onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
    >
      {cover ? (
        <img
          src={api.coverUrl(cover)}
          alt=""
          style={{ width: 48, height: 48, borderRadius: 12, objectFit: 'cover', boxShadow: '0 4px 12px rgba(0,0,0,0.3)', flexShrink: 0 }}
        />
      ) : (
        <div style={{ width: 48, height: 48, borderRadius: 12, background: 'rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <span style={{ color: 'rgba(240,240,245,0.3)', fontSize: 18 }}>&#9835;</span>
        </div>
      )}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: '#f0f0f5' }}>
          {track.name}
        </div>
        <div style={{ fontSize: 13, color: 'rgba(240,240,245,0.5)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: 2 }}>
          {track.artists?.map((a) => a.name).join(', ') || track.artist}
        </div>
      </div>
      <div style={{ fontSize: 12, color: 'rgba(240,240,245,0.4)', fontVariantNumeric: 'tabular-nums', flexShrink: 0 }}>
        {track.duration_ms
          ? `${Math.floor(track.duration_ms / 60000)}:${String(Math.floor((track.duration_ms % 60000) / 1000)).padStart(2, '0')}`
          : ''}
      </div>
      <DownloadButton track={track} onDownload={onDownload} isDownloaded={isDownloaded} />
    </motion.div>
  )
}
