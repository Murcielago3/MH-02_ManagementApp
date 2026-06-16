<template>
  <AppLayout>
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">Invoices</h1>
        <p class="page-subtitle">Manage and download all generated invoices</p>
      </div>
      <router-link to="/admin/invoices/new" class="btn-primary">
        <span class="material-symbols-outlined">add</span>
        New Invoice
      </router-link>
    </div>

    <!-- Drafts Section -->
    <div v-if="hasDrafts" class="drafts-card">
      <div class="drafts-header">
        <div class="drafts-header-left">
          <span class="material-symbols-outlined drafts-icon">edit_note</span>
          <span class="drafts-title">Saved Drafts</span>
          <span class="drafts-count">{{ drafts.length }}</span>
        </div>
      </div>
      <div class="drafts-list">
        <div v-for="d in drafts" :key="d.id" class="draft-item">
          <div class="draft-info">
            <span class="draft-label">{{ d.label }}</span>
            <span class="draft-meta">Last edited {{ formatDraftDate(d.updatedAt) }}</span>
          </div>
          <div class="draft-actions">
            <router-link :to="{ path: '/admin/invoices/new', query: { draft: d.id } }" class="draft-resume-btn">
              <span class="material-symbols-outlined">edit</span>
              Resume
            </router-link>
            <button class="draft-delete-btn" @click="handleDeleteDraft(d.id)" title="Delete draft">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Table Card -->
    <div class="table-card">
      <table class="data-table">
        <thead>
          <tr>
            <th>Invoice #</th>
            <th>Type</th>
            <th>Date</th>
            <th>Client</th>
            <th>Project</th>
            <th class="text-right">Total</th>
            <th class="text-center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="7" class="state-cell">
              <span class="material-symbols-outlined spin-icon">progress_activity</span>
              Loading invoices…
            </td>
          </tr>
          <tr v-else-if="invoices.length === 0">
            <td colspan="7" class="state-cell">
              <span class="material-symbols-outlined empty-icon">receipt_long</span>
              <span>No invoices yet. <router-link to="/admin/invoices/new" class="inline-link">Create your first invoice</router-link></span>
            </td>
          </tr>
          <tr v-for="inv in invoices" :key="inv.id" class="data-row">
            <td class="font-mono inv-num">{{ inv.invoice_type === 'tax' ? inv.invoice_number : '—' }}</td>
            <td>
              <span class="badge" :class="inv.invoice_type === 'tax' ? 'badge-teal' : 'badge-grey'">
                {{ inv.invoice_type === 'tax' ? 'Tax Invoice' : 'Proforma' }}
              </span>
            </td>
            <td class="text-muted">{{ formatDate(inv.invoice_date) }}</td>
            <td class="font-medium">{{ inv.bill_to_name || '—' }}</td>
            <td class="text-muted">{{ inv.project?.name || inv.subject || '—' }}</td>
            <td class="text-right font-mono font-medium">₹{{ formatAmount(inv.total) }}</td>
            <td class="text-center">
              <div class="action-group">
                <router-link :to="`/admin/invoices/${inv.id}`" class="icon-btn" title="View">
                  <span class="material-symbols-outlined">visibility</span>
                </router-link>
                <button class="icon-btn" @click="downloadPDF(inv.id)" title="Download PDF">
                  <span class="material-symbols-outlined">download</span>
                </button>
                <button class="icon-btn icon-btn--danger" @click="confirmDelete(inv)" title="Delete">
                  <span class="material-symbols-outlined">delete</span>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Delete Confirmation Modal -->
    <Teleport to="body">
      <div v-if="deleteTarget" class="modal-backdrop" @click.self="deleteTarget = null">
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
              Are you sure you want to permanently delete
              <strong>{{ deleteTarget.invoice_type === 'tax' ? deleteTarget.invoice_number : 'this Proforma' }}</strong>?
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
import AppLayout from '../components/AppLayout.vue'
import ToastNotification from '../components/ToastNotification.vue'
import { invoicesAPI } from '../api/invoices'
import { useInvoiceDrafts } from '../composables/useInvoiceDrafts'

const { drafts, hasDrafts, deleteDraft, refresh: refreshDrafts } = useInvoiceDrafts()

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
    invoices.value = res.data.sort((a, b) => {
      const numA = parseInt((a.invoice_number || '0').replace(/\D/g, '')) || 0
      const numB = parseInt((b.invoice_number || '0').replace(/\D/g, '')) || 0
      if (numB !== numA) return numB - numA
      return new Date(b.created_at || b.invoice_date) - new Date(a.created_at || a.invoice_date)
    })
  } catch (err) {
    showToast('Failed to load invoices', 'error')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchInvoices()
  refreshDrafts()
})

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

function handleDeleteDraft(draftId) {
  deleteDraft(draftId)
  showToast('Draft deleted')
}

