import client from './client'

export const teamsAPI = {
  // Admin
  listProjectTeams: (projectId) => client.get(`/projects/${projectId}/teams`),
  createTeam: (projectId) => client.post(`/projects/${projectId}/teams`),
  updateTeam: (projectId, teamId, body) => client.patch(`/projects/${projectId}/teams/${teamId}`, body),
  deleteTeam: (projectId, teamId) => client.delete(`/projects/${projectId}/teams/${teamId}`),
  addMember: (projectId, teamId, userId) =>
    client.post(`/projects/${projectId}/teams/${teamId}/members`, { user_id: userId }),
  removeMember: (projectId, teamId, memberId) =>
    client.delete(`/projects/${projectId}/teams/${teamId}/members/${memberId}`),

  // Employee
  getMyTeamForProject: (projectId) => client.get(`/me/projects/${projectId}/team`),
}
