<template>
  <component :is="layout">
    <!-- Page Header Actions -->
    <div class="page-actions">
      <div class="actions-left">
        <div class="search-box">
          <span class="material-symbols-outlined search-icon">search</span>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search employees..."
            class="search-input"
          />
        </div>
        <button class="filter-btn">
          <span class="material-symbols-outlined">filter_list</span>
          Filter
        </button>
      </div>
      <div class="add-btn-group">
        <button class="add-btn" @click="openAddModal('employee')">
          <span class="material-symbols-outlined">add</span>
          Add Employee
        </button>
        <button class="add-btn add-btn-admin" @click="openAddModal('admin')" title="Create a fellow administrator account">
          <span class="material-symbols-outlined">admin_panel_settings</span>
          Add Admin
        </button>
      </div>
    </div>

    <div class="employees-layout">
      <section class="cards-panel">
        <div class="cards-header">
          <div>
            <h2 class="section-title">Employee directory</h2>
            <p class="section-note">Search employees and manage them through the card list.</p>
          </div>
        </div>

        <div class="cards-grid">
          <div v-if="loading" class="cards-empty">
            <div class="loading-text">Loading employees…</div>
          </div>

          <div v-else-if="filteredEmployees.length === 0" class="cards-empty">
            No employees found.
          </div>

          <div v-else class="cards-wrap">
            <article
              v-for="emp in filteredEmployees"
              :key="emp.id"
              class="employee-card"
              @click="goToProfile(emp)"
            >
              <div class="employee-card-top">
                <div class="name-cell">
                  <div class="avatar-circle" :style="{ background: avatarColor(emp.name) }">
                    {{ initials(emp.name) }}
                  </div>
                  <div>
                    <div class="emp-name">{{ emp.name }}</div>
                    <div class="emp-id">EMP-{{ String(emp.id).padStart(3, '0') }}</div>
                  </div>
                </div>
                <span class="role-badge" :class="`role-${emp.role}`">{{ formatRole(emp.role) }}</span>
              </div>

              <div class="employee-card-body">
                <div class="stat-row">
                  <span class="stat-label">Designation</span>
                  <span>{{ emp.designation || '—' }}</span>
                </div>
                <div class="stat-row">
                  <span class="stat-label">Joining</span>
                  <span>{{ formatDate(emp.joining_date) }}</span>
                </div>
                <div class="stat-row" v-if="isAdmin">
                  <span class="stat-label">Salary</span>
                  <span>₹{{ formatSalary(emp.salary_month) }}</span>
                </div>
              </div>

              <div class="card-actions">
                <button type="button" class="btn-text" @click.stop="openEditModal(emp)">Edit</button>
              </div>
            </article>
          </div>
        </div>

        <div class="table-footer">
          <span class="page-info">
            {{ filteredEmployees.length }} {{ filteredEmployees.length === 1 ? 'employee' : 'employees' }}
          </span>
        </div>
      </section>
    </div>

    <!-- Modal Backdrop -->
    <Teleport to="body">
      <div v-if="modalOpen" class="modal-backdrop">
        <div class="modal modal-wide">
          <div class="modal-header">
            <h3 class="modal-title">{{ modalTitle }}</h3>
            <button class="modal-close" @click="closeModal">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>

          <form @submit.prevent="handleSubmit" class="modal-body">

            <!-- Draft restore banner -->
            <div v-if="showDraftBanner" class="draft-banner">
              <span class="material-symbols-outlined">history</span>
              <span>You have an unsaved draft from a previous session.</span>
              <button type="button" class="draft-restore-btn" @click="restoreEmpDraft">Restore</button>
              <button type="button" class="draft-discard-btn" @click="discardEmpDraft">Discard</button>
            </div>

            <!-- Warning banner when creating an admin -->
            <div v-if="!isEditing && form.role === 'admin'" class="admin-warn-banner">
              <span class="material-symbols-outlined">admin_panel_settings</span>
              <div>
                <strong>You're creating an administrator.</strong>
                This person will have full access to settings, salaries, invoices,
                and every other admin's data. Set a designation that reflects their
                actual role (e.g. <em>Founder</em>, <em>Partner</em>, <em>HR Head</em>).
              </div>
            </div>

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
              <div class="form-field" v-if="isAdmin">
                <label>Salary / Month (₹)</label>
                <CurrencyInput v-model="form.salary_month" placeholder="e.g. 25000" />
              </div>
              <div class="form-field" v-if="isAdmin">
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
                <label>Paid Leave Balance (days)</label>
                <input v-model.number="form.paid_leave_balance" type="number" step="0.5" placeholder="0" />
              </div>
              <div class="form-field">
                <label>PAN Number *</label>
                <input v-model="form.pan_number" type="text" required placeholder="ABCDE1234F" />
              </div>
              <div class="form-field">
                <label>Aadhar Number *</label>
                <input v-model="form.aadhar_number" type="text" required placeholder="1234 5678 9012" />
              </div>
              <div class="form-field">
                <label>Gender</label>
                <select v-model="form.gender">
                  <option value="">— Select —</option>
                  <option value="M">Male</option>
                  <option value="F">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div class="form-field">
                <label>Location</label>
                <input v-model="form.location" type="text" placeholder="e.g. Vile Parle East" />
              </div>
              <div class="form-field">
                <label>Bank Name</label>
                <input v-model="form.bank_name" type="text" placeholder="e.g. HDFC BANK" />
              </div>
              <div class="form-field">
                <label>Bank A/C Number</label>
                <input v-model="form.bank_account_number" type="text" placeholder="Account number" />
              </div>
              <div class="form-field">
                <label>Phone Number</label>
                <input v-model="form.phone_number" type="text" placeholder="e.g. +91 98765 43210" />
              </div>
              <div class="form-field">
                <label>Emergency Contact</label>
                <input v-model="form.emergency_contact_number" type="text" placeholder="e.g. +91 98765 43210" />
              </div>
              <div class="form-field">
                <label>Relationship with Emergency Contact</label>
                <input v-model="form.emergency_contact_relationship" type="text" placeholder="e.g. Spouse / Parent" />
              </div>
              <div class="form-field">
                <label>Personal Email *</label>
                <input v-model="form.personal_mail" type="email" required placeholder="user@gmail.com" />
              </div>
              <div class="form-field">
                <label>Studio Email *</label>
                <input v-model="form.studio_email" type="email" required placeholder="user@studiomh02.com" />
              </div>
              <div class="form-field">
                <label>Password {{ isEditing ? '(Optional)' : '*' }}</label>
                <input 
                  v-model="form.password" 
                  type="password" 
                  :required="!isEditing" 
                  :placeholder="isEditing ? 'Leave blank to keep current' : '••••••••'" 
                />
              </div>
              <div class="form-field">
                <label>Role</label>
                <select v-model="form.role">
                  <option value="employee">Employee</option>
                  <option value="project_manager">Project Manager</option>
                  <option value="admin">Admin</option>
                </select>
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
                {{ submitting ? 'Saving…' : (isEditing ? 'Save Changes' : (form.role === 'admin' ? 'Add Administrator' : 'Add Employee')) }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Delete Confirmation -->
    <Teleport to="body">
      <div v-if="deleteTarget" class="modal-backdrop">
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
  </component>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import EmployeeLayout from '../components/EmployeeLayout.vue'
import { useAuthStore } from '../stores/auth'
import { usersAPI } from '../api/users'
import CurrencyInput from '../components/CurrencyInput.vue'
import { useDraftStorage } from '../composables/useDraftStorage'

const getApiBaseUrl = () => {
  const envUrl = import.meta.env.VITE_API_URL
  if (envUrl && !envUrl.includes('localhost') && !envUrl.includes('127.0.0.1')) {
    return envUrl
  }
  if (typeof window !== 'undefined' && window.location) {
    return `${window.location.protocol}//${window.location.hostname}:8000`
  }
  return 'http://localhost:8000'
}

const API_BASE = getApiBaseUrl()

const router = useRouter()
const authStore = useAuthStore()

const layout = computed(() => {
  return authStore.role === 'admin' ? AppLayout : EmployeeLayout
})

const isAdmin = computed(() => authStore.role === 'admin')

// Modal title shifts based on whether we're adding/editing and what role.
// Encourages the admin to feel like the "Add Admin" button is a separate flow.
const modalTitle = computed(() => {
  if (isEditing.value) return 'Edit User'
  return form.role === 'admin' ? 'Add Administrator' : 'Add Employee'
})

const employees = ref([])
const managers = ref([])
const loading = ref(true)
const searchQuery = ref('')

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
  salary_hour: null,
  leaves_allowed: 18,
  paid_leave_balance: 0,
  manager_id: null,
  pan_number: '',
  aadhar_number: '',
  gender: '',
  location: '',
  bank_name: '',
  bank_account_number: '',
  phone_number: '',
  emergency_contact_number: '',
  emergency_contact_relationship: '',
})

