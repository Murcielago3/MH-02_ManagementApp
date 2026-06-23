import client from './client'

export const subtasksAPI = {
  list: (taskId) => client.get(`/tasks/${taskId}/subtasks/`),
  create: (taskId, data) => client.post(`/tasks/${taskId}/subtasks/`, data),
  patch: (subtaskId, data) => client.patch(`/subtasks/${subtaskId}`, data),
  remove: (subtaskId) => client.delete(`/subtasks/${subtaskId}`),
}
