import client from './client'

const getApiBaseUrl = () => {
  const envUrl = import.meta.env.VITE_API_URL
  if (envUrl && !envUrl.includes('localhost') && !envUrl.includes('127.0.0.1')) {
    return envUrl
  }
  if (typeof window !== 'undefined' && window.location) {
    return `${window.location.protocol}//${window.location.hostname}:8000`
  }
  return 'http://localhost:8000'
}

const API_BASE_URL = getApiBaseUrl()

export const usersAPI = {
  createUser: (userData) => {
    return client.post('/users/', userData)
  },

  getUsers: () => {
    return client.get('/users/')
  },

  getMe: () => {
    return client.get('/users/me')
  },

  getUser: (userId) => {
    return client.get(`/users/${userId}`)
  },

  updateUser: (userId, userData) => {
    return client.patch(`/users/${userId}`, userData)
  },

  deleteUser: (userId) => {
    return client.delete(`/users/${userId}`)
  },

  /** Upload a profile photo. `file` is a File object from an <input type="file"> */
  uploadPhoto: (userId, file) => {
    const fd = new FormData()
    fd.append('file', file)
    return client.post(`/users/${userId}/upload-photo`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /** Upload a document. doc_type: 'aadhar' | 'pan' | 'other' */
  uploadDocument: (userId, file, docType) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('doc_type', docType)
    return client.post(`/users/${userId}/upload-document`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /** Get all uploaded documents for a user */
  getDocuments: (userId) => {
    return client.get(`/users/${userId}/documents`)
  },

  /** Delete a specific document by type */
  deleteDocument: (userId, docType) => {
    return client.delete(`/users/${userId}/documents/${docType}`)
  },

  /** Resolve a relative /static/... URL to an absolute URL */
  resolveFileUrl: (relativeUrl) => {
    if (!relativeUrl) return null
    if (relativeUrl.startsWith('http')) return relativeUrl
    // Static files are served at the root by Nginx, not under /api
    const origin = typeof window !== 'undefined' ? window.location.origin : API_BASE_URL
    return `${origin}${relativeUrl}`
  },
}