const { draft: empDraft, saveDraft: saveEmpDraft, clearDraft: clearEmpDraft, hasDraft: hasEmpDraft, load: loadEmpDraft } = useDraftStorage('employee_create')
const showDraftBanner = ref(false)

// Auto-save draft during add mode
watch(() => ({ ...form }), (val) => {
  if (modalOpen.value && !isEditing.value) {
    saveEmpDraft({ ...val })
  }
}, { deep: true })

function restoreEmpDraft() {
  if (!empDraft.value) return
  const d = empDraft.value
  Object.keys(form).forEach(k => { if (d[k] !== undefined) form[k] = d[k] })
  showDraftBanner.value = false
}

function discardEmpDraft() {
  clearEmpDraft()
  showDraftBanner.value = false
}

const salaryPerHour = computed(() => {
  if (!form.salary_month) return ''
  return ((form.salary_month * 13) / 12 / 160).toFixed(2)
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
  let list = [...employees.value]
  list.sort((a, b) => (b.id || 0) - (a.id || 0))
  const q = searchQuery.value.toLowerCase()
  if (!q) return list
  return list.filter(e =>
    e.name.toLowerCase().includes(q) ||
    e.designation.toLowerCase().includes(q) ||
    e.role.toLowerCase().includes(q)
  )
})

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
  form.salary_hour = null
  form.leaves_allowed = 18
  form.paid_leave_balance = 0
  form.manager_id = null
  form.pan_number = ''
  form.aadhar_number = ''
  form.gender = ''
  form.location = ''
  form.bank_name = ''
  form.bank_account_number = ''
  form.phone_number = ''
  form.emergency_contact_number = ''
  form.emergency_contact_relationship = ''
  formError.value = ''
  photoPreview.value = null
  selectedPhoto.value = null
  docFiles.aadhar = null
  docFiles.pan = null
  docFiles.other = null
}

