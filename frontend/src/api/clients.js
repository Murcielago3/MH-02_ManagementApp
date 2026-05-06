import client from './client'

export const clientsAPI = {
  getClients: () => {
    return client.get('/clients/')
  },

  getClient: (clientId) => {
    return client.get(`/clients/${clientId}`)
  },

  createClient: (data) => {
    return client.post('/clients/', data)
  },

  updateClient: (clientId, data) => {
    return client.patch(`/clients/${clientId}`, data)
  },

  deleteClient: (clientId) => {
    return client.delete(`/clients/${clientId}`)
  },
}
