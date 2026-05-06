import client from './client'

export const dashboardAPI = {
  getStats: () => {
    return client.get('/dashboard/stats')
  },
}