async function openAddModal(role = 'employee') {
  resetForm()
  isEditing.value = false
  editingId.value = null
  form.role = role  // pre-fill the Role dropdown for whichever button was clicked
  modalOpen.value = true
  // Pull the latest draft for this account (may have been saved on another device).
  await loadEmpDraft()
  if (hasEmpDraft.value) showDraftBanner.value = true
}

function goToProfile(emp) {
  router.push(`/admin/employees/${emp.id}`)
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
  form.salary_hour = emp.salary_hour ? Number(emp.salary_hour) : null
  form.leaves_allowed = emp.leaves_allowed ?? 18
  form.paid_leave_balance = emp.paid_leave_balance != null ? Number(emp.paid_leave_balance) : 0
  form.manager_id = emp.manager_id ?? null
  form.pan_number = emp.pan_number || ''
  form.aadhar_number = emp.aadhar_number || ''
  form.gender = emp.gender || ''
  form.location = emp.location || ''
  form.bank_name = emp.bank_name || ''
  form.bank_account_number = emp.bank_account_number || ''
  form.phone_number = emp.phone_number || ''
  form.emergency_contact_number = emp.emergency_contact_number || ''
  form.emergency_contact_relationship = emp.emergency_contact_relationship || ''
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
        'joining_date', 'end_date', 'salary_month', 'salary_hour', 'leaves_allowed', 'paid_leave_balance', 'manager_id',
        'pan_number', 'aadhar_number', 'gender', 'location', 'bank_name', 'bank_account_number',
        'phone_number', 'emergency_contact_number', 'emergency_contact_relationship']
      for (const f of fields) {
        if (form[f] !== '' && form[f] !== null && form[f] !== undefined) payload[f] = form[f]
      }
      if (form.password) payload.password = form.password
      const res = await usersAPI.updateUser(editingId.value, payload)
      userId = editingId.value
    } else {
      const payload = {}
      const fields = ['name', 'designation', 'studio_email', 'personal_mail', 'password', 'role',
        'joining_date', 'end_date', 'salary_month', 'salary_hour', 'leaves_allowed', 'paid_leave_balance', 'manager_id',
        'pan_number', 'aadhar_number', 'gender', 'location', 'bank_name', 'bank_account_number',
        'phone_number', 'emergency_contact_number', 'emergency_contact_relationship']
      for (const f of fields) {
        if (form[f] !== '' && form[f] !== null && form[f] !== undefined) {
          payload[f] = form[f]
        }
      }
      const res = await usersAPI.createUser(payload)
      userId = res.data.id
      clearEmpDraft()
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

function formatRole(role) {
  if (!role) return '—'
  if (role === 'project_manager') return 'Project Manager'
  return role.charAt(0).toUpperCase() + role.slice(1)
}
</script>

<style scoped>
/* ─── Material Symbols ─── */
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

/* ─── Page Actions ─── */
.page-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.actions-left { display: flex; gap: 8px; align-items: center; }

.employees-layout {
  display: block;
}

.cards-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 18px;
}

