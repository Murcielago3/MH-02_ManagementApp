<template>
  <AppLayout>
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">Invoices</h1>
        <p class="page-subtitle">Track billed amounts, taxes and PDFs in one place</p>
      </div>
      <router-link to="/admin/invoices/new" class="btn-primary">
        <span class="material-symbols-outlined">add</span>
        New Invoice
      </router-link>
    </div>

    <!-- KPI Tiles -->
    <div class="kpi-row">
      <div class="kpi-tile kpi-primary">
        <div class="kpi-icon-wrap"><span class="material-symbols-outlined">payments</span></div>
        <div class="kpi-body">
          <div class="kpi-label">Total Billed</div>
          <div class="kpi-value">₹{{ formatAmount(allTotals.total) }}</div>
          <div class="kpi-sub">across {{ invoices.length }} {{ invoices.length === 1 ? 'invoice' : 'invoices' }}</div>
        </div>
      </div>
      <div class="kpi-tile kpi-base">
        <div class="kpi-icon-wrap"><span class="material-symbols-outlined">request_quote</span></div>
        <div class="kpi-body">
          <div class="kpi-label">Base (Pre-Tax)</div>
          <div class="kpi-value">₹{{ formatAmount(allTotals.base) }}</div>
          <div class="kpi-sub">subtotal before GST</div>
        </div>
      </div>
      <div class="kpi-tile kpi-tax">
        <div class="kpi-icon-wrap"><span class="material-symbols-outlined">account_balance</span></div>
        <div class="kpi-body">
          <div class="kpi-label">Tax Collected</div>
          <div class="kpi-value">₹{{ formatAmount(allTotals.tax) }}</div>
          <div class="kpi-sub">CGST + SGST + IGST</div>
        </div>
      </div>
    </div>

    <!-- Drafts -->
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

    <!-- Toolbar: search + filter -->
    <div class="toolbar">
      <div class="search-box">
        <span class="material-symbols-outlined search-icon">search</span>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search invoice #, client, project…"
          class="search-input"
        />
        <button v-if="searchQuery" class="search-clear" @click="searchQuery = ''" title="Clear">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <div class="filter-segment">
        <button
          v-for="opt in filterOptions"
          :key="opt.value"
          class="seg-btn"
          :class="{ active: typeFilter === opt.value }"
          @click="typeFilter = opt.value"
        >
          <span class="material-symbols-outlined">{{ opt.icon }}</span>
          {{ opt.label }}
          <span class="seg-count">{{ countByType(opt.value) }}</span>
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="table-card">
      <div class="table-scroll">
      <table class="data-table">
        <thead>
          <tr>
            <th class="col-inv">Invoice</th>
            <th class="col-date">Date</th>
            <th class="col-client">Client &amp; Project</th>
            <th class="col-amt text-right">Base</th>
            <th class="col-amt text-right">Tax</th>
            <th class="col-amt text-right">Total</th>
            <th class="col-actions text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="7" class="state-cell">
              <span class="material-symbols-outlined spin-icon">progress_activity</span>
              <span>Loading invoices…</span>
            </td>
          </tr>
          <tr v-else-if="filteredInvoices.length === 0">
            <td colspan="7">
              <div class="empty-state">
                <div class="empty-icon-wrap">
                  <span class="material-symbols-outlined">receipt_long</span>
                </div>
                <h3 v-if="invoices.length === 0">No invoices yet</h3>
                <h3 v-else>Nothing matches your filters</h3>
                <p v-if="invoices.length === 0">Create your first invoice to start tracking billing here.</p>
                <p v-else>Try clearing the search or switching the type filter.</p>
                <router-link v-if="invoices.length === 0" to="/admin/invoices/new" class="empty-cta">
                  <span class="material-symbols-outlined">add</span>
                  Create First Invoice
                </router-link>
                <button v-else type="button" class="empty-cta empty-cta-ghost" @click="resetFilters">
                  Reset Filters
                </button>
              </div>
            </td>
          </tr>
          <tr
            v-for="inv in filteredInvoices"
            :key="inv.id"
            class="data-row"
            @click="goToDetail(inv.id)"
          >
            <td class="col-inv">
              <div class="inv-cell">
                <span class="inv-number">{{ inv.invoice_type === 'tax' ? inv.invoice_number : 'Proforma' }}</span>
                <span class="badge" :class="inv.invoice_type === 'tax' ? 'badge-teal' : 'badge-amber'">
                  {{ inv.invoice_type === 'tax' ? 'Tax' : 'Proforma' }}
                </span>
              </div>
            </td>
            <td class="col-date">
              <div class="date-cell">
                <span class="date-day">{{ formatDay(inv.invoice_date) }}</span>
                <span class="date-month">{{ formatMonth(inv.invoice_date) }}</span>
              </div>
            </td>
            <td class="col-client">
              <div class="client-cell">
                <div class="client-name">{{ inv.bill_to_name || 'Unnamed' }}</div>
                <div class="client-project">
                  <span class="material-symbols-outlined">folder</span>
                  {{ inv.project?.name || inv.subject || 'No project' }}
                </div>
              </div>
            </td>
            <td class="text-right amt-cell">
              <span class="amt-secondary">₹{{ formatAmount(inv.subtotal) }}</span>
            </td>
            <td class="text-right amt-cell">
              <span class="amt-tax">₹{{ formatAmount(getTax(inv)) }}</span>
            </td>
            <td class="text-right amt-cell">
              <span class="amt-primary">₹{{ formatAmount(inv.total) }}</span>
            </td>
            <td class="text-right">
              <div class="action-group" @click.stop>
                <button class="icon-btn" @click="goToDetail(inv.id)" title="View">
                  <span class="material-symbols-outlined">visibility</span>
                </button>
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
        <tfoot v-if="!loading && filteredInvoices.length > 0">
          <tr class="totals-row">
            <td colspan="3">
              <div class="totals-label">
                <span class="material-symbols-outlined">functions</span>
                <span class="totals-label-text">Cumulative</span>
                <span class="totals-count">
                  {{ filteredInvoices.length }} {{ filteredInvoices.length === 1 ? 'invoice' : 'invoices' }}<template v-if="typeFilter !== 'all'"> · {{ filterLabel }}</template>
                </span>
              </div>
            </td>
            <td class="text-right">
              <div class="totals-cell">
                <span class="totals-mini">Base</span>
                <span class="totals-base">₹{{ formatAmount(totals.base) }}</span>
              </div>
            </td>
            <td class="text-right">
              <div class="totals-cell">
                <span class="totals-mini">Tax</span>
                <span class="totals-tax">₹{{ formatAmount(totals.tax) }}</span>
              </div>
            </td>
            <td class="text-right">
              <div class="totals-cell totals-cell--grand">
                <span class="totals-mini">Total</span>
                <span class="totals-grand">₹{{ formatAmount(totals.total) }}</span>
              </div>
            </td>
            <td></td>
          </tr>
        </tfoot>
      </table>
      </div>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import ToastNotification from '../components/ToastNotification.vue'
