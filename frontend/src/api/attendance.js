import client from './client'

export const attendanceAPI = {
  getAttendance: (params = {}) => {
    return client.get('/attendance/', { params })
  },

  getTodayAttendance: () => {
    return client.get('/attendance/today')
  },

  getMyAttendance: () => {
    return client.get('/attendance/my')
  },

  checkIn: (data) => {
    return client.post('/attendance/checkin', data)
  },

  checkOut: () => {
    return client.patch('/attendance/checkout')
  },
}