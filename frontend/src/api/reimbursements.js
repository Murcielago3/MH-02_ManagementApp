import client from './client'

export const reimbursementsAPI = {
  getReimbursements: (params) => {
    return client.get('/reimbursements/', { params })
  },

  getMyReimbursements: () => {
    return client.get('/reimbursements/my')
  },

  createReimbursement: (formData) => {
    // using formData for multipart/form-data
    return client.post('/reimbursements/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  actionReimbursement: (id, status) => {
    return client.patch(`/reimbursements/${id}/action`, { status })
  }
}
