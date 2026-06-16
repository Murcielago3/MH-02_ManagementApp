import client from './client'

export const salarySlipsAPI = {
  // Admin / manager
  getSlips: (params) => client.get('/salary-slips/', { params }),
  generate: (month) => client.post('/salary-slips/generate', { month: month || null }),
  updateSlip: (id, data) => client.patch(`/salary-slips/${id}`, data),
  approveSlip: (id) => client.patch(`/salary-slips/${id}/approve`),
  approveMonth: (month) => client.post('/salary-slips/approve-month', { month }),
  approveBulk: (ids) => client.post('/salary-slips/approve-bulk', { ids }),
  bulkSetTds: (ids, tds_percent) => client.post('/salary-slips/bulk-set-tds', { ids, tds_percent }),

  // Shared
  getSlip: (id) => client.get(`/salary-slips/${id}`),
  downloadPdf: (id) => client.get(`/salary-slips/${id}/pdf`, { responseType: 'blob' }),

  // Employee
  getMySlips: () => client.get('/salary-slips/my'),
}
