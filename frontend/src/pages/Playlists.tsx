import { useEffect, useState } from 'react'
import {
  Plus,
  RefreshCw,
  Trash2,
  Music,
  ExternalLink,
  ToggleLeft,
  ToggleRight,
  Settings,
} from 'lucide-react'
import { api, Playlist } from '../api/client'
import { formatDistanceToNow } from 'date-fns'
import { ja } from 'date-fns/locale'

export default function Playlists() {
  const [playlists, setPlaylists] = useState<Playlist[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newUrl, setNewUrl] = useState('')
  const [newName, setNewName] = useState('')
  const [newInterval, setNewInterval] = useState(24)
  const [submitting, setSubmitting] = useState(false)
  const [checkingId, setCheckingId] = useState<number | null>(null)
  const [newDownloadDir, setNewDownloadDir] = useState('')
  const [editingPlaylistId, setEditingPlaylistId] = useState<number | null>(null)
  const [editDownloadDir, setEditDownloadDir] = useState('')
  const [directories, setDirectories] = useState<string[]>([])

  async function fetchPlaylists() {
    try {
      const response = await api.getPlaylists()
      setPlaylists(response.data)
    } catch (error) {
      console.error('Failed to fetch playlists:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPlaylists()
    fetchDirectories()
  }, [])

  async function fetchDirectories() {
    try {
      const response = await api.getDirectories()
      const dirs = response.data.directories
      setDirectories(dirs)
      setNewDownloadDir(prev => prev || dirs[0] || '')
    } catch (error) {
      console.error('Failed to fetch directories:', error)
    }
  }

  async function handleAddPlaylist(e: React.FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    try {
      await api.createPlaylist({
        url: newUrl,
        name: newName || undefined,
        check_interval_hours: newInterval,
        download_dir: newDownloadDir || undefined,
      })
      setNewUrl('')
      setNewName('')
      setNewInterval(24)
      setNewDownloadDir('')
      setShowAddForm(false)
      await fetchPlaylists()
    } catch (error) {
      console.error('Failed to add playlist:', error)
      alert('Failed to add playlist. Please check the URL.')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('Are you sure you want to delete this playlist?')) return
    try {
      await api.deletePlaylist(id)
      await fetchPlaylists()
    } catch (error) {
      console.error('Failed to delete playlist:', error)
    }
  }

  async function handleToggleActive(playlist: Playlist) {
    try {
      await api.updatePlaylist(playlist.id, { is_active: !playlist.is_active })
      await fetchPlaylists()
    } catch (error) {
      console.error('Failed to update playlist:', error)
    }
  }

  async function handleUpdateDownloadDir(playlistId: number) {
    try {
      await api.updatePlaylist(playlistId, { download_dir: editDownloadDir })
      setEditingPlaylistId(null)
      await fetchPlaylists()
    } catch (error) {
      console.error('Failed to update download directory:', error)
      alert('Failed to update download directory')
    }
  }

  async function handleCheckUpdates(id: number) {
    setCheckingId(id)
    try {
      const response = await api.checkPlaylistUpdates(id)
      alert(response.data.message)
      await fetchPlaylists()
    } catch (error) {
      console.error('Failed to check updates:', error)
      alert('Failed to check for updates')
    } finally {
      setCheckingId(null)
    }
  }

  function getPlatformColor(platform: string) {
    return platform === 'youtube_music' ? 'bg-red-100 text-red-700' : 'bg-orange-100 text-orange-700'
  }

  function getPlatformLabel(platform: string) {
    return platform === 'youtube_music' ? 'YouTube Music' : 'SoundCloud'
  }

  if (loading) {
    return (
      <div className="p-8">
        <div className="animate-pulse">Loading...</div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Playlists</h1>
        <button
          onClick={() => setShowAddForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={20} />
          Add Playlist
        </button>
      </div>

      {/* Add Playlist Form */}
      {showAddForm && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Add New Playlist</h2>
          <form onSubmit={handleAddPlaylist} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                Playlist URL <span className="text-red-500">*</span>
              </label>
              <input
                type="url"
                value={newUrl}
                onChange={(e) => setNewUrl(e.target.value)}
                placeholder="https://music.youtube.com/playlist?list=... or https://soundcloud.com/..."
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Name (optional)
              </label>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Custom playlist name"
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Check Interval (hours)
              </label>
              <select
                value={newInterval}
                onChange={(e) => setNewInterval(Number(e.target.value))}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value={1}>Every hour</option>
                <option value={6}>Every 6 hours</option>
                <option value={12}>Every 12 hours</option>
                <option value={24}>Every day</option>
                <option value={48}>Every 2 days</option>
                <option value={168}>Every week</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Download Directory
              </label>
              <div className="flex gap-2">
                <select
                  value={newDownloadDir}
                  onChange={(e) => setNewDownloadDir(e.target.value)}
                  className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {directories.map((dir) => (
                    <option key={dir} value={dir}>{dir}</option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={async () => {
                    const name = prompt('Enter new directory name (e.g. "Anime" or "Anime/OST"):')
                    if (name) {
                      try {
                        const res = await api.createDirectory({ name })
                        await fetchDirectories()
                        setNewDownloadDir(res.data.directory)
                      } catch (err) {
                        alert('Failed to create directory')
                      }
                    }
                  }}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors whitespace-nowrap"
                >
                  + New
                </button>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {submitting ? 'Adding...' : 'Add Playlist'}
              </button>
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Playlist List */}
      {playlists.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <Music className="mx-auto text-gray-400 mb-4" size={48} />
          <h2 className="text-lg font-semibold mb-2">No playlists yet</h2>
          <p className="text-gray-500 mb-4">
            Add your first playlist to start monitoring and downloading music.
          </p>
          <button
            onClick={() => setShowAddForm(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus size={20} />
            Add Playlist
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {playlists.map((playlist) => (
            <div
              key={playlist.id}
              className={`bg-white rounded-lg shadow p-6 ${
                !playlist.is_active ? 'opacity-60' : ''
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold">{playlist.name}</h3>
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${getPlatformColor(
                        playlist.platform
                      )}`}
                    >
                      {getPlatformLabel(playlist.platform)}
                    </span>
                    {!playlist.is_active && (
                      <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full">
                        Paused
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 mb-2 truncate max-w-xl">
                    {playlist.url}
                  </p>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span>{playlist.track_count} tracks</span>
                    <span>Check every {playlist.check_interval_hours}h</span>
                    {playlist.last_checked_at && (
                      <span>
                        Last checked:{' '}
                        {formatDistanceToNow(new Date(playlist.last_checked_at), {
                          addSuffix: true,
                          locale: ja,
                        })}
                      </span>
                    )}
                  </div>
                  {editingPlaylistId === playlist.id ? (
                    <div className="mt-3 flex items-center gap-2 flex-wrap">
                      <select
                        value={editDownloadDir}
                        onChange={(e) => setEditDownloadDir(e.target.value)}
                        className="flex-1 px-3 py-1 text-sm border rounded min-w-[200px]"
                      >
                        {directories.map((dir) => (
                          <option key={dir} value={dir}>{dir}</option>
                        ))}
                      </select>
                      <button
                        type="button"
                        onClick={async () => {
                          const name = prompt('Enter new directory name:')
                          if (name) {
                            try {
                              const res = await api.createDirectory({ name })
                              await fetchDirectories()
                              setEditDownloadDir(res.data.directory)
                            } catch (err) {
                              alert('Failed to create directory')
                            }
                          }
                        }}
                        className="px-2 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 whitespace-nowrap"
                        title="Create New Directory"
                      >
                        + New
                      </button>
                      <button
                        onClick={() => handleUpdateDownloadDir(playlist.id)}
                        className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => setEditingPlaylistId(null)}
                        className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    playlist.download_dir && (
                      <p className="mt-2 text-sm text-gray-600 bg-gray-50 px-2 py-1 rounded inline-block">
                        Download to: <span className="font-mono">{playlist.download_dir}</span>
                      </p>
                    )
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleToggleActive(playlist)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    title={playlist.is_active ? 'Pause monitoring' : 'Resume monitoring'}
                  >
                    {playlist.is_active ? (
                      <ToggleRight className="text-green-600" size={24} />
                    ) : (
                      <ToggleLeft className="text-gray-400" size={24} />
                    )}
                  </button>
                  <button
                    onClick={() => handleCheckUpdates(playlist.id)}
                    disabled={checkingId === playlist.id}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
                    title="Check for updates now"
                  >
                    <RefreshCw
                      className={`text-blue-600 ${
                        checkingId === playlist.id ? 'animate-spin' : ''
                      }`}
                      size={20}
                    />
                  </button>
                  <a
                    href={playlist.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    title="Open playlist"
                  >
                    <ExternalLink className="text-gray-600" size={20} />
                  </a>
                  <button
                    onClick={() => {
                      setEditingPlaylistId(playlist.id)
                      setEditDownloadDir(playlist.download_dir || '')
                    }}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    title="Edit settings"
                  >
                    <Settings className="text-gray-600" size={20} />
                  </button>
                  <button
                    onClick={() => handleDelete(playlist.id)}
                    className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                    title="Delete playlist"
                  >
                    <Trash2 className="text-red-600" size={20} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
