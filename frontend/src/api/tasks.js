import client from './client'

export const tasksAPI = {
  getTasks: (params) => {
    return client.get('/tasks/', { params })
  },

  getMyTasks: (params) => {
    return client.get('/tasks/my', { params })
  },

  /**
   * Fetch calendar tasks. Pass either a date range (preferred) or year+month.
   * - opts.startDate / opts.endDate: 'YYYY-MM-DD' strings
   * - opts.year / opts.month: legacy fallback
   * - opts.employeeId: optional filter
   */
  getCalendarTasks: (opts = {}) => {
    const params = {}
    if (opts.startDate && opts.endDate) {
      params.start_date = opts.startDate
      params.end_date = opts.endDate
    } else if (opts.year && opts.month) {
      params.year = opts.year
      params.month = opts.month
    }
    if (opts.employeeId) params.employee_id = opts.employeeId
    return client.get('/tasks/calendar', { params })
  },

  createTask: (data) => {
    return client.post('/tasks/', data)
  },

  bulkAssign: (data) => {
    return client.post('/tasks/bulk-assign', data)
  },

  updateTask: (taskId, data) => {
    return client.put(`/tasks/${taskId}`, data)
  },

  patchTask: (taskId, data) => {
    return client.patch(`/tasks/${taskId}`, data)
  },

  updateTaskStatus: (taskId, status) => {
    return client.patch(`/tasks/${taskId}/status`, { status })
  },

  deleteTask: (taskId) => {
    return client.delete(`/tasks/${taskId}`)
  },
}