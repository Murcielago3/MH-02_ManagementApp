import client from './client'

export const timesheetsAPI = {
  getTimesheets: (params) => {
    return client.get('/timesheets/', { params })
  },
  
  getMyTimesheets: () => {
    return client.get('/timesheets/my')
  }
}
