import client from './client'

export const weeklyTimesheetsAPI = {
  getTimesheets(params) {
    return client.get('/weekly-timesheets/', { params })
  },
  getMyTimesheets() {
    return client.get('/weekly-timesheets/my')
  },
  getPendingWeeks() {
    return client.get('/weekly-timesheets/pending-weeks')
  },
  submitTimesheet(payload) {
    return client.post('/weekly-timesheets/', payload)
  },
  getTimesheet(id) {
    return client.get(`/weekly-timesheets/${id}`)
  },
  actionTimesheet(id, actionPayload) {
    return client.patch(`/weekly-timesheets/${id}/action`, actionPayload)
  }
}
