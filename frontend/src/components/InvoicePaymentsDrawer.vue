<template>
  <div class="ipd-overlay" @click.self="$emit('close')">
    <div class="ipd-panel">
      <div class="ipd-head">
        <div>
          <h3>Payments</h3>
          <p class="ipd-sub">{{ invoiceLabel }}</p>
        </div>
        <button class="ipd-close" @click="$emit('close')">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>

      <div class="ipd-body">
        <div v-if="loading" class="ipd-msg">Loading…</div>

        <template v-else-if="data">
          <!-- Summary -->
          <div class="ipd-summary" :class="statusClass">
            <div class="sum-row">
              <span>Invoice total</span><strong>{{ inr(data.total) }}</strong>
            </div>
            <div class="sum-row">
              <span>Received (settled)</span><strong>{{ inr(data.settled_amount) }}</strong>
            </div>
            <div class="sum-row sum-remaining">
              <span>Remaining</span><strong>{{ inr(data.remaining_amount) }}</strong>
            </div>
            <div class="sum-badges">
              <span class="status-pill" :class="'st-' + data.payment_status">{{ statusLabel }}</span>
              <span v-if="data.is_overdue" class="overdue-pill">
                <span class="material-symbols-outlined">warning</span>{{ data.days_overdue }}d overdue
              </span>
              <span v-else class="due-note">Due {{ fmtDate(data.due_date) }}</span>
            </div>
          </div>

          <!-- Existing payments -->
          <ul v-if="data.payments.length" class="ipd-list">
            <li v-for="p in data.payments" :key="p.id" class="ipd-item">
              <div class="pay-main">
                <span class="pay-amt">{{ inr(p.received_amount) }}</span>
                <span v-if="p.tds_percent > 0" class="tds-chip">
                  TDS {{ p.tds_percent }}% · {{ inr(p.tds_amount) }}
                </span>
                <span class="pay-settled">settles {{ inr(p.settled_amount) }}</span>
              </div>
              <div class="pay-meta">
                {{ fmtDate(p.payment_date) }}
                <template v-if="p.note"> · {{ p.note }}</template>
              </div>
              <button class="pay-del" title="Delete payment" @click="removePayment(p)">
                <span class="material-symbols-outlined">delete</span>
              </button>
            </li>
          </ul>
          <p v-else class="ipd-empty">No payments recorded yet.</p>

          <!-- Add payment -->
          <div v-if="data.payment_status !== 'paid'" class="ipd-add">
            <div class="ipd-add-title">Record a payment</div>
            <div class="add-grid">
              <label class="add-field">
                <span>Amount received</span>
                <CurrencyInput v-model="form.received_amount" placeholder="₹ 0.00" />
              </label>
              <label class="add-field">
                <span>Date received</span>
                <input v-model="form.payment_date" type="date" :max="today" />
              </label>
            </div>
            <div class="add-grid">
              <label class="add-field">
                <span>TDS cut?</span>
                <select v-model="form.tds_choice">
                  <option value="0">No TDS</option>
                  <option value="2">2%</option>
                  <option value="10">10%</option>
                  <option value="custom">Custom amount</option>
                </select>
              </label>
              <label v-if="form.tds_choice === 'custom'" class="add-field">
                <span>TDS amount (₹)</span>
                <CurrencyInput v-model="form.tds_amount" placeholder="₹ 0.00" />
              </label>
              <label v-else class="add-field">
                <span>Note (optional)</span>
                <input v-model="form.note" type="text" placeholder="UTR / ref" />
              </label>
            </div>
            <div v-if="form.tds_choice === 'custom'" class="add-grid">
              <label class="add-field span-2">
                <span>Note (optional)</span>
                <input v-model="form.note" type="text" placeholder="UTR / ref" />
              </label>
            </div>
            <p v-if="tdsValue > 0 && Number(form.received_amount) > 0" class="tds-preview">
              Settles <strong>{{ inr(settled) }}</strong>
              (TDS {{ inr(tdsValue) }}<template v-if="form.tds_choice !== 'custom'"> = {{ form.tds_choice }}% of {{ inr(data.subtotal) }} base</template> added back)
            </p>
            <p v-if="overpay" class="add-warn">
              <span class="material-symbols-outlined">warning</span>
              This settles {{ inr(settled) }}, more than the {{ inr(data.remaining_amount) }} remaining.
            </p>
            <div class="add-actions">
              <button class="btn-primary" :disabled="!canAdd || saving" @click="submit">
                {{ saving ? 'Saving…' : 'Add payment' }}
              </button>
            </div>
          </div>
          <div v-else class="paid-banner">
            <span class="material-symbols-outlined">check_circle</span> Fully paid
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import CurrencyInput from './CurrencyInput.vue'
import { invoicesAPI } from '../api/invoices'
import { toLocalDateStr } from '../utils/date'

