import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { IoSave, IoCheckmarkCircle, IoFolder, IoMusicalNotes, IoSwapHorizontal, IoRefresh } from 'react-icons/io5'
import GlassCard from '../components/GlassCard'
import { api } from '../lib/api'

const FORMATS = [
  { value: 'mp3_320', label: 'MP3 320kbps (Best)' },
  { value: 'mp3_256', label: 'MP3 256kbps' },
  { value: 'mp3_128', label: 'MP3 128kbps' },
]

export default function SettingsView() {
  const [config, setConfig] = useState(null)
  const [downloadPath, setDownloadPath] = useState('')
  const [format, setFormat] = useState('mp3_320')
  const [maxConcurrent, setMaxConcurrent] = useState(6)
  const [organize, setOrganize] = useState(true)
  const [saved, setSaved] = useState(false)
  const [loading, setLoading] = useState(true)
  const [update, setUpdate] = useState(null)
  const [checkingUpdate, setCheckingUpdate] = useState(false)
  const [updateStage, setUpdateStage] = useState('idle') // idle | downloading | installing | restarting | error
  const [updateProgress, setUpdateProgress] = useState(0)
  const [updateError, setUpdateError] = useState('')
  const [musicService, setMusicService] = useState('spotify')
  const [spotifyOk, setSpotifyOk] = useState(false)
  const [tidalOk, setTidalOk] = useState(false)
  const [tidalLogging, setTidalLogging] = useState(false)
  const [tidalUrl, setTidalUrl] = useState('')
  const [spotifyLogging, setSpotifyLogging] = useState(false)
  const [spotifyClientId, setSpotifyClientId] = useState('')
  const [spotifyClientSecret, setSpotifyClientSecret] = useState('')
  const [showSpotifyForm, setShowSpotifyForm] = useState(false)
  const [appVersion, setAppVersion] = useState('')

  const startTidalLogin = async () => {
    setTidalLogging(true)
    try {
      const r = await fetch('/api/tidal/login', { method: 'POST' }).then(r => r.json())
      if (r.url) {
        setTidalUrl(r.url)
        fetch('/api/open-url', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url: r.url }) }).catch(() => {})
        const poll = setInterval(async () => {
          const c = await fetch('/api/tidal/login/complete', { method: 'POST' }).then(r => r.json())
          if (c.ok) {
            clearInterval(poll)
            setMusicService('tidal')
            setTidalOk(true)
            setTidalLogging(false)
            setTidalUrl('')
          }
        }, 3000)
        setTimeout(() => { clearInterval(poll); setTidalLogging(false) }, 300000)
      }
    } catch { setTidalLogging(false) }
  }

  const startSpotifyLogin = async (clientId, clientSecret) => {
    setSpotifyLogging(true)
    setShowSpotifyForm(false)
    try {
      const r = await fetch('/api/spotify/auth-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id: clientId, client_secret: clientSecret }),
      }).then(r => r.json())
      if (r.url) {
        fetch('/api/open-url', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url: r.url }) }).catch(() => {})
        const poll = setInterval(async () => {
          const s = await fetch('/api/status').then(r => r.json())
          if (s.spotify === 'ok') {
            clearInterval(poll)
            setSpotifyOk(true)
            setSpotifyLogging(false)
          }
        }, 3000)
        setTimeout(() => { clearInterval(poll); setSpotifyLogging(false) }, 300000)
      }
    } catch { setSpotifyLogging(false) }
  }

  useEffect(() => {
    fetch('/api/version').then(r => r.json()).then(d => setAppVersion(d.version)).catch(() => {})
    fetch('/api/check-update').then(r => r.json()).then(setUpdate).catch(() => {})
    fetch('/api/status').then(r => r.json()).then(s => {
      setMusicService(s.music_service || 'spotify')
      setSpotifyOk(s.spotify === 'ok')
      setTidalOk(s.tidal === 'ok')
    }).catch(() => {})

    api.config().then((cfg) => {
      setConfig(cfg)
      const dl = cfg.download || {}
      setDownloadPath(dl.path || '~/Music/SONGER')
      setFormat(dl.format || 'mp3_320')
      setMaxConcurrent(dl.max_concurrent || 6)
      setOrganize(dl.organize !== false)
      const sp = cfg.spotify || {}
      if (sp.client_id) setSpotifyClientId(sp.client_id)
      if (sp.client_secret) setSpotifyClientSecret(sp.client_secret)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const handleSave = async () => {
    try {
      await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          download: {
            path: downloadPath,
            format,
            source: 'youtube',
            max_concurrent: maxConcurrent,
            organize,
          },
        }),
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e) { console.error(e) }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 80 }}>
        <motion.div animate={{ rotate: 360 }} transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
          style={{ width: 32, height: 32, border: '2px solid #8b5cf6', borderTopColor: 'transparent', borderRadius: '50%' }} />
      </div>
    )
  }

  const inputStyle = {
    width: '100%', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 12, padding: '10px 14px', color: '#f0f0f5', fontSize: 14, fontFamily: 'inherit', outline: 'none',
  }

  const selectStyle = {
    ...inputStyle, appearance: 'none', cursor: 'pointer',
    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M6 8L1 3h10z' fill='rgba(240,240,245,0.4)'/%3E%3C/svg%3E")`,
    backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px center',
  }

  const labelStyle = { fontSize: 13, fontWeight: 500, color: 'rgba(240,240,245,0.6)', marginBottom: 8, display: 'block' }

  return (
    <div style={{ maxWidth: 600, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: '#f0f0f5' }}>Settings</h1>
        <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={handleSave}
          style={{
            background: saved ? '#06b6d4' : 'linear-gradient(135deg, #8b5cf6, #06b6d4)',
            border: 'none', borderRadius: 14, padding: '10px 20px', color: '#fff', cursor: 'pointer',
            fontSize: 14, fontWeight: 600, fontFamily: 'inherit', display: 'flex', alignItems: 'center', gap: 8,
          }}>
          {saved ? <><IoCheckmarkCircle size={16} /> Saved</> : <><IoSave size={16} /> Save</>}
        </motion.button>
      </div>

      {/* Music Service */}
      <GlassCard hover={false}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          <span style={{ fontSize: 18 }}>&#127911;</span>
          <span style={{ fontWeight: 600, color: '#f0f0f5' }}>Music Service</span>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          {['spotify', 'tidal'].map((svc) => (
            <motion.button key={svc} whileTap={{ scale: 0.95 }}
              onClick={async () => {
                if (svc === 'tidal' && musicService !== 'tidal') {
                  await startTidalLogin()
                } else if (svc === 'spotify') {
                  await fetch('/api/service', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ service: 'spotify' }) })
                  setMusicService('spotify')
                }
              }}
              style={{
                flex: 1, padding: '14px 16px', borderRadius: 14, border: 'none', cursor: 'pointer',
                fontFamily: 'inherit', fontSize: 15, fontWeight: 600,
                background: musicService === svc
                  ? 'linear-gradient(135deg, rgba(139,92,246,0.25), rgba(6,182,212,0.25))'
                  : 'rgba(255,255,255,0.04)',
                color: musicService === svc ? '#f0f0f5' : 'rgba(240,240,245,0.4)',
                boxShadow: musicService === svc ? '0 0 20px rgba(139,92,246,0.15)' : 'none',
                border: musicService === svc ? '1px solid rgba(139,92,246,0.3)' : '1px solid rgba(255,255,255,0.06)',
              }}>
              {svc === 'spotify' ? 'Spotify' : 'Tidal'}
            </motion.button>
          ))}
        </div>
        {tidalLogging && (
          <div style={{ marginTop: 12, fontSize: 13, color: '#06b6d4' }}>
            Authorize in your browser...
            {tidalUrl && <div style={{ fontSize: 11, color: 'rgba(240,240,245,0.4)', marginTop: 4, wordBreak: 'break-all' }}>{tidalUrl}</div>}
          </div>
        )}
      </GlassCard>

      {/* Download Path */}
      <GlassCard hover={false}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          <IoFolder size={18} style={{ color: '#8b5cf6' }} />
          <span style={{ fontWeight: 600, color: '#f0f0f5' }}>Download Folder</span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <input type="text" value={downloadPath} onChange={(e) => setDownloadPath(e.target.value)} style={{ ...inputStyle, flex: 1 }} placeholder="~/Music/SONGER" />
          <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            onClick={async () => {
              try {
                const r = await fetch('/api/browse-folder').then(r => r.json())
                if (r.path) setDownloadPath(r.path)
              } catch {}
            }}
            style={{
              background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 12, padding: '10px 16px', color: 'rgba(240,240,245,0.6)', cursor: 'pointer',
              fontSize: 13, fontWeight: 500, fontFamily: 'inherit', whiteSpace: 'nowrap',
            }}>
            Browse
          </motion.button>
        </div>
      </GlassCard>

      {/* Format & Source */}
      <GlassCard hover={false}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          <IoMusicalNotes size={18} style={{ color: '#06b6d4' }} />
          <span style={{ fontWeight: 600, color: '#f0f0f5' }}>Audio Quality</span>
        </div>
        <div>
          <label style={labelStyle}>Quality</label>
          <select value={format} onChange={(e) => setFormat(e.target.value)} style={selectStyle}>
            {FORMATS.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
          </select>
        </div>
      </GlassCard>

      {/* Concurrent & Organize */}
      <GlassCard hover={false}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          <IoSwapHorizontal size={18} style={{ color: '#a78bfa' }} />
          <span style={{ fontWeight: 600, color: '#f0f0f5' }}>Download Options</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div>
            <label style={labelStyle}>Max concurrent downloads</label>
            <input type="number" min={1} max={12} value={maxConcurrent} onChange={(e) => setMaxConcurrent(parseInt(e.target.value) || 6)} style={inputStyle} />
          </div>
          <div>
            <label style={labelStyle}>Organize by Artist/Album</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, paddingTop: 4 }}>
              <motion.button whileTap={{ scale: 0.9 }} onClick={() => setOrganize(!organize)}
                style={{
                  width: 48, height: 28, borderRadius: 14, border: 'none', cursor: 'pointer', padding: 2,
                  background: organize ? 'linear-gradient(135deg, #8b5cf6, #06b6d4)' : 'rgba(255,255,255,0.1)',
                  display: 'flex', alignItems: 'center', justifyContent: organize ? 'flex-end' : 'flex-start',
                }}>
                <motion.div layout style={{ width: 22, height: 22, borderRadius: 11, background: '#fff' }} />
              </motion.button>
              <span style={{ fontSize: 14, color: organize ? '#f0f0f5' : 'rgba(240,240,245,0.4)' }}>
                {organize ? 'On' : 'Off'}
              </span>
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Refresh Data */}
      <GlassCard hover={false}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          <IoRefresh size={18} style={{ color: '#22d3ee' }} />
          <span style={{ fontWeight: 600, color: '#f0f0f5' }}>Refresh Data</span>
        </div>
        <p style={{ fontSize: 13, color: 'rgba(240,240,245,0.5)', marginBottom: 16 }}>
          Refresh to detect new liked songs, playlists, or library changes.
        </p>
        <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
          onClick={() => { window.location.reload() }}
          style={{
            width: '100%', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 14, padding: '12px 20px', color: '#f0f0f5', cursor: 'pointer',
            fontSize: 14, fontWeight: 500, fontFamily: 'inherit', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          }}>
          <IoRefresh size={16} /> Refresh App
        </motion.button>
      </GlassCard>

      {/* Updates */}
      <GlassCard hover={false}>
        {update?.translocated && (
          <div style={{
            marginBottom: 16, padding: '12px 16px', borderRadius: 12,
            background: 'rgba(251,191,36,0.08)', border: '1px solid rgba(251,191,36,0.25)',
          }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#fbbf24', marginBottom: 4 }}>App not in Applications folder</div>
            <div style={{ fontSize: 12, color: 'rgba(251,191,36,0.7)', lineHeight: 1.6 }}>
              Auto-update is disabled. Move <strong style={{ color: '#fbbf24' }}>SONGER.app</strong> to your{' '}
              <strong style={{ color: '#fbbf24' }}>/Applications</strong> folder, then relaunch — updates will work automatically.
            </div>
          </div>
        )}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <span style={{ fontWeight: 600, color: '#f0f0f5' }}>Updates</span>
            <div style={{ fontSize: 13, color: 'rgba(240,240,245,0.5)', marginTop: 4 }}>
              {updateStage === 'downloading' ? `Downloading... ${updateProgress}%`
                : updateStage === 'installing' ? 'Installing update...'
                : updateStage === 'restarting' ? 'Restarting...'
                : updateStage === 'error' ? `Error: ${updateError}`
                : update?.has_update ? `v${update.latest} available!`
                : `v${update?.current || appVersion || '...'} — up to date`}
            </div>
            {updateStage === 'downloading' && (
              <div style={{ marginTop: 6, height: 4, borderRadius: 2, background: 'rgba(255,255,255,0.08)', overflow: 'hidden' }}>
                <div style={{ height: '100%', borderRadius: 2, background: 'linear-gradient(90deg, #8b5cf6, #06b6d4)', width: `${updateProgress}%`, transition: 'width 0.3s' }} />
              </div>
            )}
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {update?.has_update && updateStage === 'idle' && !update?.translocated && (
              <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                onClick={async () => {
                  setUpdateStage('downloading')
                  setUpdateProgress(0)
                  setUpdateError('')
                  try {
                    await fetch('/api/auto-update', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ download_url: update.download_url }),
                    })
                    // Poll for status
                    const poll = setInterval(async () => {
                      try {
                        const s = await fetch('/api/update-status').then(r => r.json())
                        setUpdateStage(s.stage)
                        setUpdateProgress(s.progress)
                        if (s.error) setUpdateError(s.error)
                        if (s.stage === 'restarting' || s.stage === 'error' || s.stage === 'idle') {
                          clearInterval(poll)
                        }
                      } catch {
                        // Server restarted — update succeeded
                        clearInterval(poll)
                        setUpdateStage('restarting')
                      }
                    }, 500)
                  } catch {
                    setUpdateStage('error')
                    setUpdateError('Failed to start update')
                  }
                }}
                style={{ background: 'linear-gradient(135deg, #8b5cf6, #06b6d4)', border: 'none', borderRadius: 12, padding: '8px 16px', color: '#fff', cursor: 'pointer', fontSize: 12, fontWeight: 600, fontFamily: 'inherit' }}>
                Update to v{update.latest}
              </motion.button>
            )}
            {['downloading', 'installing', 'restarting'].includes(updateStage) && (
              <div style={{ display: 'flex', alignItems: 'center', padding: '8px 12px' }}>
                <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
                  style={{ width: 16, height: 16, border: '2px solid rgba(139,92,246,0.3)', borderTopColor: '#8b5cf6', borderRadius: '50%' }} />
              </div>
            )}
            {(updateStage === 'idle' || updateStage === 'error') && (
              <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                onClick={async () => {
                  setCheckingUpdate(true)
                  setUpdateStage('idle')
                  setUpdateError('')
                  try {
                    const r = await fetch('/api/check-update').then(r => r.json())
                    setUpdate(r)
                  } catch {}
                  setCheckingUpdate(false)
                }}
                style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, padding: '8px 12px', color: 'rgba(240,240,245,0.5)', cursor: 'pointer', fontSize: 12, fontFamily: 'inherit' }}>
                {checkingUpdate ? '...' : 'Check'}
              </motion.button>
            )}
          </div>
        </div>
      </GlassCard>

      {/* Connection Status */}
      <GlassCard hover={false}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontWeight: 500, color: '#f0f0f5', fontSize: 14 }}>Spotify</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <motion.button whileTap={{ scale: 0.95 }}
                onClick={() => setShowSpotifyForm(f => !f)}
                style={{
                  background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: 8, padding: '4px 10px', color: 'rgba(240,240,245,0.5)',
                  cursor: 'pointer', fontSize: 11, fontFamily: 'inherit',
                }}>
                Reconfigure
              </motion.button>
              <span style={{ fontSize: 12, color: 'rgba(240,240,245,0.4)' }}>{spotifyOk ? 'Connected' : 'Not connected'}</span>
              <div style={{ width: 8, height: 8, borderRadius: 4, background: spotifyOk ? '#22c55e' : '#f87171' }} />
            </div>
          </div>
          {showSpotifyForm && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, paddingTop: 4 }}>
              <input
                placeholder="Client ID"
                value={spotifyClientId}
                onChange={e => setSpotifyClientId(e.target.value)}
                style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '7px 10px', color: '#f0f0f5', fontSize: 12, fontFamily: 'inherit', outline: 'none' }}
              />
              <input
                placeholder="Client Secret"
                type="password"
                value={spotifyClientSecret}
                onChange={e => setSpotifyClientSecret(e.target.value)}
                style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '7px 10px', color: '#f0f0f5', fontSize: 12, fontFamily: 'inherit', outline: 'none' }}
              />
              <motion.button whileTap={{ scale: 0.95 }}
                onClick={() => startSpotifyLogin(spotifyClientId, spotifyClientSecret)}
                disabled={!spotifyClientId || !spotifyClientSecret}
                style={{ background: 'rgba(139,92,246,0.2)', border: '1px solid rgba(139,92,246,0.3)', borderRadius: 8, padding: '7px 10px', color: '#f0f0f5', cursor: 'pointer', fontSize: 12, fontFamily: 'inherit', opacity: (!spotifyClientId || !spotifyClientSecret) ? 0.4 : 1 }}>
                Authorize in browser
              </motion.button>
            </div>
          )}
          {spotifyLogging && (
            <div style={{ fontSize: 13, color: '#1db954' }}>Authorize in your browser, then come back...</div>
          )}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontWeight: 500, color: '#f0f0f5', fontSize: 14 }}>Tidal</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <motion.button whileTap={{ scale: 0.95 }}
                onClick={async () => {
                  await fetch('/api/tidal/disconnect', { method: 'POST' })
                  setTidalOk(false)
                  await startTidalLogin()
                }}
                style={{
                  background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: 8, padding: '4px 10px', color: 'rgba(240,240,245,0.5)',
                  cursor: 'pointer', fontSize: 11, fontFamily: 'inherit',
                }}>
                Reconfigure
              </motion.button>
              <span style={{ fontSize: 12, color: 'rgba(240,240,245,0.4)' }}>{tidalOk ? 'Connected' : 'Not connected'}</span>
              <div style={{ width: 8, height: 8, borderRadius: 4, background: tidalOk ? '#22c55e' : 'rgba(240,240,245,0.2)' }} />
            </div>
          </div>
        </div>
      </GlassCard>

      {/* About */}
      <div style={{ textAlign: 'center', paddingTop: 8, paddingBottom: 20 }}>
        <div style={{ fontSize: 13, color: 'rgba(240,240,245,0.3)', marginBottom: 6 }}>SONGER v{appVersion || '...'}</div>
        <button
          onClick={() => fetch('/api/open-url', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url: 'https://dagotinho.pt' }) }).catch(() => {})}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            fontSize: 11, fontWeight: 700, letterSpacing: 3,
            color: 'rgba(240,240,245,0.15)',
            transition: 'color 0.2s',
            fontFamily: 'inherit',
          }}
          onMouseEnter={(e) => e.currentTarget.style.color = '#8b5cf6'}
          onMouseLeave={(e) => e.currentTarget.style.color = 'rgba(240,240,245,0.15)'}
        >
          MWLBYD
        </button>
      </div>
    </div>
  )
}
