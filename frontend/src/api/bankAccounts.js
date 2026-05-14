import client from './client'

export const bankAccountsAPI = {
  getBankAccounts() {
    return client.get('/bank-accounts/')
  },
  createBankAccount(data) {
    return client.post('/bank-accounts/', data)
  },
  updateBankAccount(id, data) {
    return client.patch(`/bank-accounts/${id}`, data)
  },
  deleteBankAccount(id) {
    return client.delete(`/bank-accounts/${id}`)
  }
}
