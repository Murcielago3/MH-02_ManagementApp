<template>
  <AppLayout>
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <button class="back-btn" @click="$router.push('/admin/invoices')">
          <span class="material-symbols-outlined">arrow_back</span>
        </button>
        <div>
          <h1 class="page-title">{{ isEditing ? 'Edit Invoice' : 'Create Invoice' }}</h1>
          <p class="page-subtitle">{{ isEditing ? 'Update the invoice details below' : 'Fill in the details below to generate a new invoice' }}</p>
        </div>
      </div>
    </div>

    <div class="invoice-layout">
      <!-- ── Main Form ── -->
      <div class="form-card">
        <form @submit.prevent="submitInvoice" id="invoiceForm">

          <!-- Section: Invoice Type -->
          <div class="form-section">
            <div class="section-header">
              <span class="section-number">01</span>
              <h3 class="section-title">Invoice Type</h3>
            </div>
            <div class="type-toggles">
              <button
                type="button"
                class="type-btn"
                :class="{ active: form.invoice_type === 'tax' }"
                @click="form.invoice_type = 'tax'"
              >
                <span class="material-symbols-outlined type-icon">receipt</span>
                <span class="type-label">TAX INVOICE</span>
              </button>
              <button
                type="button"
                class="type-btn"
                :class="{ active: form.invoice_type === 'proforma' }"
                @click="form.invoice_type = 'proforma'"
              >
                <span class="material-symbols-outlined type-icon">draft</span>
                <span class="type-label">PROFORMA INVOICE</span>
              </button>
            </div>
            <div v-if="form.invoice_type === 'tax'" class="form-group mt-16">
              <label>Invoice Number {{ taxType === 'IGST' ? '(Optional)' : '*' }}</label>
              <input v-model="form.invoice_number" type="text" placeholder="e.g. AO-006" :required="taxType !== 'IGST'" />
            </div>
          </div>

          <!-- Section: Date & Place -->
          <div class="form-section">
            <div class="section-header">
              <span class="section-number">02</span>
              <h3 class="section-title">Date &amp; Location</h3>
            </div>
            <div class="row-2">
              <div class="form-group">
                <label>Invoice Date *</label>
                <input v-model="form.invoice_date" type="date" required />
              </div>
              <div class="form-group">
                <label>Place of Supply</label>
                <input v-model="form.place_of_supply" type="text" placeholder="e.g. Maharashtra" />
              </div>
            </div>
          </div>

          <!-- Section: Project -->
          <div class="form-section">
            <div class="section-header">
              <span class="section-number">03</span>
              <h3 class="section-title">Project</h3>
            </div>
            <div class="form-group">
              <label>Project *</label>
              <select v-model="form.project_id" @change="onProjectSelect" required>
                <option :value="null">— Select Project —</option>
                <option v-for="p in projects" :key="p.id" :value="p.id">
                  {{ p.project_number }} - {{ p.name }}
                </option>
              </select>
            </div>
            <div v-if="selectedClient" class="client-chip mt-12">
              <span class="material-symbols-outlined chip-icon">corporate_fare</span>
              <span><strong>{{ selectedClient.name }}</strong> &nbsp;·&nbsp; GSTIN: {{ selectedClient.gstin || 'N/A' }}</span>
            </div>
            <div v-if="taxTypeIndicator" class="tax-badge mt-8" :class="taxTypeIndicator.class">
              <span class="material-symbols-outlined" style="font-size:14px;">info</span>
              {{ taxTypeIndicator.text }}
            </div>
          </div>

          <!-- Section: Billing Details -->
          <div class="form-section">
            <div class="section-header">
              <span class="section-number">04</span>
              <h3 class="section-title">Billing Details</h3>
            </div>
            <div class="billing-grid">
              <div>
                <div class="col-label">Bill To</div>
                <div class="form-group">
                  <label>Name *</label>
                  <input v-model="form.bill_to_name" type="text" required />
                </div>
                <div class="form-group">
                  <label>Address</label>
                  <textarea v-model="form.bill_to_address" rows="3" placeholder="Full address…"></textarea>
                </div>
                <div class="form-group">
                  <label>GSTIN</label>
                  <input v-model="form.bill_to_gstin" type="text" placeholder="e.g. 27XXXXX…" />
                </div>
              </div>
              <div>
                <div class="col-label col-label--flex">
                  Ship To
                  <label class="same-as-label">
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

          <!-- Section: Line Items -->
          <div class="form-section">
            <div class="section-header">
              <span class="section-number">05</span>
              <h3 class="section-title">Line Items</h3>
            </div>
            <div class="items-table-wrap">
              <table class="items-table">
                <thead>
                  <tr>
                    <th style="width:36px">#</th>
                    <th>Description</th>
                    <th style="width:110px">HSN/SAC</th>
                    <th style="width:140px">Amount (₹)</th>
                    <th style="width:40px"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, idx) in form.items" :key="idx" class="item-row">
                    <td class="idx-cell">{{ idx + 1 }}</td>
                    <td>
                      <input v-model="item.description" type="text" required placeholder="Item description" />
                    </td>
                    <td>
                      <input v-model="item.hsn_sac" type="text" placeholder="HSN" />
                    </td>
                    <td>
                      <CurrencyInput v-model="item.amount" required />
                    </td>
                    <td class="text-center">
                      <button type="button" class="remove-btn" @click="removeItem(idx)" :disabled="form.items.length <= 1">
                        <span class="material-symbols-outlined">close</span>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <button type="button" class="add-item-btn" @click="addItem">
              <span class="material-symbols-outlined">add</span>
              Add Item
            </button>
          </div>

          <!-- Section: Bank Account -->
          <div class="form-section" style="border-bottom: none; padding-bottom: 0; margin-bottom: 0;">
            <div class="section-header">
              <span class="section-number">06</span>
              <h3 class="section-title">Bank Account</h3>
            </div>
            <div v-if="bankAccounts.length === 0" class="bank-warning">
              <span class="material-symbols-outlined">warning</span>
              No bank accounts saved.
              <router-link to="/admin/settings/bank">Add bank account →</router-link>
            </div>
            <div v-else class="form-group">
              <label>Select Account</label>
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

      <!-- ── Sidebar Summary ── -->
      <div class="form-sidebar">
        <div class="summary-card">
          <h3 class="summary-title">Summary</h3>

          <div class="summary-rows">
            <div class="summary-row">
              <span class="sr-label">Sub Total</span>
              <span class="sr-value font-mono">₹{{ formatAmount(liveTotals.subtotal) }}</span>
            </div>
            <template v-if="taxType === 'CGST_SGST'">
              <div class="summary-row">
                <span class="sr-label">CGST (9%)</span>
                <span class="sr-value font-mono">₹{{ formatAmount(liveTotals.cgst) }}</span>
              </div>
              <div class="summary-row">
                <span class="sr-label">SGST (9%)</span>
                <span class="sr-value font-mono">₹{{ formatAmount(liveTotals.sgst) }}</span>
              </div>
            </template>
            <div v-if="taxType === 'IGST'" class="summary-row">
              <span class="sr-label">IGST (18%)</span>
              <span class="sr-value font-mono">₹{{ formatAmount(liveTotals.igst) }}</span>
            </div>
          </div>

          <div class="summary-total">
            <span class="st-label">Total</span>
            <span class="st-value font-mono">₹{{ formatAmount(liveTotals.total) }}</span>
          </div>

          <p class="words-total">{{ numberToWords(liveTotals.total) }}</p>

          <button
            type="submit"
            form="invoiceForm"
            class="submit-btn"
            :disabled="!isFormValid || submitting"
          >
            <span v-if="submitting" class="material-symbols-outlined spin-icon">progress_activity</span>
            <span class="material-symbols-outlined" v-else>check_circle</span>
            {{ submitting ? (isEditing ? 'Saving…' : 'Creating…') : (isEditing ? 'Save Changes' : 'Create Invoice') }}
          </button>
          <button
            v-if="!isEditing"
            type="button"
            class="draft-btn"
            @click="handleSaveDraft"
          >
            <span class="material-symbols-outlined">save</span>
            Save as Draft
          </button>
        </div>
      </div>
    </div>

    <ToastNotification v-if="toastMsg" :message="toastMsg" :type="toastType" @done="toastMsg = ''" />
  </AppLayout>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import ToastNotification from '../components/ToastNotification.vue'
