import client from './client'

export const estimatesAPI = {
  getEstimates: () => client.get('/estimates/'),
  getEstimate: (id) => client.get(`/estimates/${id}`),
  createEstimate: (data) => client.post('/estimates/', data),
  updateEstimate: (id, data) => client.put(`/estimates/${id}`, data),
  deleteEstimate: (id) => client.delete(`/estimates/${id}`),
}
