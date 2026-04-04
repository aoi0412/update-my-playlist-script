import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Music, Download, CheckCircle, XCircle, Clock, HardDrive } from 'lucide-react'
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

  useEffect(() => {
    let isMounted = true

    async function fetchData(showLoading = true) {
      if (showLoading && loading) setLoading(true)
      try {
        const [playlistsRes, statsRes, downloadsRes, schedulerRes] = await Promise.all([
          api.getPlaylists(),
          api.getDownloadStats(),
          api.getDownloadHistory({ limit: 5 }),
          api.getSchedulerStatus(),
        ])
        if (isMounted) {
          setPlaylists(playlistsRes.data)
          setStats(statsRes.data)
          setRecentDownloads(downloadsRes.data)
          setSchedulerStatus(schedulerRes.data)
        }
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(() => fetchData(false), 3000)
    return () => {
      isMounted = false
      clearInterval(interval)
    }
  }, [])

  if (loading) {
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

      {/* Stats Cards */}
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Downloads */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b flex justify-between items-center">
            <h2 className="font-semibold">Recent Downloads</h2>
            <Link to="/history" className="text-sm text-blue-600 hover:underline">
              View all
            </Link>
          </div>
          <div className="p-4">
            {recentDownloads.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No downloads yet</p>
            ) : (
              <ul className="space-y-3">
                {recentDownloads.map((download) => (
                  <li key={download.id} className="flex items-center gap-3">
                    <div
                      className={`p-2 rounded-full ${
                        download.status === 'completed'
                          ? 'bg-green-100'
                          : download.status === 'failed'
                          ? 'bg-red-100'
                          : 'bg-yellow-100'
                      }`}
                    >
                      {download.status === 'completed' ? (
                        <CheckCircle className="text-green-600" size={16} />
                      ) : download.status === 'failed' ? (
                        <XCircle className="text-red-600" size={16} />
                      ) : (
                        <Clock className="text-yellow-600" size={16} />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{download.track.title}</p>
                      <p className="text-sm text-gray-500 truncate">
                        {download.track.artist || download.track.playlist_name}
                      </p>
                    </div>
                    <span className="text-xs text-gray-400">
                      {download.completed_at &&
                        formatDistanceToNow(new Date(download.completed_at), {
                          addSuffix: true,
                          locale: ja,
                        })}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Scheduler Status */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b">
            <h2 className="font-semibold">Scheduler Status</h2>
          </div>
          <div className="p-4">
            <div className="flex items-center gap-2 mb-4">
              <span
                className={`w-3 h-3 rounded-full ${
                  schedulerStatus?.running ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
              <span className="font-medium">
                {schedulerStatus?.running ? 'Running' : 'Stopped'}
              </span>
              <span className="text-gray-500">
                ({schedulerStatus?.job_count || 0} jobs)
              </span>
            </div>

            {schedulerStatus?.jobs && schedulerStatus.jobs.length > 0 && (
              <ul className="space-y-2">
                {schedulerStatus.jobs.map((job) => (
                  <li key={job.id} className="text-sm">
                    <p className="font-medium">{job.name}</p>
                    <p className="text-gray-500">
                      Next run:{' '}
                      {job.next_run_time
                        ? formatDistanceToNow(new Date(job.next_run_time), {
                            addSuffix: true,
                            locale: ja,
                          })
                        : 'Not scheduled'}
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
