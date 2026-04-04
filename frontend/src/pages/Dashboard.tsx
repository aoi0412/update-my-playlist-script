import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Music, CheckCircle, XCircle, Clock, RefreshCw, HardDrive } from 'lucide-react'
import { api, Playlist, DownloadHistory, DownloadStats, SchedulerStatus } from '../api/client'
import { formatDistanceToNow } from 'date-fns'
import { ja } from 'date-fns/locale'

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export default function Dashboard() {
  const [playlists, setPlaylists] = useState<Playlist[]>([])
  const [stats, setStats] = useState<DownloadStats | null>(null)
  const [recentDownloads, setRecentDownloads] = useState<DownloadHistory[]>([])
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [retryingId, setRetryingId] = useState<number | null>(null)

  async function fetchData(showLoading = true) {
    if (showLoading) setLoading(true)
    try {
      const [playlistsRes, statsRes, downloadsRes, schedulerRes] = await Promise.all([
        api.getPlaylists(),
        api.getDownloadStats(),
        api.getDownloadHistory({ limit: 10 }),
        api.getSchedulerStatus(),
      ])
      setPlaylists(playlistsRes.data)
      setStats(statsRes.data)
      setRecentDownloads(downloadsRes.data)
      setSchedulerStatus(schedulerRes.data)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(() => fetchData(false), 3000)
    return () => clearInterval(interval)
  }, [])

  const handleRetry = async (downloadId: number) => {
    setRetryingId(downloadId)
    try {
      await api.retryDownload(downloadId)
      await fetchData(false)
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

  if (loading && !recentDownloads.length) {
    return (
      <div className="p-8">
        <div className="animate-pulse">Loading...</div>
      </div>
    )
  }

  const activePlaylists = playlists.filter((p) => p.is_active)

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Music className="text-blue-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500">Active Playlists</p>
              <p className="text-2xl font-bold">{activePlaylists.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle className="text-green-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500">Completed Downloads</p>
              <p className="text-2xl font-bold">{stats?.completed_downloads || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-red-100 rounded-lg">
              <XCircle className="text-red-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500">Failed Downloads</p>
              <p className="text-2xl font-bold">{stats?.failed_downloads || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-purple-100 rounded-lg">
              <HardDrive className="text-purple-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Size</p>
              <p className="text-2xl font-bold">{formatBytes(stats?.total_file_size_bytes || 0)}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <h2 className="text-xl font-semibold mb-4">Recent Downloads</h2>
          <div className="bg-white rounded-lg shadow overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Track</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Playlist</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {recentDownloads.map((download) => (
                  <tr key={download.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(download.status)}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-medium truncate max-w-xs">{download.track.title}</p>
                      <p className="text-xs text-gray-500">{download.track.artist}</p>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">{download.track.playlist_name}</td>
                    <td className="px-6 py-4">
                      {download.status === 'failed' && (
                        <button
                          onClick={() => handleRetry(download.id)}
                          disabled={retryingId === download.id}
                          className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
                          title="Retry"
                        >
                          <RefreshCw size={18} className={retryingId === download.id ? 'animate-spin' : ''} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b">
            <h2 className="font-semibold">Scheduler Status</h2>
          </div>
          <div className="p-4">
            <div className="flex items-center gap-2 mb-4">
              <span className={`w-3 h-3 rounded-full ${schedulerStatus?.running ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="font-medium">{schedulerStatus?.running ? 'Running' : 'Stopped'}</span>
            </div>
            {schedulerStatus?.jobs && (
              <ul className="space-y-2">
                {schedulerStatus.jobs.map((job) => (
                  <li key={job.id} className="text-sm">
                    <p className="font-medium">{job.name}</p>
                    <p className="text-gray-500">
                      Next: {job.next_run_time ? formatDistanceToNow(new Date(job.next_run_time), { addSuffix: true, locale: ja }) : 'N/A'}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
