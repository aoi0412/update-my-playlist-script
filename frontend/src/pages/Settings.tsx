import React, { useState, useEffect, useRef } from 'react'
import { UploadCloud, CheckCircle, FileText, AlertCircle } from 'lucide-react'
import { api } from '../api/client'

export default function Settings() {
  const [cookiesStatus, setCookiesStatus] = useState<boolean>(false)
  const [isUploading, setIsUploading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  
  const fileInputRef = useRef<HTMLInputElement>(null)

  const fetchStatus = async () => {
    try {
      const res = await api.getCookiesStatus()
      setCookiesStatus(res.data.exists)
    } catch (e) {
      console.error("Failed to fetch cookies status", e)
    }
  }

  useEffect(() => {
    fetchStatus()
  }, [])

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.name.endsWith('.txt')) {
      setError('Only .txt files are allowed (cookies.txt).')
      return
    }

    setIsUploading(true)
    setError(null)
    setSuccessMsg(null)

    try {
      await api.uploadCookies(file)
      setSuccessMsg('cookies.txt uploaded successfully!')
      setCookiesStatus(true)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload cookies file.')
    } finally {
      setIsUploading(false)
      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Settings</h1>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-8">
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2 mb-2">
            YouTube Authentication
          </h2>
          <p className="text-gray-500 text-sm">
            Upload your cookies.txt file to allow the downloader to access age-restricted videos and personalized playlists like "Liked Music" on YouTube Music.
          </p>
        </div>

        <div className="flex flex-col md:flex-row gap-6">
          <div className="flex-1">
            <div
              className="border-2 border-dashed border-gray-300 rounded-xl p-8 flex flex-col items-center justify-center text-center hover:bg-gray-50 transition-colors cursor-pointer"
              onClick={() => fileInputRef.current?.click()}
            >
              <UploadCloud className="w-12 h-12 text-blue-500 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-1">
                Upload cookies.txt
              </h3>
              <p className="text-sm text-gray-500 mb-4 max-w-xs">
                Click here to browse for your exported Netscape cookies file.
              </p>
              
              <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                accept=".txt"
                onChange={handleFileChange}
              />
              
              <button 
                className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition"
                disabled={isUploading}
              >
                {isUploading ? 'Uploading...' : 'Select File'}
              </button>
            </div>
          </div>
          
          <div className="flex-1 flex flex-col justify-center">
            <div className="bg-gray-50 rounded-xl p-6 border border-gray-100 h-full flex flex-col justify-center">
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-4">Current Status</h3>
              
              {cookiesStatus ? (
                <div className="flex items-center gap-3 text-green-600">
                  <CheckCircle className="w-8 h-8" />
                  <div>
                    <p className="font-semibold text-lg">Cookies Active</p>
                    <p className="text-sm text-green-700">Ready to download restricted and liked songs.</p>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-3 text-amber-600">
                  <FileText className="w-8 h-8" />
                  <div>
                    <p className="font-semibold text-lg">No Cookies Found</p>
                    <p className="text-sm text-amber-700">Downloads will be limited to public videos.</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-lg flex items-center gap-2 border border-red-100">
            <AlertCircle size={20} />
            <p>{error}</p>
          </div>
        )}

        {successMsg && (
          <div className="mt-4 p-4 bg-green-50 text-green-700 rounded-lg flex items-center gap-2 border border-green-100">
            <CheckCircle size={20} />
            <p>{successMsg}</p>
          </div>
        )}
      </div>

    </div>
  )
}
