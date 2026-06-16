<template>
  <AppLayout>
    <!-- Page Header -->
    <div class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">Expenses</h1>
        <p class="page-subtitle">Track and manage company expenditures</p>
      </div>
      <button class="btn-primary" @click="openAddModal">
        <span class="material-symbols-outlined">add</span>
        Add Expense
      </button>
    </div>

    <!-- Filter Bar -->
    <div class="filter-bar">
      <div class="filter-bar-left">
        <div class="search-box">
          <span class="material-symbols-outlined search-icon">search</span>
          <input v-model="searchQuery" type="text" placeholder="Search expenses..." class="search-input" />
        </div>
        <select v-model="filterCategory" class="filter-select">
          <option value="">All Categories</option>
          <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
        </select>
      </div>
    </div>

    <!-- Table Card -->
    <div class="table-card">
      <table class="data-table">
        <thead>
          <tr>
            <th>Title</th>
            <th>Category</th>
            <th>Amount</th>
            <th>Date</th>
            <th>Recurring</th>
            <th class="col-actions">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="6" class="empty-cell">
              <div class="empty-state">
                <span class="material-symbols-outlined empty-icon">hourglass_empty</span>
                <p>Loading expenses…</p>
              </div>
            </td>
          </tr>
          <tr v-else-if="filtered.length === 0">
            <td colspan="6" class="empty-cell">
              <div class="empty-state">
                <span class="material-symbols-outlined empty-icon">receipt_long</span>
                <p>No expenses found.</p>
              </div>
            </td>
          </tr>
          <tr v-for="e in filtered" :key="e.id" class="data-row">
            <td><span class="row-name">{{ e.title }}</span></td>
            <td class="cell-muted">{{ e.category }}</td>
            <td class="cell-mono cell-amount">₹{{ formatAmount(e.amount) }}</td>
            <td class="cell-mono cell-muted">{{ formatDate(e.date) }}</td>
            <td>
              <span class="badge" :class="e.recurring ? 'badge-blue' : 'badge-neutral'">
                {{ e.recurring ? 'Recurring' : 'One-time' }}
              </span>
            </td>
            <td>
              <div class="row-actions">
                <button class="icon-btn icon-btn-edit" title="Edit" @click="openEditModal(e)">
                  <span class="material-symbols-outlined">edit</span>
                </button>
                <button class="icon-btn icon-btn-delete" title="Delete" @click="confirmDelete(e)">
                  <span class="material-symbols-outlined">delete</span>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="table-footer">
        <span class="page-info">
          {{ filtered.length }} {{ filtered.length === 1 ? 'expense' : 'expenses' }}
        </span>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <Teleport to="body">
      <div v-if="modalOpen" class="modal-backdrop" @click.self="closeModal">
        <div class="modal modal-wide">
          <div class="modal-header">
            <div>
              <h3 class="modal-title">{{ isEditing ? 'Edit Expense' : 'Add New Expense' }}</h3>
              <p class="modal-subtitle">{{ isEditing ? 'Update expense details below' : 'Fill in the expense details below' }}</p>
            </div>
            <button class="modal-close" @click="closeModal">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>

          <form @submit.prevent="handleSubmit" class="modal-body">
            <div class="form-grid">
              <!-- Title -->
              <div class="form-field">
                <label class="form-label">Title *</label>
                <input v-model="form.title" type="text" required placeholder="e.g. Office Rent" class="form-input" />
              </div>
              <!-- Category -->
              <div class="form-field">
                <label class="form-label">Category *</label>
                <select v-model="form.category" required class="form-input">
                  <option value="">— Select Category —</option>
                  <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
                </select>
              </div>
              <!-- Amount -->
              <div class="form-field">
                <label class="form-label">Amount (₹)</label>
                <CurrencyInput v-model="form.amount" required placeholder="0" class="form-input" />
              </div>
              <!-- Date -->
              <div class="form-field">
                <label class="form-label">Date *</label>
                <input v-model="form.date" type="date" required class="form-input" />
              </div>
              <!-- Recurring -->
              <div class="form-field form-field-checkbox">
                <label class="form-label">Recurring</label>
                <label class="checkbox-label">
                  <input v-model="form.recurring" type="checkbox" class="checkbox-input" />
                  <span class="checkbox-text">Mark as recurring expense</span>
                </label>
              </div>
              <!-- Notes -->
              <div class="form-field span-2">
                <label class="form-label">Notes</label>
                <textarea v-model="form.notes" placeholder="Additional notes..." rows="3" class="form-input"></textarea>
              </div>
            </div>

            <div v-if="formError" class="form-error">
              <span class="material-symbols-outlined">error</span>
              {{ formError }}
            </div>

            <div class="modal-footer">
              <button type="button" class="btn-cancel" @click="closeModal">Cancel</button>
              <button type="submit" class="btn-submit" :disabled="submitting">
                {{ submitting ? 'Saving…' : (isEditing ? 'Save Changes' : 'Add Expense') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Delete Confirmation Modal -->
    <Teleport to="body">
      <div v-if="deleteTarget" class="modal-backdrop" @click.self="deleteTarget = null">
        <div class="modal modal-sm">
          <div class="modal-header">
            <div>
              <h3 class="modal-title">Delete Expense</h3>
              <p class="modal-subtitle">This action cannot be undone</p>
            </div>
            <button class="modal-close" @click="deleteTarget = null">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <div class="modal-body">
            <div class="delete-warning">
              <span class="material-symbols-outlined delete-warning-icon">warning</span>
              <p>Are you sure you want to delete <strong>{{ deleteTarget.title }}</strong>? This action cannot be undone.</p>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="deleteTarget = null">Cancel</button>
            <button class="btn-danger" :disabled="submitting" @click="handleDelete">
              {{ submitting ? 'Deleting…' : 'Delete Expense' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </AppLayout>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import { expensesAPI } from '../api/expenses'
import CurrencyInput from '../components/CurrencyInput.vue'

const expenses = ref([])
const loading = ref(true)
const searchQuery = ref('')
const filterCategory = ref('')

const modalOpen = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const submitting = ref(false)
const formError = ref('')
const deleteTarget = ref(null)

const categories = [
  'rent', 'utilities', 'software', 'misc'
]

const form = reactive({
  title: '',
  category: '',
  amount: null,
  date: new Date().toISOString().split('T')[0],
  recurring: false,
  notes: '',
})

async function fetchExpenses() {
  loading.value = true
  try {
    const res = await expensesAPI.getExpenses()
    expenses.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchExpenses)

const filtered = computed(() => {
  let list = [...expenses.value]
  list.sort((a, b) => new Date(b.date) - new Date(a.date))
  if (filterCategory.value) list = list.filter(e => e.category === filterCategory.value)
  const q = searchQuery.value.toLowerCase()
  if (q) list = list.filter(e =>
    e.title.toLowerCase().includes(q) ||
    e.category.toLowerCase().includes(q) ||
    (e.notes || '').toLowerCase().includes(q)
  )
  return list
})

function resetForm() {
  form.title = ''
  form.category = ''
  form.amount = null
  form.date = new Date().toISOString().split('T')[0]
  form.recurring = false
  form.notes = ''
  formError.value = ''
}

function openAddModal() {
  resetForm()
  isEditing.value = false
  editingId.value = null
  modalOpen.value = true
}

function openEditModal(e) {
  isEditing.value = true
  editingId.value = e.id
  form.title = e.title
  form.category = e.category
  form.amount = Number(e.amount)
  form.date = e.date
  form.recurring = e.recurring
  form.notes = e.notes || ''
  formError.value = ''
  modalOpen.value = true
}

function closeModal() { modalOpen.value = false }

async function handleSubmit() {
  formError.value = ''
  submitting.value = true
  try {
    const payload = {
      title: form.title,
      category: form.category,
      amount: form.amount,
      date: form.date,
      recurring: form.recurring,
      notes: form.notes || null,
    }
    if (isEditing.value) {
      await expensesAPI.updateExpense(editingId.value, payload)
    } else {
      await expensesAPI.createExpense(payload)
    }
    closeModal()
    await fetchExpenses()
  } catch (err) {
    formError.value = err.response?.data?.detail || 'Operation failed. Please try again.'
  } finally {
    submitting.value = false
  }
}

function confirmDelete(e) { deleteTarget.value = e }

async function handleDelete() {
  submitting.value = true
  try {
    await expensesAPI.deleteExpense(deleteTarget.value.id)
    deleteTarget.value = null
    await fetchExpenses()
  } catch (err) {
    console.error(err)
  } finally {
    submitting.value = false
  }
}

// Helpers
function formatAmount(val) {
  return (Number(val) || 0).toLocaleString('en-IN')
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('en-IN')
}
</script>

<style scoped>
/* ── Page Header ── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}
.page-header-left { display: flex; flex-direction: column; gap: 2px; }
.page-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--color-on-surface);
  margin: 0;
}
.page-subtitle {
  font-size: 13px;
  color: var(--color-on-surface-variant);
  margin: 0;
}

/* ── Primary Button ── */
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition);
  white-space: nowrap;
}
.btn-primary:hover { background: #1f5c5d; }
.btn-primary .material-symbols-outlined { font-size: 18px; }

/* ── Filter Bar ── */
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-xl);
  padding: 12px 16px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-sm);
}
.filter-bar-left { display: flex; gap: 10px; align-items: center; }
.search-box { position: relative; }
.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-on-surface-variant);
  font-size: 18px;
  pointer-events: none;
}
.search-input {
  padding: 8px 12px 8px 36px;
  background: var(--color-surface-dim);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  outline: none;
  transition: border var(--transition);
  min-width: 220px;
}
.search-input:focus { border-color: var(--color-primary); background: var(--color-surface); }
.filter-select {
  padding: 8px 12px;
  background: var(--color-surface-dim);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  outline: none;
  transition: border var(--transition);
  cursor: pointer;
}
.filter-select:focus { border-color: var(--color-primary); background: var(--color-surface); }

