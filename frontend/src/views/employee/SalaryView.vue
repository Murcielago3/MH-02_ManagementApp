<template>
  <EmployeeLayout>
    <div class="salary-view">
      <div class="view-header">
        <h2 class="view-title">Salary Slips</h2>
        <p class="view-sub">Base salary plus approved reimbursements, less TDS. Slips are released after admin approval.</p>
      </div>

      <!-- Year selector -->
      <div class="controls-row">
        <div class="year-select-group">
          <label>Financial Year</label>
          <select v-model="selectedYear" class="field-select">
            <option v-for="y in yearOptions" :key="y" :value="y">{{ y }} – {{ y + 1 }}</option>
          </select>
        </div>
      </div>

      <!-- Slips Grid -->
      <div v-if="loading" class="loading-state">
        <span class="material-symbols-outlined spin-icon">progress_activity</span>
        Loading salary slips…
      </div>
      <div v-else class="slips-grid">
        <div
          v-for="month in months"
          :key="month.key"
          class="slip-card"
          :class="{
            'is-future': month.isFuture && !month.slip,
            'is-clickable': month.slip && month.slip.status === 'approved',
            'is-approved': month.slip && month.slip.status === 'approved',
          }"
          @click="month.slip && month.slip.status === 'approved' ? openSlip(month.slip) : null"
        >
          <div class="slip-card-top">
            <div>
              <div class="slip-month">{{ month.label }}</div>
              <div class="slip-year">{{ month.year }}</div>
            </div>
            <span v-if="month.slip" class="slip-badge" :class="`badge-${month.slip.status}`">
              {{ month.slip.status === 'approved' ? 'Released' : 'Processing' }}
            </span>
          </div>

          <!-- Approved slip → show net + open -->
          <template v-if="month.slip && month.slip.status === 'approved'">
            <div class="slip-net">{{ formatCurrency(month.slip.net_total) }}</div>
            <div class="slip-foot">
              <span class="slip-payout">Paid {{ formatDate(month.slip.payout_date) }}</span>
              <span class="slip-view">View <span class="material-symbols-outlined">chevron_right</span></span>
            </div>
          </template>

          <!-- Pending slip -->
          <template v-else-if="month.slip">
            <div class="slip-status-line">Awaiting admin approval</div>
          </template>

          <!-- No slip -->
          <template v-else>
            <div class="slip-status-line muted">{{ month.isFuture ? 'Upcoming' : 'Not available' }}</div>
          </template>
        </div>
      </div>

      <!-- Info Notice -->
      <div class="info-notice">
        <span class="material-symbols-outlined">info</span>
        <p>Salary slips are released around the 7th of each month after admin approval. If a released slip looks incorrect, please contact HR.</p>
      </div>
    </div>

    <!-- Slip PDF Modal -->
    <Teleport to="body">
      <div v-if="modalOpen" class="modal-backdrop" @click.self="closeModal">
        <div class="modal pdf-modal">
          <div class="pdf-modal-head">
            <div class="pdf-modal-title">
              {{ activeSlip ? monthLabel(activeSlip.month) : '' }} · Salary Slip
            </div>
            <div class="pdf-modal-actions">
              <button class="btn-print" :disabled="pdfLoading || !pdfUrl" @click="downloadActive">
                <span class="material-symbols-outlined">download</span>
                Download PDF
              </button>
              <button class="modal-x" @click="closeModal">
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>
          </div>
          <div class="pdf-frame-wrap">
            <div v-if="pdfLoading" class="pdf-loading">
              <span class="material-symbols-outlined spin-icon">progress_activity</span>
              Loading slip…
            </div>
            <iframe v-else-if="pdfUrl" :src="pdfUrl" class="pdf-frame" title="Salary Slip"></iframe>
          </div>
        </div>
      </div>
    </Teleport>

    <ToastNotification v-if="toastMsg" :message="toastMsg" :type="toastType" @done="toastMsg = ''" />
  </EmployeeLayout>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import EmployeeLayout from '../../components/EmployeeLayout.vue'
