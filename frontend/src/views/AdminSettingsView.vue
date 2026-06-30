<template>
  <AppLayout>
    <!-- Page Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Settings</h1>
        <p class="page-subtitle">Configure company profile, compensation defaults, and bank accounts</p>
      </div>
    </div>

    <!-- Tabs -->
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

    <!-- COMPANY PROFILE -->
    <section v-if="activeTab === 'company'" class="panel">
      <div v-if="loading" class="loading-state">
        <span class="material-symbols-outlined spin-icon">progress_activity</span>
        Loading settings…
      </div>
      <form v-else class="settings-form" @submit.prevent="saveSettings">
        <div class="settings-group">
          <div class="group-header">
            <h2 class="group-title">Company Profile</h2>
            <p class="group-desc">These values appear on every generated invoice PDF</p>
          </div>

          <div class="field-row two-col">
            <div class="field">
              <label>Company Name</label>
              <input v-model="form.company_name" type="text" placeholder="Studio MH02 LLP" />
            </div>
            <div class="field">
              <label>GSTIN</label>
              <input v-model="form.company_gstin" type="text" placeholder="27AEQFS5715Q1Z1" />
            </div>
          </div>

          <div class="field">
            <label>Address</label>
            <textarea
              v-model="form.company_address"
              rows="3"
              placeholder="Line 1&#10;City, State PIN"
            />
            <p class="field-hint">Use new lines to break the address into multiple lines on the invoice</p>
          </div>

          <div class="field-row two-col">
            <div class="field">
              <label>Phone</label>
              <input v-model="form.company_phone" type="text" placeholder="9769911588" />
            </div>
            <div class="field">
              <label>Email</label>
              <input v-model="form.company_email" type="email" placeholder="info@studio.com" />
            </div>
          </div>
        </div>

        <div class="settings-group">
          <div class="group-header">
            <h2 class="group-title">Authorized Signatory</h2>
            <p class="group-desc">Shown in the signature block at the bottom of invoices</p>
          </div>
          <div class="field-row two-col">
            <div class="field">
              <label>Signatory Name</label>
              <input v-model="form.company_signatory_name" type="text" placeholder="Srujan Gadgil" />
            </div>
            <div class="field">
              <label>Signatory Role</label>
              <input v-model="form.company_signatory_role" type="text" placeholder="Partner" />
            </div>
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn-primary" :disabled="saving">
            <span v-if="saving" class="material-symbols-outlined spin-icon">progress_activity</span>
            <span class="material-symbols-outlined" v-else>save</span>
            {{ saving ? 'Saving…' : 'Save Company Profile' }}
          </button>
        </div>
      </form>
    </section>

    <!-- COMPENSATION -->
    <section v-if="activeTab === 'compensation'" class="panel">
      <div v-if="loading" class="loading-state">
        <span class="material-symbols-outlined spin-icon">progress_activity</span>
        Loading settings…
      </div>
      <form v-else class="settings-form" @submit.prevent="saveSettings">
        <div class="settings-group">
          <div class="group-header">
            <h2 class="group-title">Compensation Defaults</h2>
            <p class="group-desc">
              Controls the hourly-rate formula used across project summaries, billing, and projected cost.
            </p>
          </div>

          <div class="formula-card">
            <div class="formula-label-row">
              <span class="formula-chip">Formula</span>
              <span class="formula-text">Hourly rate</span>
            </div>
            <div class="formula-body">
              (Base monthly salary
              <span class="formula-op">×</span>
              <strong>{{ form.salary_months_per_year || '—' }}</strong>
              / 12)
              <span class="formula-op">÷</span>
              <strong>{{ form.working_hours_per_month || '—' }}</strong>
            </div>
            <p class="formula-note">
              Employees with an explicit <code>salary_hour</code> on their profile bypass this formula.
            </p>
          </div>

          <div class="field-row two-col">
            <div class="field">
              <label>Working Hours per Month</label>
              <input
                v-model.number="form.working_hours_per_month"
                type="number"
                min="1"
                step="1"
                placeholder="160"
              />
              <p class="field-hint">Default: 160 (20 working days × 8 hours)</p>
            </div>
            <div class="field">
              <label>Salary Months per Year</label>
              <input
                v-model.number="form.salary_months_per_year"
                type="number"
                min="1"
                step="0.1"
                placeholder="13"
              />
              <p class="field-hint">Default: 13 (12 months + 1 annual bonus equivalent)</p>
            </div>
          </div>
        </div>

        <div v-if="previewBasePay" class="preview-card">
          <div class="preview-header">
            <span class="material-symbols-outlined preview-icon">calculate</span>
            <span class="preview-title">Live Preview</span>
          </div>
          <p class="preview-line">
            An employee on ₹{{ formatInr(previewBasePay, 0) }} / month earns
            <strong class="preview-rate">₹{{ formatInr(previewHourly, 2) }}/hr</strong>
          </p>
        </div>

        <div class="settings-group" style="padding-left:0; padding-right:0; border-bottom:none;">
          <div class="group-header">
            <h2 class="group-title">Payroll — TDS</h2>
            <p class="group-desc">
              TDS percentage deducted from base salary on every salary slip. Can be adjusted per-slip before approval.
            </p>
          </div>
          <div class="field-row two-col">
            <div class="field">
              <label>TDS Percentage (%)</label>
              <input
                v-model.number="form.tds_percent"
                type="number"
                min="0"
                max="100"
                step="0.5"
                placeholder="10"
              />
              <p class="field-hint">Applied as: base salary × TDS% ÷ 100</p>
            </div>
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn-primary" :disabled="saving">
            <span v-if="saving" class="material-symbols-outlined spin-icon">progress_activity</span>
            <span class="material-symbols-outlined" v-else>save</span>
            {{ saving ? 'Saving…' : 'Save Compensation Defaults' }}
          </button>
        </div>
      </form>
    </section>

    <!-- BANK ACCOUNTS -->
    <section v-if="activeTab === 'bank'" class="panel">
      <BankAccountsManager />
    </section>

    <ToastNotification v-if="toastMsg" :message="toastMsg" :type="toastType" @done="toastMsg = ''" />
  </AppLayout>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import BankAccountsManager from '../components/BankAccountsManager.vue'
