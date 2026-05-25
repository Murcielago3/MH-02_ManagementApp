<template>
  <AppLayout>
    <div class="page-header">
      <div>
        <h1 class="page-title">Settings</h1>
        <p class="page-sub">Configure company profile, pay calculation, and saved bank accounts</p>
      </div>
    </div>

    <div class="tabs">
      <button
        v-for="t in tabs"
        :key="t.key"
        type="button"
        :class="['tab-btn', { active: activeTab === t.key }]"
        @click="activeTab = t.key"
      >
        <span class="material-symbols-outlined">{{ t.icon }}</span>
        {{ t.label }}
      </button>
    </div>

    <!-- COMPANY PROFILE -->
    <section v-if="activeTab === 'company'" class="panel">
      <div v-if="loading" class="loading-state">Loading settings...</div>
      <form v-else class="form-grid" @submit.prevent="saveSettings">
        <div class="panel-head">
          <h2 class="panel-title">Company Profile</h2>
          <p class="panel-sub">These values are used on every generated invoice PDF</p>
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
          <p class="field-hint">Use new lines to break the address</p>
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

        <div class="panel-head subhead">
          <h3 class="panel-subtitle">Authorized Signatory</h3>
          <p class="panel-sub">Shown in the signature block at the bottom of invoices</p>
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

        <div class="actions">
          <button type="submit" class="btn-primary" :disabled="saving">
            {{ saving ? 'Saving…' : 'Save Company Profile' }}
          </button>
        </div>
      </form>
    </section>

    <!-- COMPENSATION -->
    <section v-if="activeTab === 'compensation'" class="panel">
      <div v-if="loading" class="loading-state">Loading settings...</div>
      <form v-else class="form-grid" @submit.prevent="saveSettings">
        <div class="panel-head">
          <h2 class="panel-title">Compensation Defaults</h2>
          <p class="panel-sub">
            Controls the hourly-rate formula used across project summaries,
            billing, and projected cost.
          </p>
        </div>

        <div class="formula-card">
          <span class="formula-label">Hourly rate =</span>
          <span class="formula-body">
            (Base monthly salary
            <span class="formula-mul">×</span>
            <strong>{{ form.salary_months_per_year || '—' }}</strong>
            / 12)
            <span class="formula-mul">÷</span>
            <strong>{{ form.working_hours_per_month || '—' }}</strong>
          </span>
          <p class="formula-hint">
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

        <div v-if="previewBasePay" class="preview-card">
          <p class="preview-title">Preview</p>
          <p class="preview-line">
            An employee on ₹{{ formatInr(previewBasePay, 0) }} / month →
            <strong>₹{{ formatInr(previewHourly, 2) }}/hr</strong>
          </p>
        </div>

        <div class="actions">
          <button type="submit" class="btn-primary" :disabled="saving">
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
.page-header { margin-bottom: 24px; }
.page-title {
  font-family: var(--font-display);
  font-size: 28px; font-weight: 700;
  color: var(--color-on-surface);
  margin: 0 0 4px; letter-spacing: -0.02em;
}
.page-sub { margin: 0; font-size: 14px; color: var(--color-on-surface-variant); }

.tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--color-outline-variant);
  margin-bottom: 24px;
  flex-wrap: wrap;
}
.tab-btn {
  display: inline-flex; align-items: center; gap: 6px;
  background: transparent; border: none;
  padding: 12px 20px;
  font-family: var(--font-display); font-size: 14px; font-weight: 600;
  color: var(--color-on-surface-variant);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color .15s, border-color .15s, background .15s;
  border-radius: 8px 8px 0 0;
}
.tab-btn:hover { background: rgba(40,116,117,0.06); color: var(--color-on-surface); }
.tab-btn.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}
.tab-btn .material-symbols-outlined { font-size: 18px; }

.panel {
  background: #fff;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 28px;
}
.loading-state { padding: 32px; text-align: center; color: var(--color-on-surface-variant); }

.form-grid { display: flex; flex-direction: column; gap: 20px; max-width: 760px; }
.panel-head { margin-bottom: 0; }
.panel-head.subhead { margin-top: 12px; padding-top: 16px; border-top: 1px solid var(--color-outline-variant); }
.panel-title { font-family: var(--font-display); font-size: 18px; font-weight: 700; margin: 0 0 4px; color: var(--color-on-surface); }
.panel-subtitle { font-family: var(--font-display); font-size: 15px; font-weight: 700; margin: 0 0 4px; color: var(--color-on-surface); }
.panel-sub { margin: 0; font-size: 13px; color: var(--color-on-surface-variant); }

.field-row { display: flex; gap: 16px; flex-wrap: wrap; }
.field-row.two-col > .field { flex: 1 1 280px; min-width: 0; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label {
  font-size: 12px; font-weight: 600;
  color: var(--color-on-surface-variant);
}
.field input, .field textarea {
  padding: 10px 12px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  font-family: var(--font-body); font-size: 14px;
  background: #fff;
  resize: vertical;
}
.field input:focus, .field textarea:focus {
  outline: none; border-color: var(--color-primary);
  box-shadow: 0 0 0 1px var(--color-primary);
}
.field-hint { margin: 0; font-size: 11px; color: var(--color-on-surface-variant); }

.formula-card {
  background: #f8fafc;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 14px 18px;
  display: flex; flex-direction: column; gap: 4px;
}
.formula-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--color-on-surface-variant); font-weight: 700; }
.formula-body { font-family: var(--font-mono, ui-monospace, monospace); font-size: 14px; color: var(--color-on-surface); }
.formula-mul { color: var(--color-primary); padding: 0 4px; font-weight: 700; }
.formula-hint { margin: 4px 0 0; font-size: 11px; color: var(--color-on-surface-variant); }
.formula-hint code {
  background: #e2e8f0;
  padding: 1px 4px; border-radius: 3px;
  font-size: 11px;
}

.preview-card {
  background: #ecfeff;
  border: 1px solid #a5f3fc;
  border-radius: var(--radius-lg);
  padding: 12px 16px;
}
.preview-title { margin: 0 0 4px; font-size: 11px; font-weight: 700; text-transform: uppercase; color: #0e7490; letter-spacing: 0.06em; }
.preview-line { margin: 0; font-size: 14px; color: var(--color-on-surface); }

.actions { display: flex; gap: 8px; justify-content: flex-end; padding-top: 8px; }
.btn-primary {
  padding: 10px 20px; border: none;
  border-radius: var(--radius-lg);
  background: var(--color-primary); color: #fff;
  font-family: var(--font-body); font-size: 14px; font-weight: 600;
  cursor: pointer; transition: opacity .15s;
}
.btn-primary:hover { opacity: 0.92; }
.btn-primary:disabled { opacity: 0.55; cursor: not-allowed; }
</style>