.section-note {
  margin: 4px 0 0;
  color: var(--color-on-surface-variant);
  font-size: 13px;
}

.panel-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.cards-grid {
  min-height: 220px;
}

.cards-wrap {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

.employee-card {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: 20px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  cursor: pointer;
  transition: transform .16s ease, border-color .16s ease, box-shadow .16s ease;
}

.employee-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-primary);
  box-shadow: var(--shadow-sm);
}

.employee-card--selected {
  border-color: var(--color-primary);
  box-shadow: 0 18px 34px rgba(40, 116, 117, 0.14);
}

.employee-card-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.employee-card-body {
  display: grid;
  gap: 10px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: var(--color-on-surface-variant);
  font-size: 13px;
}

.stat-label {
  font-weight: 700;
  color: var(--color-on-surface);
}

.card-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: auto;
}

.btn-text {
  border: none;
  background: none;
  color: var(--color-primary);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  padding: 0;
}

.btn-text:hover {
  text-decoration: underline;
}


/* Search */
.search-box { position: relative; }
.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-on-surface-variant);
  font-size: 16px;
  pointer-events: none;
}
.search-input {
  padding: 9px 12px 9px 34px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  width: 240px;
  outline: none;
  transition: border-color var(--transition), box-shadow var(--transition);
}
.search-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}
.search-input::placeholder { color: var(--color-on-surface-variant); }

/* Filter button (outline style) */
.filter-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 9px 14px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-surface);
  cursor: pointer;
  transition: background var(--transition);
}
.filter-btn:hover { background: var(--color-outline-variant); }
.filter-btn .material-symbols-outlined { font-size: 15px; }

/* Add buttons */
.add-btn-group { display: inline-flex; gap: 8px; }
.add-btn {
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
  transition: opacity var(--transition), box-shadow var(--transition);
  box-shadow: var(--shadow-sm);
}
.add-btn:hover { opacity: 0.88; box-shadow: var(--shadow-md); }
.add-btn .material-symbols-outlined { font-size: 16px; }

