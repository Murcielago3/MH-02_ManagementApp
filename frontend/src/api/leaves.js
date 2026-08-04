import client from './client'

export const leavesAPI = {
  getLeaves: () => {
    return client.get('/leaves/')
  },

  getMyLeaves: () => {
    return client.get('/leaves/my')
  },

  createLeave: (data) => {
    return client.post('/leaves/', data)
  },

  actionLeave: (leaveId, status) => {
    return client.patch(`/leaves/${leaveId}/action`, { status })
  },

  // Admin records an absence for an employee who didn't apply for leave.
  markAbsent: (data) => {
    return client.post('/leaves/mark-absent', data)
  },

  // Overtime (comp-off) leave earned from weekday 12h+/14h+ days and Saturday work (8h+ = 1, under 8h = ½).
  getMyOvertime: () => {
    return client.get('/leaves/overtime/my')
  },

  getOvertime: (employeeId) => {
    return client.get('/leaves/overtime', { params: { employee_id: employeeId } })
  },
}