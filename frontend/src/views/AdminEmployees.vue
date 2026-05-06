<template>
  <AppLayout>
    <!-- Page Header Actions -->
    <div class="page-actions">
      <div class="actions-left">
        <div class="search-box">
          <span class="material-symbols-outlined search-icon">search</span>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search directory..."
            class="search-input"
          />
        </div>
        <button class="filter-btn">
          <span class="material-symbols-outlined">filter_list</span>
          Filter
        </button>
      </div>
      <button class="add-btn" @click="openAddModal">
        <span class="material-symbols-outlined">add</span>
        Add New Employee
      </button>
    </div>

    <!-- Data Table -->
    <div class="table-card">
      <table class="emp-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Designation</th>
            <th>Role</th>
            <th>Joining Date</th>
            <th class="text-right">Monthly Salary (₹)</th>
            <th class="text-center col-actions">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="6" class="empty-cell">
              <div class="loading-text">Loading employees…</div>
            </td>
          </tr>
          <tr v-else-if="paginatedEmployees.length === 0">
            <td colspan="6" class="empty-cell">No employees found.</td>
          </tr>
          <tr
            v-for="emp in paginatedEmployees"
            :key="emp.id"
            class="emp-row"
          >
            <td>
              <div class="name-cell">
                <div class="avatar-circle" :style="{ background: avatarColor(emp.name) }">
                  {{ initials(emp.name) }}
                </div>
                <div>
                  <div class="emp-name">{{ emp.name }}</div>
                  <div class="emp-id">EMP-{{ String(emp.id).padStart(3, '0') }}</div>
                </div>
              </div>
            </td>
            <td>{{ emp.designation }}</td>
            <td>
              <span class="role-badge">{{ emp.role }}</span>
            </td>
            <td class="mono muted">{{ formatDate(emp.joining_date) }}</td>
            <td class="text-right mono">{{ formatSalary(emp.salary_month) }}</td>
            <td>
              <div class="row-actions">
                <button class="action-btn edit-btn" title="Edit" @click="openEditModal(emp)">
                  <span class="material-symbols-outlined">edit</span>
                </button>
                <button class="action-btn delete-btn" title="Deactivate" @click="confirmDelete(emp)">
                  <span class="material-symbols-outlined">block</span>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div class="table-footer">
        <span class="page-info">
          Showing {{ filteredEmployees.length === 0 ? 0 : startIndex + 1 }} to {{ endIndex }} of {{ filteredEmployees.length }} entries
        </span>
        <div class="page-btns">
          <button class="page-btn" :disabled="currentPage === 1" @click="currentPage--">Prev</button>
          <button class="page-btn" :disabled="currentPage >= totalPages" @click="currentPage++">Next</button>
        </div>
      </div>
    </div>

    <!-- Modal Backdrop -->
    <Teleport to="body">
      <div v-if="modalOpen" class="modal-backdrop" @click.self="closeModal">
        <div class="modal modal-wide">
          <div class="modal-header">
            <h3 class="modal-title">{{ isEditing ? 'Edit Employee' : 'Add New Employee' }}</h3>
            <button class="modal-close" @click="closeModal">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>

          <form @submit.prevent="handleSubmit" class="modal-body">

            <!-- Photo + Docs side panel -->
            <div class="upload-row">
              <!-- Profile Photo -->
              <div class="photo-upload-area" @click="triggerPhotoInput">
                <img v-if="photoPreview" :src="photoPreview" class="photo-preview" alt="Profile" />
                <div v-else class="photo-placeholder">
                  <span class="material-symbols-outlined">account_circle</span>
                  <span>Upload Photo</span>
                </div>
                <input ref="photoInputRef" type="file" accept="image/*" class="hidden-input" @change="onPhotoSelected" />
              </div>

              <!-- Document Uploads -->
              <div class="doc-upload-area">
                <div class="doc-slot" @click="triggerDocInput('aadhar')">
                  <span class="material-symbols-outlined doc-icon">{{ docFiles.aadhar ? 'check_circle' : 'upload_file' }}</span>
                  <div class="doc-slot-text">
                    <strong>Aadhar Card</strong>
                    <span>{{ docFiles.aadhar ? docFiles.aadhar.name : 'PDF / Image' }}</span>
                  </div>
                </div>
                <div class="doc-slot" @click="triggerDocInput('pan')">
                  <span class="material-symbols-outlined doc-icon">{{ docFiles.pan ? 'check_circle' : 'upload_file' }}</span>
                  <div class="doc-slot-text">
                    <strong>PAN Card</strong>
                    <span>{{ docFiles.pan ? docFiles.pan.name : 'PDF / Image' }}</span>
                  </div>
                </div>
                <div class="doc-slot" @click="triggerDocInput('other')">
                  <span class="material-symbols-outlined doc-icon">{{ docFiles.other ? 'check_circle' : 'upload_file' }}</span>
                  <div class="doc-slot-text">
                    <strong>Other Document</strong>
                    <span>{{ docFiles.other ? docFiles.other.name : 'PDF / Image' }}</span>
                  </div>
                </div>
                <input ref="docInputRef" type="file" accept=".pdf,image/*" class="hidden-input" @change="onDocSelected" />
              </div>
            </div>

            <!-- Form Fields -->
            <div class="form-grid">
              <div class="form-field">
                <label>Full Name *</label>
                <input v-model="form.name" type="text" required placeholder="e.g. Arjun Sharma" />
              </div>
              <div class="form-field">
                <label>Designation *</label>
                <input v-model="form.designation" type="text" required placeholder="e.g. BIM Engineer" />
              </div>
              <div class="form-field">
                <label>Joining Date *</label>
                <input v-model="form.joining_date" type="date" required />
              </div>
              <div class="form-field">
                <label>End Date</label>
                <input v-model="form.end_date" type="date" />
              </div>
              <div class="form-field">
                <label>Monthly Salary (₹)</label>
                <input v-model.number="form.salary_month" type="number" placeholder="e.g. 25000" />
              </div>
              <div class="form-field">
                <label>Hourly Rate (₹) — auto</label>
                <input :value="salaryPerHour" type="text" disabled class="readonly-input" />
              </div>
              <div class="form-field">
                <label>Manager</label>
                <select v-model="form.manager_id">
                  <option :value="null">— None —</option>
                  <option v-for="m in managers" :key="m.id" :value="m.id">{{ m.name }}</option>
                </select>
              </div>
              <div class="form-field">
                <label>Leaves Allowed</label>
                <input v-model.number="form.leaves_allowed" type="number" placeholder="18" />
              </div>
              <div class="form-field">
                <label>PAN Number</label>
                <input v-model="form.pan_number" type="text" placeholder="ABCDE1234F" />
              </div>
              <div class="form-field">
                <label>Aadhar Number</label>
                <input v-model="form.aadhar_number" type="text" placeholder="1234 5678 9012" />
              </div>
              <div class="form-field">
                <label>Personal Email *</label>
                <input v-model="form.personal_mail" type="email" required placeholder="user@gmail.com" />
              </div>
              <div class="form-field">
                <label>Studio Email *</label>
                <input v-model="form.studio_email" type="email" required placeholder="user@studiomh02.com" />
              </div>
              <div class="form-field" v-if="!isEditing">
                <label>Password *</label>
                <input v-model="form.password" type="password" required placeholder="••••••••" />
              </div>
              <div class="form-field">
                <label>Role</label>
                <select v-model="form.role">
                  <option value="employee">Employee</option>
                  <option value="project_manager">Project Manager</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div class="form-field">
                <label>Time Tracker Login (User ID)</label>
                <input v-model="form.time_tracker_login" type="text" placeholder="user@studiomh02.com" />
              </div>
              <div class="form-field">
                <label>Time Tracker Password</label>
                <input v-model="form.time_tracker_password" type="password" placeholder="••••••••" />
              </div>
            </div>

            <!-- Errors -->
            <div v-if="formError" class="form-error">
              <span class="material-symbols-outlined">error</span>
              {{ formError }}
            </div>

            <div class="modal-footer">
              <button type="button" class="btn-cancel" @click="closeModal">Cancel</button>
              <button type="submit" class="btn-submit" :disabled="submitting">
                {{ submitting ? 'Saving…' : (isEditing ? 'Save Changes' : 'Add Employee') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Delete Confirmation -->
    <Teleport to="body">
      <div v-if="deleteTarget" class="modal-backdrop" @click.self="deleteTarget = null">
        <div class="modal modal-sm">
          <div class="modal-header">
            <h3 class="modal-title">Deactivate Employee</h3>
            <button class="modal-close" @click="deleteTarget = null">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <div class="modal-body">
            <p>Are you sure you want to deactivate <strong>{{ deleteTarget.name }}</strong>?<br/>This will mark the employee as inactive.</p>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="deleteTarget = null">Cancel</button>
            <button class="btn-danger" :disabled="submitting" @click="handleDelete">
              {{ submitting ? 'Processing…' : 'Deactivate' }}
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
import { usersAPI } from '../api/users'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const employees = ref([])
const managers = ref([])
const loading = ref(true)
const searchQuery = ref('')
const currentPage = ref(1)
const perPage = 10

// Modal state
const modalOpen = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const submitting = ref(false)
const formError = ref('')
const deleteTarget = ref(null)

// File upload state
const photoInputRef = ref(null)
const docInputRef = ref(null)
const photoPreview = ref(null)
const selectedPhoto = ref(null)
const currentDocType = ref('aadhar')
const docFiles = reactive({ aadhar: null, pan: null, other: null })

const form = reactive({
  name: '',
  designation: '',
  studio_email: '',
  personal_mail: '',
  password: '',
  role: 'employee',
  joining_date: '',
  end_date: '',
  salary_month: null,
  leaves_allowed: 18,
  manager_id: null,
  pan_number: '',
  aadhar_number: '',
  time_tracker_login: '',
  time_tracker_password: '',
})

const salaryPerHour = computed(() => {
  if (!form.salary_month) return ''
  return (form.salary_month / 160).toFixed(2)
})

// ── Fetch employees ──
async function fetchEmployees() {
  loading.value = true
  try {
    const res = await usersAPI.getUsers()
    employees.value = res.data
    managers.value = res.data.filter(u => u.role === 'project_manager' || u.role === 'admin')
  } catch (err) {
    console.error('Failed to load employees:', err)
  } finally {
    loading.value = false
  }
}

onMounted(fetchEmployees)

// ── Filtered + paginated ──
const filteredEmployees = computed(() => {
  const q = searchQuery.value.toLowerCase()
  if (!q) return employees.value
  return employees.value.filter(e =>
    e.name.toLowerCase().includes(q) ||
    e.designation.toLowerCase().includes(q) ||
    e.role.toLowerCase().includes(q)
  )
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredEmployees.value.length / perPage)))
const startIndex = computed(() => (currentPage.value - 1) * perPage)
const endIndex = computed(() => Math.min(startIndex.value + perPage, filteredEmployees.value.length))
const paginatedEmployees = computed(() => filteredEmployees.value.slice(startIndex.value, endIndex.value))

// ── Photo upload ──
function triggerPhotoInput() { photoInputRef.value?.click() }
function onPhotoSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return
  selectedPhoto.value = file
  photoPreview.value = URL.createObjectURL(file)
}