import ToastNotification from '../components/ToastNotification.vue'
import { settingsAPI } from '../api/settings'
import { formatInr } from '../utils/currency'

const tabs = [
  { key: 'company', label: 'Company Profile', icon: 'business' },
  { key: 'compensation', label: 'Compensation', icon: 'payments' },
  { key: 'bank', label: 'Bank Accounts', icon: 'account_balance' },
]
const activeTab = ref('company')

const loading = ref(true)
const saving = ref(false)
const toastMsg = ref('')
const toastType = ref('success')

const form = reactive({
  company_name: '',
  company_address: '',
  company_gstin: '',
  company_phone: '',
  company_email: '',
  company_signatory_name: '',
  company_signatory_role: '',
  working_hours_per_month: 160,
  salary_months_per_year: 13,
  tds_percent: 10,
})

function toast(msg, type = 'success') {
  toastType.value = type
  toastMsg.value = msg
}

function apiErr(e) {
  const d = e.response?.data?.detail
  if (Array.isArray(d)) return d.map((x) => x.msg || JSON.stringify(x)).join(' ')
  if (typeof d === 'object' && d !== null) return JSON.stringify(d)
  return d || e.message || 'Request failed'
}

async function loadSettings() {
  loading.value = true
  try {
    const res = await settingsAPI.get()
    Object.assign(form, res.data)
  } catch (e) {
    toast(apiErr(e), 'error')
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  try {
    const res = await settingsAPI.update({ ...form })
    Object.assign(form, res.data)
    toast('Settings saved.')
  } catch (e) {
    toast(apiErr(e), 'error')
  } finally {
    saving.value = false
  }
}

const previewBasePay = ref(50000)
const previewHourly = computed(() => {
  const bp = Number(previewBasePay.value) || 0
  const smpy = Number(form.salary_months_per_year) || 0
  const whpm = Number(form.working_hours_per_month) || 0
  if (bp <= 0 || smpy <= 0 || whpm <= 0) return 0
  return Math.round(((bp * smpy / 12) / whpm) * 100) / 100
})

onMounted(loadSettings)
</script>

<style scoped>
/* ── Page Header ── */
.page-header { margin-bottom: 24px; }
.page-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 800;
  color: var(--color-on-surface);
  margin: 0 0 4px;
  letter-spacing: -0.01em;
}
.page-subtitle { margin: 0; font-size: 13px; color: var(--color-on-surface-variant); }

