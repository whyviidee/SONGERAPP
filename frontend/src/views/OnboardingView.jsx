import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const V = '#8b5cf6'
const C = '#06b6d4'
const REDIRECT_URI = 'http://127.0.0.1:8888/callback'
const DASHBOARD_URL = 'https://developer.spotify.com/dashboard'

function CopyButton({ text, label = 'Copy' }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }
  return (
    <motion.button whileTap={{ scale: 0.93 }} onClick={copy}
      style={{
        background: copied ? 'rgba(6,182,212,0.15)' : 'rgba(139,92,246,0.15)',
        border: `1px solid ${copied ? 'rgba(6,182,212,0.3)' : 'rgba(139,92,246,0.3)'}`,
        borderRadius: 10, padding: '6px 14px', color: copied ? C : V,
        cursor: 'pointer', fontSize: 12, fontWeight: 600, fontFamily: 'inherit',
        display: 'flex', alignItems: 'center', gap: 6, whiteSpace: 'nowrap',
        transition: 'all 0.2s',
      }}>
      {copied ? (
        <><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg> Copied!</>
      ) : (
        <><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> {label}</>
      )}
    </motion.button>
  )
}

function CodeBox({ value, label, onCopy }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(value).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }
  return (
    <div style={{ marginBottom: 12 }}>
      {label && <div style={{ fontSize: 12, color: 'rgba(240,240,245,0.5)', marginBottom: 6, fontWeight: 500 }}>{label}</div>}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 12, padding: '10px 14px',
      }}>
        <span style={{ flex: 1, fontSize: 13, color: '#f0f0f5', fontFamily: 'monospace', letterSpacing: 0.5, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {value}
        </span>
        <motion.button whileTap={{ scale: 0.9 }} onClick={copy}
          style={{
            background: copied ? 'rgba(6,182,212,0.15)' : 'rgba(255,255,255,0.06)',
            border: `1px solid ${copied ? 'rgba(6,182,212,0.3)' : 'rgba(255,255,255,0.1)'}`,
            borderRadius: 8, padding: '5px 12px', color: copied ? C : 'rgba(240,240,245,0.6)',
            cursor: 'pointer', fontSize: 12, fontWeight: 600, fontFamily: 'inherit',
            transition: 'all 0.15s', whiteSpace: 'nowrap',
          }}>
          {copied ? '✓ Copied' : 'Copy'}
        </motion.button>
      </div>
    </div>
  )
}

function StepDots({ total, current }) {
  return (
    <div style={{ display: 'flex', gap: 6, justifyContent: 'center', marginBottom: 32 }}>
      {Array.from({ length: total }).map((_, i) => (
        <motion.div key={i} animate={{ width: i === current ? 20 : 6, opacity: i <= current ? 1 : 0.3 }}
          transition={{ duration: 0.3 }}
          style={{ height: 6, borderRadius: 3, background: `linear-gradient(90deg, ${V}, ${C})` }} />
      ))}
    </div>
  )
}

// ── Welcome ─────────────────────────────────────────────────────────────────
function StepWelcome({ onNext }) {
  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
      style={{ textAlign: 'center', maxWidth: 420 }}>
      <div style={{ marginBottom: 24 }}>
        <motion.div
          animate={{ scale: [1, 1.05, 1], rotate: [0, 2, -2, 0] }}
          transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
          style={{
            width: 80, height: 80, borderRadius: 22, margin: '0 auto 20px',
            background: `linear-gradient(135deg, ${V}, ${C})`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: `0 0 40px rgba(139,92,246,0.4)`,
          }}>
          <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round">
            <path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>
          </svg>
        </motion.div>
        <h1 style={{ fontSize: 32, fontWeight: 800, color: '#f0f0f5', marginBottom: 10, letterSpacing: -0.5 }}>
          Welcome to SONGER
        </h1>
        <p style={{ fontSize: 15, color: 'rgba(240,240,245,0.55)', lineHeight: 1.6, maxWidth: 340, margin: '0 auto' }}>
          Connect your music service and start downloading your music in seconds.
        </p>
      </div>
      <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }} onClick={onNext}
        style={{
          width: '100%', padding: '16px 24px',
          background: `linear-gradient(135deg, ${V}, ${C})`,
          border: 'none', borderRadius: 16, color: '#fff',
          cursor: 'pointer', fontSize: 16, fontWeight: 700, fontFamily: 'inherit',
          boxShadow: `0 8px 32px rgba(139,92,246,0.35)`,
        }}>
        Get Started →
      </motion.button>
    </motion.div>
  )
}