import { invoicesAPI } from '../api/invoices'
import { useInvoiceDrafts } from '../composables/useInvoiceDrafts'

const router = useRouter()
const { drafts, hasDrafts, deleteDraft, refresh: refreshDrafts } = useInvoiceDrafts()

const invoices = ref([])
const loading = ref(true)
const submitting = ref(false)
const deleteTarget = ref(null)
const typeFilter = ref('all')
const searchQuery = ref('')

const filterOptions = [
  { value: 'all', label: 'All', icon: 'inbox' },
  { value: 'tax', label: 'Tax Invoice', icon: 'verified' },
  { value: 'proforma', label: 'Proforma', icon: 'description' },
]

const filterLabel = computed(
  () => filterOptions.find((o) => o.value === typeFilter.value)?.label || 'All'
)

const getTax = (inv) =>
  Number(inv.cgst || 0) + Number(inv.sgst || 0) + Number(inv.igst || 0)

const filteredInvoices = computed(() => {
  let list = invoices.value
  if (typeFilter.value !== 'all') {
    list = list.filter((i) => i.invoice_type === typeFilter.value)
  }
  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    list = list.filter((i) => {
      return (
        (i.invoice_number || '').toLowerCase().includes(q) ||
        (i.bill_to_name || '').toLowerCase().includes(q) ||
        (i.project?.name || '').toLowerCase().includes(q) ||
        (i.subject || '').toLowerCase().includes(q)
      )
    })
  }
  return list
})

