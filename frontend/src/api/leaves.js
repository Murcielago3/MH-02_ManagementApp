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

  // Overtime (comp-off) leave earned from 11h+/13h+ days.
  getMyOvertime: () => {
    return client.get('/leaves/overtime/my')
  },

  getOvertime: (employeeId) => {
    return client.get('/leaves/overtime', { params: { employee_id: employeeId } })
  },
}