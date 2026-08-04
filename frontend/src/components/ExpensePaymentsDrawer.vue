<template>
  <div class="epd-overlay" @click.self="$emit('close')">
    <div class="epd-panel">
      <div class="epd-head">
        <div>
          <h3>Payments</h3>
          <p class="epd-sub">{{ expense.title }} · {{ inr(expense.amount) }}</p>
        </div>
        <button class="epd-close" @click="$emit('close')">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>

      <div class="epd-body">
        <div v-if="loading" class="epd-msg">Loading…</div>
        <template v-else-if="data">
          <div class="epd-summary">
            <div class="sum-row"><span>Bill total</span><strong>{{ inr(data.total) }}</strong></div>
            <div class="sum-row"><span>Paid</span><strong>{{ inr(data.paid_amount) }}</strong></div>
            <div class="sum-row sum-remaining"><span>Remaining</span><strong>{{ inr(data.remaining_amount) }}</strong></div>
            <span class="status-pill" :class="'st-' + data.payment_status">{{ statusLabel }}</span>
          </div>

          <ul v-if="data.payments.length" class="epd-list">
            <li v-for="p in data.payments" :key="p.id" class="epd-item">
              <div>
                <span class="pay-amt">{{ inr(p.amount) }}</span>
                <span class="pay-meta">{{ fmtDate(p.payment_date) }}<template v-if="p.note"> · {{ p.note }}</template></span>
              </div>
              <button class="pay-del" @click="remove(p)" title="Delete">
                <span class="material-symbols-outlined">delete</span>
              </button>
            </li>
          </ul>
          <p v-else class="epd-empty">No payments recorded yet.</p>

          <div v-if="data.payment_status !== 'paid'" class="epd-add">
            <div class="epd-add-title">Record a payment</div>
            <div class="add-grid">
              <label class="add-field"><span>Amount paid</span>
                <CurrencyInput v-model="form.amount" placeholder="₹ 0.00" />
              </label>
              <label class="add-field"><span>Date</span>
                <input v-model="form.payment_date" type="date" :max="today" />
              </label>
            </div>
            <label class="add-field"><span>Note (optional)</span>
              <input v-model="form.note" type="text" placeholder="UTR / ref" />
            </label>
            <p v-if="overpay" class="add-warn">
              <span class="material-symbols-outlined">warning</span>
              More than the {{ inr(data.remaining_amount) }} remaining.
            </p>
            <div class="add-actions">
              <button class="btn-primary" :disabled="!(Number(form.amount) > 0) || saving" @click="submit">
                {{ saving ? 'Saving…' : 'Add payment' }}
              </button>
            </div>
          </div>
          <div v-else class="paid-banner"><span class="material-symbols-outlined">check_circle</span> Fully paid</div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import CurrencyInput from './CurrencyInput.vue'
import { expensesAPI } from '../api/expenses'
import { toLocalDateStr } from '../utils/date'

const props = defineProps({ expense: { type: Object, required: true } })
const emit = defineEmits(['close', 'changed'])

const loading = ref(true)
const saving = ref(false)
const data = ref(null)
const today = toLocalDateStr()
const form = ref({ amount: null, payment_date: today, note: '' })

const overpay = computed(() => data.value && Number(form.value.amount) > Number(data.value.remaining_amount) + 0.01)
const statusLabel = computed(() => ({ paid: 'Paid', partial: 'Partially paid', unpaid: 'Unpaid' }[data.value?.payment_status] || ''))

const inrFmt = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
function inr(v) { return inrFmt.format(Number(v) || 0) }
function fmtDate(d) { return d ? new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '' }

async function load() {
  loading.value = true
  try { data.value = (await expensesAPI.getPayments(props.expense.id)).data }
  finally { loading.value = false }
}
async function submit() {
  if (!(Number(form.value.amount) > 0)) return
  saving.value = true
  try {
    await expensesAPI.addPayment(props.expense.id, {
      amount: Number(form.value.amount), payment_date: form.value.payment_date, note: form.value.note?.trim() || null,
    })
    form.value = { amount: null, payment_date: today, note: '' }
    await load(); emit('changed')
  } catch (e) { alert(e.response?.data?.detail || 'Could not add payment.') }
  finally { saving.value = false }
}
async function remove(p) {
  if (!confirm(`Delete this ${inr(p.amount)} payment?`)) return
  try { await expensesAPI.deletePayment(p.id); await load(); emit('changed') }
  catch (e) { alert('Could not delete.') }
}
onMounted(load)
</script>