// ── Choose Service ───────────────────────────────────────────────────────────
function StepChooseService({ onNext }) {
  const [selected, setSelected] = useState(null)

  const services = [
    {
      id: 'spotify',
      name: 'Spotify',
      desc: 'Search playlists, liked songs, artists & albums.',
      icon: (
        <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm4.586 14.424a.622.622 0 0 1-.857.207c-2.348-1.435-5.304-1.76-8.785-.964a.623.623 0 0 1-.277-1.215c3.809-.87 7.076-.496 9.712 1.115a.623.623 0 0 1 .207.857zm1.224-2.724a.779.779 0 0 1-1.072.257c-2.687-1.652-6.785-2.131-9.965-1.166a.779.779 0 0 1-.973-.516.779.779 0 0 1 .516-.973c3.632-1.102 8.147-.568 11.238 1.327a.779.779 0 0 1 .256 1.071zm.105-2.835C14.692 8.95 9.375 8.775 6.297 9.71a.935.935 0 1 1-.543-1.79c3.532-1.072 9.404-.865 13.115 1.337a.935.935 0 0 1-.954 1.608z"/>
        </svg>
      ),
      color: '#1DB954',
    },
    {
      id: 'tidal',
      name: 'Tidal',
      desc: 'Login directly — no credentials needed.',
      icon: (
        <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12.012 3.992L8.008 7.996 4.004 3.992 0 7.996l4.004 4.004 4.004-4.004 4.004 4.004 4.004-4.004L20.02 12l4.004-4.004-4.004-4.004-4.004 4.004-4.004-4.004zM8.008 16.004L12.012 20.008 16.016 16.004 12.012 12 8.008 16.004z"/>
        </svg>
      ),
      color: '#00FFFF',
    },
  ]

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
      style={{ maxWidth: 420, width: '100%' }}>
      <div style={{ textAlign: 'center', marginBottom: 28 }}>
        <h2 style={{ fontSize: 24, fontWeight: 700, color: '#f0f0f5', marginBottom: 8 }}>Choose your service</h2>
        <p style={{ fontSize: 14, color: 'rgba(240,240,245,0.5)' }}>You can connect more later in Settings.</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 24 }}>
        {services.map(svc => (
          <motion.button key={svc.id} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
            onClick={() => setSelected(svc.id)}
            style={{
              display: 'flex', alignItems: 'center', gap: 16,
              padding: '18px 20px', borderRadius: 18, cursor: 'pointer',
              fontFamily: 'inherit', textAlign: 'left',
              background: selected === svc.id ? 'rgba(139,92,246,0.12)' : 'rgba(255,255,255,0.04)',
              border: selected === svc.id ? `1px solid rgba(139,92,246,0.4)` : '1px solid rgba(255,255,255,0.07)',
              boxShadow: selected === svc.id ? '0 0 24px rgba(139,92,246,0.15)' : 'none',
              transition: 'all 0.2s',
            }}>
            <div style={{ width: 52, height: 52, borderRadius: 14, background: `${svc.color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: svc.color, flexShrink: 0 }}>
              {svc.icon}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 16, fontWeight: 600, color: '#f0f0f5', marginBottom: 3 }}>{svc.name}</div>
              <div style={{ fontSize: 13, color: 'rgba(240,240,245,0.45)' }}>{svc.desc}</div>
            </div>
            <div style={{
              width: 22, height: 22, borderRadius: 11,
              border: `2px solid ${selected === svc.id ? V : 'rgba(255,255,255,0.15)'}`,
              background: selected === svc.id ? `linear-gradient(135deg, ${V}, ${C})` : 'transparent',
              display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
              transition: 'all 0.2s',
            }}>
              {selected === svc.id && <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>}
            </div>
          </motion.button>
        ))}
      </div>

      <motion.button whileHover={{ scale: selected ? 1.03 : 1 }} whileTap={{ scale: selected ? 0.97 : 1 }}
        onClick={() => selected && onNext(selected)}
        style={{
          width: '100%', padding: '16px 24px',
          background: selected ? `linear-gradient(135deg, ${V}, ${C})` : 'rgba(255,255,255,0.06)',
          border: 'none', borderRadius: 16, color: selected ? '#fff' : 'rgba(240,240,245,0.3)',
          cursor: selected ? 'pointer' : 'default', fontSize: 15, fontWeight: 700, fontFamily: 'inherit',
          boxShadow: selected ? `0 8px 32px rgba(139,92,246,0.3)` : 'none',
          transition: 'all 0.3s',
        }}>
        Continue →
      </motion.button>
    </motion.div>
  )
}

// ── Spotify Setup ────────────────────────────────────────────────────────────
function StepSpotify({ onDone, onSkip }) {
  const [clientId, setClientId] = useState('')
  const [clientSecret, setClientSecret] = useState('')
  const [connecting, setConnecting] = useState(false)
  const [error, setError] = useState('')
  const [substep, setSubstep] = useState(0) // 0=create, 1=credentials, 2=connecting

  const inputStyle = {
    width: '100%', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 12, padding: '12px 14px', color: '#f0f0f5', fontSize: 14,
    fontFamily: 'monospace', outline: 'none', boxSizing: 'border-box',
  }

  const openDashboard = () => {
    fetch('/api/open-url', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url: DASHBOARD_URL }) }).catch(() => {})
    setSubstep(1)
  }

  const connect = async () => {
    if (!clientId.trim() || !clientSecret.trim()) { setError('Fill in both fields.'); return }
    setConnecting(true)
    setError('')
    try {
      // Save credentials (server also redirects but we ignore that)
      await fetch('/setup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `client_id=${encodeURIComponent(clientId.trim())}&client_secret=${encodeURIComponent(clientSecret.trim())}`,
        redirect: 'manual',
      })

      // Open Spotify auth in the system browser
      const authUrl = `https://accounts.spotify.com/authorize?client_id=${encodeURIComponent(clientId.trim())}&response_type=code&redirect_uri=${encodeURIComponent('http://127.0.0.1:8888/callback')}&scope=user-library-read%20user-read-private%20playlist-read-private%20playlist-read-collaborative`
      await fetch('/api/open-url', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url: authUrl }) })

      setSubstep(2)
      // Poll for token
      const poll = setInterval(async () => {
        try {
          const s = await fetch('/api/status').then(r => r.json())
          if (s.spotify === 'ok') { clearInterval(poll); setConnecting(false); onDone() }
        } catch {}
      }, 1500)
      setTimeout(() => { clearInterval(poll); setConnecting(false); setError('Timeout — try again.') }, 120000)
    } catch (e) { setConnecting(false); setError('Connection failed. Check credentials.') }
  }

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
      style={{ maxWidth: 420, width: '100%' }}>
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <div style={{ width: 52, height: 52, borderRadius: 14, background: '#1DB95420', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#1DB954', margin: '0 auto 14px' }}>
          <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm4.586 14.424a.622.622 0 0 1-.857.207c-2.348-1.435-5.304-1.76-8.785-.964a.623.623 0 0 1-.277-1.215c3.809-.87 7.076-.496 9.712 1.115a.623.623 0 0 1 .207.857zm1.224-2.724a.779.779 0 0 1-1.072.257c-2.687-1.652-6.785-2.131-9.965-1.166a.779.779 0 0 1-.973-.516.779.779 0 0 1 .516-.973c3.632-1.102 8.147-.568 11.238 1.327a.779.779 0 0 1 .256 1.071zm.105-2.835C14.692 8.95 9.375 8.775 6.297 9.71a.935.935 0 1 1-.543-1.79c3.532-1.072 9.404-.865 13.115 1.337a.935.935 0 0 1-.954 1.608z"/></svg>
        </div>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: '#f0f0f5', marginBottom: 6 }}>Connect Spotify</h2>
        <p style={{ fontSize: 13, color: 'rgba(240,240,245,0.45)', lineHeight: 1.5 }}>Takes 2 minutes. Free Spotify account works.</p>
      </div>

      <AnimatePresence mode="wait">
        {substep === 0 && (
          <motion.div key="s0" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 16, padding: 20, marginBottom: 16, display: 'flex', flexDirection: 'column', gap: 18 }}>

              {/* Mini-step 1 */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <div style={{ width: 20, height: 20, borderRadius: '50%', background: `linear-gradient(135deg, ${V}, ${C})`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, color: '#fff', flexShrink: 0 }}>1</div>
                  <span style={{ fontSize: 13, fontWeight: 600, color: '#f0f0f5' }}>Open the Spotify Developer Dashboard</span>
                </div>
                <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }} onClick={openDashboard}
                  style={{
                    width: '100%', padding: '11px 16px',
                    background: `linear-gradient(135deg, ${V}, ${C})`,
                    border: 'none', borderRadius: 11, color: '#fff',
                    cursor: 'pointer', fontSize: 13, fontWeight: 700, fontFamily: 'inherit',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  }}>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                  developer.spotify.com/dashboard
                </motion.button>
              </div>

              {/* Divider */}
              <div style={{ height: 1, background: 'rgba(255,255,255,0.05)' }} />

              {/* Mini-step 2 */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <div style={{ width: 20, height: 20, borderRadius: '50%', background: `linear-gradient(135deg, ${V}, ${C})`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, color: '#fff', flexShrink: 0 }}>2</div>
                  <span style={{ fontSize: 13, fontWeight: 600, color: '#f0f0f5' }}>Click <em style={{ fontStyle: 'normal', color: V }}>Create app</em>, fill any name</span>
                </div>
                <div style={{ marginLeft: 28, display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <p style={{ fontSize: 12, color: 'rgba(240,240,245,0.4)', lineHeight: 1.5 }}>
                    In <strong style={{ color: 'rgba(240,240,245,0.7)' }}>Which API/SDKs are you planning to use?</strong> select <strong style={{ color: '#1DB954' }}>Web API</strong>.
                  </p>
                  <p style={{ fontSize: 12, color: 'rgba(240,240,245,0.4)', lineHeight: 1.5 }}>
                    In <strong style={{ color: 'rgba(240,240,245,0.7)' }}>Redirect URIs</strong>, paste this exactly:
                  </p>
                </div>
              </div>

              {/* Redirect URI to copy */}
              <div style={{ marginLeft: 0 }}>
                <CodeBox value={REDIRECT_URI} label="Redirect URI — copy and paste into Spotify" />
              </div>

              {/* Divider */}
              <div style={{ height: 1, background: 'rgba(255,255,255,0.05)' }} />

              {/* Mini-step 3 */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 20, height: 20, borderRadius: '50%', background: `linear-gradient(135deg, ${V}, ${C})`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, color: '#fff', flexShrink: 0 }}>3</div>
                  <span style={{ fontSize: 13, fontWeight: 600, color: '#f0f0f5' }}>Save the app — then click below</span>
                </div>
              </div>
            </div>

            <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }} onClick={() => setSubstep(1)}
              style={{
                width: '100%', padding: '13px',
                background: `linear-gradient(135deg, ${V}, ${C})`,
                border: 'none', borderRadius: 13, color: '#fff',
                cursor: 'pointer', fontSize: 14, fontWeight: 700, fontFamily: 'inherit',
              }}>
              I created the app → Next →
            </motion.button>
            <button onClick={() => setSubstep(1)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(240,240,245,0.3)', fontSize: 12, fontFamily: 'inherit', marginTop: 10, width: '100%' }}>
              Already have an app, skip this
            </button>
          </motion.div>
        )}

        {substep === 1 && (
          <motion.div key="s1" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 16, padding: 20, marginBottom: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: V, marginBottom: 16, textTransform: 'uppercase', letterSpacing: 1 }}>Step 2 — Paste your credentials</div>
              <p style={{ fontSize: 13, color: 'rgba(240,240,245,0.5)', marginBottom: 20, lineHeight: 1.5 }}>
                In your Spotify app dashboard, find <strong style={{ color: '#f0f0f5' }}>Client ID</strong> and <strong style={{ color: '#f0f0f5' }}>Client Secret</strong>.
              </p>
              <div style={{ marginBottom: 14 }}>
                <label style={{ fontSize: 12, color: 'rgba(240,240,245,0.5)', marginBottom: 6, display: 'block', fontWeight: 500 }}>Client ID</label>
                <input value={clientId} onChange={e => setClientId(e.target.value)} placeholder="Paste here..."
                  style={inputStyle} autoComplete="off" spellCheck={false} />
              </div>
              <div style={{ marginBottom: 8 }}>
                <label style={{ fontSize: 12, color: 'rgba(240,240,245,0.5)', marginBottom: 6, display: 'block', fontWeight: 500 }}>Client Secret</label>
                <input value={clientSecret} onChange={e => setClientSecret(e.target.value)} placeholder="Paste here..." type="password"
                  style={inputStyle} autoComplete="off" />
              </div>
            </div>
            {error && <div style={{ fontSize: 13, color: '#f87171', marginBottom: 12, textAlign: 'center' }}>{error}</div>}
            <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }} onClick={connect}
              disabled={connecting}
              style={{
                width: '100%', padding: '15px',
                background: `linear-gradient(135deg, ${V}, ${C})`,
                border: 'none', borderRadius: 13, color: '#fff',
                cursor: connecting ? 'wait' : 'pointer', fontSize: 15, fontWeight: 700, fontFamily: 'inherit',
                opacity: connecting ? 0.8 : 1,
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
              }}>
              {connecting ? (
                <><motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
                  style={{ width: 16, height: 16, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', borderRadius: '50%' }} /> Connecting...</>
              ) : 'Connect Spotify →'}
            </motion.button>
            <button onClick={() => setSubstep(0)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(240,240,245,0.35)', fontSize: 13, fontFamily: 'inherit', marginTop: 12, width: '100%' }}>
              ← Back
            </button>
          </motion.div>
        )}

        {substep === 2 && (
          <motion.div key="s2" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}
            style={{ textAlign: 'center', padding: '24px 0' }}>
            <motion.div animate={{ scale: [1, 1.08, 1] }} transition={{ repeat: Infinity, duration: 2 }}
              style={{ width: 56, height: 56, borderRadius: '50%', background: 'rgba(139,92,246,0.15)', border: `2px solid ${V}`, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
              <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1.2, ease: 'linear' }}
                style={{ width: 28, height: 28, border: `3px solid rgba(139,92,246,0.3)`, borderTopColor: V, borderRadius: '50%' }} />
            </motion.div>
            <p style={{ fontSize: 15, fontWeight: 600, color: '#f0f0f5', marginBottom: 8 }}>Authorize in your browser</p>
            <p style={{ fontSize: 13, color: 'rgba(240,240,245,0.45)' }}>Log in with Spotify in the window that just opened. Waiting...</p>
            {error && <div style={{ fontSize: 13, color: '#f87171', marginTop: 16 }}>{error}</div>}
          </motion.div>
        )}
      </AnimatePresence>

      <button onClick={onSkip} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(240,240,245,0.25)', fontSize: 12, fontFamily: 'inherit', marginTop: 16, width: '100%' }}>
        Skip for now
      </button>
    </motion.div>
  )
}

