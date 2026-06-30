import client from './client'

export const salaryAPI = {
  // Roster of employees + project_managers with current salary/rate
  employees: () => client.get('/salary/employees'),
  history: (userId) => client.get(`/salary/${userId}/history`),
  increment: (userId, data) => client.post(`/salary/${userId}/increment`, data),
  editPeriod: (periodId, data) => client.patch(`/salary/period/${periodId}`, data),
  deletePeriod: (periodId) => client.delete(`/salary/period/${periodId}`),
}
