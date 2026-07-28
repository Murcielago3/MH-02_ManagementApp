import client from './client'

export const reportsAPI = {
  // Omit employeeId for the studio-wide roll-up (adds a per-employee breakdown).
  quarterly: ({ fyYear, quarter, employeeId } = {}) =>
    client.get('/reports/quarterly', {
      params: {
        fy_year: fyYear ?? undefined,
        quarter: quarter ?? undefined,
        employee_id: employeeId ?? undefined,
      },
    }),
  availableQuarters: () => client.get('/reports/quarterly/available'),
}