// ── Doc upload ──
function triggerDocInput(type) {
  currentDocType.value = type
  docInputRef.value.value = ''
  docInputRef.value?.click()
}
function onDocSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return
  docFiles[currentDocType.value] = file
}

// ── Modal helpers ──
function resetForm() {
  form.name = ''
  form.designation = ''
  form.studio_email = ''
  form.personal_mail = ''
  form.password = ''
  form.role = 'employee'
  form.joining_date = ''
  form.end_date = ''
  form.salary_month = null
  form.leaves_allowed = 18
  form.manager_id = null
  form.pan_number = ''
  form.aadhar_number = ''
  form.time_tracker_login = ''
  form.time_tracker_password = ''
  formError.value = ''
  photoPreview.value = null
  selectedPhoto.value = null
  docFiles.aadhar = null
  docFiles.pan = null
  docFiles.other = null
}

function openAddModal() {
  resetForm()
  isEditing.value = false
  editingId.value = null
  modalOpen.value = true
}

function openEditModal(emp) {
  isEditing.value = true
  editingId.value = emp.id
  form.name = emp.name
  form.designation = emp.designation
  form.studio_email = emp.studio_email
  form.personal_mail = emp.personal_mail
  form.password = ''
  form.role = emp.role
  form.joining_date = emp.joining_date || ''
  form.end_date = emp.end_date || ''
  form.salary_month = emp.salary_month ? Number(emp.salary_month) : null
  form.leaves_allowed = emp.leaves_allowed ?? 18
  form.manager_id = emp.manager_id ?? null
  form.pan_number = emp.pan_number || ''
  form.aadhar_number = emp.aadhar_number || ''
  form.time_tracker_login = emp.time_tracker_login || ''
  form.time_tracker_password = emp.time_tracker_password || ''
  formError.value = ''
  photoPreview.value = emp.photo_url ? `${API_BASE}${emp.photo_url}` : null
  selectedPhoto.value = null
  docFiles.aadhar = null
  docFiles.pan = null
  docFiles.other = null
  modalOpen.value = true
}

