import client from './client'

export const tasksAPI = {
  getTasks: (params) => {
    return client.get('/tasks/', { params })
  },

  getCalendarTasks: (year, month, employeeId) => {
    const params = { year, month }
    if (employeeId) params.employee_id = employeeId
    return client.get('/tasks/calendar', { params })
  },

  createTask: (data) => {
    return client.post('/tasks/', data)
  },

  updateTask: (taskId, data) => {
    return client.put(`/tasks/${taskId}`, data)
  },

  updateTaskStatus: (taskId, status) => {
    return client.patch(`/tasks/${taskId}/status`, { status })
  },

  deleteTask: (taskId) => {
    return client.delete(`/tasks/${taskId}`)
  },
}