// ── Tidal Setup ──────────────────────────────────────────────────────────────
function StepTidal({ onDone, onSkip }) {
  const [logging, setLogging] = useState(false)
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')

  const login = async () => {
    setLogging(true)
    setError('')
    try {
      const r = await fetch('/api/tidal/login', { method: 'POST' }).then(r => r.json())
      if (r.url) {
        setUrl(r.url)
        fetch('/api/open-url', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url: r.url }) }).catch(() => {})
        const poll = setInterval(async () => {
          try {
            const c = await fetch('/api/tidal/login/complete', { method: 'POST' }).then(r => r.json())
            if (c.ok) { clearInterval(poll); setLogging(false); onDone() }
          } catch {}
        }, 2000)
        setTimeout(() => { clearInterval(poll); setLogging(false); setError('Timed out — try again.') }, 300000)
      } else {
        setLogging(false)
        setError(r.error || 'Failed to start Tidal login.')
      }
    } catch { setLogging(false); setError('Connection failed.') }
  }

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
      style={{ maxWidth: 420, width: '100%', textAlign: 'center' }}>
      <div style={{ marginBottom: 28 }}>
        <div style={{ width: 52, height: 52, borderRadius: 14, background: '#00FFFF18', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#00FFFF', margin: '0 auto 14px' }}>
          <svg width="26" height="26" viewBox="0 0 24 24" fill="currentColor"><path d="M12.012 3.992L8.008 7.996 4.004 3.992 0 7.996l4.004 4.004 4.004-4.004 4.004 4.004 4.004-4.004L20.02 12l4.004-4.004-4.004-4.004-4.004 4.004-4.004-4.004zM8.008 16.004L12.012 20.008 16.016 16.004 12.012 12 8.008 16.004z"/></svg>
        </div>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: '#f0f0f5', marginBottom: 8 }}>Connect Tidal</h2>
        <p style={{ fontSize: 13, color: 'rgba(240,240,245,0.45)', lineHeight: 1.6, maxWidth: 320, margin: '0 auto' }}>
          No credentials needed. Just log in with your Tidal account in the browser.
        </p>
      </div>

      {!logging ? (
        <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }} onClick={login}
          style={{
            width: '100%', padding: '16px 24px',
            background: `linear-gradient(135deg, ${V}, ${C})`,
            border: 'none', borderRadius: 16, color: '#fff',
            cursor: 'pointer', fontSize: 15, fontWeight: 700, fontFamily: 'inherit',
            boxShadow: `0 8px 32px rgba(139,92,246,0.3)`,
          }}>
          Log in with Tidal →
        </motion.button>
      ) : (
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
          style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 16, padding: 24 }}>
          <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1.2, ease: 'linear' }}
            style={{ width: 36, height: 36, border: `3px solid rgba(6,182,212,0.2)`, borderTopColor: C, borderRadius: '50%', margin: '0 auto 16px' }} />
          <p style={{ fontSize: 14, fontWeight: 600, color: '#f0f0f5', marginBottom: 6 }}>Authorize in your browser</p>
          <p style={{ fontSize: 12, color: 'rgba(240,240,245,0.4)', marginBottom: url ? 16 : 0 }}>Log in with Tidal in the window that opened.</p>
          {url && <CodeBox value={url} label="Or open this link manually" />}
        </motion.div>
      )}

      {error && <div style={{ fontSize: 13, color: '#f87171', marginTop: 12 }}>{error}</div>}

      <button onClick={onSkip} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(240,240,245,0.25)', fontSize: 12, fontFamily: 'inherit', marginTop: 20, width: '100%' }}>
        Skip for now
      </button>
    </motion.div>
  )
}

