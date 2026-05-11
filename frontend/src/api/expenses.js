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
}