/* ── Table Card ── */
.table-card {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
}
.data-table thead {
  background: #f8fafc;
}
.data-table th {
  padding: 12px 16px;
  text-align: left;
  font-family: var(--font-body);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-on-surface-variant);
  border-bottom: 1px solid var(--color-outline);
}
.data-table td {
  padding: 12px 16px;
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  border-bottom: 1px solid #f1f5f9;
}
.data-row:last-child td { border-bottom: none; }
.data-row:hover { background: #fafbfc; }
.col-actions { width: 100px; text-align: center; }

.row-name { font-weight: 600; }
.cell-muted { color: var(--color-on-surface-variant); }
.cell-mono { font-variant-numeric: tabular-nums; }
.cell-amount { font-weight: 600; color: var(--color-on-surface); }

/* ── Empty State ── */
.empty-cell { text-align: center; padding: 0; }
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 48px 16px;
  color: var(--color-on-surface-variant);
}
.empty-icon { font-size: 36px; opacity: 0.4; }
.empty-state p { margin: 0; font-size: 13px; }

/* ── Table Footer ── */
.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8fafc;
  border-top: 1px solid var(--color-outline);
}
.page-info {
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface-variant);
}
.page-btns { display: flex; gap: 6px; }
.page-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface-variant);
  cursor: pointer;
  transition: all var(--transition);
}
.page-btn .material-symbols-outlined { font-size: 16px; }
.page-btn:hover:not(:disabled) { background: var(--color-outline-variant); color: var(--color-on-surface); }
.page-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* ── Row Actions ── */
.row-actions { display: flex; justify-content: center; gap: 6px; }
.icon-btn {
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition);
}
.icon-btn .material-symbols-outlined { font-size: 16px; }
.icon-btn-edit .material-symbols-outlined { color: var(--color-primary); }
.icon-btn-edit:hover { background: var(--color-primary-light); border-color: var(--color-primary); }
.icon-btn-delete .material-symbols-outlined { color: var(--color-error); }
.icon-btn-delete:hover { background: #fef2f2; border-color: #fca5a5; }

/* ── Badges ── */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.badge-blue { background: #dbeafe; color: #1e40af; }
.badge-neutral { background: var(--color-outline-variant); color: var(--color-on-surface-variant); }

/* ── Modals ── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.14);
  max-width: 560px;
  width: 92%;
  max-height: 90vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.modal-wide { max-width: 760px; }
.modal-sm { max-width: 420px; }

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px 24px 20px;
  border-bottom: 1px solid var(--color-outline);
}
.modal-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--color-on-surface);
  margin: 0 0 2px;
}
.modal-subtitle {
  font-size: 13px;
  color: var(--color-on-surface-variant);
  margin: 0;
}
.modal-close {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition);
  flex-shrink: 0;
}
.modal-close:hover { background: var(--color-outline-variant); }
.modal-close .material-symbols-outlined { font-size: 18px; color: var(--color-on-surface-variant); }

.modal-body { padding: 24px; flex: 1; }
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 24px;
  border-top: 1px solid var(--color-outline);
  background: #f8fafc;
  border-radius: 0 0 var(--radius-xl) var(--radius-xl);
}

/* ── Form ── */
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}
.span-2 { grid-column: span 2; }
.form-label {
  display: block;
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-on-surface-variant);
  margin-bottom: 6px;
}
.form-input {
  width: 100%;
  padding: 9px 12px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  outline: none;
  transition: border var(--transition);
  box-sizing: border-box;
}
.form-input:focus { border-color: var(--color-primary); }
textarea.form-input { resize: vertical; }
.form-field-checkbox { display: flex; flex-direction: column; }
.checkbox-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  margin-top: 4px;
}
.checkbox-input { width: 16px; height: 16px; accent-color: var(--color-primary); cursor: pointer; }
.checkbox-text { font-size: 13px; color: var(--color-on-surface); }