import CurrencyInput from '../components/CurrencyInput.vue'
import { invoicesAPI } from '../api/invoices'
import { bankAccountsAPI } from '../api/bankAccounts'
import { projectsAPI } from '../api/projects'
import { clientsAPI } from '../api/clients'
import { useInvoiceDrafts, newInvoiceDraftId } from '../composables/useInvoiceDrafts'

const route = useRoute()
const router = useRouter()

const isEditing = computed(() => !!route.params.id)
const editingId = computed(() => route.params.id ? Number(route.params.id) : null)

const { saveDraft: saveDraftToStorage, deleteDraft, getDraft } = useInvoiceDrafts()
const activeDraftId = ref(route.query.draft || null)
let autoSaveTimer = null

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

function populateFormFromData(data) {
  form.invoice_type = data.invoice_type || 'tax'
  form.invoice_number = data.invoice_number || ''
  form.invoice_date = data.invoice_date || new Date().toISOString().split('T')[0]
  form.place_of_supply = data.place_of_supply || ''
  form.project_id = data.project_id || null
  form.client_id = data.client_id || null
  form.bill_to_name = data.bill_to_name || ''
  form.bill_to_address = data.bill_to_address || ''
  form.bill_to_gstin = data.bill_to_gstin || ''
  form.ship_to_name = data.ship_to_name || ''
  form.ship_to_address = data.ship_to_address || ''
  form.ship_to_gstin = data.ship_to_gstin || ''
  form.subject = data.subject || ''
  form.bank_account_id = data.bank_account_id || null
  form.items = (data.items || []).map(i => ({
    description: i.description || '',
    hsn_sac: i.hsn_sac || '',
    amount: Number(i.amount) || 0
  }))
  if (form.items.length === 0) {
    form.items = [{ description: '', hsn_sac: '', amount: 0 }]
  }
}