const countByType = (type) => {
  if (type === 'all') return invoices.value.length
  return invoices.value.filter((i) => i.invoice_type === type).length
}

function sumKeys(list) {
  const base = list.reduce((acc, i) => acc + Number(i.subtotal || 0), 0)
  const tax = list.reduce((acc, i) => acc + getTax(i), 0)
  const total = list.reduce((acc, i) => acc + Number(i.total || 0), 0)
  return { base, tax, total }
}

const totals = computed(() => sumKeys(filteredInvoices.value))
const allTotals = computed(() => sumKeys(invoices.value))

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

const formatDay = (dateStr) => {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit' })
}

const formatMonth = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-GB', { month: 'short', year: '2-digit' })
}

const formatAmount = (val) => Number(val || 0).toLocaleString('en-IN')

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

function goToDetail(id) {
  router.push(`/admin/invoices/${id}`)
}

function resetFilters() {
  typeFilter.value = 'all'
  searchQuery.value = ''
}
</script>

<style scoped>
/* ── Page Header ── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 16px;
}
.page-title {
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 800;
  color: var(--color-on-surface);
  margin: 0 0 4px;
  letter-spacing: -0.015em;
}
.page-subtitle {
  margin: 0;
  font-size: 13px;
  color: var(--color-on-surface-variant);
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  padding: 11px 20px;
  border-radius: var(--radius-lg);
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
  white-space: nowrap;
  transition: transform 0.15s, box-shadow 0.18s, opacity 0.18s;
  box-shadow: 0 4px 14px rgba(40,116,117,0.22);
}
.btn-primary:hover { opacity: 0.92; transform: translateY(-1px); box-shadow: 0 6px 18px rgba(40,116,117,0.28); }
.btn-primary .material-symbols-outlined { font-size: 18px; }

/* ── KPI Tiles ── */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-bottom: 22px;
}
.kpi-tile {
  display: flex;
  gap: 14px;
  align-items: center;
  padding: 18px 20px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-xl);
  position: relative;
  overflow: hidden;
  transition: transform 0.16s, box-shadow 0.16s;
}
.kpi-tile::before {
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 3px;
  height: 100%;
}
.kpi-primary::before { background: var(--color-primary); }
.kpi-base::before { background: #6366f1; }
.kpi-tax::before { background: #f59e0b; }
.kpi-tile:hover { box-shadow: 0 4px 14px rgba(15,23,42,0.06); }

.kpi-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.kpi-primary .kpi-icon-wrap { background: var(--color-primary-light); color: var(--color-primary); }
.kpi-base .kpi-icon-wrap { background: #eef2ff; color: #6366f1; }
.kpi-tax .kpi-icon-wrap { background: #fef3c7; color: #b45309; }
.kpi-icon-wrap .material-symbols-outlined { font-size: 22px; }

.kpi-body { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.kpi-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-on-surface-variant);
}
.kpi-value {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 800;
  color: var(--color-on-surface);
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.01em;
  line-height: 1.15;
}
.kpi-sub {
  font-size: 11px;
  color: var(--color-on-surface-variant);
  margin-top: 1px;
}

/* ── Toolbar ── */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  gap: 14px;
  flex-wrap: wrap;
}
.search-box {
  position: relative;
  flex: 1;
  max-width: 380px;
  min-width: 220px;
}
.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-on-surface-variant);
  font-size: 18px;
  pointer-events: none;
}
.search-input {
  width: 100%;
  padding: 11px 36px 11px 38px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.search-input::placeholder { color: var(--color-on-surface-variant); }
.search-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}
.search-clear {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  color: var(--color-on-surface-variant);
  display: flex;
  align-items: center;
}
.search-clear:hover { background: var(--color-surface-dim); color: var(--color-on-surface); }
.search-clear .material-symbols-outlined { font-size: 16px; }

