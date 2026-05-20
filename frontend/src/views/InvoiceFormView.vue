<template>
  <AppLayout>
    <div class="page-header">
      <h2>Create New Invoice</h2>
    </div>

    <div class="invoice-form-layout">
      <!-- Main Form Area -->
      <div class="form-main">
        <form @submit.prevent="submitInvoice" id="invoiceForm">
          
          <!-- Section 1: Type & Number -->
          <div class="form-section">
            <h3 class="section-title">Invoice Type</h3>
            <div class="type-toggles">
              <button 
                type="button" 
                class="type-btn" 
                :class="{ active: form.invoice_type === 'tax' }"
                @click="form.invoice_type = 'tax'"
              >
                TAX INVOICE
              </button>
              <button 
                type="button" 
                class="type-btn" 
                :class="{ active: form.invoice_type === 'proforma' }"
                @click="form.invoice_type = 'proforma'"
              >
                PROFORMA INVOICE
              </button>
            </div>
            
            <div v-if="form.invoice_type === 'tax'" class="form-group mt-16">
              <label>Invoice Number {{ taxType === 'IGST' ? '(Optional)' : '*' }}</label>
              <input v-model="form.invoice_number" type="text" placeholder="e.g. AO-006" :required="taxType !== 'IGST'" />
            </div>
          </div>

          <!-- Section 2: Date & Place of Supply -->
          <div class="form-section row-2">
            <div class="form-group">
              <label>Invoice Date *</label>
              <input v-model="form.invoice_date" type="date" required />
            </div>
            <div class="form-group">
              <label>Place of Supply</label>
              <input v-model="form.place_of_supply" type="text" placeholder="e.g. Maharashtra" />
            </div>
          </div>


          <!-- Section 5: Project -->
          <div class="form-section">
            <div class="form-group">
              <label>Project *</label>
              <select v-model="form.project_id" @change="onProjectSelect" required>
                <option :value="null">— Select Project —</option>
                <option v-for="p in projects" :key="p.id" :value="p.id">
                  {{ p.project_number }} - {{ p.name }}
                </option>
              </select>
            </div>
            <div v-if="selectedClient" class="client-pill mt-16">
              Linked Client: <strong>{{ selectedClient.name }}</strong> | GSTIN: {{ selectedClient.gstin || 'N/A' }}
            </div>
            <div v-if="taxTypeIndicator" class="tax-indicator mt-8" :class="taxTypeIndicator.class">
              {{ taxTypeIndicator.text }}
            </div>
          </div>

          <!-- Section 4: Bill To / Ship To -->
          <div class="form-section">
            <h3 class="section-title">Billing Details</h3>
            <div class="billing-grid">
              <!-- Bill To -->
              <div class="bill-to-col">
                <div class="col-header">Bill To</div>
                <div class="form-group">
                  <label>Name *</label>
                  <input v-model="form.bill_to_name" type="text" required />
                </div>
                <div class="form-group">
                  <label>Address</label>
                  <textarea v-model="form.bill_to_address" rows="3"></textarea>
                </div>
                <div class="form-group">
                  <label>GSTIN</label>
                  <input v-model="form.bill_to_gstin" type="text" />
                </div>
              </div>
              
              <!-- Ship To -->
              <div class="ship-to-col">
                <div class="col-header">
                  Ship To
                  <label class="same-as-checkbox">
                    <input type="checkbox" v-model="sameAsBillTo" @change="handleSameAsChange" />
                    Same as Bill To
                  </label>
                </div>
                <div class="form-group">
                  <label>Name</label>
                  <input v-model="form.ship_to_name" type="text" :disabled="sameAsBillTo" />
                </div>
                <div class="form-group">
                  <label>Address</label>
                  <textarea v-model="form.ship_to_address" rows="3" :disabled="sameAsBillTo"></textarea>
                </div>
                <div class="form-group">
                  <label>GSTIN</label>
                  <input v-model="form.ship_to_gstin" type="text" :disabled="sameAsBillTo" />
                </div>
              </div>
            </div>
          </div>

          <!-- Section 6: Items -->
          <div class="form-section">
            <h3 class="section-title">Items</h3>
            <table class="items-table">
              <thead>
                <tr>
                  <th style="width: 40px">#</th>
                  <th>Description</th>
                  <th style="width: 120px">HSN/SAC</th>
                  <th style="width: 160px">Amount (₹)</th>
                  <th style="width: 50px"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in form.items" :key="idx" class="item-row">
                  <td class="text-center">{{ idx + 1 }}</td>
                  <td>
                    <input v-model="item.description" type="text" required placeholder="Item description" />
                  </td>
                  <td>
                    <input v-model="item.hsn_sac" type="text" placeholder="HSN" />
                  </td>
                  <td>
                    <input v-model.number="item.amount" type="number" min="0" step="0.01" required />
                  </td>
                  <td class="text-center">
                    <button type="button" class="icon-btn text-danger" @click="removeItem(idx)" :disabled="form.items.length <= 1">
                      <span class="material-symbols-outlined">close</span>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
            <button type="button" class="btn-text mt-16" @click="addItem">
              + Add Item
            </button>
          </div>

          <!-- Section 8: Bank Account -->
          <div class="form-section">
            <h3 class="section-title">Bank Account</h3>
            <div v-if="bankAccounts.length === 0" class="bank-warning">
              No bank accounts saved. <router-link to="/admin/settings/bank">Add bank account →</router-link>
            </div>
            <div v-else class="form-group">
              <select v-model="form.bank_account_id">
                <option :value="null">— Select Bank Account —</option>
                <option v-for="b in bankAccounts" :key="b.id" :value="b.id">
                  {{ b.bank_name }} — {{ b.account_number }} ({{ b.account_holder_name }})
                </option>
              </select>
            </div>
          </div>
        </form>
      </div>

      <!-- Sidebar Summary Area -->
      <div class="form-sidebar">
        <div class="summary-card">
          <h3 class="summary-title">Summary</h3>
          
          <div class="summary-row">
            <span>Sub Total</span>
            <span class="font-mono">₹{{ formatAmount(liveTotals.subtotal) }}</span>
          </div>

          <div v-if="taxType === 'CGST_SGST'" class="summary-row">
            <span>CGST (9%)</span>
            <span class="font-mono">₹{{ formatAmount(liveTotals.cgst) }}</span>
          </div>
          <div v-if="taxType === 'CGST_SGST'" class="summary-row">
            <span>SGST (9%)</span>
            <span class="font-mono">₹{{ formatAmount(liveTotals.sgst) }}</span>
          </div>
          
          <div v-if="taxType === 'IGST'" class="summary-row">
            <span>IGST (18%)</span>
            <span class="font-mono">₹{{ formatAmount(liveTotals.igst) }}</span>
          </div>

          <div class="summary-row total-row">
            <span>Total</span>
            <span class="font-mono">₹{{ formatAmount(liveTotals.total) }}</span>
          </div>

          <div class="words-total mt-16">
            {{ numberToWords(liveTotals.total) }}
          </div>

          <button 
            type="submit" 
            form="invoiceForm" 
            class="btn-primary w-full mt-24" 
            :disabled="!isFormValid || submitting"
          >
            {{ submitting ? 'Creating...' : 'Create Invoice' }}
          </button>
        </div>
      </div>
    </div>

    <ToastNotification v-if="toastMsg" :message="toastMsg" :type="toastType" @done="toastMsg = ''" />
  </AppLayout>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import ToastNotification from '../components/ToastNotification.vue'