function closeModal() {
  modalOpen.value = false
}

async function handleSubmit() {
  formError.value = ''
  submitting.value = true

  try {
    let userId
    if (isEditing.value) {
      const payload = {}
      const fields = ['name', 'designation', 'studio_email', 'personal_mail', 'role',
        'joining_date', 'end_date', 'salary_month', 'leaves_allowed', 'manager_id',
        'pan_number', 'aadhar_number', 'time_tracker_login', 'time_tracker_password']
      for (const f of fields) {
        if (form[f] !== '' && form[f] !== null && form[f] !== undefined) payload[f] = form[f]
      }
      if (form.password) payload.password = form.password
      const res = await usersAPI.updateUser(editingId.value, payload)
      userId = editingId.value
    } else {
      const res = await usersAPI.createUser({ ...form })
      userId = res.data.id
    }

    // Upload photo if selected
    if (selectedPhoto.value) {
      await usersAPI.uploadPhoto(userId, selectedPhoto.value)
    }

    // Upload documents if selected
    for (const [docType, file] of Object.entries(docFiles)) {
      if (file) await usersAPI.uploadDocument(userId, file, docType)
    }

    closeModal()
    await fetchEmployees()
  } catch (err) {
    formError.value = err.response?.data?.detail || 'Operation failed. Please try again.'
    console.error('Submit error:', err)
  } finally {
    submitting.value = false
  }
}

