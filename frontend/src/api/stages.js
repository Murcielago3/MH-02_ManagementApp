import client from './client'

export const stagesAPI = {
  // Every stage across all projects (studio-wide Stages board)
  listAll: () => client.get('/stages/all'),

  // Stages + derived amounts/hours + remaining bucket for a project
  list: (projectId) => client.get(`/projects/${projectId}/stages`),
  create: (projectId, data) => client.post(`/projects/${projectId}/stages`, data),
  update: (stageId, data) => client.patch(`/stages/${stageId}`, data),
  remove: (stageId) => client.delete(`/stages/${stageId}`),

  // Stage subtasks (the studio-wide project todo list)
  listSubtasks: (projectId, openOnly = false) =>
    client.get(`/projects/${projectId}/stage-subtasks`, { params: { open_only: openOnly } }),
  createSubtask: (stageId, data) => client.post(`/stages/${stageId}/subtasks`, data),
  updateSubtask: (subtaskId, data) => client.patch(`/stage-subtasks/${subtaskId}`, data),
  removeSubtask: (subtaskId) => client.delete(`/stage-subtasks/${subtaskId}`),

  // Subtask deadlines for the employee calendar
  myDeadlines: (params) => client.get('/my/stage-subtask-deadlines', { params }),
}
