import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { IoClose, IoTrash, IoCheckmarkCircle, IoAlertCircle, IoCloudDownload, IoTime, IoMusicalNotes, IoArchive } from 'react-icons/io5'
import GlassCard from '../components/GlassCard'
import { useDownloadQueue } from '../hooks/useDownloadQueue'
import { useSSE } from '../hooks/useSSE'
import { api } from '../lib/api'

export default function QueueView() {
  const { jobs, refresh } = useDownloadQueue()
  const [history, setHistory] = useState([])
  const [zipJobs, setZipJobs] = useState({})

  // Load zip jobs and history on mount
  useEffect(() => {
    api.history().then((d) => setHistory(Array.isArray(d) ? d : (d.history || []))).catch(() => {})
    fetch('/api/zip-jobs').then(r => r.json()).then(jobs => {
      const map = {}
      for (const j of jobs) map[j.id] = j
      setZipJobs(map)
    }).catch(() => {})
  }, [])

  // Listen for ALL updates via SSE
  useSSE((event) => {
    if (event.type === 'zip_update') {
      setZipJobs(prev => ({ ...prev, [event.job_id]: { ...prev[event.job_id], ...event } }))
    }
    if (event.type === 'done' || event.type === 'queue_update') {
      api.history().then((d) => setHistory(Array.isArray(d) ? d : (d.history || []))).catch(() => {})
    }
  })

  const active = jobs.filter((j) => j.status === 'downloading' || j.status === 'pending')
  const done = jobs.filter((j) => j.status === 'done')
  const failed = jobs.filter((j) => j.status === 'error')
  const allZips = Object.values(zipJobs)
  const activeZips = allZips.filter(z => z.status === 'downloading' || z.status === 'pending')
  const doneZips = allZips.filter(z => z.status === 'done')

  const hasActive = active.length > 0 || activeZips.length > 0

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: '#f0f0f5' }}>Downloads</h1>
        {active.length > 0 && (
          <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            onClick={async () => { await api.cancelAll(); refresh() }}
            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 14, padding: '8px 16px', color: 'rgba(240,240,245,0.5)', cursor: 'pointer', fontSize: 13, fontFamily: 'inherit', display: 'flex', alignItems: 'center', gap: 6 }}>
            <IoTrash size={14} /> Clear queue
          </motion.button>
        )}
      </div>

      {/* Active ZIP jobs */}
      {activeZips.length > 0 && (
        <GlassCard hover={false} style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 4 }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'rgba(240,240,245,0.5)', padding: '4px 8px 8px' }}>Zipping</h3>
          {activeZips.map((zip) => (
            <div key={zip.job_id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 12, borderRadius: 16 }}>
              <div style={{ width: 40, height: 40, borderRadius: 10, background: 'rgba(139,92,246,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <IoArchive size={16} style={{ color: '#8b5cf6' }} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 500, color: '#f0f0f5' }}>
                  {zip.name || 'Playlist'} <span style={{ fontSize: 12, color: 'rgba(240,240,245,0.4)' }}>(.zip)</span>
                </div>
                <div style={{ fontSize: 12, color: 'rgba(240,240,245,0.4)' }}>
                  {zip.done || 0}/{zip.total || '?'} tracks
                </div>
                <div style={{ marginTop: 8, height: 6, borderRadius: 3, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                  <motion.div style={{ height: '100%', borderRadius: 3, background: 'linear-gradient(90deg, #8b5cf6, #06b6d4)' }} initial={{ width: 0 }} animate={{ width: `${zip.progress || 0}%` }} transition={{ duration: 0.3 }} />
                </div>
              </div>
            </div>
          ))}
        </GlassCard>
      )}

      {/* Active track downloads */}
      {active.length > 0 && (
        <GlassCard hover={false} style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 4 }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'rgba(240,240,245,0.5)', padding: '4px 8px 8px' }}>In Progress</h3>
          {active.map((job) => (
            <div key={job.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 12, borderRadius: 16 }}>
              {job.cover ? (
                <img src={api.coverUrl(job.cover)} alt="" style={{ width: 40, height: 40, borderRadius: 10, objectFit: 'cover' }} />
              ) : (
                <div style={{ width: 40, height: 40, borderRadius: 10, background: 'rgba(139,92,246,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <IoCloudDownload size={16} style={{ color: '#8b5cf6' }} />
                </div>
              )}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 500, color: '#f0f0f5', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{job.name}</div>
                <div style={{ fontSize: 12, color: 'rgba(240,240,245,0.4)' }}>{job.artist}</div>
                <div style={{ marginTop: 8, height: 6, borderRadius: 3, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                  <motion.div style={{ height: '100%', borderRadius: 3, background: 'linear-gradient(90deg, #8b5cf6, #06b6d4)' }} initial={{ width: 0 }} animate={{ width: `${job.progress || 0}%` }} transition={{ duration: 0.3 }} />
                </div>
              </div>
              <motion.button whileHover={{ scale: 1.2 }} whileTap={{ scale: 0.8 }}
                onClick={async () => { await api.cancelJob(job.id); refresh() }}
                style={{ background: 'none', border: 'none', color: 'rgba(240,240,245,0.4)', cursor: 'pointer' }}>
                <IoClose size={18} />
              </motion.button>
            </div>
          ))}
        </GlassCard>
      )}

      {/* Completed (session) */}
      {(done.length > 0 || doneZips.length > 0) && (
        <GlassCard hover={false} style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 4 }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'rgba(240,240,245,0.5)', padding: '4px 8px 8px' }}>Completed</h3>
          {doneZips.map((zip) => (
            <div key={zip.job_id || zip.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 12, borderRadius: 16 }}>
              <div style={{ width: 40, height: 40, borderRadius: 10, background: 'rgba(6,182,212,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <IoArchive size={16} style={{ color: '#06b6d4' }} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 500, color: '#f0f0f5' }}>{zip.name || 'Playlist'}.zip</div>
                <div style={{ fontSize: 12, color: 'rgba(240,240,245,0.4)' }}>{zip.total || 0} tracks</div>
              </div>
              <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                onClick={async () => {
                  const name = zip.name || 'Playlist'
                  if (!confirm(`Extract "${name}.zip" to your music folder?\n\nThis will:\n- Extract ${zip.total || 0} tracks to your download folder\n- Delete the .zip file after extracting`)) return
                  const id = zip.job_id || zip.id
                  try {
                    const r = await fetch(`/api/zip/${id}/extract`, { method: 'POST', headers: { 'Content-Type': 'application/json' } })
                    const data = await r.json()
                    if (data.ok) {
                      alert(`Done! ${data.extracted} files extracted to your music folder.`)
                      setZipJobs(prev => {
                        const copy = { ...prev }
                        delete copy[id]
                        return copy
                      })
                      // Refresh history and queue to show new entries
                      refresh()
                      api.history().then((d) => setHistory(Array.isArray(d) ? d : (d.history || []))).catch(() => {})
                    } else {
                      alert('Error: ' + (data.error || 'Unknown'))
                    }
                  } catch (e) { console.error(e) }
                }}
                style={{ background: 'rgba(6,182,212,0.1)', border: '1px solid rgba(6,182,212,0.2)', borderRadius: 12, padding: '6px 12px', color: '#06b6d4', cursor: 'pointer', fontSize: 11, fontWeight: 600, fontFamily: 'inherit', flexShrink: 0, display: 'flex', alignItems: 'center', gap: 4 }}>
                Unzip
              </motion.button>
            </div>
          ))}
          {done.map((job) => (
            <div key={job.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 12, borderRadius: 16 }}>
              {job.cover ? (
                <img src={api.coverUrl(job.cover)} alt="" style={{ width: 40, height: 40, borderRadius: 10, objectFit: 'cover' }} />
              ) : (
                <div style={{ width: 40, height: 40, borderRadius: 10, background: 'rgba(6,182,212,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <IoCheckmarkCircle size={16} style={{ color: '#06b6d4' }} />
                </div>
              )}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 500, color: '#f0f0f5', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{job.name}</div>
                <div style={{ fontSize: 12, color: 'rgba(240,240,245,0.4)' }}>{job.artist}</div>
              </div>
              <IoCheckmarkCircle size={18} style={{ color: '#06b6d4', flexShrink: 0 }} />
            </div>
          ))}
        </GlassCard>
      )}

      {/* Failed */}
      {failed.length > 0 && (
        <GlassCard hover={false} style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 4 }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: 'rgba(240,240,245,0.5)', padding: '4px 8px 8px' }}>Failed</h3>
          {failed.map((job) => (
            <div key={job.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 12, borderRadius: 16 }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 500, color: '#f0f0f5' }}>{job.name}</div>
                <div style={{ fontSize: 12, color: '#f87171' }}>{job.error}</div>
              </div>
              <IoAlertCircle size={18} style={{ color: '#f87171', flexShrink: 0 }} />
            </div>
          ))}
        </GlassCard>
      )}

      {/* Empty */}
      {!hasActive && done.length === 0 && doneZips.length === 0 && failed.length === 0 && history.length === 0 && (
        <div style={{ textAlign: 'center', color: 'rgba(240,240,245,0.4)', paddingTop: 40 }}>
          <IoCloudDownload size={48} style={{ opacity: 0.2, marginBottom: 16 }} />
          <p>No downloads yet</p>
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <IoTime size={18} style={{ color: '#8b5cf6' }} />
              <h2 style={{ fontSize: 18, fontWeight: 600, color: '#f0f0f5', margin: 0 }}>History</h2>
              <span style={{ fontSize: 12, color: 'rgba(240,240,245,0.4)' }}>{history.length}</span>
            </div>
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={async () => { await api.clearHistory(); setHistory([]) }}
              style={{ background: 'none', border: 'none', color: 'rgba(240,240,245,0.4)', cursor: 'pointer', fontSize: 12, fontFamily: 'inherit' }}>
              Clear
            </motion.button>
          </div>
          <GlassCard hover={false} style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 2 }}>
            {history.map((h, i) => (
              <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: Math.min(i * 0.02, 0.3) }}
                style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px', borderRadius: 14, transition: 'background 0.2s' }}
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
                    {h.done_count}/{h.tracks_count} · {h.format} · {h.date?.split('T')[0]}
                  </div>
                </div>
                {h.fail_count > 0 && <span style={{ fontSize: 11, color: '#f87171', flexShrink: 0 }}>{h.fail_count} failed</span>}
                {h.fail_count === 0 && <IoCheckmarkCircle size={16} style={{ color: 'rgba(6,182,212,0.5)', flexShrink: 0 }} />}
              </motion.div>
            ))}
          </GlassCard>
        </>
      )}
    </div>
  )
}
