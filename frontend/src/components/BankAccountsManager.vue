<template>
  <div class="bank-mgr">
    <div class="mgr-header">
      <div>
        <h3 class="mgr-title">Bank Accounts</h3>
        <p class="mgr-sub">Accounts used in invoices</p>
      </div>
      <button class="btn-primary" @click="openAddModal">
        <span class="material-symbols-outlined">add</span>
        Add Bank Account
      </button>
    </div>

    <div v-if="loading" class="loading-state">Loading bank accounts...</div>
    <div v-else-if="bankAccounts.length === 0" class="empty-state">
      No bank accounts saved yet. Add your first bank account to use in invoices.
    </div>
    <div v-else class="cards-grid">
      <div v-for="account in bankAccounts" :key="account.id" class="bank-card">
        <div class="bank-card-header">
          <div class="bank-name">{{ account.bank_name }}</div>
          <div class="bank-actions">
            <button class="icon-btn edit-btn" @click="openEditModal(account)" title="Edit">
              <span class="material-symbols-outlined">edit</span>
            </button>
            <button class="icon-btn delete-btn" @click="confirmDelete(account)" title="Delete">
              <span class="material-symbols-outlined">delete</span>
            </button>
          </div>
        </div>
        <div class="bank-details">
          <div class="detail-row">
            <span class="label">Account Number:</span>
            <span class="value">{{ maskAccount(account.account_number) }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Account Type:</span>
            <span class="value">{{ account.account_type }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Holder Name:</span>
            <span class="value">{{ account.account_holder_name }}</span>
          </div>
          <div class="detail-row">
            <span class="label">IFSC Code:</span>
            <span class="value">{{ account.ifsc_code }}</span>
          </div>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="modalOpen" class="modal-backdrop">
        <div class="modal">
          <div class="modal-header">
            <h3>{{ isEditing ? 'Edit Bank Account' : 'Add Bank Account' }}</h3>
            <button class="icon-btn" @click="closeModal">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <form @submit.prevent="handleSubmit" class="modal-body">
            <div class="form-group">
              <label>Bank Name *</label>
              <input v-model="form.bank_name" type="text" required placeholder="e.g. HDFC Bank" />
            </div>
            <div class="form-group">
              <label>Account Number *</label>
              <input v-model="form.account_number" type="text" required placeholder="e.g. 1234567890" />
            </div>
            <div class="form-group">
              <label>Account Type *</label>
              <select v-model="form.account_type" required>
                <option value="Current">Current</option>
                <option value="Savings">Savings</option>
              </select>
            </div>
            <div class="form-group">
              <label>Account Holder Name *</label>
              <input v-model="form.account_holder_name" type="text" required placeholder="e.g. Studio MH02 LLP" />
            </div>
            <div class="form-group">
              <label>IFSC Code *</label>
              <input v-model="form.ifsc_code" type="text" required placeholder="e.g. HDFC0001234" />
            </div>
            <div class="modal-footer">
              <button type="button" class="btn-secondary" @click="closeModal">Cancel</button>
              <button type="submit" class="btn-primary" :disabled="submitting">
                {{ submitting ? 'Saving...' : 'Save Account' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="deleteTarget" class="modal-backdrop">
        <div class="modal delete-modal">
          <div class="modal-header">
            <h3>Delete Bank Account</h3>
            <button class="icon-btn" @click="deleteTarget = null">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <div class="modal-body">
            <p>Are you sure you want to remove <strong>{{ deleteTarget.bank_name }}</strong> ending in {{ deleteTarget.account_number.slice(-4) }}?</p>
            <div class="modal-footer">
              <button class="btn-secondary" @click="deleteTarget = null">Cancel</button>
              <button class="btn-danger" :disabled="submitting" @click="handleDelete">
                {{ submitting ? 'Deleting...' : 'Delete' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <ToastNotification v-if="toastMsg" :message="toastMsg" :type="toastType" @done="toastMsg = ''" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import ToastNotification from './ToastNotification.vue'
import { bankAccountsAPI } from '../api/bankAccounts'

const bankAccounts = ref([])
const loading = ref(true)
const submitting = ref(false)
const modalOpen = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const deleteTarget = ref(null)

const toastMsg = ref('')
const toastType = ref('success')

const form = reactive({
  bank_name: '',
  account_number: '',
  account_type: 'Current',
  account_holder_name: '',
  ifsc_code: ''
})

const showToast = (msg, type = 'success') => {
  toastMsg.value = msg
  toastType.value = type
}

const fetchAccounts = async () => {
  loading.value = true
  try {
    const res = await bankAccountsAPI.getBankAccounts()
    bankAccounts.value = res.data
  } catch (err) {
    showToast('Failed to load bank accounts', 'error')
  } finally {
    loading.value = false
  }
}

onMounted(fetchAccounts)

const maskAccount = (num) => {
  if (!num) return ''
  if (num.length <= 4) return num
  return 'X'.repeat(num.length - 4) + num.slice(-4)
}

const openAddModal = () => {
  isEditing.value = false
  editingId.value = null
  Object.assign(form, { bank_name: '', account_number: '', account_type: 'Current', account_holder_name: '', ifsc_code: '' })
  modalOpen.value = true
}

const openEditModal = (account) => {
  isEditing.value = true
  editingId.value = account.id
  Object.assign(form, {
    bank_name: account.bank_name,
    account_number: account.account_number,
    account_type: account.account_type,
    account_holder_name: account.account_holder_name,
    ifsc_code: account.ifsc_code
  })
  modalOpen.value = true
}

const closeModal = () => { modalOpen.value = false }

const handleSubmit = async () => {
  submitting.value = true
  try {
    if (isEditing.value) {
      await bankAccountsAPI.updateBankAccount(editingId.value, form)
      showToast('Bank account updated')
    } else {
      await bankAccountsAPI.createBankAccount(form)
      showToast('Bank account added')
    }
    closeModal()
    fetchAccounts()
  } catch (err) {
    showToast('Failed to save bank account', 'error')
  } finally {
    submitting.value = false
  }
}

const confirmDelete = (account) => { deleteTarget.value = account }

const handleDelete = async () => {
  if (!deleteTarget.value) return
  submitting.value = true
  try {
    await bankAccountsAPI.deleteBankAccount(deleteTarget.value.id)
    showToast('Bank account removed')
    deleteTarget.value = null
    fetchAccounts()
  } catch (err) {
    showToast('Failed to delete account', 'error')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.bank-mgr { display: flex; flex-direction: column; gap: 16px; }
.mgr-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }
.mgr-title { font-family: var(--font-display); font-size: 18px; font-weight: 700; margin: 0 0 2px; }
.mgr-sub { margin: 0; font-size: 13px; color: var(--color-on-surface-variant); }

.btn-primary {
  display: inline-flex; align-items: center; gap: 8px;
  background: var(--color-primary); color: white;
  border: none; padding: 10px 16px;
  border-radius: var(--radius-lg);
  font-family: var(--font-body); font-weight: 600;
  cursor: pointer; transition: opacity 0.15s;
}
.btn-primary:hover { opacity: 0.92; }
.btn-primary:disabled { opacity: 0.55; cursor: not-allowed; }

.btn-secondary {
  background: white; border: 1px solid var(--color-outline);
  padding: 10px 16px; border-radius: var(--radius-lg);
  font-family: var(--font-body); cursor: pointer;
}
.btn-danger {
  background: #ef4444; color: white; border: none;
  padding: 10px 16px; border-radius: var(--radius-lg);
  font-family: var(--font-body); font-weight: 600; cursor: pointer;
}
.btn-danger:disabled { opacity: 0.55; cursor: not-allowed; }

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}
.bank-card {
  background: white; border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg); padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}
.bank-card-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px; padding-bottom: 12px;
  border-bottom: 1px solid var(--color-outline-variant);
}
.bank-name { font-family: var(--font-display); font-size: 18px; font-weight: 700; color: var(--color-on-surface); }
.bank-actions { display: flex; gap: 4px; }
.icon-btn {
  background: none; border: none; cursor: pointer;
  padding: 6px; border-radius: 4px; color: var(--color-on-surface-variant);
}
.icon-btn:hover { background: rgba(0,0,0,0.06); color: var(--color-on-surface); }
.icon-btn.delete-btn:hover { color: #ef4444; }
.bank-details { display: flex; flex-direction: column; gap: 8px; }
.detail-row { display: flex; justify-content: space-between; font-size: 13px; }
.detail-row .label { color: var(--color-on-surface-variant); }
.detail-row .value { font-family: var(--font-mono, monospace); color: var(--color-on-surface); }

.loading-state, .empty-state {
  text-align: center; padding: 40px;
  color: var(--color-on-surface-variant);
  background: white; border-radius: var(--radius-lg);
  border: 1px solid var(--color-outline-variant);
}

.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.modal {
  background: white; border-radius: var(--radius-lg);
  width: 480px; max-width: 92vw; max-height: 90vh; overflow-y: auto;
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid var(--color-outline-variant);
}
.modal-header h3 { margin: 0; font-family: var(--font-display); }
.modal-body { padding: 20px; }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 8px;
  margin-top: 16px; padding-top: 16px;
  border-top: 1px solid var(--color-outline-variant);
}
.form-group { margin-bottom: 16px; }
.form-group label {
  display: block; margin-bottom: 6px;
  font-size: 13px; font-weight: 600; color: var(--color-on-surface-variant);
}
.form-group input, .form-group select {
  width: 100%; padding: 10px 12px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  font-size: 14px; font-family: var(--font-body);
}
.form-group input:focus, .form-group select:focus {
  outline: none; border-color: var(--color-primary);
}
</style>
