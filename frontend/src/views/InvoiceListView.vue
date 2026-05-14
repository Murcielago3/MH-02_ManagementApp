<template>
  <AppLayout>
    <div class="page-header">
      <h2>Invoices</h2>
      <router-link to="/admin/invoices/new" class="btn-primary">
        <span class="material-symbols-outlined">add</span>
        New Invoice
      </router-link>
    </div>

    <div class="table-card">
      <table class="data-table">
        <thead>
          <tr>
            <th>Invoice #</th>
            <th>Type</th>
            <th>Date</th>
            <th>Client</th>
            <th>Subject</th>
            <th class="text-right">Total</th>
            <th class="text-center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="7" class="text-center loading-text">Loading invoices...</td>
          </tr>
          <tr v-else-if="invoices.length === 0">
            <td colspan="7" class="text-center empty-state">No invoices yet. Create your first invoice.</td>
          </tr>
          <tr v-for="inv in invoices" :key="inv.id">
            <td class="font-mono">{{ inv.invoice_type === 'tax' ? inv.invoice_number : '—' }}</td>
            <td>
              <span class="badge" :class="inv.invoice_type === 'tax' ? 'badge-teal' : 'badge-grey'">
                {{ inv.invoice_type === 'tax' ? 'Tax Invoice' : 'Proforma' }}
              </span>
            </td>
            <td>{{ formatDate(inv.invoice_date) }}</td>
            <td class="font-medium">{{ inv.bill_to_name || '—' }}</td>
            <td class="text-muted">{{ inv.subject || '—' }}</td>
            <td class="text-right font-mono font-medium">₹{{ formatAmount(inv.total) }}</td>
            <td class="actions-cell text-center">
              <router-link :to="`/admin/invoices/${inv.id}`" class="icon-btn" title="View">
                <span class="material-symbols-outlined">visibility</span>
              </router-link>
              <button class="icon-btn" @click="downloadPDF(inv.id)" title="Download PDF">
                <span class="material-symbols-outlined">download</span>
              </button>
              <button class="icon-btn text-danger" @click="confirmDelete(inv)" title="Delete">
                <span class="material-symbols-outlined">delete</span>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Delete Confirmation Modal -->
    <Teleport to="body">
      <div v-if="deleteTarget" class="modal-backdrop" @click.self="deleteTarget = null">
        <div class="modal delete-modal">
          <div class="modal-header">
            <h3>Delete Invoice</h3>
            <button class="icon-btn-close" @click="deleteTarget = null">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <div class="modal-body">
            <p>Are you sure you want to delete this invoice ({{ deleteTarget.invoice_type === 'tax' ? deleteTarget.invoice_number : 'Proforma' }})?</p>
            <div class="modal-footer">
              <button class="btn-secondary" @click="deleteTarget = null">Cancel</button>
              <button class="btn-danger" :disabled="submitting" @click="handleDelete">
                {{ submitting ? 'Deleting...' : 'Delete' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <ToastNotification v-if="toastMsg" :message="toastMsg" :type="toastType" @done="toastMsg = ''" />
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import ToastNotification from '../components/ToastNotification.vue'
import { invoicesAPI } from '../api/invoices'

const invoices = ref([])
const loading = ref(true)
const submitting = ref(false)
const deleteTarget = ref(null)

const toastMsg = ref('')
const toastType = ref('success')

const showToast = (msg, type = 'success') => {
  toastMsg.value = msg
  toastType.value = type
}

const fetchInvoices = async () => {
  loading.value = true
  try {
    const res = await invoicesAPI.getInvoices()
    invoices.value = res.data.sort((a, b) => new Date(b.created_at || b.invoice_date) - new Date(a.created_at || a.invoice_date))
  } catch (err) {
    showToast('Failed to load invoices', 'error')
  } finally {
    loading.value = false
  }
}

onMounted(fetchInvoices)

const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-GB')
}

const formatAmount = (val) => {
  return Number(val || 0).toLocaleString('en-IN')
}

const downloadPDF = async (id) => {
  try {
    const res = await invoicesAPI.downloadPDF(id)
    const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `invoice_${id}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    showToast('Failed to download PDF', 'error')
  }
}

const confirmDelete = (inv) => {
  deleteTarget.value = inv
}

const handleDelete = async () => {
  if (!deleteTarget.value) return
  submitting.value = true
  try {
    await invoicesAPI.deleteInvoice(deleteTarget.value.id)
    showToast('Invoice deleted')
    deleteTarget.value = null
    fetchInvoices()
  } catch (err) {
    showToast('Failed to delete invoice', 'error')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  font-family: var(--font-display);
  font-size: 24px;
  margin: 0;
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--color-primary);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: var(--radius);
  font-family: var(--font-display);
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-primary:hover {
  opacity: 0.9;
}

.table-card {
  background: white;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th, .data-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--color-outline-variant);
}

.data-table th {
  background: var(--color-surface-container);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-on-surface-variant);
  font-weight: 600;
}

.data-table tr:hover {
  background: var(--color-background);
}

.text-right { text-align: right; }
.text-center { text-align: center; }
.font-mono { font-family: 'Courier New', Courier, monospace; }
.font-medium { font-weight: 600; }
.text-muted { color: var(--color-on-surface-variant); }

.badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.badge-teal {
  background: #e0f2f1;
  color: #00796b;
}

.badge-grey {
  background: var(--color-surface-container-high);
  color: var(--color-on-surface-variant);
}

.actions-cell {
  display: flex;
  justify-content: center;
  gap: 8px;
}

.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-on-surface-variant);
  padding: 4px;
  border-radius: 4px;
}

.icon-btn:hover {
  background: var(--color-surface-container);
  color: var(--color-primary);
}

.text-danger:hover {
  color: var(--color-error);
  background: #ffdad6;
}

.empty-state, .loading-text {
  padding: 40px;
  color: var(--color-on-surface-variant);
}

/* Modals */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  width: 400px;
  max-width: 90vw;
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-outline-variant);
}

.modal-header h3 {
  margin: 0;
  font-family: var(--font-display);
}

.icon-btn-close {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-on-surface-variant);
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.btn-secondary {
  padding: 8px 16px;
  background: white;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius);
  cursor: pointer;
}

.btn-secondary:hover {
  background: var(--color-surface-container);
}

.btn-danger {
  padding: 8px 16px;
  background: var(--color-error);
  color: white;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
}

.btn-danger:hover {
  opacity: 0.9;
}
</style>
