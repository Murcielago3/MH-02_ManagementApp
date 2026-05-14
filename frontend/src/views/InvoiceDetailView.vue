<template>
  <AppLayout>
    <div class="page-header">
      <h2>Invoice Detail</h2>
      <div class="actions">
        <button class="btn-secondary" @click="goBack">Back</button>
        <button class="btn-primary" @click="downloadPDF">
          <span class="material-symbols-outlined">download</span> Download PDF
        </button>
        <button class="btn-danger" @click="confirmDelete">
          <span class="material-symbols-outlined">delete</span> Delete
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-state">Loading invoice...</div>
    <div v-else-if="!invoice" class="empty-state">Invoice not found.</div>
    <div v-else class="preview-container">
      <InvoicePreview :invoice="invoice" />
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
            <p>Are you sure you want to delete this invoice?</p>
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
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import InvoicePreview from '../components/InvoicePreview.vue'
import ToastNotification from '../components/ToastNotification.vue'
import { invoicesAPI } from '../api/invoices'

const route = useRoute()
const router = useRouter()
const invoice = ref(null)
const loading = ref(true)
const submitting = ref(false)
const deleteTarget = ref(null)

const toastMsg = ref('')
const toastType = ref('success')

const showToast = (msg, type = 'success') => {
  toastMsg.value = msg
  toastType.value = type
}

const fetchInvoice = async () => {
  const id = route.params.id
  loading.value = true
  try {
    const res = await invoicesAPI.getInvoice(id)
    invoice.value = res.data
  } catch (err) {
    showToast('Failed to load invoice details', 'error')
  } finally {
    loading.value = false
  }
}

onMounted(fetchInvoice)

const goBack = () => {
  router.push('/admin/invoices')
}

const downloadPDF = async () => {
  if (!invoice.value) return
  const id = invoice.value.id
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

const confirmDelete = () => {
  deleteTarget.value = true
}

const handleDelete = async () => {
  submitting.value = true
  try {
    await invoicesAPI.deleteInvoice(invoice.value.id)
    showToast('Invoice deleted')
    deleteTarget.value = null
    setTimeout(() => {
      router.push('/admin/invoices')
    }, 1000)
  } catch (err) {
    showToast('Failed to delete invoice', 'error')
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

.actions {
  display: flex;
  gap: 12px;
}

.btn-primary, .btn-secondary, .btn-danger {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius);
  font-family: var(--font-display);
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s, background 0.2s;
  border: none;
}

.btn-primary { background: var(--color-primary); color: white; }
.btn-primary:hover { opacity: 0.9; }

.btn-secondary { background: white; border: 1px solid var(--color-outline); color: var(--color-on-surface); }
.btn-secondary:hover { background: var(--color-surface-container); }

.btn-danger { background: var(--color-error); color: white; }
.btn-danger:hover { opacity: 0.9; }

.preview-container {
  background: var(--color-surface-container-lowest);
  padding: 32px 0;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-outline);
}

.loading-state, .empty-state {
  text-align: center;
  padding: 60px;
  color: var(--color-on-surface-variant);
  background: white;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-outline-variant);
}

/* Modals */
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}

.modal {
  background: white; width: 400px; max-width: 90vw;
  border-radius: var(--radius-lg); overflow: hidden;
}

.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid var(--color-outline-variant);
}

.modal-header h3 { margin: 0; font-family: var(--font-display); }
.icon-btn-close { background: none; border: none; cursor: pointer; color: var(--color-on-surface-variant); }
.modal-body { padding: 20px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; }
</style>
