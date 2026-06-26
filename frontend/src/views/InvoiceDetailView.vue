<template>
  <AppLayout>
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">
          <span class="material-symbols-outlined">arrow_back</span>
        </button>
        <div>
          <h1 class="page-title">Invoice Detail</h1>
          <p class="page-subtitle">View and manage this invoice</p>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn-outline" @click="editInvoice">
          <span class="material-symbols-outlined">edit</span>
          Edit
        </button>
        <button class="btn-outline" @click="downloadPDF">
          <span class="material-symbols-outlined">download</span>
          Download PDF
        </button>
        <button class="btn-danger-outline" @click="confirmDelete">
          <span class="material-symbols-outlined">delete</span>
          Delete
        </button>
      </div>
    </div>

    <!-- States -->
    <div v-if="loading" class="state-card">
      <span class="material-symbols-outlined spin-icon">progress_activity</span>
      <span>Loading invoice…</span>
    </div>
    <div v-else-if="!invoice" class="state-card">
      <span class="material-symbols-outlined empty-icon">receipt_long</span>
      <span>Invoice not found.</span>
    </div>

    <!-- Preview: renders the exact HTML used to generate the PDF in an iframe
         (iframe sandboxes the invoice's global CSS resets from the app shell). -->
    <div v-else class="preview-wrap">
      <iframe
        v-if="previewHTML"
        :srcdoc="previewHTML"
        class="invoice-iframe"
        title="Invoice preview"
      />
      <div v-else class="state-card">
        <span class="material-symbols-outlined spin-icon">progress_activity</span>
        <span>Loading preview…</span>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <Teleport to="body">
      <div v-if="deleteTarget" class="modal-backdrop">
        <div class="modal">
          <div class="modal-header">
            <div class="modal-icon-wrap danger">
              <span class="material-symbols-outlined">delete_forever</span>
            </div>
            <button class="modal-close" @click="deleteTarget = null">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <div class="modal-body">
            <h3 class="modal-title">Delete Invoice</h3>
            <p class="modal-desc">
              Are you sure you want to permanently delete this invoice?
              This action cannot be undone.
            </p>
          </div>
          <div class="modal-footer">
            <button class="btn-outline" @click="deleteTarget = null">Cancel</button>
            <button class="btn-danger" :disabled="submitting" @click="handleDelete">
              <span v-if="submitting" class="material-symbols-outlined spin-icon">progress_activity</span>
              {{ submitting ? 'Deleting…' : 'Delete Invoice' }}
            </button>
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
import ToastNotification from '../components/ToastNotification.vue'
import { invoicesAPI } from '../api/invoices'

const route = useRoute()
const router = useRouter()
const invoice = ref(null)
const previewHTML = ref('')
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
    // Pull the invoice metadata (for buttons/header) and the rendered preview
    // HTML in parallel — the HTML drives the iframe; the JSON drives controls.
    const [res, htmlRes] = await Promise.all([
      invoicesAPI.getInvoice(id),
      invoicesAPI.getPreviewHTML(id),
    ])
    invoice.value = res.data
    previewHTML.value = htmlRes.data
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

const editInvoice = () => {
  if (invoice.value) {
    router.push(`/admin/invoices/${invoice.value.id}/edit`)
  }
}

const downloadPDF = async () => {
  if (!invoice.value) return
  const id = invoice.value.id
  try {
    const res = await invoicesAPI.downloadPDF(id)
    const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
    const a = document.createElement('a')
    a.href = url
    // Name the file as the invoice number (matches server's Content-Disposition).
    const number = invoice.value.invoice_number
    a.download = number ? `${number}.pdf` : `proforma_${id}.pdf`
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
/* ── Page Header ── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
  gap: 16px;
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-outline);
  background: var(--color-surface);
  color: var(--color-on-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s, color 0.15s;
}
.back-btn:hover { background: var(--color-surface-dim); color: var(--color-on-surface); }
.back-btn .material-symbols-outlined { font-size: 20px; }

.page-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 800;
  color: var(--color-on-surface);
  margin: 0 0 2px;
  letter-spacing: -0.01em;
}
.page-subtitle {
  margin: 0;
  font-size: 13px;
  color: var(--color-on-surface-variant);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* ── Buttons ── */
.btn-outline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-surface);
  cursor: pointer;
  transition: background 0.15s;
}
.btn-outline:hover { background: var(--color-surface-dim); }
.btn-outline .material-symbols-outlined { font-size: 17px; }

.btn-danger-outline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 16px;
  background: var(--color-surface);
  border: 1px solid #fca5a5;
  border-radius: var(--radius-lg);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-error);
  cursor: pointer;
  transition: background 0.15s;
}
.btn-danger-outline:hover { background: #fef2f2; }
.btn-danger-outline .material-symbols-outlined { font-size: 17px; }

/* ── State Cards ── */
.state-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 72px 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-xl);
  text-align: center;
  color: var(--color-on-surface-variant);
  font-size: 14px;
  box-shadow: var(--shadow-sm);
}
.empty-icon { font-size: 40px; opacity: 0.3; }

/* ── Spinner ── */
.spin-icon { animation: spin 0.8s linear infinite; font-size: 32px; color: var(--color-primary); }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Invoice Preview Wrapper ── */
.preview-wrap {
  background: var(--color-surface-dim);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-xl);
  padding: 36px 24px;
  box-shadow: var(--shadow-sm);
}

/* Sized for an A4-ratio invoice (~210/297 ≈ 0.707). The iframe loads the same
   HTML the server feeds WeasyPrint, so what's shown here IS the PDF. */
.invoice-iframe {
  display: block;
  margin: 0 auto;
  width: 100%;
  max-width: 820px;
  aspect-ratio: 210 / 297;
  border: 1px solid var(--color-outline);
  background: white;
  box-shadow: var(--shadow-md);
}

/* ── Modal ── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.modal {
  background: var(--color-surface);
  width: 420px;
  max-width: 100%;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px 24px 0;
}

.modal-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-icon-wrap.danger { background: #fef2f2; color: var(--color-error); }
.modal-icon-wrap .material-symbols-outlined { font-size: 24px; }

.modal-close {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-on-surface-variant);
  padding: 4px;
  border-radius: var(--radius-md);
  line-height: 1;
}
.modal-close:hover { background: var(--color-surface-dim); }
.modal-close .material-symbols-outlined { font-size: 20px; }

.modal-body { padding: 16px 24px 0; }
.modal-title {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 800;
  margin: 0 0 8px;
  color: var(--color-on-surface);
}
.modal-desc {
  font-size: 14px;
  color: var(--color-on-surface-variant);
  line-height: 1.55;
  margin: 0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 24px;
}

.btn-danger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
  background: var(--color-error);
  color: #fff;
  border: none;
  border-radius: var(--radius-lg);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}
.btn-danger:hover { opacity: 0.88; }
.btn-danger:disabled { opacity: 0.55; cursor: not-allowed; }

@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; gap: 10px; }
  .header-actions { flex-wrap: wrap; width: 100%; }
  .preview-wrap { padding: 12px; overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .modal { max-width: 100%; width: 100%; }
  .modal-backdrop { padding: 8px; }
}
</style>
