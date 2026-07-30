import client from './client'

export const exportsAPI = {
  // Single entity → CSV blob
  exportCsv: (entity) => client.get(`/exports/${entity}.csv`, { responseType: 'blob' }),
  // Multiple entities → zip blob
  exportBundle: (types) => client.get('/exports/bundle', { params: { types: types.join(',') }, responseType: 'blob' }),
  // Months that have salary slips (newest first), for the CA sheet picker
  salaryMonths: () => client.get('/exports/salary-months'),
  // CA Salary Sheet for one 'YYYY-MM' month → CSV blob
  caSalarySheet: (month) => client.get('/exports/ca-salary-sheet.csv', { params: { month }, responseType: 'blob' }),
}

/** Trigger a browser download for a blob response. */
export function downloadBlob(res, fallbackName) {
  // Filename from Content-Disposition when present
  const cd = res.headers?.['content-disposition'] || ''
  const m = cd.match(/filename="?([^";]+)"?/)
  const name = m ? m[1] : fallbackName
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = url
  a.download = name
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