import { invoicesAPI } from '../api/invoices'
import { bankAccountsAPI } from '../api/bankAccounts'
import { projectsAPI } from '../api/projects'
import { clientsAPI } from '../api/clients'

const router = useRouter()

const form = reactive({
  invoice_type: 'tax',
  invoice_number: '',
  invoice_date: new Date().toISOString().split('T')[0],
  place_of_supply: 'Maharashtra',
  project_id: null,
  client_id: null,
  bill_to_name: '',
  bill_to_address: '',
  bill_to_gstin: '',
  ship_to_name: '',
  ship_to_address: '',
  ship_to_gstin: '',
  subject: '',
  bank_account_id: null,
  items: [
    { description: '', hsn_sac: '', amount: 0 }
  ]
})

const sameAsBillTo = ref(false)
const projects = ref([])
const bankAccounts = ref([])
const selectedClient = ref(null)
const submitting = ref(false)

const toastMsg = ref('')
const toastType = ref('success')

const showToast = (msg, type = 'success') => {
  toastMsg.value = msg
  toastType.value = type
}

onMounted(async () => {
  try {
    const [pRes, bRes] = await Promise.all([
      projectsAPI.getProjects(),
      bankAccountsAPI.getBankAccounts()
    ])
    projects.value = pRes.data
    bankAccounts.value = bRes.data
  } catch (err) {
    showToast('Failed to load required data', 'error')
  }
})