// ── Done ─────────────────────────────────────────────────────────────────────
function StepDone({ service, onFinish }) {
  return (
    <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}
      style={{ textAlign: 'center', maxWidth: 380 }}>
      <motion.div
        initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', stiffness: 200, damping: 12 }}
        style={{
          width: 80, height: 80, borderRadius: '50%', margin: '0 auto 24px',
          background: `linear-gradient(135deg, ${V}, ${C})`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: `0 0 48px rgba(139,92,246,0.4)`,
        }}>
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
      </motion.div>
      <h2 style={{ fontSize: 26, fontWeight: 800, color: '#f0f0f5', marginBottom: 10 }}>You're all set!</h2>
      <p style={{ fontSize: 14, color: 'rgba(240,240,245,0.5)', lineHeight: 1.7, marginBottom: 32 }}>
        {service === 'spotify' ? 'Spotify connected.' : 'Tidal connected.'} Search for any song, playlist or artist and download it instantly.
      </p>
      <motion.button whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.96 }} onClick={onFinish}
        style={{
          width: '100%', padding: '16px 24px',
          background: `linear-gradient(135deg, ${V}, ${C})`,
          border: 'none', borderRadius: 16, color: '#fff',
          cursor: 'pointer', fontSize: 16, fontWeight: 700, fontFamily: 'inherit',
          boxShadow: `0 8px 32px rgba(139,92,246,0.35)`,
        }}>
        Start using SONGER →
      </motion.button>
    </motion.div>
  )
}

