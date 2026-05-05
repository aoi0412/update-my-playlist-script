import { useEffect, useRef, useState } from 'react'
import {
  CheckCircle,
  XCircle,
  Clock,
  Download,
  RefreshCw,
  Filter,
} from 'lucide-react'
import { api, DownloadHistory, Playlist } from '../api/client'
import { format } from 'date-fns'
import { ja } from 'date-fns/locale'

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

export default function HistoryPage() {
  const [downloads, setDownloads] = useState<DownloadHistory[]>([])
  const [playlists, setPlaylists] = useState<Playlist[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [playlistFilter, setPlaylistFilter] = useState<string>('')
  const [retryingId, setRetryingId] = useState<number | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  // Refs always hold the latest filter values, avoiding stale closures in the interval
  const statusFilterRef = useRef(statusFilter)
  const playlistFilterRef = useRef(playlistFilter)
  statusFilterRef.current = statusFilter
  playlistFilterRef.current = playlistFilter

  useEffect(() => {
    let isCurrent = true

    async function fetchData(showLoading = true) {
      if (showLoading) setLoading(true)
      try {
        const currentStatus = statusFilterRef.current
        const currentPlaylist = playlistFilterRef.current
        const params: Record<string, string | number> = { limit: 100 }
        if (currentStatus) params.status = currentStatus
        if (currentPlaylist) params.playlist_id = Number(currentPlaylist)

        const [downloadsRes, playlistsRes] = await Promise.all([
          api.getDownloadHistory(params),
          api.getPlaylists(),
        ])

        if (!isCurrent) return
        setDownloads(downloadsRes.data)
        setPlaylists(playlistsRes.data)
      } catch (error) {
        if (!isCurrent) return
        console.error('Failed to fetch history:', error)
      } finally {
        if (isCurrent) setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(() => fetchData(false), 3000)
    return () => {
      isCurrent = false
      clearInterval(interval)
    }
  }, [statusFilter, playlistFilter, refreshKey])

  async function handleRetry(downloadId: number) {
    setRetryingId(downloadId)
    try {
      await api.retryDownload(downloadId)
      setRefreshKey((k) => k + 1)
    } catch (error) {
      console.error('Failed to retry download:', error)
      alert('Failed to retry download')
    } finally {
      setRetryingId(null)
    }
  }

  function getStatusIcon(status: string) {
    switch (status) {
      case 'completed':
        return <CheckCircle className="text-green-600" size={20} />
      case 'failed':
        return <XCircle className="text-red-600" size={20} />
      case 'downloading':
        return <RefreshCw className="text-blue-600 animate-spin" size={20} />
      default:
        return <Clock className="text-yellow-600" size={20} />
    }
  }

  function getStatusBadge(status: string) {
    const styles: Record<string, string> = {
      completed: 'bg-green-100 text-green-700',
      failed: 'bg-red-100 text-red-700',
      downloading: 'bg-blue-100 text-blue-700',
      pending: 'bg-yellow-100 text-yellow-700',
    }
    return styles[status] || 'bg-gray-100 text-gray-700'
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Download History</h1>
        <button
          onClick={() => setRefreshKey((k) => k + 1)}
          className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
        >
          <RefreshCw size={20} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex items-center gap-4">
          <Filter className="text-gray-500" size={20} />
          <div className="flex gap-4">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Status</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="downloading">Downloading</option>
              <option value="pending">Pending</option>
            </select>
            <select
              value={playlistFilter}
              onChange={(e) => setPlaylistFilter(e.target.value)}
              className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Playlists</option>
              {playlists.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* History Table */}
      <div className="bg-white rounded-lg shadow overflow-x-auto">
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-pulse">Loading...</div>
          </div>
        ) : downloads.length === 0 ? (
          <div className="p-8 text-center">
            <Download className="mx-auto text-gray-400 mb-4" size={48} />
            <h2 className="text-lg font-semibold mb-2">No downloads yet</h2>
            <p className="text-gray-500">
              Downloads will appear here once playlists are checked.
            </p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Track
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Playlist
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Duration
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Size
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {downloads.map((download) => {
                if (!download.track) return null;
                return (
                  <tr key={download.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(download.status)}
                      <span
                        className={`px-2 py-1 text-xs rounded-full ${getStatusBadge(
                          download.status
                        )}`}
                      >
                        {download.status}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      {download.track.thumbnail_url && (
                        <img
                          src={download.track.thumbnail_url}
                          alt=""
                          className="w-10 h-10 rounded object-cover"
                        />
                      )}
                      <div>
                        <p className="font-medium truncate max-w-xs">
                          {download.track.title}
                        </p>
                        {download.track.artist && (
                          <p className="text-sm text-gray-500 truncate max-w-xs">
                            {download.track.artist}
                          </p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {download.track.playlist_name}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {download.track.duration_seconds
                      ? formatDuration(download.track.duration_seconds)
                      : '-'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {download.file_size_bytes
                      ? formatBytes(download.file_size_bytes)
                      : '-'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {download.completed_at
                      ? format(new Date(download.completed_at), 'yyyy/MM/dd HH:mm', {
                          locale: ja,
                        })
                      : '-'}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {download.status === 'completed' && download.file_path && (
                        <a
                          href={`/api/downloads/files/${encodeURIComponent(
                            download.file_path.split('/').pop() || ''
                          )}`}
                          className="p-2 hover:bg-blue-100 rounded-lg transition-colors"
                          title="Download file"
                        >
                          <Download className="text-blue-600" size={18} />
                        </a>
                      )}
                      {download.status === 'failed' && (
                        <button
                          onClick={() => handleRetry(download.id)}
                          disabled={retryingId === download.id}
                          className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
                          title="Retry download"
                        >
                          <RefreshCw
                            className={`text-gray-600 ${
                              retryingId === download.id ? 'animate-spin' : ''
                            }`}
                            size={18}
                          />
                        </button>
                      )}
                    </div>
                  </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Error Messages */}
      {downloads.some((d) => d.status === 'failed' && d.error_message) && (
        <div className="mt-6 bg-red-50 rounded-lg p-4">
          <h3 className="font-semibold text-red-700 mb-2">Error Details</h3>
          <ul className="space-y-2">
            {downloads
              .filter((d) => d.status === 'failed' && d.error_message)
              .map((d) => (
                <li key={d.id} className="text-sm text-red-600">
                  <strong>{d.track.title}:</strong> {d.error_message}
                </li>
              ))}
          </ul>
        </div>
      )}
    </div>
  )
}