<style scoped>
.epd-overlay { position: fixed; inset: 0; background: rgba(15,23,42,.5); z-index: 1100; display: flex; justify-content: flex-end; }
.epd-panel { width: 400px; max-width: 100vw; height: 100%; background: var(--color-surface); display: flex; flex-direction: column; box-shadow: -4px 0 24px rgba(0,0,0,.15); animation: slideIn .22s ease-out; }
@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }
.epd-head { display: flex; justify-content: space-between; align-items: flex-start; padding: 18px 22px; border-bottom: 1px solid var(--color-outline); }
.epd-head h3 { margin: 0; font-size: 16px; font-weight: 800; }
.epd-sub { margin: 2px 0 0; font-size: 12px; color: var(--color-on-surface-variant); }
.epd-close { background: none; border: none; cursor: pointer; color: var(--color-on-surface-variant); }
.epd-body { padding: 18px 22px; overflow-y: auto; flex: 1; }
.epd-msg, .epd-empty { font-size: 13px; color: var(--color-on-surface-variant); font-style: italic; }
.epd-summary { border: 1px solid var(--color-outline); border-radius: var(--radius-lg); padding: 14px; margin-bottom: 18px; background: var(--color-surface-dim, #f8fafc); }
.sum-row { display: flex; justify-content: space-between; font-size: 13px; padding: 3px 0; }
.sum-remaining { border-top: 1px solid var(--color-outline); margin-top: 4px; padding-top: 7px; font-weight: 700; }
.sum-remaining strong { color: var(--color-primary); font-size: 15px; }
.status-pill { display: inline-block; margin-top: 10px; font-size: 11px; font-weight: 800; text-transform: uppercase; padding: 3px 10px; border-radius: 999px; }
.st-paid { background: #dcfce7; color: #166534; } .st-partial { background: #fef3c7; color: #92400e; } .st-unpaid { background: #e5e7eb; color: #374151; }
.epd-list { list-style: none; margin: 0 0 18px; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.epd-item { display: flex; justify-content: space-between; align-items: center; padding: 10px; border: 1px solid var(--color-outline); border-radius: var(--radius-md); }
.pay-amt { font-weight: 700; margin-right: 8px; } .pay-meta { font-size: 11px; color: var(--color-on-surface-variant); }
.pay-del { background: none; border: none; cursor: pointer; color: var(--color-on-surface-variant); } .pay-del:hover { color: var(--color-error, #dc2626); }
.pay-del .material-symbols-outlined { font-size: 17px; }
.epd-add { border-top: 1px dashed var(--color-outline); padding-top: 16px; }
.epd-add-title { font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: .05em; color: var(--color-on-surface-variant); margin-bottom: 10px; }
.add-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }
.add-field { display: flex; flex-direction: column; gap: 4px; font-size: 11px; font-weight: 700; color: var(--color-on-surface-variant); margin-bottom: 10px; }
.add-field input { padding: 8px 10px; border: 1px solid var(--color-outline); border-radius: var(--radius-md); font-size: 13px; font-weight: 500; background: var(--color-surface); color: var(--color-on-surface); outline: none; }
.add-field input:focus { border-color: var(--color-primary); }
.add-warn { display: flex; align-items: center; gap: 5px; font-size: 12px; color: #b45309; margin: 0 0 8px; }
.add-warn .material-symbols-outlined { font-size: 15px; }
.add-actions { display: flex; justify-content: flex-end; }
.btn-primary { padding: 9px 18px; border: none; border-radius: var(--radius-md); background: var(--color-primary); color: #fff; font-size: 13px; font-weight: 700; cursor: pointer; }
.btn-primary:disabled { opacity: .5; cursor: not-allowed; }
.paid-banner { display: flex; align-items: center; justify-content: center; gap: 6px; padding: 14px; color: #166534; font-weight: 700; }
</style>