// ── Delete ──
function confirmDelete(emp) { deleteTarget.value = emp }

async function handleDelete() {
  submitting.value = true
  try {
    await usersAPI.deleteUser(deleteTarget.value.id)
    deleteTarget.value = null
    await fetchEmployees()
  } catch (err) {
    console.error('Delete error:', err)
  } finally {
    submitting.value = false
  }
}

// ── Formatting ──
function initials(name) {
  if (!name) return '?'
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
}

const avatarColors = ['#e2e0fc', '#d5e3fd', '#f2e1b7', '#c5c4dc', '#d2e1fa', '#ffdad6']
function avatarColor(name) {
  if (!name) return avatarColors[0]
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  return avatarColors[Math.abs(hash) % avatarColors.length]
}

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatSalary(val) {
  return (Number(val) || 0).toLocaleString('en-IN')
}
</script>

<style scoped>
/* ───────── Page Actions ───────── */
.page-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.actions-left {
  display: flex;
  gap: 8px;
}

.search-box {
  position: relative;
}

.search-icon {
  position: absolute;
  left: 8px;
  top: 50%;
  transform: translateY(-50%);
  color: #78767d;
  font-size: 18px;
}

.search-input {
  padding: 8px 8px 8px 32px;
  background: #ffffff;
  border: 1px solid #c8c5cd;
  border-radius: 6px;
  font-family: 'Inter', sans-serif;
  font-size: 13px;
  line-height: 18px;
  color: #1c1b1d;
  width: 256px;
  outline: none;
  transition: border 0.15s;
}

