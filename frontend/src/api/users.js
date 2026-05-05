import client from './client'

export const usersAPI = {
  createUser: (userData) => {
    return client.post('/users', userData)
  },

  getUsers: () => {
    return client.get('/users')
  },

  getUser: (userId) => {
    return client.get(`/users/${userId}`)
  },

  updateUser: (userId, userData) => {
    return client.put(`/users/${userId}`, userData)
  },

  deleteUser: (userId) => {
    return client.delete(`/users/${userId}`)
  },
}
