<template>
  <AppLayout>
    <div class="page-header">
      <div>
        <h1 class="page-title">Human Resources</h1>
        <p class="page-subtitle">Salary increments and the company holiday calendar</p>
      </div>
    </div>

    <div class="tabs-bar">
      <button
        v-for="t in tabs"
        :key="t.key"
        type="button"
        :class="['tab-btn', { active: activeTab === t.key }]"
        @click="activeTab = t.key"
      >
        <span class="material-symbols-outlined tab-icon">{{ t.icon }}</span>
        {{ t.label }}
      </button>
    </div>

    <!-- SALARY INCREMENTS -->
    <section v-if="activeTab === 'salary'" class="panel">
      <div v-if="loading" class="loading-state">
        <span class="material-symbols-outlined spin-icon">progress_activity</span>
        Loading employees…
      </div>
      <table v-else class="hr-table">
        <thead>
          <tr>
            <th>Employee</th>
            <th>Designation</th>
            <th class="num">Current Salary</th>
            <th class="num">Hourly Rate</th>
            <th>Effective From</th>
            <th class="actions-col"></th>
          </tr>
        </thead>
        <tbody>
          <template v-for="e in employees" :key="e.id">
            <tr>
              <td class="strong">{{ e.name }}</td>
              <td class="muted">{{ e.designation }}</td>
              <td class="num">{{ e.current_salary != null ? '₹' + formatInr(e.current_salary, 0) : '—' }}</td>
              <td class="num">{{ e.current_hourly_rate != null ? '₹' + formatInr(e.current_hourly_rate, 2) : '—' }}</td>
              <td class="muted">{{ e.effective_from || '—' }}</td>
              <td class="actions-col">
                <button class="btn-link" @click="toggleHistory(e)">
                  {{ openHistory === e.id ? 'Hide' : 'History' }}
                </button>
                <button class="btn-primary sm" @click="openIncrement(e)">
                  <span class="material-symbols-outlined">add</span> Increment
                </button>
              </td>
            </tr>
            <tr v-if="openHistory === e.id" class="history-row">
              <td colspan="6">
                <div v-if="historyLoading" class="muted small">Loading history…</div>
                <table v-else class="history-table">
                  <thead>
                    <tr><th>From</th><th>To</th><th class="num">Monthly</th><th class="num">Hourly</th><th>Note</th><th></th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="p in history" :key="p.id">
                      <td>{{ p.effective_from }}</td>
                      <td>{{ p.effective_to || 'current' }}</td>
                      <td class="num">{{ p.monthly_salary != null ? '₹' + formatInr(p.monthly_salary, 0) : '—' }}</td>
                      <td class="num">{{ p.hourly_rate != null ? '₹' + formatInr(p.hourly_rate, 2) : '—' }}</td>
                      <td class="muted">{{ p.note || '' }}</td>
                      <td>
                        <button class="btn-link danger" @click="removePeriod(e, p)">Delete</button>
                      </td>
                    </tr>
                    <tr v-if="!history.length"><td colspan="6" class="muted small">No salary history.</td></tr>
                  </tbody>
                </table>
              </td>
            </tr>
          </template>
          <tr v-if="!employees.length">
            <td colspan="6" class="muted small" style="text-align:center;padding:24px">
              No employees or project managers found.
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- HOLIDAYS -->
    <section v-if="activeTab === 'holidays'" class="panel">
      <HolidaysManager />
    </section>

    <!-- ADD INCREMENT MODAL -->
    <div v-if="modal.open" class="modal-backdrop" @click.self="modal.open = false">
      <div class="modal">
        <h2 class="modal-title">Add Increment — {{ modal.name }}</h2>
        <p class="modal-sub">Takes effect on the 1st of the chosen month. Backdating is limited to last month.</p>
        <div class="field">
          <label>New Monthly Salary (₹)</label>
          <input v-model.number="modal.monthly_salary" type="number" min="0" step="1" />
        </div>
        <div class="field">
          <label>Effective From (month)</label>
          <input v-model="modal.month" type="month" />
        </div>
        <div class="field">
          <label>Note (optional)</label>
          <input v-model="modal.note" type="text" placeholder="e.g. Annual increment FY26" />
        </div>
        <div class="modal-actions">
          <button class="btn-ghost" @click="modal.open = false">Cancel</button>
          <button class="btn-primary" :disabled="modal.saving || !modal.monthly_salary || !modal.month" @click="submitIncrement">
            <span v-if="modal.saving" class="material-symbols-outlined spin-icon">progress_activity</span>
            Save Increment
          </button>
        </div>
      </div>
    </div>

    <ToastNotification v-if="toastMsg" :message="toastMsg" :type="toastType" @done="toastMsg = ''" />
  </AppLayout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import HolidaysManager from '../components/HolidaysManager.vue'
import ToastNotification from '../components/ToastNotification.vue'
import { salaryAPI } from '../api/salary'
import { formatInr } from '../utils/currency'

const tabs = [
  { key: 'salary', label: 'Salary Increments', icon: 'trending_up' },
  { key: 'holidays', label: 'Holidays', icon: 'event' },
]
const activeTab = ref('salary')

const loading = ref(true)
const employees = ref([])
const openHistory = ref(null)
const history = ref([])
const historyLoading = ref(false)

const toastMsg = ref('')
const toastType = ref('success')
function toast(msg, type = 'success') { toastType.value = type; toastMsg.value = msg }

const modal = reactive({ open: false, userId: null, name: '', monthly_salary: null, month: '', note: '', saving: false })

