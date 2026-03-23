import { useState, useEffect } from 'react'
import { api } from '../lib/api'

export function useSpotifyStatus() {
  const [status, setStatus] = useState({ spotify: false, soulseek: false })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.status().then(setStatus).catch(() => {}).finally(() => setLoading(false))
  }, [])

  return { ...status, loading }
}
