<template>
  <EmployeeLayout>
    <div class="reimbursement-view">
      <div class="view-header">
        <h2 class="view-title">Reimbursements</h2>
      </div>

      <div class="content-grid">
        <!-- Left: Apply Form -->
        <div class="apply-panel">
          <h3 class="panel-title">Submit Reimbursement</h3>
          <form @submit.prevent="submitReimbursement" class="reimbursement-form">
            <div class="form-group">
              <label>Amount (₹)</label>
              <input type="number" v-model.number="form.amount" required min="1" class="field-input" placeholder="e.g. 1500">
            </div>

            <div class="form-group">
              <label>Date of Expense</label>
              <input type="date" v-model="form.date" required class="field-input" :max="todayDate">
            </div>

            <div class="form-group">
              <label>Reason / Description</label>
              <textarea v-model="form.reason" rows="2" required class="field-input" placeholder="What was this expense for?"></textarea>
            </div>

            <div class="form-group">
              <label>Proof Document (Optional but recommended)</label>
              <input type="file" ref="fileInput" @change="handleFileChange" accept="image/jpeg,image/png,application/pdf" class="field-input file-input">
              <small class="help-text">Max 5MB. PDF, JPG, PNG allowed.</small>
            </div>

            <button type="submit" class="btn-submit" :disabled="submitting">
              {{ submitting ? 'Submitting...' : 'Submit Claim' }}
            </button>
          </form>
        </div>

        <!-- Right: History -->
        <div class="history-panel">
          <h3 class="panel-title">Reimbursement History</h3>
          
          <div v-if="loadingHistory" class="loading-state">
            <span class="material-symbols-outlined spinner">refresh</span>
          </div>
          
          <div v-else-if="history.length === 0" class="empty-state">
            <span class="material-symbols-outlined">receipt_long</span>
            <p>No reimbursements submitted yet</p>
          </div>
          
          <div v-else class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Amount</th>
                  <th>Reason</th>
                  <th>Proof</th>
                  <th>Status</th>
                  <th>Added to Payroll</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in history" :key="item.id">
                  <td>{{ formatDateShort(item.date) }}</td>
                  <td class="amount-cell">{{ formatCurrency(item.amount) }}</td>
                  <td class="reason-cell" :title="item.reason">{{ item.reason }}</td>
                  <td>
                    <a v-if="item.proof_url" :href="resolveUrl(item.proof_url)" target="_blank" class="proof-link">
                      <span class="material-symbols-outlined">attachment</span> View Proof
                    </a>
                    <span v-else class="no-proof">—</span>
                  </td>
                  <td>
                    <span class="status-badge" :class="item.status">
                      {{ formatStatus(item.status) }}
                    </span>
                  </td>
                  <td class="payroll-cell">
                    <span v-if="item.month_added" class="payroll-badge">Added to {{ item.month_added }}</span>
                    <span v-else>—</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </EmployeeLayout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import EmployeeLayout from '../../components/EmployeeLayout.vue'
import { reimbursementsAPI } from '../../api/reimbursements'
import { usersAPI } from '../../api/users'

const history = ref([])
const loadingHistory = ref(true)
const submitting = ref(false)
const fileInput = ref(null)
const selectedFile = ref(null)

const todayDate = new Date().toISOString().split('T')[0]

const form = reactive({
  amount: '',
  date: todayDate,
  reason: ''
})

onMounted(async () => {
  await fetchHistory()
})

const fetchHistory = async () => {
  loadingHistory.value = true
  try {
    const res = await reimbursementsAPI.getMyReimbursements()
    history.value = res.data.sort((a, b) => new Date(b.date) - new Date(a.date))
  } catch (e) {
    console.error(e)
  } finally {
    loadingHistory.value = false
  }
}

const handleFileChange = (e) => {
  if (e.target.files.length > 0) {
    selectedFile.value = e.target.files[0]
  } else {
    selectedFile.value = null
  }
}