function apiErr(e) {
  const d = e.response?.data?.detail
  if (Array.isArray(d)) return d.map((x) => x.msg || JSON.stringify(x)).join(' ')
  return d || e.message || 'Request failed'
}

async function loadEmployees() {
  loading.value = true
  try {
    employees.value = (await salaryAPI.employees()).data
  } catch (e) {
    toast(apiErr(e), 'error')
  } finally {
    loading.value = false
  }
}

async function toggleHistory(e) {
  if (openHistory.value === e.id) { openHistory.value = null; return }
  openHistory.value = e.id
  historyLoading.value = true
  try {
    history.value = (await salaryAPI.history(e.id)).data
  } catch (err) {
    toast(apiErr(err), 'error')
  } finally {
    historyLoading.value = false
  }
}

function openIncrement(e) {
  modal.userId = e.id
  modal.name = e.name
  modal.monthly_salary = e.current_salary
  modal.month = ''
  modal.note = ''
  modal.open = true
}

async function submitIncrement() {
  modal.saving = true
  try {
    await salaryAPI.increment(modal.userId, {
      monthly_salary: modal.monthly_salary,
      effective_from: `${modal.month}-01`,   // <input type=month> -> YYYY-MM
      note: modal.note || null,
    })
    toast('Increment saved.')
    modal.open = false
    await loadEmployees()
    if (openHistory.value === modal.userId) {
      history.value = (await salaryAPI.history(modal.userId)).data
    }
  } catch (e) {
    toast(apiErr(e), 'error')
  } finally {
    modal.saving = false
  }
}

async function removePeriod(e, p) {
  try {
    await salaryAPI.deletePeriod(p.id)
    history.value = (await salaryAPI.history(e.id)).data
    await loadEmployees()
    toast('Salary record removed.')
  } catch (err) {
    toast(apiErr(err), 'error')
  }
}

onMounted(loadEmployees)
</script>

<style scoped>
.page-header { margin-bottom: 24px; }
.page-title { font-family: var(--font-display); font-size: 24px; font-weight: 800; color: var(--color-on-surface); margin: 0 0 4px; }
.page-subtitle { margin: 0; font-size: 13px; color: var(--color-on-surface-variant); }

.tabs-bar { display: flex; gap: 2px; border-bottom: 1px solid var(--color-outline); margin-bottom: 24px; }
.tab-btn { display: inline-flex; align-items: center; gap: 7px; background: transparent; border: none; padding: 11px 20px; font-family: var(--font-display); font-size: 13px; font-weight: 700; color: var(--color-on-surface-variant); cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -1px; }
.tab-btn:hover { color: var(--color-on-surface); }
.tab-btn.active { color: var(--color-primary); border-bottom-color: var(--color-primary); }
.tab-icon { font-size: 18px; }

.panel { background: var(--color-surface); border: 1px solid var(--color-outline); border-radius: var(--radius-xl); overflow: hidden; box-shadow: var(--shadow-sm); }
.loading-state { display: flex; align-items: center; gap: 10px; padding: 40px; color: var(--color-on-surface-variant); font-size: 14px; justify-content: center; }

.hr-table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
.hr-table th { text-align: left; padding: 12px 16px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; color: var(--color-on-surface-variant); border-bottom: 1px solid var(--color-outline); }
.hr-table td { padding: 12px 16px; border-bottom: 1px solid var(--color-outline); color: var(--color-on-surface); }
.hr-table .num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
.strong { font-weight: 600; }
.muted { color: var(--color-on-surface-variant); }
.small { font-size: 12px; }
.actions-col { text-align: right; white-space: nowrap; }

.history-row td { background: var(--color-surface-dim); padding: 8px 16px 16px; }
.history-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.history-table th { text-align: left; padding: 6px 10px; color: var(--color-on-surface-variant); font-weight: 700; }
.history-table td { padding: 6px 10px; border-top: 1px solid var(--color-outline); }

.btn-link { background: none; border: none; color: var(--color-primary); font-weight: 600; cursor: pointer; font-size: 12.5px; margin-right: 10px; }
.btn-link.danger { color: var(--color-error); }
.btn-primary { display: inline-flex; align-items: center; gap: 5px; padding: 8px 14px; border: none; border-radius: var(--radius-lg); background: var(--color-primary); color: #fff; font-family: var(--font-display); font-size: 12.5px; font-weight: 700; cursor: pointer; }
.btn-primary.sm { padding: 6px 12px; }
.btn-primary:disabled { opacity: .55; cursor: not-allowed; }
.btn-primary .material-symbols-outlined { font-size: 16px; }
.btn-ghost { padding: 8px 16px; border: 1px solid var(--color-outline); border-radius: var(--radius-lg); background: #fff; font-weight: 600; cursor: pointer; font-size: 13px; }

.modal-backdrop { position: fixed; inset: 0; background: rgba(15,23,42,.45); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: var(--color-surface); border-radius: var(--radius-xl); padding: 24px; width: 380px; max-width: 92vw; box-shadow: var(--shadow-lg); }
.modal-title { font-family: var(--font-display); font-size: 17px; font-weight: 800; margin: 0 0 4px; }
.modal-sub { margin: 0 0 16px; font-size: 12px; color: var(--color-on-surface-variant); }
.field { display: flex; flex-direction: column; gap: 5px; margin-bottom: 14px; }
.field label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; color: var(--color-on-surface-variant); }
.field input { padding: 10px 12px; border: 1px solid var(--color-outline); border-radius: var(--radius-md); font-size: 14px; background: #fff; }
.field input:focus { outline: none; border-color: var(--color-primary); box-shadow: 0 0 0 3px rgba(40,116,117,.1); }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 8px; }

.spin-icon { animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
