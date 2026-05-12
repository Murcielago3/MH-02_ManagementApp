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
}