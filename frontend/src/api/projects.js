import client from './client'

export const projectsAPI = {
  getProjects: (year) => {
    const params = year ? { year } : {}
    return client.get('/projects/', { params })
  },

  getProject: (projectId) => {
    return client.get(`/projects/${projectId}`)
  },
  
  getNextNumber: () => {
    return client.get('/projects/next-number')
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

  /** Body: { user_id } — salary is pulled from the User profile by the backend */
  assignEmployee: (projectId, body) => {
    return client.post(`/projects/${projectId}/assign`, body)
  },

  getProjectSummary: (projectId) => {
    return client.get(`/projects/${projectId}/summary`)
  },

  getProjectBilling: (projectId) => {
    return client.get(`/projects/${projectId}/billing`)
  },

  /**
   * Query: billed_amount, partner_hourly_rate (optional).
   * Backend may require billed_amount on every call — callers should always pass current billed_amount.
   */
  patchProjectBilling: (projectId, params) => {
    return client.patch(`/projects/${projectId}/billing`, null, { params })
  },

  /** Returns reserve balance for all projects (accurate full calculation) */
  getReserveStatus: () => {
    return client.get('/projects/reserve-status')
  },

  /** Returns task-based projected cost breakdown for a project */
  getProjectedCost: (projectId) => {
    return client.get(`/projects/${projectId}/projected-cost`)
  },
}