.search-input:focus {
  border-color: #1a1a2e;
  box-shadow: 0 0 0 1px #1a1a2e;
}

.search-input::placeholder {
  color: #78767d;
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px;
  border: 1px solid #c8c5cd;
  border-radius: 6px;
  background: #ffffff;
  font-family: 'Inter', sans-serif;
  font-size: 13px;
  line-height: 18px;
  color: #1c1b1d;
  cursor: pointer;
  transition: background 0.15s;
}

.filter-btn:hover {
  background: #f1edef;
}

.filter-btn .material-symbols-outlined {
  font-size: 16px;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  background: #1a1a2e;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  font-weight: 600;
  line-height: 20px;
  cursor: pointer;
  transition: opacity 0.15s;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.add-btn:hover {
  opacity: 0.9;
}

.add-btn:active {
  transform: scale(0.95);
}

.add-btn .material-symbols-outlined {
  font-size: 18px;
}

/* ───────── Table Card ───────── */
.table-card {
  background: #ffffff;
  border: 1px solid #c8c5cd;
  border-radius: 8px;
  overflow: hidden;
}

.emp-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.emp-table thead {
  background: #f6f2f4;
  border-bottom: 1px solid #c8c5cd;
}

.emp-table th {
  padding: 8px 16px;
  font-size: 11px;
  font-weight: 600;
  line-height: 16px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #47464c;
}

.col-actions {
  width: 96px;
}

.emp-table tbody tr {
  border-bottom: 1px solid #e5e1e3;
  transition: background 0.1s;
}

.emp-table tbody tr:last-child {
  border-bottom: none;
}

.emp-row:hover {
  background: #fcf8fa;
}

.emp-table td {
  padding: 8px 16px;
  font-size: 13px;
  line-height: 18px;
  color: #1c1b1d;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.avatar-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #1a1a2e;
  flex-shrink: 0;
}

.emp-name {
  font-weight: 600;
  color: #1c1b1d;
}

.emp-id {
  font-size: 13px;
  color: #47464c;
  font-variant-numeric: tabular-nums;
}

.role-badge {
  display: inline-block;
  padding: 4px 8px;
  background: #ebe7e9;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: capitalize;
  color: #1c1b1d;
  letter-spacing: 0.05em;
}

.mono {
  font-variant-numeric: tabular-nums;
}

.muted {
  color: #47464c;
}

.text-right {
  text-align: right;
}

.text-center {
  text-align: center;
}

.row-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s;
}

.emp-row:hover .row-actions {
  opacity: 1;
}

.action-btn {
  padding: 4px;
  border: none;
  background: none;
  border-radius: 4px;
  cursor: pointer;
  color: #47464c;
  transition: all 0.15s;
}

.action-btn .material-symbols-outlined {
  font-size: 18px;
}

.edit-btn:hover {
  color: #1a1a2e;
  background: #f1edef;
}

.delete-btn:hover {
  color: #ba1a1a;
  background: #ffdad6;
}

.empty-cell {
  padding: 24px;
  text-align: center;
  color: #78767d;
}

