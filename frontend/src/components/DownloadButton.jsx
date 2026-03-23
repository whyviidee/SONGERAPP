import { useState } from 'react'
import { motion } from 'framer-motion'
import { IoCloudDownload, IoCheckmarkCircle } from 'react-icons/io5'

export default function DownloadButton({ track, onDownload, isDownloaded }) {
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  if (isDownloaded || done) {
    return <IoCheckmarkCircle size={22} style={{ color: '#06b6d4', flexShrink: 0 }} />
  }

  return (
    <motion.button
      whileHover={{ scale: 1.3 }}
      whileTap={{ scale: 0.7 }}
      disabled={loading}
      onClick={async (e) => {
        e.stopPropagation()
        if (loading || !onDownload) return
        setLoading(true)
        try {
          await onDownload(track)
          setDone(true)
        } catch (err) {
          console.error('Download failed:', err)
        } finally {
          setLoading(false)
        }
      }}
      style={{
        background: loading ? 'rgba(139,92,246,0.15)' : 'rgba(139,92,246,0.1)',
        border: 'none',
        color: loading ? '#8b5cf6' : '#a78bfa',
        cursor: loading ? 'wait' : 'pointer',
        flexShrink: 0,
        padding: 8,
        borderRadius: 10,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        transition: 'all 0.2s',
      }}
      onMouseEnter={(e) => { if (!loading) { e.currentTarget.style.background = 'rgba(139,92,246,0.25)'; e.currentTarget.style.color = '#c4b5fd' } }}
      onMouseLeave={(e) => { if (!loading) { e.currentTarget.style.background = 'rgba(139,92,246,0.1)'; e.currentTarget.style.color = '#a78bfa' } }}
    >
      {loading ? (
        <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}>
          <IoCloudDownload size={18} />
        </motion.div>
      ) : (
        <IoCloudDownload size={18} />
      )}
    </motion.button>
  )
}