.form-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: var(--radius-md);
  font-size: 13px;
  color: var(--color-error);
  margin-bottom: 16px;
}
.form-error .material-symbols-outlined { font-size: 16px; flex-shrink: 0; }

/* ── Delete Warning ── */
.delete-warning {
  display: flex;
  gap: 14px;
  padding: 16px;
  background: #fef9f0;
  border: 1px solid #fde68a;
  border-radius: var(--radius-md);
  align-items: flex-start;
}
.delete-warning-icon { font-size: 22px; color: #d97706; flex-shrink: 0; }
.delete-warning p { margin: 0; font-size: 14px; line-height: 1.5; color: var(--color-on-surface); }

/* ── Action Buttons ── */
.btn-cancel {
  padding: 8px 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface-variant);
  cursor: pointer;
  transition: all var(--transition);
}
.btn-cancel:hover { background: var(--color-outline-variant); }
.btn-submit {
  padding: 9px 18px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition);
}
.btn-submit:hover:not(:disabled) { background: #1f5c5d; }
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger {
  padding: 9px 18px;
  background: var(--color-error);
  color: #fff;
  border: none;
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition);
}
.btn-danger:hover:not(:disabled) { background: #b91c1c; }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }

@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; gap: 10px; }
  .filter-bar { flex-direction: column; align-items: stretch; gap: 8px; }
  .filter-bar-left { flex-wrap: wrap; }
  .table-card { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .data-table { min-width: 520px; }
  .form-grid { grid-template-columns: 1fr; }
  .span-2 { grid-column: span 1; }
}
</style>