const props = defineProps({
  invoiceId: { type: Number, required: true },
  invoiceLabel: { type: String, default: '' },
})
const emit = defineEmits(['close', 'changed'])

const loading = ref(true)
const saving = ref(false)
const data = ref(null)
const today = toLocalDateStr()
// tds_choice: '0' | '2' | '10' | 'custom'. Custom lets you type the exact
// rupee amount the client withheld instead of a slab percentage.
const form = ref({ received_amount: null, tds_choice: '0', tds_amount: null, payment_date: today, note: '' })

// TDS on a slab % is levied on the invoice's non-taxed base (subtotal), not on
// the received amount — matching how Indian TDS is actually deducted.
const tdsValue = computed(() => {
  if (form.value.tds_choice === 'custom') {
    return Math.round((Number(form.value.tds_amount) || 0) * 100) / 100
  }
  const t = Number(form.value.tds_choice) || 0
  const base = Number(data.value?.subtotal) || 0
  return Math.round((base * t / 100) * 100) / 100
})
// Full amount this payment settles against the invoice (received + TDS).
const settled = computed(() =>
  Math.round(((Number(form.value.received_amount) || 0) + tdsValue.value) * 100) / 100)
const overpay = computed(() =>
  data.value && settled.value > Number(data.value.remaining_amount) + 0.01)
const canAdd = computed(() => Number(form.value.received_amount) > 0 && !!form.value.payment_date)

const statusLabel = computed(() => ({
  paid: 'Paid', partial: 'Partially paid', unpaid: 'Unpaid',
}[data.value?.payment_status] || ''))
const statusClass = computed(() => 'sum-' + (data.value?.payment_status || 'unpaid'))

const inrFmt = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
function inr(v) { return inrFmt.format(Number(v) || 0) }
function fmtDate(d) {
  return d ? new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : ''
}

async function load() {
  loading.value = true
  try {
    const { data: res } = await invoicesAPI.getPayments(props.invoiceId)
    data.value = res
  } finally {
    loading.value = false
  }
}

async function submit() {
  if (!canAdd.value) return
  saving.value = true
  try {
    const isCustom = form.value.tds_choice === 'custom'
    await invoicesAPI.addPayment(props.invoiceId, {
      received_amount: Number(form.value.received_amount),
      tds_percent: isCustom ? 0 : (Number(form.value.tds_choice) || 0),
      tds_amount: isCustom ? (Number(form.value.tds_amount) || 0) : null,
      payment_date: form.value.payment_date,
      note: form.value.note?.trim() || null,
    })
    form.value = { received_amount: null, tds_choice: '0', tds_amount: null, payment_date: today, note: '' }
    await load()
    emit('changed')
  } catch (e) {
    alert(e.response?.data?.detail || 'Could not add the payment.')
  } finally {
    saving.value = false
  }
}

async function removePayment(p) {
  if (!confirm(`Delete this ${inr(p.received_amount)} payment?`)) return
  try {
    await invoicesAPI.deletePayment(p.id)
    await load()
    emit('changed')
  } catch (e) {
    alert('Could not delete the payment.')
  }
}

onMounted(load)
</script>

