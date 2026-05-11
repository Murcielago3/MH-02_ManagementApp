import client from './client'

export const leavesAPI = {
  getLeaves: () => {
    return client.get('/leaves/')
  },

  actionLeave: (leaveId, status) => {
    return client.patch(`/leaves/${leaveId}/action`, { status })
  },
}