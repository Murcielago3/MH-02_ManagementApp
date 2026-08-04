import client from './client'

export const expensesAPI = {
  getExpenses: (category) => {
    const params = category ? { category } : {}
    return client.get('/expenses/', { params })
  },

  createExpense: (data) => {
    return client.post('/expenses/', data)
  },

  updateExpense: (expenseId, data) => {
    return client.patch(`/expenses/${expenseId}`, data)
  },

  deleteExpense: (expenseId) => {
    return client.delete(`/expenses/${expenseId}`)
  },

  // ── Parties (vendors) ──
  getParties: () => client.get('/expenses/parties'),
  createParty: (data) => client.post('/expenses/parties', data),
  updateParty: (id, data) => client.patch(`/expenses/parties/${id}`, data),
  deleteParty: (id) => client.delete(`/expenses/parties/${id}`),

  // ── Payments (bills paid in parts) ──
  getPayments: (expenseId) => client.get(`/expenses/${expenseId}/payments`),
  addPayment: (expenseId, data) => client.post(`/expenses/${expenseId}/payments`, data),
  deletePayment: (paymentId) => client.delete(`/expenses/payments/${paymentId}`),
}