import ToastNotification from '../../components/ToastNotification.vue'
import { salarySlipsAPI } from '../../api/salarySlips'

const now = new Date()
const currentMonth = now.getMonth()
const currentCalendarYear = now.getFullYear()

const defaultFY = currentMonth >= 3 ? currentCalendarYear : currentCalendarYear - 1
const selectedYear = ref(defaultFY)

const slips = ref([])
const loading = ref(true)

const modalOpen = ref(false)
const activeSlip = ref(null)
const pdfUrl = ref('')
const pdfLoading = ref(false)

const toastMsg = ref('')
const toastType = ref('success')
function toast(msg, type = 'success') { toastType.value = type; toastMsg.value = msg }

const inrFmt = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
function formatCurrency(v) { return inrFmt.format(Number(v) || 0) }

const monthNamesFull = ['January','February','March','April','May','June','July','August','September','October','November','December']
function monthLabel(ms) {
  if (!ms) return ''
  const [y, m] = ms.split('-').map(Number)
  return `${monthNamesFull[m - 1]} ${y}`
}
function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

const slipsByMonth = computed(() => {
  const map = {}
  for (const s of slips.value) map[s.month] = s
  return map
})

async function fetchSlips() {
  loading.value = true
  try {
    const res = await salarySlipsAPI.getMySlips()
    slips.value = res.data
  } catch (e) {
    toast('Failed to load salary slips', 'error')
  } finally {
    loading.value = false
  }
}

onMounted(fetchSlips)

const yearOptions = computed(() => {
  const years = []
  for (let y = defaultFY; y >= defaultFY - 4; y--) years.push(y)
  return years
})

const monthNames = ['April','May','June','July','August','September','October','November','December','January','February','March']

const months = computed(() => {
  const fy = selectedYear.value
  return monthNames.map((label, i) => {
    const monthIndex = (i + 3) % 12          // April=3 … Mar=2
    const year = i < 9 ? fy : fy + 1
    const key = `${year}-${String(monthIndex + 1).padStart(2, '0')}`
    const isFuture = new Date(year, monthIndex + 1, 0) > now
    return {
      key,
      label,
      year,
      monthIndex,
      isFuture,
      slip: slipsByMonth.value[key] || null,
    }
  })
})

async function openSlip(slip) {
  activeSlip.value = slip
  modalOpen.value = true
  pdfLoading.value = true
  pdfUrl.value = ''
  try {
    const res = await salarySlipsAPI.downloadPdf(slip.id)
    pdfUrl.value = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
  } catch (e) {
    toast('Failed to load salary slip', 'error')
    modalOpen.value = false
  } finally {
    pdfLoading.value = false
  }
}

function closeModal() {
  modalOpen.value = false
  if (pdfUrl.value) {
    URL.revokeObjectURL(pdfUrl.value)
    pdfUrl.value = ''
  }
  activeSlip.value = null
}

function downloadActive() {
  if (!pdfUrl.value || !activeSlip.value) return
  const a = document.createElement('a')
  a.href = pdfUrl.value
  a.download = `salary_slip_${activeSlip.value.month}.pdf`
  a.click()
}
</script>

<style scoped>
.salary-view { max-width: 1000px; margin: 0 auto; }

.view-header { margin-bottom: 20px; }
.view-title {
  font-family: 'Integral CF', sans-serif;
  font-size: 28px; font-weight: 700;
  color: var(--color-on-surface); margin: 0; letter-spacing: -0.02em;
}
.view-sub { margin: 6px 0 0; font-size: 13px; color: var(--color-on-surface-variant); }