<style scoped>
.ipd-overlay {
  position: fixed; inset: 0; background: rgba(15,23,42,.5);
  z-index: 1100; display: flex; justify-content: flex-end;
}
.ipd-panel {
  width: 440px; max-width: 100vw; height: 100%; background: var(--color-surface);
  display: flex; flex-direction: column; box-shadow: -4px 0 24px rgba(0,0,0,.15);
  animation: slideIn .22s ease-out;
}
@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }
.ipd-head {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding: 18px 22px; border-bottom: 1px solid var(--color-outline);
}
.ipd-head h3 { margin: 0; font-size: 16px; font-weight: 800; }
.ipd-sub { margin: 2px 0 0; font-size: 12px; color: var(--color-on-surface-variant); }
.ipd-close { background: none; border: none; cursor: pointer; color: var(--color-on-surface-variant); }
.ipd-body { padding: 18px 22px; overflow-y: auto; flex: 1; }
.ipd-msg, .ipd-empty { font-size: 13px; color: var(--color-on-surface-variant); font-style: italic; }

.ipd-summary {
  border: 1px solid var(--color-outline); border-radius: var(--radius-lg);
  padding: 14px; margin-bottom: 18px; background: var(--color-surface-dim, #f8fafc);
}
.sum-row { display: flex; justify-content: space-between; font-size: 13px; padding: 3px 0; color: var(--color-on-surface); }
.sum-remaining { border-top: 1px solid var(--color-outline); margin-top: 4px; padding-top: 7px; font-weight: 700; }
.sum-remaining strong { color: var(--color-primary); font-size: 15px; }
.sum-badges { display: flex; align-items: center; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
.status-pill { font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: .04em; padding: 3px 10px; border-radius: 999px; }
.st-paid { background: #dcfce7; color: #166534; }
.st-partial { background: #fef3c7; color: #92400e; }
.st-unpaid { background: #e5e7eb; color: #374151; }
.overdue-pill {
  display: inline-flex; align-items: center; gap: 3px; font-size: 11px; font-weight: 800;
  background: #fee2e2; color: #991b1b; padding: 3px 10px; border-radius: 999px;
}
.overdue-pill .material-symbols-outlined { font-size: 13px; }
.due-note { font-size: 11px; color: var(--color-on-surface-variant); }

.ipd-list { list-style: none; margin: 0 0 18px; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.ipd-item {
  display: grid; grid-template-columns: 1fr auto; gap: 2px 8px;
  padding: 10px; border: 1px solid var(--color-outline); border-radius: var(--radius-md);
}
.pay-main { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.pay-amt { font-weight: 700; font-variant-numeric: tabular-nums; }
.tds-chip { font-size: 10px; font-weight: 700; background: #ede9fe; color: #5b21b6; padding: 1px 7px; border-radius: 999px; }
.pay-settled { font-size: 11px; color: var(--color-on-surface-variant); }
.pay-meta { font-size: 11px; color: var(--color-on-surface-variant); grid-column: 1; }
.pay-del { grid-row: 1 / 3; grid-column: 2; background: none; border: none; cursor: pointer; color: var(--color-on-surface-variant); align-self: center; }
.pay-del:hover { color: var(--color-error, #dc2626); }
.pay-del .material-symbols-outlined { font-size: 17px; }

.ipd-add { border-top: 1px dashed var(--color-outline); padding-top: 16px; }
.ipd-add-title { font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: .05em; color: var(--color-on-surface-variant); margin-bottom: 10px; }
.add-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }
.add-field.span-2 { grid-column: 1 / -1; }
.add-field { display: flex; flex-direction: column; gap: 4px; font-size: 11px; font-weight: 700; color: var(--color-on-surface-variant); }
.add-field input, .add-field select {
  padding: 8px 10px; border: 1px solid var(--color-outline); border-radius: var(--radius-md);
  font-size: 13px; font-weight: 500; background: var(--color-surface); color: var(--color-on-surface); outline: none;
}
.add-field input:focus, .add-field select:focus { border-color: var(--color-primary); }
.tds-preview { font-size: 12px; color: var(--color-primary); margin: 0 0 8px; }
.add-warn { display: flex; align-items: center; gap: 5px; font-size: 12px; color: #b45309; margin: 0 0 8px; }
.add-warn .material-symbols-outlined { font-size: 15px; }
.add-actions { display: flex; justify-content: flex-end; }
.btn-primary {
  padding: 9px 18px; border: none; border-radius: var(--radius-md);
  background: var(--color-primary); color: #fff; font-size: 13px; font-weight: 700; cursor: pointer;
}
.btn-primary:disabled { opacity: .5; cursor: not-allowed; }
.paid-banner {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 14px; color: #166534; font-weight: 700; font-size: 14px;
}
</style>