function formatDraftDate(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  const now = new Date()
  const diffMs = now - d
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHrs = Math.floor(diffMins / 60)
  if (diffHrs < 24) return `${diffHrs}h ago`
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
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
/* ── Page Header ── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 28px;
  gap: 16px;
}

.page-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 800;
  color: var(--color-on-surface);
  margin: 0 0 4px;
  letter-spacing: -0.01em;
}

.page-subtitle {
  margin: 0;
  font-size: 13px;
  color: var(--color-on-surface-variant);
}

/* ── Primary Button ── */
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  padding: 10px 18px;
  border-radius: var(--radius-lg);
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
  white-space: nowrap;
  transition: opacity 0.18s;
  box-shadow: 0 2px 8px rgba(40,116,117,0.18);
}
.btn-primary:hover { opacity: 0.88; }
.btn-primary .material-symbols-outlined { font-size: 18px; }

/* ── Table Card ── */
.table-card {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  background: var(--color-surface-dim);
  padding: 10px 16px;
  text-align: left;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-on-surface-variant);
  border-bottom: 1px solid var(--color-outline);
}

.data-table td {
  padding: 13px 16px;
  font-size: 13px;
  color: var(--color-on-surface);
  border-bottom: 1px solid var(--color-outline);
}

.data-row:last-child td { border-bottom: none; }
.data-row:hover td { background: #fafbfc; }

/* ── Cell Helpers ── */
.text-right { text-align: right; }
.text-center { text-align: center; }
.font-mono { font-family: 'Courier New', Courier, monospace; letter-spacing: 0.02em; }
.font-medium { font-weight: 600; }
.text-muted { color: var(--color-on-surface-variant); }
.inv-num { font-size: 12px; color: var(--color-on-surface-variant); }

/* ── Badge ── */
.badge {
  display: inline-block;
  padding: 3px 9px;
  border-radius: var(--radius-full);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.badge-teal { background: var(--color-primary-light); color: var(--color-primary); }
.badge-grey { background: #f1f5f9; color: #64748b; }

/* ── Action Buttons ── */
.action-group {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-on-surface-variant);
  padding: 6px;
  border-radius: var(--radius-md);
  display: inline-flex;
  align-items: center;
  transition: background 0.15s, color 0.15s;
}
.icon-btn .material-symbols-outlined { font-size: 18px; }
.icon-btn:hover { background: var(--color-surface-dim); color: var(--color-primary); }
.icon-btn--danger:hover { background: #fef2f2; color: var(--color-error); }

/* ── Empty / Loading states ── */
.state-cell {
  text-align: center;
  padding: 56px 16px;
  color: var(--color-on-surface-variant);
  font-size: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
.empty-icon { font-size: 36px; opacity: 0.35; }
.inline-link { color: var(--color-primary); font-weight: 600; text-decoration: none; }
.inline-link:hover { text-decoration: underline; }

/* ── Spinner ── */
.spin-icon { animation: spin 0.8s linear infinite; font-size: 20px; }
@keyframes spin { to { transform: rotate(360deg); } }

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
.modal-icon-wrap.danger {
  background: #fef2f2;
  color: var(--color-error);
}
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

.modal-body {
  padding: 16px 24px 0;
}
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

.btn-outline {
  padding: 9px 18px;
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

/* ── Drafts Section ── */
.drafts-card {
  background: #fffdf7;
  border: 1px solid #fde68a;
  border-radius: var(--radius-xl);
  overflow: hidden;
  margin-bottom: 20px;
  box-shadow: var(--shadow-sm);
}
.drafts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 18px;
  background: #fefce8;
  border-bottom: 1px solid #fde68a;
}
.drafts-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.drafts-icon {
  font-size: 18px;
  color: #b45309;
}
.drafts-title {
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 800;
  color: #92400e;
}
.drafts-count {
  font-size: 11px;
  font-weight: 700;
  background: #fbbf24;
  color: #78350f;
  padding: 1px 7px;
  border-radius: var(--radius-full);
}
.drafts-list {
  padding: 6px 10px;
}
.draft-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 8px;
  border-bottom: 1px solid #fef3c7;
  gap: 12px;
}
.draft-item:last-child { border-bottom: none; }
.draft-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.draft-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.draft-meta {
  font-size: 11px;
  color: var(--color-on-surface-variant);
}
.draft-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.draft-resume-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: 12px;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
  transition: opacity 0.15s;
}
.draft-resume-btn:hover { opacity: 0.88; }
.draft-resume-btn .material-symbols-outlined { font-size: 14px; }
.draft-delete-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-on-surface-variant);
  transition: background 0.15s, color 0.15s;
}
.draft-delete-btn:hover { background: #fee2e2; color: var(--color-error); }
.draft-delete-btn .material-symbols-outlined { font-size: 16px; }
</style>
