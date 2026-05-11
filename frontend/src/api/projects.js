import client from './client'

export const projectsAPI = {
  getProjects: (year) => {
    const params = year ? { year } : {}
    return client.get('/projects/', { params })
  },

  getProject: (projectId) => {
    return client.get(`/projects/${projectId}`)
  },

  createProject: (data) => {
    return client.post('/projects/', data)
  },

  updateProject: (projectId, data) => {
    return client.patch(`/projects/${projectId}`, data)
  },

  deleteProject: (projectId) => {
    return client.delete(`/projects/${projectId}`)
  },

  assignUser: (projectId, userId) => {
    return client.post(`/projects/${projectId}/assign`, { user_id: userId })
  },
}