/* ─── Table Card ─── */
.table-card {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}
.emp-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}
.emp-table thead { background: #f8fafc; }
.emp-table th {
  padding: 12px 16px;
  font-family: var(--font-body);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .06em;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
  border-bottom: 1px solid var(--color-outline);
  white-space: nowrap;
}
.col-actions { width: 100px; }

.emp-table tbody tr {
  border-bottom: 1px solid var(--color-outline-variant);
  transition: background var(--transition);
}
.emp-table tbody tr:last-child { border-bottom: none; }
.emp-row:hover { background: #fafbfc; }
.emp-table td {
  padding: 12px 16px;
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  vertical-align: middle;
}

/* Name cell with avatar */
.name-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.avatar-circle {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 700;
  color: var(--color-primary);
  flex-shrink: 0;
}
.emp-name { font-weight: 600; color: var(--color-on-surface); }
.emp-id {
  font-family: 'Courier New', monospace;
  font-size: 11px;
  color: var(--color-on-surface-variant);
}

/* Role badges */
.role-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 9px;
  border-radius: var(--radius-full);
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 600;
  text-transform: capitalize;
  background: var(--color-outline-variant);
  color: var(--color-on-surface-variant);
}
.role-badge.role-admin {
  background: var(--color-primary-light);
  color: var(--color-primary);
}
.role-badge.role-project_manager {
  background: #fef3c7;
  color: #92400e;
}
.role-badge.role-employee {
  background: var(--color-outline-variant);
  color: var(--color-on-surface-variant);
}

/* Admin warning banner */
.admin-warn-banner {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 14px 16px;
  margin-bottom: 20px;
  background: var(--color-primary-light);
  border: 1px solid rgba(40, 116, 117, 0.3);
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 13px;
  line-height: 1.5;
  color: var(--color-on-surface);
}
.admin-warn-banner .material-symbols-outlined {
  font-size: 20px;
  color: var(--color-primary);
  flex-shrink: 0;
  margin-top: 1px;
}
.admin-warn-banner strong {
  display: block;
  margin-bottom: 2px;
  color: var(--color-primary);
  font-weight: 700;
}

.mono { font-variant-numeric: tabular-nums; }
.muted { color: var(--color-on-surface-variant); }
.text-right  { text-align: right; }
.text-center { text-align: center; }

/* Row action buttons */
.row-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  opacity: 0;
  transition: opacity var(--transition);
}
.emp-row:hover .row-actions { opacity: 1; }
.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: none;
  background: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-on-surface-variant);
  transition: background var(--transition), color var(--transition);
}
.action-btn .material-symbols-outlined { font-size: 17px; }
.view-btn:hover   { color: var(--color-primary); background: var(--color-primary-light); }
.edit-btn:hover   { color: var(--color-primary); background: var(--color-primary-light); }
.delete-btn:hover { color: var(--color-error);   background: #fee2e2; }

/* Empty / loading */
.empty-cell {
  padding: 48px 16px;
  text-align: center;
  color: var(--color-on-surface-variant);
  font-size: 13px;
}
.loading-text { animation: pulse 1.4s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }

/* ─── Pagination ─── */
.table-footer {
  padding: 10px 16px;
  border-top: 1px solid var(--color-outline);
  background: #f8fafc;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.page-info {
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--color-on-surface-variant);
}
.page-btns { display: flex; gap: 6px; }
.page-btn {
  padding: 5px 12px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-on-surface);
  cursor: pointer;
  transition: background var(--transition);
}
.page-btn:hover:not(:disabled) { background: var(--color-outline-variant); }
.page-btn:disabled { opacity: 0.45; cursor: not-allowed; }

/* ─── Modal ─── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  animation: fadeIn 0.15s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.modal {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  width: 600px;
  max-width: 95vw;
  max-height: 92vh;
  overflow-y: auto;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.18);
  animation: slideUp 0.2s ease;
}
.modal-wide { width: 840px; }
.modal-sm   { width: 420px; }
@keyframes slideUp { from { transform: translateY(16px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-outline);
}
.modal-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  color: var(--color-on-surface);
  margin: 0;
  letter-spacing: -0.01em;
}
.modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: none;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-on-surface-variant);
  cursor: pointer;
  transition: background var(--transition);
}
.modal-close:hover { background: var(--color-outline-variant); }

.modal-body { padding: 24px; }
.modal-body p {
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-on-surface-variant);
  margin: 0;
}

/* ─── Form ─── */
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.form-field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.form-field label {
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: var(--color-on-surface-variant);
}
.form-field input,
.form-field select {
  height: 38px;
  padding: 0 12px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  background: var(--color-surface);
  outline: none;
  transition: border-color var(--transition), box-shadow var(--transition);
}
.form-field input:focus,
.form-field select:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}
.form-field input::placeholder { color: var(--color-on-surface-variant); }