// ── Main Onboarding ──────────────────────────────────────────────────────────
export default function OnboardingView({ onComplete }) {
  const [step, setStep] = useState('welcome') // welcome | choose | spotify | tidal | done
  const [service, setService] = useState(null)

  const STEP_MAP = { welcome: 0, choose: 1, spotify: 2, tidal: 2, done: 3 }
  const TOTAL_STEPS = 4

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 100,
      background: 'rgba(6,6,10,0.96)',
      backdropFilter: 'blur(20px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 24,
    }}>
      {/* Liquid blobs */}
      <motion.div animate={{ x: [0, 60, -30, 0], y: [0, -40, 60, 0], scale: [1, 1.1, 0.95, 1] }} transition={{ duration: 20, repeat: Infinity }}
        style={{ position: 'absolute', width: 400, height: 400, borderRadius: '50%', opacity: 0.12, background: `radial-gradient(circle, ${V}, transparent 70%)`, filter: 'blur(60px)', top: '-5%', left: '-5%', pointerEvents: 'none' }} />
      <motion.div animate={{ x: [0, -50, 40, 0], y: [0, 60, -40, 0], scale: [1, 0.9, 1.05, 1] }} transition={{ duration: 25, repeat: Infinity }}
        style={{ position: 'absolute', width: 350, height: 350, borderRadius: '50%', opacity: 0.10, background: `radial-gradient(circle, ${C}, transparent 70%)`, filter: 'blur(60px)', bottom: '-5%', right: '-5%', pointerEvents: 'none' }} />

      <div style={{ position: 'relative', zIndex: 1, width: '100%', maxWidth: 460, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <StepDots total={TOTAL_STEPS} current={STEP_MAP[step] || 0} />

        <AnimatePresence mode="wait">
          {step === 'welcome' && (
            <StepWelcome key="welcome" onNext={() => setStep('choose')} />
          )}
          {step === 'choose' && (
            <StepChooseService key="choose" onNext={(svc) => { setService(svc); setStep(svc) }} />
          )}
          {step === 'spotify' && (
            <StepSpotify key="spotify"
              onDone={() => setStep('done')}
              onSkip={() => setStep('done')} />
          )}
          {step === 'tidal' && (
            <StepTidal key="tidal"
              onDone={() => setStep('done')}
              onSkip={() => setStep('done')} />
          )}
          {step === 'done' && (
            <StepDone key="done" service={service} onFinish={onComplete} />
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