.filter-segment {
  display: inline-flex;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  padding: 4px;
  gap: 2px;
}
.seg-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 700;
  color: var(--color-on-surface-variant);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
}
.seg-btn:hover { color: var(--color-on-surface); }
.seg-btn.active {
  background: var(--color-primary);
  color: #fff;
  box-shadow: 0 2px 6px rgba(40,116,117,0.25);
}
.seg-btn .material-symbols-outlined { font-size: 15px; }
.seg-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 18px;
  padding: 0 6px;
  background: var(--color-outline-variant);
  color: var(--color-on-surface-variant);
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
}
.seg-btn.active .seg-count { background: rgba(255,255,255,0.22); color: #fff; }

/* ── Table Card ── */
.table-card {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(15,23,42,0.04);
}
.table-scroll {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 820px;
}

.data-table th {
  background: #fafbfc;
  padding: 12px 18px;
  text-align: left;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-on-surface-variant);
  border-bottom: 1px solid var(--color-outline);
  white-space: nowrap;
}

.data-table td {
  padding: 14px 18px;
  font-size: 13px;
  color: var(--color-on-surface);
  border-bottom: 1px solid var(--color-outline-variant);
  vertical-align: middle;
}

.data-row { cursor: pointer; transition: background 0.12s; }
.data-row:last-child td { border-bottom: none; }
.data-row:hover td { background: #fafbfc; }

.text-right { text-align: right; }

.col-inv { width: 180px; }
.col-date { width: 84px; }
.col-amt { width: 132px; }
.col-actions { width: 130px; }

/* Invoice cell */
.inv-cell { display: flex; flex-direction: column; gap: 4px; }
.inv-number {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 700;
  color: var(--color-on-surface);
  letter-spacing: -0.005em;
}
.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 9.5px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  width: fit-content;
}
.badge-teal { background: var(--color-primary-light); color: var(--color-primary); }
.badge-amber { background: #fef3c7; color: #b45309; }

/* Date cell */
.date-cell { display: flex; flex-direction: column; gap: 1px; line-height: 1.2; }
.date-day {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 800;
  color: var(--color-on-surface);
  font-variant-numeric: tabular-nums;
}
.date-month {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-on-surface-variant);
}

/* Client cell */
.client-cell { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.client-name {
  font-size: 13.5px;
  font-weight: 700;
  color: var(--color-on-surface);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 340px;
}
.client-project {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11.5px;
  font-weight: 500;
  color: var(--color-on-surface-variant);
  max-width: 340px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.client-project .material-symbols-outlined {
  font-size: 13px;
  color: #94a3b8;
  flex-shrink: 0;
}

/* Amount cells */
.amt-cell { font-variant-numeric: tabular-nums; }
.amt-secondary {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-surface-variant);
}
.amt-tax {
  font-size: 13px;
  font-weight: 700;
  color: #b45309;
}
.amt-primary {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 800;
  color: var(--color-on-surface);
  letter-spacing: -0.005em;
}

/* Action buttons */
.action-group {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  background: var(--color-surface-dim);
  border-radius: 8px;
  padding: 2px;
}
.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-on-surface-variant);
  padding: 6px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  transition: background 0.15s, color 0.15s;
}
.icon-btn .material-symbols-outlined { font-size: 17px; }
.icon-btn:hover { background: #fff; color: var(--color-primary); box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.icon-btn--danger:hover { color: var(--color-error); background: #fef2f2; }

/* Empty / Loading states */
.state-cell {
  text-align: center;
  padding: 64px 16px;
  color: var(--color-on-surface-variant);
  font-size: 14px;
}
.state-cell .spin-icon { font-size: 22px; vertical-align: middle; margin-right: 8px; }
.spin-icon { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.empty-state {
  padding: 56px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
}
.empty-icon-wrap {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--color-primary-light);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 6px;
}
.empty-icon-wrap .material-symbols-outlined {
  font-size: 32px;
  color: var(--color-primary);
}
.empty-state h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 800;
  color: var(--color-on-surface);
}
.empty-state p {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--color-on-surface-variant);
  max-width: 320px;
  line-height: 1.5;
}
.empty-cta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-lg);
  font-size: 13px;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
  transition: opacity 0.15s;
}
.empty-cta:hover { opacity: 0.92; }
.empty-cta .material-symbols-outlined { font-size: 17px; }
.empty-cta-ghost {
  background: var(--color-surface);
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
}