.form-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 11px 14px;
  background: #fee2e2;
  border: 1px solid #fecaca;
  border-radius: var(--radius-md);
  color: #b91c1c;
  font-family: var(--font-body);
  font-size: 13px;
  margin-top: 16px;
}
.form-error .material-symbols-outlined { font-size: 16px; flex-shrink: 0; }

/* Modal footer */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 18px 24px;
  border-top: 1px solid var(--color-outline);
  background: #f8fafc;
  border-radius: 0 0 var(--radius-xl) var(--radius-xl);
}
form .modal-footer {
  margin-top: 24px;
  padding: 0;
  border-top: none;
  background: none;
  border-radius: 0;
}

/* Buttons */
.btn-cancel {
  padding: 9px 18px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-surface);
  cursor: pointer;
  transition: background var(--transition);
}
.btn-cancel:hover { background: var(--color-outline-variant); }

.btn-submit {
  padding: 9px 18px;
  border: none;
  border-radius: var(--radius-lg);
  background: var(--color-primary);
  color: #fff;
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity var(--transition);
}
.btn-submit:hover:not(:disabled) { opacity: 0.88; }
.btn-submit:disabled { opacity: 0.45; cursor: not-allowed; }

.btn-danger {
  padding: 9px 18px;
  border: none;
  border-radius: var(--radius-lg);
  background: var(--color-error);
  color: #fff;
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity var(--transition);
}
.btn-danger:hover:not(:disabled) { opacity: 0.88; }
.btn-danger:disabled { opacity: 0.45; cursor: not-allowed; }

/* ─── Upload UI ─── */
.upload-row {
  display: flex;
  gap: 14px;
  margin-bottom: 20px;
}
.hidden-input { display: none; }

.photo-upload-area {
  width: 112px;
  height: 112px;
  border: 2px dashed var(--color-outline);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  overflow: hidden;
  transition: border-color var(--transition);
}
.photo-upload-area:hover { border-color: var(--color-primary); }
.photo-preview { width: 100%; height: 100%; object-fit: cover; }

.photo-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  color: var(--color-on-surface-variant);
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 600;
  text-align: center;
}
.photo-placeholder .material-symbols-outlined { font-size: 30px; opacity: 0.4; }

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
  gap: 10px;
  padding: 8px 12px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition), border-color var(--transition);
}
.doc-slot:hover {
  background: var(--color-surface-dim);
  border-color: var(--color-primary);
}
.doc-icon { font-size: 18px; color: var(--color-primary); }
.doc-slot-text { display: flex; flex-direction: column; }
.doc-slot-text strong {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 700;
  color: var(--color-on-surface);
}
.doc-slot-text span {
  font-family: var(--font-body);
  font-size: 11px;
  color: var(--color-on-surface-variant);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.readonly-input {
  background: var(--color-outline-variant) !important;
  color: var(--color-on-surface-variant) !important;
  cursor: not-allowed;
}

/* Draft banner */
.draft-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  margin-bottom: 18px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 13px;
  color: #92400e;
}
.draft-banner .material-symbols-outlined { font-size: 18px; flex-shrink: 0; }
.draft-restore-btn {
  margin-left: auto;
  padding: 5px 12px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}
.draft-restore-btn:hover { opacity: 0.88; }
.draft-discard-btn {
  padding: 5px 12px;
  background: none;
  border: 1px solid #d97706;
  color: #d97706;
  border-radius: var(--radius-md);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}
.draft-discard-btn:hover { background: #fef3c7; }

@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; gap: 10px; }
  .header-actions { flex-wrap: wrap; }
  .filter-bar { flex-direction: column; align-items: stretch; gap: 8px; }
  .filter-bar-left { flex-wrap: wrap; }
  .table-card { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .data-table { min-width: 560px; }
  .modal { max-width: 100%; width: 100%; }
  .modal-backdrop { padding: 8px; }
  .form-grid { grid-template-columns: 1fr !important; }
  .span-2 { grid-column: span 1 !important; }
}
</style>