/* Controls */
.controls-row { margin-bottom: 28px; }
.year-select-group { display: flex; align-items: center; gap: 12px; }
.year-select-group label {
  font-size: 12px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--color-on-surface-variant);
}
.field-select {
  height: 40px; padding: 0 12px; border-radius: 4px; border: 1px solid #cbd5e1;
  font-family: var(--font-body); font-size: 14px; background: var(--color-surface);
  outline: none; cursor: pointer; min-width: 160px;
}
.field-select:focus { border-color: var(--color-primary); box-shadow: 0 0 0 2px rgba(40, 116, 117, 0.1); }

.loading-state {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  padding: 48px; color: var(--color-on-surface-variant); font-size: 14px;
}

/* Slips Grid */
.slips-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 32px;
}
@media (max-width: 900px) { .slips-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 640px) { .slips-grid { grid-template-columns: repeat(2, 1fr); } }

.slip-card {
  background: var(--color-surface);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 18px;
  display: flex; flex-direction: column; gap: 10px;
  min-height: 130px;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.1s;
}
.slip-card.is-future { opacity: 0.5; }
.slip-card.is-clickable { cursor: pointer; }
.slip-card.is-clickable:hover {
  border-color: var(--color-primary);
  box-shadow: 0 4px 14px rgba(40,116,117,0.12);
  transform: translateY(-1px);
}
.slip-card.is-approved { border-color: #a7f3d0; }

.slip-card-top { display: flex; justify-content: space-between; align-items: flex-start; }
.slip-month { font-family: 'Integral CF', sans-serif; font-size: 15px; font-weight: 700; color: var(--color-on-surface); }
.slip-year { font-size: 12px; color: var(--color-on-surface-variant); font-variant-numeric: tabular-nums; }

.slip-badge {
  padding: 2px 8px; border-radius: var(--radius-full);
  font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;
}
.badge-approved { background: #dcfce7; color: #166534; }
.badge-pending { background: #fef3c7; color: #92400e; }

.slip-net {
  font-family: 'Integral CF', sans-serif; font-size: 20px; font-weight: 800;
  color: var(--color-primary); font-variant-numeric: tabular-nums; margin-top: auto;
}
.slip-foot { display: flex; justify-content: space-between; align-items: center; }
.slip-payout { font-size: 11px; color: var(--color-on-surface-variant); }
.slip-view {
  display: inline-flex; align-items: center; gap: 1px;
  font-size: 12px; font-weight: 700; color: var(--color-primary);
}
.slip-view .material-symbols-outlined { font-size: 16px; }

.slip-status-line { margin-top: auto; font-size: 12px; font-weight: 600; color: #b45309; }
.slip-status-line.muted { color: var(--color-outline); font-weight: 500; }

/* Info Notice */
.info-notice {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 16px 20px; background: var(--color-surface-container);
  border: 1px solid var(--color-outline-variant); border-radius: 4px;
}
.info-notice .material-symbols-outlined { font-size: 20px; color: var(--color-primary); margin-top: 1px; }
.info-notice p { margin: 0; font-size: 13px; color: var(--color-on-surface-variant); line-height: 1.5; }

/* ── Modal ── */
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(15, 23, 42, 0.5);
  display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 16px;
}
.modal {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: 0 20px 60px rgba(0,0,0,0.18);
  max-width: 460px; width: 100%; overflow: hidden;
}

/* PDF preview modal */
.pdf-modal {
  max-width: 880px;
  height: 90vh;
  display: flex;
  flex-direction: column;
}
.pdf-modal-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px; border-bottom: 1px solid var(--color-outline-variant);
  flex-shrink: 0;
}
.pdf-modal-title { font-family: 'Integral CF', sans-serif; font-size: 15px; font-weight: 700; color: var(--color-on-surface); }
.pdf-modal-actions { display: flex; align-items: center; gap: 8px; }
.modal-x {
  width: 34px; height: 34px; display: inline-flex; align-items: center; justify-content: center;
  border: 1px solid var(--color-outline); border-radius: var(--radius-md);
  background: var(--color-surface); cursor: pointer; color: var(--color-on-surface-variant);
}
.modal-x:hover { background: var(--color-surface-dim); }
.pdf-frame-wrap { flex: 1; min-height: 0; background: #525659; }
.pdf-frame { width: 100%; height: 100%; border: none; display: block; }
.pdf-loading {
  display: flex; align-items: center; justify-content: center; gap: 10px; height: 100%;
  color: #fff; font-size: 14px;
}

/* Payslip document */
.payslip-doc { display: flex; flex-direction: column; }
.doc-header {
  background: var(--color-on-surface);
  padding: 24px 28px 20px;
  display: flex; flex-direction: column; gap: 6px;
}
.doc-badge {
  align-self: flex-start; padding: 3px 10px;
  background: var(--color-primary); color: #fff; border-radius: 3px;
  font-size: 10px; font-weight: 800; letter-spacing: 0.1em; text-transform: uppercase;
}
.doc-name { font-family: 'Integral CF', sans-serif; font-size: 20px; font-weight: 700; color: #fff; }
.doc-period {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; color: rgba(255,255,255,0.65); font-variant-numeric: tabular-nums;
}
.doc-period .material-symbols-outlined { font-size: 15px; }

.doc-section { padding: 16px 28px; border-bottom: 1px solid var(--color-outline-variant); }
.doc-section-title {
  font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.07em;
  color: var(--color-on-surface-variant); margin-bottom: 12px;
}
.doc-line {
  display: flex; justify-content: space-between; align-items: center;
  padding: 5px 0; font-size: 14px; color: var(--color-on-surface);
}
.doc-line.sub { font-size: 13px; padding-left: 12px; }
.doc-line .amt { font-weight: 600; font-variant-numeric: tabular-nums; }
.doc-line .amt.pos { color: #047857; }
.doc-line .amt.neg { color: #b45309; }
.doc-line .muted, .muted { color: var(--color-on-surface-variant); }

.doc-net {
  display: flex; justify-content: space-between; align-items: center;
  padding: 20px 28px; background: linear-gradient(135deg, #1e5d5e, var(--color-primary));
}
.net-label { font-size: 12px; font-weight: 800; letter-spacing: 0.1em; color: rgba(255,255,255,0.8); }
.net-value { font-family: 'Integral CF', sans-serif; font-size: 26px; font-weight: 800; color: #fff; font-variant-numeric: tabular-nums; }

.modal-actions {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 16px 24px; background: #f8fafc; border-top: 1px solid var(--color-outline-variant);
}
.btn-cancel {
  padding: 9px 16px; background: var(--color-surface);
  border: 1px solid var(--color-outline); border-radius: var(--radius-lg);
  font-size: 13px; color: var(--color-on-surface-variant); cursor: pointer;
}
.btn-cancel:hover { background: var(--color-outline-variant); }
.btn-print {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 9px 18px; background: var(--color-primary); color: #fff;
  border: none; border-radius: var(--radius-lg); font-size: 13px; font-weight: 600; cursor: pointer;
}
.btn-print:hover { background: #1f5c5d; }
.btn-print .material-symbols-outlined { font-size: 17px; }

.spin-icon { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Print only the payslip */
@media print {
  body * { visibility: hidden; }
  #payslip-print, #payslip-print * { visibility: visible; }
  #payslip-print { position: absolute; left: 0; top: 0; width: 100%; }
  .modal-actions { display: none !important; }
}

@media (max-width: 768px) {
  .slips-grid { grid-template-columns: repeat(2, 1fr); }
  .controls-row { margin-bottom: 16px; }
  .pdf-modal { height: 85vh; }
  .modal-backdrop { padding: 0; align-items: flex-end; }
  .pdf-modal { border-radius: var(--radius-xl) var(--radius-xl) 0 0; }
}
@media (max-width: 480px) {
  .slips-grid { grid-template-columns: 1fr; }
}
</style>
