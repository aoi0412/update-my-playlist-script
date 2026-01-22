import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || ''

const client = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface Playlist {
  id: number
  url: string
  name: string
  platform: string
  check_interval_hours: number
  is_active: boolean
  last_checked_at: string | null
  created_at: string
  updated_at: string
  track_count: number
}

export interface Track {
  id: number
  playlist_id: number
  external_id: string
  title: string
  artist: string | null
  duration_seconds: number | null
  thumbnail_url: string | null
  first_seen_at: string
  playlist_name?: string
}

export interface DownloadHistory {
  id: number
  track_id: number
  status: 'pending' | 'downloading' | 'completed' | 'failed'
  file_path: string | null
  file_size_bytes: number | null
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
  track: Track
}

export interface DownloadStats {
  total_downloads: number
  completed_downloads: number
  failed_downloads: number
  pending_downloads: number
  total_file_size_bytes: number
}

export interface SchedulerStatus {
  running: boolean
  job_count: number
  jobs: Array<{
    id: string
    name: string
    next_run_time: string | null
  }>
}

// API functions
export const api = {
  // Playlists
  getPlaylists: () => client.get<Playlist[]>('/api/playlists'),
  getPlaylist: (id: number) => client.get<Playlist & { tracks: Track[] }>(`/api/playlists/${id}`),
  createPlaylist: (data: { url: string; name?: string; check_interval_hours?: number }) =>
    client.post<Playlist>('/api/playlists', data),
  updatePlaylist: (id: number, data: { name?: string; check_interval_hours?: number; is_active?: boolean }) =>
    client.put<Playlist>(`/api/playlists/${id}`, data),
  deletePlaylist: (id: number) => client.delete(`/api/playlists/${id}`),
  checkPlaylistUpdates: (id: number) =>
    client.post<{ message: string; new_tracks: Array<{ id: number; title: string }> }>(`/api/playlists/${id}/check`),

  // Downloads
  getDownloadHistory: (params?: { limit?: number; offset?: number; status?: string; playlist_id?: number }) =>
    client.get<DownloadHistory[]>('/api/downloads', { params }),
  getDownloadStats: () => client.get<DownloadStats>('/api/downloads/stats'),
  downloadTrack: (trackId: number) => client.post<DownloadHistory>(`/api/downloads/track/${trackId}`),
  retryDownload: (downloadId: number) => client.post<DownloadHistory>(`/api/downloads/${downloadId}/retry`),

  // Scheduler
  getSchedulerStatus: () => client.get<SchedulerStatus>('/api/scheduler/status'),
  pauseScheduler: () => client.post('/api/scheduler/pause'),
  resumeScheduler: () => client.post('/api/scheduler/resume'),
}

export default client
