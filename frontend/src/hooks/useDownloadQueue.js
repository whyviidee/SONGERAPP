import { useState, useEffect, useCallback } from 'react'
import { api } from '../lib/api'
import { useSSE } from './useSSE'

export function useDownloadQueue() {
  const [jobs, setJobs] = useState([])

  const refresh = useCallback(() => {
    api.queue().then((data) => {
      // API returns either a list directly or {queue: [...]}
      const list = Array.isArray(data) ? data : (data.queue || [])
      setJobs(list)
    }).catch(() => {})
  }, [])

  useEffect(() => { refresh() }, [refresh])

  // Listen for ALL SSE events related to queue
  useSSE((event) => {
    if (event.type === 'progress' || event.type === 'done' || event.type === 'error' || event.type === 'queue_update') {
      refresh()
    }
  })

  return { jobs, refresh }
}
