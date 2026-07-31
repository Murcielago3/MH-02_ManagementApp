<template>
  <div class="export-panel">
    <div class="ep-head">
      <h2 class="ep-title">Data Export</h2>
      <p class="ep-note">Select the data you want to export. One selection downloads a CSV; multiple selections download a ZIP of CSVs.</p>
    </div>

    <div class="ep-grid">
      <label v-for="e in entities" :key="e.key" class="ep-card" :class="{ checked: selected.includes(e.key) }">
        <input type="checkbox" :value="e.key" v-model="selected" />
        <span class="material-symbols-outlined ep-icon">{{ e.icon }}</span>
        <span class="ep-label">{{ e.label }}</span>
      </label>
    </div>

    <div class="ep-actions">
      <button type="button" class="btn-ghost" @click="toggleAll">
        {{ selected.length === entities.length ? 'Clear all' : 'Select all' }}
      </button>
      <button type="button" class="btn-primary" :disabled="!selected.length || exporting" @click="doExport">
        <span v-if="exporting" class="material-symbols-outlined spin-icon">progress_activity</span>
        <span v-else class="material-symbols-outlined">download</span>
        {{ exporting ? 'Preparing…' : `Export ${selected.length ? selected.length : ''} selected` }}
      </button>
    </div>

    <!-- CA Salary Sheet - a per-month register in the studio CA's layout -->
    <div class="ca-section">
      <div class="ca-head">
        <span class="material-symbols-outlined ca-icon">description</span>
        <div>
          <h2 class="ep-title">CA Salary Sheet</h2>
          <p class="ep-note">A month's salary register in your CA's format (Salary, Bonus, TDS, Conveyance, rounded pay) with column totals.</p>
        </div>
      </div>
      <div class="ca-controls">
        <label class="ca-field">
          <span class="ca-label">Month</span>
          <select v-if="salaryMonths.length" v-model="caMonth" class="ca-select">
            <option v-for="m in salaryMonths" :key="m" :value="m">{{ monthLabel(m) }}</option>
          </select>
          <input v-else v-model="caMonth" type="month" class="ca-select" />
        </label>
        <button type="button" class="btn-primary" :disabled="!caMonth || caExporting" @click="doCaExport">
          <span v-if="caExporting" class="material-symbols-outlined spin-icon">progress_activity</span>
          <span v-else class="material-symbols-outlined">download</span>
          {{ caExporting ? 'Preparing…' : 'Export CA Salary Sheet' }}
        </button>
      </div>
    </div>

    <ToastNotification v-if="toastMsg" :message="toastMsg" :type="toastType" @done="toastMsg = ''" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import ToastNotification from './ToastNotification.vue'
import { exportsAPI, downloadBlob } from '../api/exports'

const entities = [
  { key: 'employees', label: 'Employees', icon: 'group' },
  { key: 'projects', label: 'Projects', icon: 'architecture' },
  { key: 'reimbursements', label: 'Reimbursements', icon: 'request_quote' },
  { key: 'salary-slips', label: 'Salary Slips', icon: 'paid' },
  { key: 'clients', label: 'Clients', icon: 'handshake' },
  { key: 'leaves', label: 'Leaves', icon: 'event_busy' },
  { key: 'timesheets', label: 'Timesheets', icon: 'pending_actions' },
  { key: 'estimates', label: 'Estimates', icon: 'calculate' },
]

const selected = ref([])
const exporting = ref(false)
const toastMsg = ref('')
const toastType = ref('success')
function toast(msg, type = 'success') { toastType.value = type; toastMsg.value = msg }

function toggleAll() {
  selected.value = selected.value.length === entities.length ? [] : entities.map(e => e.key)
}

// ── CA Salary Sheet ──
const salaryMonths = ref([])
const caMonth = ref('')
const caExporting = ref(false)

function monthLabel(ym) {
  if (!ym) return ''
  const [y, m] = ym.split('-')
  return new Date(Number(y), Number(m) - 1, 1).toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })
}

