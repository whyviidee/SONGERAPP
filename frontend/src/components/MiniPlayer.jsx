import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { IoPlay, IoPause, IoClose } from 'react-icons/io5'
import { api } from '../lib/api'

export default function MiniPlayer({ track, onClose }) {
  const [playing, setPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [seeking, setSeeking] = useState(false)
  const audioRef = useRef(null)
  const barRef = useRef(null)
  const rafRef = useRef(null)

  // Update time via requestAnimationFrame for smooth progress
  const updateTime = useCallback(() => {
    const audio = audioRef.current
    if (audio && !seeking) {
      setCurrentTime(audio.currentTime)
      if (audio.duration && !isNaN(audio.duration)) {
        setDuration(audio.duration)
      }
    }
    rafRef.current = requestAnimationFrame(updateTime)
  }, [seeking])

  useEffect(() => {
    rafRef.current = requestAnimationFrame(updateTime)
    return () => cancelAnimationFrame(rafRef.current)
  }, [updateTime])

  // Load track
  useEffect(() => {
    if (!track) return
    const audio = audioRef.current
    if (!audio) return

    const src = track.path ? api.streamUrl(track.path) : ''
    if (!src) return

    setCurrentTime(0)
    setDuration(0)
    setPlaying(false)

    audio.src = src
    audio.preload = 'auto'

    const onCanPlay = () => {
      audio.play().then(() => setPlaying(true)).catch(() => {})
    }
    const onLoadedMeta = () => {
      if (audio.duration && !isNaN(audio.duration) && isFinite(audio.duration)) {
        setDuration(audio.duration)
      }
    }
    const onDurationChange = () => {
      if (audio.duration && !isNaN(audio.duration) && isFinite(audio.duration)) {
        setDuration(audio.duration)
      }
    }
    const onEnded = () => { setPlaying(false); setCurrentTime(0) }

    audio.addEventListener('canplay', onCanPlay)
    audio.addEventListener('loadedmetadata', onLoadedMeta)
    audio.addEventListener('durationchange', onDurationChange)
    audio.addEventListener('ended', onEnded)

    audio.load()

    return () => {
      audio.removeEventListener('canplay', onCanPlay)
      audio.removeEventListener('loadedmetadata', onLoadedMeta)
      audio.removeEventListener('durationchange', onDurationChange)
      audio.removeEventListener('ended', onEnded)
      audio.pause()
      audio.removeAttribute('src')
    }
  }, [track])

  const togglePlay = () => {
    const audio = audioRef.current
    if (!audio) return
    if (playing) { audio.pause(); setPlaying(false) }
    else { audio.play().then(() => setPlaying(true)).catch(() => {}) }
  }

  const seekToPosition = useCallback((clientX) => {
    const bar = barRef.current
    const audio = audioRef.current
    if (!bar || !audio || !duration) return
    const rect = bar.getBoundingClientRect()
    const pct = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width))
    const newTime = pct * duration
    audio.currentTime = newTime
    setCurrentTime(newTime)
  }, [duration])

  const handleBarClick = (e) => {
    seekToPosition(e.clientX)
  }

  const handleMouseDown = (e) => {
    e.preventDefault()
    setSeeking(true)
    seekToPosition(e.clientX)

    const onMove = (ev) => {
      ev.preventDefault()
      seekToPosition(ev.clientX)
    }
    const onUp = (ev) => {
      seekToPosition(ev.clientX)
      setSeeking(false)
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
  }

  const fmt = (s) => {
    if (!s || isNaN(s) || !isFinite(s)) return '0:00'
    const m = Math.floor(s / 60)
    const sec = Math.floor(s % 60)
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  if (!track) return null

  const coverUrl = track.cover ? api.coverUrl(track.cover) : (track.path ? api.trackCoverUrl(track.path) : null)
  const pct = duration > 0 ? (currentTime / duration) * 100 : 0

  return (
    <AnimatePresence>
      <motion.div
        initial={{ y: 40, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 40, opacity: 0 }}
        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
        style={{
          position: 'fixed', bottom: 100, left: 0, right: 0,
          display: 'flex', justifyContent: 'center', zIndex: 45, pointerEvents: 'none',
        }}
      >
        <div style={{
          display: 'flex', alignItems: 'center', gap: 12, padding: '12px 18px',
          background: 'rgba(15,15,25,0.95)', backdropFilter: 'blur(24px)', WebkitBackdropFilter: 'blur(24px)',
          border: '1px solid rgba(255,255,255,0.1)', borderRadius: 22,
          boxShadow: '0 12px 40px rgba(0,0,0,0.6), 0 0 30px rgba(139,92,246,0.1)',
          width: 420, pointerEvents: 'auto',
        }}>
          <audio ref={audioRef} />

          {coverUrl ? (
            <img src={coverUrl} alt="" style={{ width: 44, height: 44, borderRadius: 12, objectFit: 'cover', flexShrink: 0 }} onError={(e) => e.target.style.display = 'none'} />
          ) : (
            <div style={{ width: 44, height: 44, borderRadius: 12, background: 'rgba(139,92,246,0.15)', flexShrink: 0 }} />
          )}

          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#f0f0f5', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {track.name || track.title}
            </div>
            <div style={{ fontSize: 11, color: 'rgba(240,240,245,0.4)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: 1 }}>
              {track.artists?.map(a => a.name).join(', ') || track.artist}
            </div>
            {/* Seek bar */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6 }}>
              <span style={{ fontSize: 9, color: 'rgba(240,240,245,0.4)', fontVariantNumeric: 'tabular-nums', width: 30, textAlign: 'right' }}>{fmt(currentTime)}</span>
              <div
                ref={barRef}
                onClick={handleBarClick}
                onMouseDown={handleMouseDown}
                style={{ flex: 1, height: 20, display: 'flex', alignItems: 'center', cursor: 'pointer', position: 'relative', touchAction: 'none' }}
              >
                <div style={{ position: 'absolute', left: 0, right: 0, height: 4, borderRadius: 2, background: 'rgba(255,255,255,0.1)' }} />
                <div style={{ position: 'absolute', left: 0, width: `${pct}%`, height: 4, borderRadius: 2, background: 'linear-gradient(90deg, #8b5cf6, #06b6d4)', transition: seeking ? 'none' : 'width 0.15s' }} />
                <div style={{
                  position: 'absolute', left: `calc(${pct}% - 6px)`,
                  width: 12, height: 12, borderRadius: 6,
                  background: '#fff', boxShadow: '0 2px 8px rgba(0,0,0,0.4)',
                  transition: seeking ? 'none' : 'left 0.15s',
                }} />
              </div>
              <span style={{ fontSize: 9, color: 'rgba(240,240,245,0.4)', fontVariantNumeric: 'tabular-nums', width: 30 }}>{fmt(duration)}</span>
            </div>
          </div>

          <motion.button whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.85 }} onClick={togglePlay}
            style={{ background: 'linear-gradient(135deg, #8b5cf6, #06b6d4)', border: 'none', borderRadius: 12, width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', cursor: 'pointer', flexShrink: 0 }}>
            {playing ? <IoPause size={16} /> : <IoPlay size={16} style={{ marginLeft: 2 }} />}
          </motion.button>

          <motion.button whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.85 }}
            onClick={() => { const a = audioRef.current; if (a) { a.pause(); a.removeAttribute('src') }; setPlaying(false); onClose() }}
            style={{ background: 'none', border: 'none', color: 'rgba(240,240,245,0.3)', cursor: 'pointer', flexShrink: 0, padding: 4 }}>
            <IoClose size={16} />
          </motion.button>
        </div>
      </motion.div>
    </AnimatePresence>
  )
}