/* Footer Totals Row */
.totals-row td {
  background: #f8fafc;
  border-top: 1px solid var(--color-outline);
  border-bottom: none !important;
  padding: 18px;
  vertical-align: middle;
  white-space: nowrap;
}
.totals-label {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}
.totals-label .material-symbols-outlined {
  font-size: 20px;
  color: var(--color-primary);
  background: var(--color-primary-light);
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.totals-label-text {
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-on-surface);
}
.totals-count {
  font-family: var(--font-body);
  font-size: 11.5px;
  font-weight: 600;
  color: var(--color-on-surface-variant);
}
.totals-cell {
  font-variant-numeric: tabular-nums;
  display: inline-flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  line-height: 1.15;
}
.totals-mini {
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-on-surface-variant);
}
.totals-base {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-on-surface-variant);
}
.totals-tax {
  font-size: 14px;
  font-weight: 700;
  color: #b45309;
}
.totals-grand {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 800;
  color: var(--color-primary);
  letter-spacing: -0.01em;
}
.totals-cell--grand .totals-mini { color: var(--color-primary); }

/* ── Drafts Section ── */
.drafts-card {
  background: #fffdf7;
  border: 1px solid #fde68a;
  border-radius: var(--radius-xl);
  overflow: hidden;
  margin-bottom: 20px;
}
.drafts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 18px;
  background: #fefce8;
  border-bottom: 1px solid #fde68a;
}
.drafts-header-left { display: flex; align-items: center; gap: 8px; }
.drafts-icon { font-size: 18px; color: #b45309; }
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
  border-radius: 999px;
}
.drafts-list { padding: 6px 10px; }
.draft-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 8px;
  border-bottom: 1px solid #fef3c7;
  gap: 12px;
}
.draft-item:last-child { border-bottom: none; }
.draft-info { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.draft-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.draft-meta { font-size: 11px; color: var(--color-on-surface-variant); }
.draft-actions { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.draft-resume-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
}
.draft-resume-btn:hover { opacity: 0.9; }
.draft-resume-btn .material-symbols-outlined { font-size: 14px; }
.draft-delete-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: none;
  border-radius: 6px;
  cursor: pointer;
  color: var(--color-on-surface-variant);
}
.draft-delete-btn:hover { background: #fee2e2; color: var(--color-error); }
.draft-delete-btn .material-symbols-outlined { font-size: 16px; }

/* Modal */
.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(2px);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000; padding: 16px;
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
  width: 44px; height: 44px;
  border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
}
.modal-icon-wrap.danger { background: #fef2f2; color: var(--color-error); }
.modal-icon-wrap .material-symbols-outlined { font-size: 24px; }
.modal-close {
  background: none; border: none;
  cursor: pointer;
  color: var(--color-on-surface-variant);
  padding: 4px;
  border-radius: var(--radius-md);
}
.modal-close:hover { background: var(--color-surface-dim); }
.modal-close .material-symbols-outlined { font-size: 20px; }
.modal-body { padding: 16px 24px 0; }
.modal-title {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 800;
  margin: 0 0 8px;
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
  cursor: pointer;
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
}
.btn-danger:hover { opacity: 0.92; }
.btn-danger:disabled { opacity: 0.55; cursor: not-allowed; }

/* Responsive */
@media (max-width: 1024px) {
  .kpi-row { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; }
  .toolbar { flex-direction: column; align-items: stretch; }
  .search-box { max-width: none; }
  .filter-segment { width: 100%; overflow-x: auto; }
  .draft-item { flex-direction: column; align-items: flex-start; gap: 8px; }
  .draft-actions { align-self: flex-end; }
  .modal { max-width: 100%; width: 100%; }
  .modal-backdrop { padding: 8px; }
}
</style>