function getFormSnapshot() {
  return {
    invoice_type: form.invoice_type,
    invoice_number: form.invoice_number,
    invoice_date: form.invoice_date,
    place_of_supply: form.place_of_supply,
    project_id: form.project_id,
    client_id: form.client_id,
    bill_to_name: form.bill_to_name,
    bill_to_address: form.bill_to_address,
    bill_to_gstin: form.bill_to_gstin,
    ship_to_name: form.ship_to_name,
    ship_to_address: form.ship_to_address,
    ship_to_gstin: form.ship_to_gstin,
    subject: form.subject,
    bank_account_id: form.bank_account_id,
    items: form.items.map(i => ({ ...i })),
  }
}

// Has the user actually entered something? Avoids saving blank drafts from the
// form's defaults (which would clutter the list / overwrite real work).
function invoiceHasContent() {
  if (form.bill_to_name || form.project_id || form.invoice_number || form.subject) return true
  return form.items.some(i => (i.description && i.description.trim()) || Number(i.amount) > 0)
}

function autoSave() {
  if (isEditing.value) return
  if (!invoiceHasContent()) return
  // Claim the id synchronously so repeated autosaves upsert the same draft.
  if (!activeDraftId.value) activeDraftId.value = newInvoiceDraftId()
  saveDraftToStorage(activeDraftId.value, getFormSnapshot())
}

async function handleSaveDraft() {
  if (!activeDraftId.value) activeDraftId.value = newInvoiceDraftId()
  await saveDraftToStorage(activeDraftId.value, getFormSnapshot())
  showToast('Draft saved')
}

onMounted(async () => {
  try {
    const [pRes, bRes] = await Promise.all([
      projectsAPI.getProjects(),
      bankAccountsAPI.getBankAccounts()
    ])
    projects.value = pRes.data
    bankAccounts.value = bRes.data

    // Always pre-select the bank account — default to the only one if just one exists
    if (!form.bank_account_id && bankAccounts.value.length === 1) {
      form.bank_account_id = bankAccounts.value[0].id
    }

    if (isEditing.value && editingId.value) {
      // Edit mode — load existing invoice
      const res = await invoicesAPI.getInvoice(editingId.value)
      const inv = res.data
      populateFormFromData(inv)
      // If the saved invoice had no bank account, still auto-select the only one
      if (!form.bank_account_id && bankAccounts.value.length === 1) {
        form.bank_account_id = bankAccounts.value[0].id
      }
      if (inv.client) {
        selectedClient.value = inv.client
      }
    } else if (activeDraftId.value) {
      // Resume draft mode
      const draft = await getDraft(activeDraftId.value)
      if (draft) {
        populateFormFromData(draft.data)
        // Resolve the client from the project
        if (form.project_id) {
          const proj = projects.value.find(p => p.id === form.project_id)
          if (proj?.client) {
            selectedClient.value = proj.client
          }
        }
        if (!form.bank_account_id && bankAccounts.value.length === 1) {
          form.bank_account_id = bankAccounts.value[0].id
        }
        showToast('Draft restored')
      }
    }
  } catch (err) {
    showToast('Failed to load required data', 'error')
  }

  // Auto-save every 10 seconds in create mode
  if (!isEditing.value) {
    autoSaveTimer = setInterval(autoSave, 10000)
  }
})

