import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { IoTime, IoTrash, IoMusicalNotes } from 'react-icons/io5'
import GlassCard from '../components/GlassCard'
import { api } from '../lib/api'

export default function HistoryView() {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    api.history().then((d) => setHistory(d.history || [])).catch(() => {}).finally(() => setLoading(false))
  }
  useEffect(load, [])

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: '#f0f0f5' }}>History</h1>
        {history.length > 0 && (
          <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            onClick={async () => { await api.clearHistory(); load() }}
            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 14, padding: '8px 16px', color: 'rgba(240,240,245,0.5)', cursor: 'pointer', fontSize: 13, fontFamily: 'inherit', display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <IoTrash size={14} /> Clear
          </motion.button>
        )}
      </div>

      {history.length > 0 && (
        <GlassCard hover={false} style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 4 }}>
          {history.map((h, i) => (
            <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.03 }}
              style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 12, borderRadius: 16, transition: 'background 0.2s' }}
              onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.06)'}
              onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
              {h.cover ? (
                <img src={api.coverUrl(h.cover)} alt="" style={{ width: 40, height: 40, borderRadius: 10, objectFit: 'cover' }} />
              ) : (
                <div style={{ width: 40, height: 40, borderRadius: 10, background: 'rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <IoMusicalNotes size={16} style={{ color: 'rgba(240,240,245,0.3)' }} />
                </div>
              )}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 500, color: '#f0f0f5', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{h.name}</div>
                <div style={{ fontSize: 12, color: 'rgba(240,240,245,0.5)' }}>
                  {h.done_count}/{h.tracks_count} tracks &middot; {h.format} &middot; {h.date}
                </div>
              </div>
              {h.fail_count > 0 && <span style={{ fontSize: 12, color: '#f87171', flexShrink: 0 }}>{h.fail_count} failed</span>}
            </motion.div>
          ))}
        </GlassCard>
      )}

      {!loading && history.length === 0 && (
        <div style={{ textAlign: 'center', color: 'rgba(240,240,245,0.4)', paddingTop: 80 }}>
          <IoTime size={48} style={{ opacity: 0.2, marginBottom: 16 }} />
          <p>No download history yet</p>
        </div>
      )}
    </div>
  )
}