.loading-text {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ── Pagination ── */
.table-footer {
  padding: 8px 16px;
  border-top: 1px solid #c8c5cd;
  background: #f6f2f4;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-info {
  font-size: 13px;
  line-height: 18px;
  color: #47464c;
}

.page-btns {
  display: flex;
  gap: 4px;
}

.page-btn {
  padding: 4px 8px;
  border: 1px solid #c8c5cd;
  border-radius: 4px;
  background: #ffffff;
  font-family: 'Inter', sans-serif;
  font-size: 13px;
  color: #1c1b1d;
  cursor: pointer;
  transition: background 0.15s;
}

.page-btn:hover:not(:disabled) {
  background: #f1edef;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ───────── Modal ───────── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  animation: fadeIn 0.15s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal {
  background: #ffffff;
  border-radius: 12px;
  width: 600px;
  max-width: 95vw;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  animation: slideUp 0.2s ease;
}

.modal-wide {
  width: 820px;
}

.modal-sm {
  width: 400px;
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e1e3;
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: #1c1b1d;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  color: #47464c;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}

.modal-close:hover {
  background: #f1edef;
}

.modal-body {
  padding: 24px;
}

.modal-body p {
  font-size: 14px;
  line-height: 22px;
  color: #47464c;
  margin: 0;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-field label {
  font-size: 13px;
  font-weight: 600;
  color: #47464c;
}

.form-field input,
.form-field select {
  height: 40px;
  padding: 0 12px;
  border: 1px solid #c8c5cd;
  border-radius: 6px;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  color: #1c1b1d;
  outline: none;
  transition: border 0.15s;
  background: #ffffff;
}

.form-field input:focus,
.form-field select:focus {
  border-color: #1a1a2e;
  box-shadow: 0 0 0 1px #1a1a2e;
}

.form-field input::placeholder {
  color: #78767d;
}

.form-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #ffdad6;
  border-radius: 8px;
  color: #93000a;
  font-size: 14px;
  margin-top: 16px;
}

.form-error .material-symbols-outlined {
  font-size: 18px;
  flex-shrink: 0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 20px 24px;
  border-top: 1px solid #e5e1e3;
}

.modal .modal-footer {
  padding: 20px 24px;
}

form .modal-footer {
  margin-top: 24px;
  padding: 0;
  border-top: none;
}

.btn-cancel {
  padding: 8px 16px;
  border: 1px solid #c8c5cd;
  border-radius: 6px;
  background: #ffffff;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  color: #1c1b1d;
  cursor: pointer;
}

.btn-cancel:hover {
  background: #f1edef;
}

.btn-submit {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  background: #1a1a2e;
  color: #ffffff;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}

.btn-submit:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-danger {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  background: #ba1a1a;
  color: #ffffff;
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}

.btn-danger:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ───────── Material Symbols ───────── */
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

/* ───────── Upload UI ───────── */
.upload-row {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.hidden-input {
  display: none;
}

.photo-upload-area {
  width: 120px;
  height: 120px;
  border: 2px dashed #c8c5cd;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  overflow: hidden;
  transition: border-color 0.15s;
}

.photo-upload-area:hover {
  border-color: #1a1a2e;
}

.photo-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  color: #78767d;
  font-size: 11px;
  font-weight: 600;
  text-align: center;
}

.photo-placeholder .material-symbols-outlined {
  font-size: 32px;
}

.doc-upload-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  justify-content: center;
}

.doc-slot {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border: 1px solid #e5e1e3;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.doc-slot:hover {
  background: #f6f2f4;
  border-color: #c8c5cd;
}

.doc-icon {
  font-size: 20px;
  color: #1a1a2e;
}

.doc-slot-text {
  display: flex;
  flex-direction: column;
}

.doc-slot-text strong {
  font-size: 12px;
  font-weight: 600;
  color: #1c1b1d;
}

.doc-slot-text span {
  font-size: 11px;
  color: #78767d;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.readonly-input {
  background: #f6f2f4 !important;
  color: #47464c;
  cursor: not-allowed;
}
</style>