/* ── Tabs ── */
.tabs-bar {
  display: flex;
  gap: 2px;
  border-bottom: 1px solid var(--color-outline);
  margin-bottom: 24px;
}
.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  background: transparent;
  border: none;
  padding: 11px 20px;
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 700;
  color: var(--color-on-surface-variant);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  border-radius: 8px 8px 0 0;
  transition: color 0.15s, background 0.15s;
}
.tab-btn:hover { background: rgba(40,116,117,0.05); color: var(--color-on-surface); }
.tab-btn.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}
.tab-icon { font-size: 18px; }

/* ── Panel ── */
.panel {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.loading-state {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 40px;
  color: var(--color-on-surface-variant);
  font-size: 14px;
  justify-content: center;
}

/* ── Settings Form ── */
.settings-form {
  max-width: 720px;
}

.settings-group {
  padding: 28px 32px;
  border-bottom: 1px solid var(--color-outline);
}
.settings-group:last-of-type { border-bottom: none; }

.group-header {
  margin-bottom: 20px;
}
.group-title {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 800;
  margin: 0 0 4px;
  color: var(--color-on-surface);
}
.group-desc { margin: 0; font-size: 13px; color: var(--color-on-surface-variant); }

/* ── Fields ── */
.field-row { display: flex; gap: 16px; flex-wrap: wrap; }
.field-row.two-col > .field { flex: 1 1 240px; min-width: 0; }
.field { display: flex; flex-direction: column; gap: 5px; margin-bottom: 16px; }
.field:last-child { margin-bottom: 0; }

.field label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-on-surface-variant);
}

.field input,
.field textarea {
  padding: 10px 12px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-on-surface);
  background: #fff;
  resize: vertical;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.field input:focus,
.field textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(40,116,117,0.1);
}
.field-hint { margin: 0; font-size: 11px; color: var(--color-on-surface-variant); }

/* ── Formula Card ── */
.formula-card {
  background: var(--color-surface-dim);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  margin-bottom: 20px;
}
.formula-label-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.formula-chip {
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  padding: 2px 8px;
  border-radius: var(--radius-full);
}
.formula-text {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-on-surface-variant);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.formula-body {
  font-family: ui-monospace, 'Courier New', monospace;
  font-size: 14px;
  color: var(--color-on-surface);
  margin-bottom: 8px;
}
.formula-op { color: var(--color-primary); font-weight: 800; padding: 0 4px; }
.formula-note {
  margin: 0;
  font-size: 11px;
  color: var(--color-on-surface-variant);
}
.formula-note code {
  background: var(--color-outline);
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 11px;
}

/* ── Preview Card ── */
.preview-card {
  background: #ecfdf5;
  border: 1px solid #6ee7b7;
  border-radius: var(--radius-lg);
  padding: 14px 20px;
  margin-bottom: 20px;
}
.preview-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}
.preview-icon { font-size: 16px; color: #059669; }
.preview-title { font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.06em; color: #065f46; }
.preview-line { margin: 0; font-size: 14px; color: #065f46; }
.preview-rate { color: #047857; }

/* ── Form Actions ── */
.form-actions {
  padding: 20px 32px 28px;
  display: flex;
  justify-content: flex-end;
}

/* ── Buttons ── */
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 10px 20px;
  border: none;
  border-radius: var(--radius-lg);
  background: var(--color-primary);
  color: #fff;
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.15s;
  box-shadow: 0 2px 8px rgba(40,116,117,0.18);
}
.btn-primary:hover { opacity: 0.88; }
.btn-primary:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-primary .material-symbols-outlined { font-size: 17px; }

/* ── Spinner ── */
.spin-icon { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .tabs-bar { overflow-x: auto; -webkit-overflow-scrolling: touch; flex-wrap: nowrap; white-space: nowrap; }
  .tab-btn { padding: 10px 14px; }
  .settings-form { max-width: 100%; }
  .settings-group { padding: 18px 16px; }
  .field-row.two-col { flex-direction: column; }
  .push-setting-grid { grid-template-columns: 1fr; }
  .form-actions { padding: 16px; }
}
</style>