const submitReimbursement = async () => {
  if (!form.amount || !form.date || !form.reason) return

  submitting.value = true
  try {
    const formData = new FormData()
    formData.append('amount', form.amount)
    formData.append('date', form.date)
    formData.append('reason', form.reason)
    if (selectedFile.value) {
      formData.append('proof', selectedFile.value)
    }

    await reimbursementsAPI.createReimbursement(formData)
    alert('Reimbursement submitted successfully!')
    
    // Reset
    form.amount = ''
    form.reason = ''
    selectedFile.value = null
    if (fileInput.value) fileInput.value.value = ''
    
    await fetchHistory()
  } catch (err) {
    alert('Error submitting reimbursement: ' + (err.response?.data?.detail || err.message))
  } finally {
    submitting.value = false
  }
}

// Formatters
const formatDateShort = (d) => {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

const formatCurrency = (val) => {
  if (!val) return '₹0'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(val)
}

const formatStatus = (s) => {
  if (!s) return ''
  return s.charAt(0).toUpperCase() + s.slice(1)
}

const resolveUrl = (url) => {
  return usersAPI.resolveFileUrl(url)
}
</script>

<style scoped>
.reimbursement-view {
  max-width: 1200px;
  margin: 0 auto;
}

.view-header {
  margin-bottom: 32px;
}

.view-title {
  font-family: var(--font-display);
  font-size: 28px;
  color: var(--color-on-surface);
  margin: 0;
}

.content-grid {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 32px;
}

@media (max-width: 1024px) {
  .content-grid { grid-template-columns: 1fr; }
}

.panel-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--color-on-surface);
  margin: 0 0 24px 0;
}

/* Apply Form */
.apply-panel {
  background: var(--color-surface);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 24px;
  height: max-content;
}

.reimbursement-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-surface-variant);
}

.field-input {
  width: 100%;
  height: 48px;
  padding: 0 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-outline-variant);
  font-family: var(--font-body);
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
}

textarea.field-input {
  height: auto;
  padding: 12px 16px;
  resize: vertical;
}

.file-input {
  padding: 12px 16px;
}

.field-input:focus {
  border-color: var(--color-primary);
}

.help-text {
  font-size: 11px;
  color: var(--color-outline);
}

.btn-submit {
  height: 48px;
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-family: var(--font-display);
  font-size: 16px;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: opacity 0.2s;
  margin-top: 8px;
}
.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-submit:hover:not(:disabled) {
  opacity: 0.9;
}

/* History Panel */
.history-panel {
  background: var(--color-surface);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 24px;
}

.loading-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 0;
  color: var(--color-outline);
}

.empty-state .material-symbols-outlined {
  font-size: 48px;
  margin-bottom: 16px;
}

.table-container {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  text-align: left;
  padding: 16px;
  font-size: 12px;
  text-transform: uppercase;
  color: var(--color-outline);
  border-bottom: 1px solid var(--color-outline-variant);
}

.data-table td {
  padding: 16px;
  font-size: 14px;
  color: var(--color-on-surface);
  border-bottom: 1px solid var(--color-outline-variant);
}

.amount-cell {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.reason-cell {
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.proof-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--color-primary);
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
}
.proof-link:hover {
  text-decoration: underline;
}
.proof-link .material-symbols-outlined {
  font-size: 16px;
}

.no-proof {
  color: var(--color-outline);
}

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

.status-badge.pending { background: #fef3c7; color: #b45309; }
.status-badge.approved { background: #dcfce7; color: #15803d; }
.status-badge.rejected { background: #fee2e2; color: #b91c1c; }

.payroll-badge {
  display: inline-block;
  padding: 4px 8px;
  background: rgba(40, 116, 117, 0.1);
  color: var(--color-primary);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

@keyframes spin { 100% { transform: rotate(360deg); } }
.spinner { animation: spin 1s linear infinite; }

@media (max-width: 768px) {
  .layout { flex-direction: column; }
  .form-panel { min-width: 0; }
  .table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .data-table { min-width: 480px; }
  .modal { max-width: 100%; width: 100%; }
  .modal-backdrop { padding: 8px; }
}
</style>
