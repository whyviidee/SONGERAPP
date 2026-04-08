const BASE = ''

async function get(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

async function del(path) {
  const res = await fetch(`${BASE}${path}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

async function submitDownloads(list) {
  const results = []
  for (const t of list) {
    const body = {
      id: t.id || t.url || t.uri || '',
      name: t.name || t.title || '',
      artist: t.artists ? t.artists.map(a => a.name).join(', ') : (t.artist || ''),
      album: typeof t.album === 'object' ? (t.album?.name || '') : (t.album || ''),
      cover: t.cover || t.album?.images?.[0]?.url || '',
      uri: t.uri || t.url || '',
    }
    if (!body.id && !body.name) continue
    try {
      const r = await post('/api/download', body)
      results.push(r)
    } catch (e) { console.error('Download error:', e) }
  }
  return results
}

export const api = {
  status: () => get('/api/status'),
  stats: () => get('/api/stats'),
  config: () => get('/api/config'),

  search: (q) => get(`/api/search?q=${encodeURIComponent(q)}`),
  artist: (id) => get(`/api/artist/${id}`),
  album: (id) => get(`/api/album/${id}`),

  playlists: () => get('/api/playlists'),
  playlistTracks: (id) => get(`/api/playlists/${id}/tracks`),
  likedSongs: (offset = 0, limit = 50) => get(`/api/liked-songs?offset=${offset}&limit=${limit}`),

  download: async (tracksOrTrack, { skipExisting = true } = {}) => {
    const list = Array.isArray(tracksOrTrack) ? tracksOrTrack : [tracksOrTrack]

    if (skipExisting && list.length > 1) {
      try {
        const dlIds = await get('/api/downloaded-ids')
        const existing = new Set(dlIds.ids || [])
        const newTracks = list.filter(t => !existing.has(t.id || t.url))
        const dupeCount = list.length - newTracks.length

        if (dupeCount > 0 && newTracks.length > 0) {
          const choice = confirm(`${dupeCount} track(s) already downloaded. Skip them and download ${newTracks.length} new?\n\nOK = Skip existing\nCancel = Download ALL`)
          if (choice) return submitDownloads(newTracks)
        } else if (dupeCount > 0 && newTracks.length === 0) {
          if (!confirm('All tracks already downloaded. Download again?')) return []
        }
      } catch {}
    }

    return submitDownloads(list)
  },

  queue: () => get('/api/queue'),
  cancelJob: (id) => del(`/api/queue/${id}`),
  cancelAll: () => del('/api/queue'),
  downloadedIds: () => get('/api/downloaded-ids'),

  library: () => get('/api/library'),

  history: () => get('/api/history'),
  clearHistory: () => del('/api/history'),

  urlInfo: (url) => post('/api/url-info', { url }),
  downloadDirect: (track) => post('/api/download', {
    id: track.id,
    name: track.title,
    artist: track.artist,
    album: track.album || '',
    cover: track.cover_url || '',
    url: track.url,
    _source: 'direct',
  }),

  trending: () => get('/api/trending'),
  trendingRefresh: (key) => post(`/api/trending/${key}/refresh`),

  coverUrl: (url) => `/api/cover?url=${encodeURIComponent(url)}`,
  streamUrl: (path) => `/api/stream?path=${encodeURIComponent(path)}`,
  trackCoverUrl: (path) => `/api/track-cover?path=${encodeURIComponent(path)}`,
}