// Watch bill to fields to sync ship to if checked
watch(
  () => [form.bill_to_name, form.bill_to_address, form.bill_to_gstin],
  ([name, addr, gst]) => {
    if (sameAsBillTo.value) {
      form.ship_to_name = name
      form.ship_to_address = addr
      form.ship_to_gstin = gst
    }
  }
)

const handleSameAsChange = () => {
  if (sameAsBillTo.value) {
    form.ship_to_name = form.bill_to_name
    form.ship_to_address = form.bill_to_address
    form.ship_to_gstin = form.bill_to_gstin
  }
}

const onProjectSelect = () => {
  if (!form.project_id) {
    selectedClient.value = null
    form.client_id = null
    form.subject = ''
    return
  }
  const proj = projects.value.find(p => p.id === form.project_id)
  if (proj) {
    form.subject = proj.name
    if (proj.client) {
      selectedClient.value = proj.client
      form.client_id = proj.client.id
      
      // Auto populate Bill To
      form.bill_to_name = proj.client.name
      form.bill_to_address = proj.client.address || ''
      form.bill_to_gstin = proj.client.gstin || ''
    } else {
      selectedClient.value = null
      form.client_id = null
    }
  } else {
    selectedClient.value = null
    form.client_id = null
    form.subject = ''
  }
}

const taxType = computed(() => {
  const gst = form.bill_to_gstin
  if (gst && gst.length >= 2 && !gst.startsWith('27')) return 'IGST'
  return 'CGST_SGST'
})

const taxTypeIndicator = computed(() => {
  if (!form.bill_to_gstin) return null
  if (taxType.value === 'CGST_SGST') {
    return { text: 'Tax: CGST + SGST (9% + 9%)', class: 'indicator-teal' }
  }
  return { text: 'Tax: IGST (18%)', class: 'indicator-amber' }
})

const liveTotals = computed(() => {
  const subtotal = form.items.reduce((s, i) => s + (Number(i.amount) || 0), 0)
  let cgst = 0, sgst = 0, igst = 0
  
  if (taxType.value === 'CGST_SGST') {
    cgst = subtotal * 0.09
    sgst = subtotal * 0.09
  } else {
    igst = subtotal * 0.18
  }
  
  return {
    subtotal,
    cgst,
    sgst,
    igst,
    total: subtotal + cgst + sgst + igst
  }
})

const isFormValid = computed(() => {
  if (form.invoice_type === 'tax' && taxType.value !== 'IGST' && !form.invoice_number) return false
  if (!form.project_id) return false
  if (!form.bill_to_name) return false
  if (form.items.length === 0) return false
  const validItems = form.items.filter(i => i.description.trim() !== '' && i.amount > 0)
  if (validItems.length === 0) return false
  return true
})

const addItem = () => {
  form.items.push({ description: '', hsn_sac: '', amount: 0 })
}

const removeItem = (idx) => {
  if (form.items.length > 1) {
    form.items.splice(idx, 1)
  }
}

const formatAmount = (val) => {
  return Number(val || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function numberToWords(amount) {
  const ones = ['', 'One', 'Two', 'Three', 'Four', 'Five',
    'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Eleven',
    'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
    'Seventeen', 'Eighteen', 'Nineteen']
  const tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty',
    'Sixty', 'Seventy', 'Eighty', 'Ninety']

  function wordsUnderThousand(n) {
    if (n === 0) return ''
    if (n < 20) return ones[n]
    if (n < 100) return tens[Math.floor(n/10)] + 
      (n%10 ? ' ' + ones[n%10] : '')
    return ones[Math.floor(n/100)] + ' Hundred' + 
      (n%100 ? ' ' + wordsUnderThousand(n%100) : '')
  }

  let n = Math.floor(amount)
  if (n === 0) return 'Zero Rupees Only'

  const crore = Math.floor(n / 10000000); n %= 10000000
  const lakh = Math.floor(n / 100000); n %= 100000
  const thousand = Math.floor(n / 1000); n %= 1000
  const rest = n

  const parts = []
  if (crore) parts.push(wordsUnderThousand(crore) + ' Crore')
  if (lakh) parts.push(wordsUnderThousand(lakh) + ' Lakh')
  if (thousand) parts.push(wordsUnderThousand(thousand) + ' Thousand')
  if (rest) parts.push(wordsUnderThousand(rest))

  return 'Indian Rupee ' + parts.join(' ') + ' Only'
}

const submitInvoice = async () => {
  if (!isFormValid.value) return
  submitting.value = true
  
  // Clean empty items
  const payload = { ...form }
  payload.items = payload.items.filter(i => i.description.trim() !== '')

  try {
    await invoicesAPI.createInvoice(payload)
    showToast('Invoice created successfully!')
    setTimeout(() => {
      router.push('/admin/invoices')
    }, 1000)
  } catch (err) {
    showToast(err.response?.data?.detail || 'Failed to create invoice', 'error')
    submitting.value = false
  }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 24px;
}
.page-header h2 {
  font-family: var(--font-display);
  font-size: 24px;
  margin: 0;
}

.invoice-form-layout {
  display: flex;
  gap: 32px;
  align-items: flex-start;
}

.form-main {
  flex: 1;
  background: white;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-outline);
  padding: 32px;
}

