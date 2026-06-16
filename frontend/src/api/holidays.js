import client from './client'

export const holidaysAPI = {
  getHolidays: () => client.get('/holidays/'),
  createHoliday: (data) => client.post('/holidays/', data),
  deleteHoliday: (id) => client.delete(`/holidays/${id}`),
}