onUnmounted(() => {
  if (autoSaveTimer) clearInterval(autoSaveTimer)
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
  return { subtotal, cgst, sgst, igst, total: subtotal + cgst + sgst + igst }
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
  if (form.items.length > 1) form.items.splice(idx, 1)
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
    if (n < 100) return tens[Math.floor(n/10)] + (n%10 ? ' ' + ones[n%10] : '')
    return ones[Math.floor(n/100)] + ' Hundred' + (n%100 ? ' ' + wordsUnderThousand(n%100) : '')
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
  const payload = { ...form }
  payload.items = payload.items.filter(i => i.description.trim() !== '')
  try {
    if (isEditing.value) {
      await invoicesAPI.updateInvoice(editingId.value, payload)
      showToast('Invoice updated successfully!')
      setTimeout(() => { router.push(`/admin/invoices/${editingId.value}`) }, 1000)
    } else {
      // Delete the draft on successful creation
      if (autoSaveTimer) clearInterval(autoSaveTimer)
      if (activeDraftId.value) {
        await deleteDraft(activeDraftId.value)
        activeDraftId.value = null
      }
      await invoicesAPI.createInvoice(payload)
      showToast('Invoice created successfully!')
      setTimeout(() => { router.push('/admin/invoices') }, 1000)
    }
  } catch (err) {
    showToast(err.response?.data?.detail || 'Failed to save invoice', 'error')
    submitting.value = false
  }
}
</script>

<style scoped>
/* ── Page Header ── */
.page-header {
  margin-bottom: 28px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.back-btn {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-outline);
  background: var(--color-surface);
  color: var(--color-on-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s;
}
.back-btn:hover { background: var(--color-surface-dim); }
.back-btn .material-symbols-outlined { font-size: 20px; }

.page-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 800;
  color: var(--color-on-surface);
  margin: 0 0 2px;
  letter-spacing: -0.01em;
}
.page-subtitle { margin: 0; font-size: 13px; color: var(--color-on-surface-variant); }

/* ── Layout ── */
.invoice-layout {
  display: flex;
  gap: 28px;
  align-items: flex-start;
}

.form-card {
  flex: 1;
  min-width: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-xl);
  padding: 32px;
  box-shadow: var(--shadow-sm);
}

.form-sidebar {
  width: 300px;
  flex-shrink: 0;
  position: sticky;
  top: 88px;
}

/* ── Form Sections ── */
.form-section {
  margin-bottom: 32px;
  padding-bottom: 32px;
  border-bottom: 1px solid var(--color-outline);
}
.form-section:last-child {
  margin-bottom: 0; padding-bottom: 0; border-bottom: none;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
}
.section-number {
  font-family: var(--font-display);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.1em;
  color: var(--color-primary);
  background: var(--color-primary-light);
  border-radius: var(--radius-md);
  padding: 3px 8px;
}
.section-title {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 800;
  margin: 0;
  color: var(--color-on-surface);
}

/* ── Invoice Type Toggles ── */
.type-toggles {
  display: flex;
  gap: 12px;
}
.type-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 18px 16px;
  border: 2px solid var(--color-outline);
  background: var(--color-surface-dim);
  border-radius: var(--radius-xl);
  cursor: pointer;
  transition: all 0.18s;
}
.type-btn.active {
  background: var(--color-primary-light);
  border-color: var(--color-primary);
  color: var(--color-primary);
}
.type-icon { font-size: 22px; color: inherit; }
.type-label {
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: inherit;
}

/* ── Form Fields ── */
.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-bottom: 14px;
}
.form-group:last-child { margin-bottom: 0; }

.form-group label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-on-surface-variant);
}

.form-group input,
.form-group select,
.form-group textarea {
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
.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(40,116,117,0.1);
}
.form-group input:disabled,
.form-group textarea:disabled {
  background: var(--color-surface-dim);
  color: var(--color-on-surface-variant);
  cursor: not-allowed;
}

.row-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.mt-12 { margin-top: 12px; }
.mt-16 { margin-top: 16px; }
.mt-8  { margin-top: 8px; }

/* ── Client Chip ── */
.client-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: var(--color-surface-dim);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-full);
  font-size: 13px;
  color: var(--color-on-surface);
}
.chip-icon { font-size: 16px; color: var(--color-primary); }

