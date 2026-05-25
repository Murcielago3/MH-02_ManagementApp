import client from './client'

export const settingsAPI = {
  get: () => client.get('/settings/'),
  update: (data) => client.patch('/settings/', data),
}
