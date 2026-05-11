import client from './client'

export const attendanceAPI = {
  getAttendance: (params = {}) => {
    return client.get('/attendance/', { params })
  },

  getTodayAttendance: () => {
    return client.get('/attendance/today')
  },
}