/* ── Tax Badge ── */
.tax-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 700;
}
.indicator-teal { background: var(--color-primary-light); color: var(--color-primary); }
.indicator-amber { background: #fff8e1; color: #b45309; }

/* ── Billing Grid ── */
.billing-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 28px;
}
.col-label {
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-on-surface-variant);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-outline);
}
.col-label--flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.same-as-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: none;
  letter-spacing: 0;
  color: var(--color-on-surface-variant);
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
}

/* ── Items Table ── */
.items-table-wrap {
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  overflow: hidden;
}
.items-table {
  width: 100%;
  border-collapse: collapse;
}
.items-table th {
  background: var(--color-surface-dim);
  padding: 9px 12px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-on-surface-variant);
  text-align: left;
  border-bottom: 1px solid var(--color-outline);
}
.items-table td {
  padding: 7px 6px;
  vertical-align: middle;
  border-bottom: 1px solid var(--color-outline);
}
.item-row:last-child td { border-bottom: none; }
.idx-cell { text-align: center; font-size: 11px; color: var(--color-on-surface-variant); padding: 0 4px; }
.text-center { text-align: center; }

.items-table input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 13px;
  background: transparent;
  transition: background 0.15s, border-color 0.15s;
}
.items-table input:focus {
  outline: none;
  border-color: var(--color-primary);
  background: #fff;
  box-shadow: 0 0 0 2px rgba(40,116,117,0.1);
}

.remove-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-on-surface-variant);
  padding: 4px;
  border-radius: var(--radius-md);
  display: inline-flex;
  align-items: center;
  transition: background 0.15s, color 0.15s;
}
.remove-btn:hover:not(:disabled) { background: #fef2f2; color: var(--color-error); }
.remove-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.remove-btn .material-symbols-outlined { font-size: 17px; }

.add-item-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 12px;
  background: none;
  border: none;
  color: var(--color-primary);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  padding: 4px 0;
}
.add-item-btn:hover { text-decoration: underline; }
.add-item-btn .material-symbols-outlined { font-size: 16px; }

/* ── Bank Warning ── */
.bank-warning {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 13px 16px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: var(--radius-lg);
  font-size: 13px;
  color: #92400e;
}
.bank-warning .material-symbols-outlined { font-size: 18px; }
.bank-warning a { color: #92400e; font-weight: 700; text-decoration: none; }
.bank-warning a:hover { text-decoration: underline; }

/* ── Summary Card ── */
.summary-card {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-xl);
  padding: 24px;
  box-shadow: var(--shadow-sm);
}
.summary-title {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 800;
  margin: 0 0 16px;
  color: var(--color-on-surface);
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-outline);
}
.summary-rows {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 8px;
}
.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.sr-label { font-size: 13px; color: var(--color-on-surface-variant); }
.sr-value { font-size: 13px; color: var(--color-on-surface); }

.summary-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  margin-top: 8px;
  border-top: 2px solid var(--color-outline);
}
.st-label { font-size: 15px; font-weight: 700; color: var(--color-on-surface); }
.st-value {
  font-size: 18px;
  font-weight: 800;
  color: var(--color-on-surface);
}

.font-mono { font-family: 'Courier New', Courier, monospace; }

.words-total {
  font-size: 11px;
  font-style: italic;
  color: var(--color-on-surface-variant);
  line-height: 1.5;
  margin: 12px 0 0;
}

.submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  width: 100%;
  margin-top: 20px;
  padding: 12px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-lg);
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
  transition: opacity 0.18s;
  box-shadow: 0 2px 8px rgba(40,116,117,0.2);
}
.submit-btn:hover:not(:disabled) { opacity: 0.88; }
.submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.submit-btn .material-symbols-outlined { font-size: 18px; }

/* ── Draft Button ── */
.draft-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  width: 100%;
  margin-top: 10px;
  padding: 10px;
  background: var(--color-surface);
  color: var(--color-on-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s;
}
.draft-btn:hover { background: var(--color-surface-dim); }
.draft-btn .material-symbols-outlined { font-size: 17px; color: var(--color-on-surface-variant); }

/* ── Spinner ── */
.spin-icon { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 900px) {
  .invoice-layout { flex-direction: column; }
  .form-sidebar { width: 100%; position: static; }
  .billing-grid { grid-template-columns: 1fr; }
  .row-2 { grid-template-columns: 1fr; }
  .type-toggles { flex-direction: column; }
  .items-table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .items-table { min-width: 480px; }
  .form-card { padding: 18px; }
}
</style>
