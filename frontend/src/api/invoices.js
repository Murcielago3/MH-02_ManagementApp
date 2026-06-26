import client from './client'

export const invoicesAPI = {
  getInvoices() {
    return client.get('/invoices/')
  },
  getInvoice(id) {
    return client.get(`/invoices/${id}`)
  },
  createInvoice(data) {
    return client.post('/invoices/', data)
  },
  updateInvoice(id, data) {
    return client.put(`/invoices/${id}`, data)
  },
  deleteInvoice(id) {
    return client.delete(`/invoices/${id}`)
  },
  downloadPDF(id) {
    return client.get(`/invoices/${id}/pdf`, { responseType: 'blob' })
  },
  // Returns the exact HTML used to render the PDF (admin-only). The detail
  // view srcdocs this into an iframe so the preview can never drift from the
  // downloaded PDF.
  getPreviewHTML(id) {
    return client.get(`/invoices/${id}/preview-html`, { responseType: 'text' })
  }
}