onMounted(async () => {
  try {
    const res = await exportsAPI.salaryMonths()
    salaryMonths.value = res.data || []
    if (salaryMonths.value.length) {
      caMonth.value = salaryMonths.value[0]
    } else {
      // No slips yet - default the native picker to last month.
      const d = new Date(); d.setMonth(d.getMonth() - 1)
      caMonth.value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    }
  } catch (e) {
    // Non-fatal - the native month input still works.
  }
})

async function doCaExport() {
  if (!caMonth.value) return
  caExporting.value = true
  try {
    const res = await exportsAPI.caSalarySheet(caMonth.value)
    downloadBlob(res, `ca-salary-sheet-${caMonth.value}.csv`)
    toast('CA Salary Sheet downloaded.')
  } catch (e) {
    toast('Export failed. Please try again.', 'error')
  } finally {
    caExporting.value = false
  }
}

async function doExport() {
  exporting.value = true
  try {
    if (selected.value.length === 1) {
      const entity = selected.value[0]
      const res = await exportsAPI.exportCsv(entity)
      downloadBlob(res, `${entity}.csv`)
    } else {
      const res = await exportsAPI.exportBundle(selected.value)
      downloadBlob(res, 'mh02-export.zip')
    }
    toast('Export downloaded.')
  } catch (e) {
    toast('Export failed. Please try again.', 'error')
  } finally {
    exporting.value = false
  }
}
</script>

<style scoped>
.export-panel { padding: 28px 32px; }
.ep-head { margin-bottom: 20px; }
.ep-title { font-family: var(--font-display); font-size: 15px; font-weight: 800; margin: 0 0 4px; color: var(--color-on-surface); }
.ep-note { margin: 0; font-size: 13px; color: var(--color-on-surface-variant); max-width: 560px; }

.ep-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; margin-bottom: 20px; }
.ep-card {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 14px; border: 1px solid var(--color-outline); border-radius: var(--radius-lg);
  cursor: pointer; background: var(--color-surface); transition: border-color .15s, background .15s;
  font-size: 13px; font-weight: 600; color: var(--color-on-surface);
}
.ep-card:hover { border-color: var(--color-primary); }
.ep-card.checked { border-color: var(--color-primary); background: var(--color-primary-light); }
.ep-card input { width: 15px; height: 15px; accent-color: var(--color-primary); margin: 0; }
.ep-icon { font-size: 18px; color: var(--color-primary); }

.ep-actions { display: flex; gap: 10px; align-items: center; }
.btn-primary {
  display: inline-flex; align-items: center; gap: 7px; padding: 10px 20px;
  border: none; border-radius: var(--radius-lg); background: var(--color-primary); color: #fff;
  font-family: var(--font-display); font-size: 13px; font-weight: 700; cursor: pointer;
}
.btn-primary:disabled { opacity: .5; cursor: not-allowed; }
.btn-primary .material-symbols-outlined { font-size: 17px; }
.btn-ghost {
  padding: 10px 16px; border: 1px solid var(--color-outline); border-radius: var(--radius-lg);
  background: var(--color-surface); font-size: 13px; font-weight: 600; cursor: pointer;
  color: var(--color-on-surface-variant);
}
.btn-ghost:hover { background: var(--color-surface-dim); }
.spin-icon { animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── CA Salary Sheet ── */
.ca-section {
  margin-top: 24px;
  padding-top: 22px;
  border-top: 1px solid var(--color-outline);
}
.ca-head { display: flex; gap: 12px; align-items: flex-start; margin-bottom: 16px; }
.ca-icon { font-size: 22px; color: var(--color-primary); }
.ca-controls { display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap; }
.ca-field { display: flex; flex-direction: column; gap: 5px; }
.ca-label {
  font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em;
  color: var(--color-on-surface-variant);
}
.ca-select {
  padding: 9px 12px; min-width: 200px;
  border: 1px solid var(--color-outline); border-radius: var(--radius-lg);
  font-size: 13px; color: var(--color-on-surface); background: var(--color-surface); outline: none;
}
.ca-select:focus { border-color: var(--color-primary); }

@media (max-width: 768px) {
  .export-panel { padding: 18px 16px; }
}
</style>