.form-sidebar {
  width: 320px;
  position: sticky;
  top: 96px;
}

.form-section {
  margin-bottom: 32px;
  padding-bottom: 32px;
  border-bottom: 1px solid var(--color-outline-variant);
}

.form-section:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.section-title {
  font-family: var(--font-display);
  font-size: 16px;
  margin: 0 0 16px 0;
  color: var(--color-on-surface);
}

.type-toggles {
  display: flex;
  gap: 16px;
}

.type-btn {
  flex: 1;
  padding: 16px;
  border: 2px solid var(--color-outline-variant);
  background: white;
  border-radius: var(--radius);
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 700;
  color: var(--color-on-surface-variant);
  cursor: pointer;
  transition: all 0.2s;
}

.type-btn.active {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}
.form-group:last-child { margin-bottom: 0; }

.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-surface-variant);
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 10px 12px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius);
  font-family: var(--font-body);
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 1px var(--color-primary);
}

.form-group input:disabled,
.form-group textarea:disabled {
  background: var(--color-surface-container);
  color: var(--color-on-surface-variant);
}

.row-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.mt-16 { margin-top: 16px; }
.mt-8 { margin-top: 8px; }
.mt-24 { margin-top: 24px; }
.w-full { width: 100%; }

.client-pill {
  padding: 10px 16px;
  background: var(--color-surface-container);
  border-radius: var(--radius);
  font-size: 13px;
}

.tax-indicator {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}
.indicator-teal { background: #e0f2f1; color: #00796b; }
.indicator-amber { background: #fff8e1; color: #f57f17; }

.billing-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}

.col-header {
  font-weight: 600;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-outline-variant);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.same-as-checkbox {
  font-size: 12px;
  font-weight: 400;
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--color-on-surface-variant);
  cursor: pointer;
}

.items-table {
  width: 100%;
  border-collapse: collapse;
}

.items-table th {
  text-align: left;
  padding: 8px 12px;
  font-size: 12px;
  color: var(--color-on-surface-variant);
  font-weight: 600;
  border-bottom: 2px solid var(--color-outline-variant);
}

.items-table td {
  padding: 8px 4px;
  vertical-align: top;
}

.items-table input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--color-outline);
  border-radius: 4px;
  font-size: 13px;
}
.items-table input:focus {
  outline: none;
  border-color: var(--color-primary);
}

.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  color: var(--color-on-surface-variant);
}
.icon-btn.text-danger:hover:not(:disabled) {
  background: #ffdad6;
  color: var(--color-error);
}
.icon-btn:disabled { opacity: 0.3; cursor: not-allowed; }

.btn-text {
  background: none;
  border: none;
  color: var(--color-primary);
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
}
.btn-text:hover { text-decoration: underline; }

.summary-card {
  background: var(--color-surface-container-lowest);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  padding: 24px;
}

.summary-title {
  margin: 0 0 16px 0;
  font-family: var(--font-display);
  font-size: 18px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-outline-variant);
}

.summary-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 14px;
}

.total-row {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 2px solid var(--color-outline-variant);
  font-weight: 700;
  font-size: 18px;
}

.font-mono { font-family: 'Courier New', Courier, monospace; }

.words-total {
  font-size: 12px;
  font-style: italic;
  color: var(--color-on-surface-variant);
  line-height: 1.4;
}

.btn-primary {
  padding: 12px;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius);
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: opacity 0.2s;
}
.btn-primary:hover:not(:disabled) { opacity: 0.9; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.bank-warning {
  padding: 16px;
  background: #fff8e1;
  color: #f57f17;
  border-radius: var(--radius);
  font-size: 13px;
}
.bank-warning a { color: #f57f17; font-weight: bold; }
</style>
