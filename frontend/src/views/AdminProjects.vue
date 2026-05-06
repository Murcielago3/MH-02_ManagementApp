<template>
  <AppLayout>
    <!-- Page Actions -->
    <div class="page-actions">
      <div class="actions-left">
        <div class="search-box">
          <span class="material-symbols-outlined search-icon">search</span>
          <input v-model="searchQuery" type="text" placeholder="Search projects..." class="search-input" />
        </div>
        <select v-model="filterYear" class="year-select">
          <option value="">All Years</option>
          <option v-for="y in yearOptions" :key="y" :value="y">{{ y }}</option>
        </select>
      </div>
      <button class="add-btn" @click="openAddModal">
        <span class="material-symbols-outlined">add</span>
        Add New Project
      </button>
    </div>

    <!-- Table -->
    <div class="table-card">
      <table class="proj-table">
        <thead>
          <tr>
            <th>Project No.</th>
            <th>Name</th>
            <th>Location</th>
            <th>Stage</th>
            <th>Year</th>
            <th>Billing</th>
            <th class="text-right">Remuneration (₹)</th>
            <th class="text-center col-actions">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="8" class="empty-cell"><div class="loading-text">Loading projects…</div></td>
          </tr>
          <tr v-else-if="paginated.length === 0">
            <td colspan="8" class="empty-cell">No projects found.</td>
          </tr>
          <tr v-for="p in paginated" :key="p.id" class="proj-row">
            <td class="mono"><span class="proj-num">{{ p.project_number }}</span></td>
            <td><span class="proj-name">{{ p.name }}</span></td>
            <td class="muted">{{ p.location || '—' }}</td>
            <td>
              <span class="stage-badge" :class="stageBadgeClass(p.current_stage)">
                {{ p.current_stage || 'N/A' }}
              </span>
            </td>
            <td class="mono muted">{{ p.year || '—' }}</td>
            <td>
              <span class="billing-badge" :class="p.is_billed === 'billed' ? 'billed' : 'unbilled'">
                {{ p.is_billed }}
              </span>
            </td>
            <td class="text-right mono">{{ formatAmount(p.project_remuneration) }}</td>
            <td>
              <div class="row-actions">
                <button class="action-btn edit-btn" title="Edit" @click="openEditModal(p)">
                  <span class="material-symbols-outlined">edit</span>
                </button>
                <button class="action-btn delete-btn" title="Delete" @click="confirmDelete(p)">
                  <span class="material-symbols-outlined">delete</span>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="table-footer">
        <span class="page-info">
          Showing {{ filtered.length === 0 ? 0 : startIdx + 1 }} to {{ endIdx }} of {{ filtered.length }} entries
        </span>
        <div class="page-btns">
          <button class="page-btn" :disabled="currentPage === 1" @click="currentPage--">Prev</button>
          <button class="page-btn" :disabled="currentPage >= totalPages" @click="currentPage++">Next</button>
        </div>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <Teleport to="body">
      <div v-if="modalOpen" class="modal-backdrop" @click.self="closeModal">
        <div class="modal modal-wide">
          <div class="modal-header">
            <h3 class="modal-title">{{ isEditing ? 'Edit Project' : 'Add New Project' }}</h3>
            <button class="modal-close" @click="closeModal">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>

          <form @submit.prevent="handleSubmit" class="modal-body">
            <div class="form-grid">
              <!-- Project Number -->
              <div class="form-field">
                <label>Project Number *</label>
                <input v-model="form.project_number" type="text" required placeholder="e.g. MH02-2024-001" :disabled="isEditing" />
              </div>
              <!-- Name -->
              <div class="form-field">
                <label>Project Name *</label>
                <input v-model="form.name" type="text" required placeholder="e.g. Residence at Banjara Hills" />
              </div>
              <!-- Location -->
              <div class="form-field">
                <label>Location</label>
                <input v-model="form.location" type="text" placeholder="e.g. Hyderabad, Telangana" />
              </div>
              <!-- Google Maps Link -->
              <div class="form-field">
                <label>Google Maps Link</label>
                <input v-model="form.gmap_link" type="url" placeholder="https://maps.google.com/..." />
              </div>
              <!-- Year -->
              <div class="form-field">
                <label>Year</label>
                <input v-model.number="form.year" type="number" placeholder="2024" min="2000" max="2100" />
              </div>
              <!-- Current Stage -->
              <div class="form-field">
                <label>Current Stage</label>
                <select v-model="form.current_stage">
                  <option value="">— Select Stage —</option>
                  <option v-for="s in stages" :key="s" :value="s">{{ s }}</option>
                </select>
              </div>
              <!-- Billing Status -->
              <div class="form-field">
                <label>Billing Status</label>
                <select v-model="form.is_billed">
                  <option value="unbilled">Unbilled</option>
                  <option value="billed">Billed</option>
                  <option value="partial">Partial</option>
                </select>
              </div>
              <!-- Client -->
              <div class="form-field">
                <label>Client</label>
                <select v-model="form.client_id">
                  <option :value="null">— No Client —</option>
                  <option v-for="c in clients" :key="c.id" :value="c.id">{{ c.name }}</option>
                </select>
              </div>
              <!-- Partner Remuneration -->
              <div class="form-field">
                <label>Partner Remuneration (₹)</label>
                <input v-model.number="form.partner_remuneration" type="number" placeholder="0" min="0" />
              </div>
              <!-- Employee Remuneration -->
              <div class="form-field">
                <label>Employee Remuneration (₹)</label>
                <input v-model.number="form.employee_remuneration" type="number" placeholder="0" min="0" />
              </div>
              <!-- Project Remuneration -->
              <div class="form-field span-2">
                <label>Total Project Remuneration (₹)</label>
                <input v-model.number="form.project_remuneration" type="number" placeholder="0" min="0" />
              </div>
            </div>

            <div v-if="formError" class="form-error">
              <span class="material-symbols-outlined">error</span>
              {{ formError }}
            </div>

            <div class="modal-footer">
              <button type="button" class="btn-cancel" @click="closeModal">Cancel</button>
              <button type="submit" class="btn-submit" :disabled="submitting">
                {{ submitting ? 'Saving…' : (isEditing ? 'Save Changes' : 'Add Project') }}
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
            <h3 class="modal-title">Delete Project</h3>
            <button class="modal-close" @click="deleteTarget = null">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <div class="modal-body">
            <p>Are you sure you want to delete <strong>{{ deleteTarget.name }}</strong>?<br/>This action cannot be undone.</p>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="deleteTarget = null">Cancel</button>
            <button class="btn-danger" :disabled="submitting" @click="handleDelete">
              {{ submitting ? 'Deleting…' : 'Delete' }}
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
import { projectsAPI } from '../api/projects'
import { clientsAPI } from '../api/clients'

const projects = ref([])
const clients = ref([])
const loading = ref(true)
const searchQuery = ref('')
const filterYear = ref('')
const currentPage = ref(1)
const perPage = 10

const modalOpen = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const submitting = ref(false)
const formError = ref('')
const deleteTarget = ref(null)

const stages = [
  'Concept Design', 'Schematic Design', 'Design Development',
  'Construction Documents', 'Bidding', 'Construction Administration', 'Completed'
]

const form = reactive({
  project_number: '',
  name: '',
  location: '',
  gmap_link: '',
  year: new Date().getFullYear(),
  current_stage: '',
  is_billed: 'unbilled',
  client_id: null,
  partner_remuneration: null,
  employee_remuneration: null,
  project_remuneration: null,
})

async function fetchAll() {
  loading.value = true
  try {
    const [pr, cl] = await Promise.all([projectsAPI.getProjects(), clientsAPI.getClients()])
    projects.value = pr.data
    clients.value = cl.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchAll)

const yearOptions = computed(() => {
  const years = [...new Set(projects.value.map(p => p.year).filter(Boolean))].sort((a, b) => b - a)
  return years
})

const filtered = computed(() => {
  let list = projects.value
  if (filterYear.value) list = list.filter(p => p.year === Number(filterYear.value))
  const q = searchQuery.value.toLowerCase()
  if (q) list = list.filter(p =>
    p.name.toLowerCase().includes(q) ||
    p.project_number.toLowerCase().includes(q) ||
    (p.location || '').toLowerCase().includes(q)
  )
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage)))
const startIdx = computed(() => (currentPage.value - 1) * perPage)
const endIdx = computed(() => Math.min(startIdx.value + perPage, filtered.value.length))
const paginated = computed(() => filtered.value.slice(startIdx.value, endIdx.value))

function resetForm() {
  form.project_number = ''
  form.name = ''
  form.location = ''
  form.gmap_link = ''
  form.year = new Date().getFullYear()
  form.current_stage = ''
  form.is_billed = 'unbilled'
  form.client_id = null
  form.partner_remuneration = null
  form.employee_remuneration = null
  form.project_remuneration = null
  formError.value = ''
}

function openAddModal() {
  resetForm()
  isEditing.value = false
  editingId.value = null
  modalOpen.value = true
}

function openEditModal(p) {
  isEditing.value = true
  editingId.value = p.id
  form.project_number = p.project_number
  form.name = p.name
  form.location = p.location || ''
  form.gmap_link = p.gmap_link || ''
  form.year = p.year || new Date().getFullYear()
  form.current_stage = p.current_stage || ''
  form.is_billed = p.is_billed || 'unbilled'
  form.client_id = p.client_id || null
  form.partner_remuneration = p.partner_remuneration ? Number(p.partner_remuneration) : null
  form.employee_remuneration = p.employee_remuneration ? Number(p.employee_remuneration) : null
  form.project_remuneration = p.project_remuneration ? Number(p.project_remuneration) : null
  formError.value = ''
  modalOpen.value = true
}

function closeModal() { modalOpen.value = false }

async function handleSubmit() {
  formError.value = ''
  submitting.value = true
  try {
    const payload = {
      project_number: form.project_number,
      name: form.name,
      location: form.location || null,
      gmap_link: form.gmap_link || null,
      year: form.year || null,
      current_stage: form.current_stage || null,
      is_billed: form.is_billed,
      client_id: form.client_id || null,
      partner_remuneration: form.partner_remuneration,
      employee_remuneration: form.employee_remuneration,
      project_remuneration: form.project_remuneration,
    }
    if (isEditing.value) {
      await projectsAPI.updateProject(editingId.value, payload)
    } else {
      await projectsAPI.createProject(payload)
    }
    closeModal()
    await fetchAll()
  } catch (err) {
    formError.value = err.response?.data?.detail || 'Operation failed. Please try again.'
  } finally {
    submitting.value = false
  }
}

function confirmDelete(p) { deleteTarget.value = p }

async function handleDelete() {
  submitting.value = true
  try {
    await projectsAPI.deleteProject(deleteTarget.value.id)
    deleteTarget.value = null
    await fetchAll()
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

function stageBadgeClass(stage) {
  if (!stage) return 'stage-na'
  if (stage === 'Completed') return 'stage-done'
  if (stage === 'Construction Administration') return 'stage-const'
  return 'stage-active'
}
</script>

<style scoped>
/* ─── Page Actions ─── */
.page-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.actions-left { display: flex; gap: 8px; align-items: center; }
.search-box { position: relative; }
.search-icon {
  position: absolute; left: 8px; top: 50%;
  transform: translateY(-50%); color: #78767d; font-size: 18px;
}
.search-input {
  padding: 8px 8px 8px 32px; background: #fff; border: 1px solid #c8c5cd;
  border-radius: 6px; font-family: 'Inter', sans-serif; font-size: 13px;
  color: #1c1b1d; width: 256px; outline: none; transition: border 0.15s;
}
.search-input:focus { border-color: #1a1a2e; box-shadow: 0 0 0 1px #1a1a2e; }
.search-input::placeholder { color: #78767d; }
.year-select {
  height: 36px; padding: 0 10px; border: 1px solid #c8c5cd; border-radius: 6px;
  font-family: 'Inter', sans-serif; font-size: 13px; color: #1c1b1d;
  background: #fff; outline: none; cursor: pointer;
}
.add-btn {
  display: flex; align-items: center; gap: 4px; padding: 8px 16px;
  background: #1a1a2e; color: #fff; border: none; border-radius: 6px;
  font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 600;
  cursor: pointer; transition: opacity 0.15s;
}
.add-btn:hover { opacity: 0.9; }
.add-btn .material-symbols-outlined { font-size: 18px; }

/* ─── Table ─── */
.table-card {
  background: #fff; border: 1px solid #c8c5cd; border-radius: 8px; overflow: hidden;
}
.proj-table { width: 100%; border-collapse: collapse; text-align: left; }
.proj-table thead { background: #f6f2f4; border-bottom: 1px solid #c8c5cd; }
.proj-table th {
  padding: 8px 16px; font-size: 11px; font-weight: 600;
  letter-spacing: 0.05em; text-transform: uppercase; color: #47464c;
}
.proj-table tbody tr { border-bottom: 1px solid #e5e1e3; transition: background 0.1s; }
.proj-table tbody tr:last-child { border-bottom: none; }
.proj-row:hover { background: #fcf8fa; }
.proj-table td { padding: 8px 16px; font-size: 13px; color: #1c1b1d; }
.proj-num {
  font-family: 'Courier New', monospace; font-size: 12px;
  background: #ebe7e9; padding: 2px 6px; border-radius: 4px;
}
.proj-name { font-weight: 600; }
.mono { font-variant-numeric: tabular-nums; }
.muted { color: #47464c; }
.text-right { text-align: right; }
.text-center { text-align: center; }
.col-actions { width: 96px; }

/* Stage badges */
.stage-badge {
  display: inline-block; padding: 3px 8px; border-radius: 4px;
  font-size: 11px; font-weight: 600; text-transform: capitalize;
}
.stage-active { background: #d5e3fd; color: #1a1a2e; }
.stage-done { background: #c8f5d0; color: #145a23; }
.stage-const { background: #f2e1b7; color: #7a4f00; }
.stage-na { background: #ebe7e9; color: #47464c; }

/* Billing badges */
.billing-badge {
  display: inline-block; padding: 3px 8px; border-radius: 4px;
  font-size: 11px; font-weight: 600; text-transform: capitalize;
}
.billed { background: #c8f5d0; color: #145a23; }
.unbilled { background: #ffdad6; color: #93000a; }

/* Row actions */
.row-actions {
  display: flex; align-items: center; justify-content: center;
  gap: 4px; opacity: 0; transition: opacity 0.15s;
}
.proj-row:hover .row-actions { opacity: 1; }
.action-btn {
  padding: 4px; border: none; background: none;
  border-radius: 4px; cursor: pointer; color: #47464c; transition: all 0.15s;
}
.action-btn .material-symbols-outlined { font-size: 18px; }
.edit-btn:hover { color: #1a1a2e; background: #f1edef; }
.delete-btn:hover { color: #ba1a1a; background: #ffdad6; }
.empty-cell { padding: 24px; text-align: center; color: #78767d; }
.loading-text { animation: pulse 1.5s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

/* Pagination */
.table-footer {
  padding: 8px 16px; border-top: 1px solid #c8c5cd; background: #f6f2f4;
  display: flex; justify-content: space-between; align-items: center;
}
.page-info { font-size: 13px; color: #47464c; }
.page-btns { display: flex; gap: 4px; }
.page-btn {
  padding: 4px 8px; border: 1px solid #c8c5cd; border-radius: 4px;
  background: #fff; font-family: 'Inter', sans-serif; font-size: 13px;
  color: #1c1b1d; cursor: pointer; transition: background 0.15s;
}
.page-btn:hover:not(:disabled) { background: #f1edef; }
.page-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ─── Modal ─── */
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
  z-index: 100; animation: fadeIn 0.15s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.modal {
  background: #fff; border-radius: 12px; width: 600px; max-width: 95vw;
  max-height: 90vh; overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15); animation: slideUp 0.2s ease;
}
.modal-wide { width: 760px; }
.modal-sm { width: 400px; }
@keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 20px 24px; border-bottom: 1px solid #e5e1e3;
}
.modal-title { font-size: 18px; font-weight: 600; color: #1c1b1d; margin: 0; }
.modal-close {
  background: none; border: none; color: #47464c; cursor: pointer;
  padding: 4px; border-radius: 4px;
}
.modal-close:hover { background: #f1edef; }
.modal-body { padding: 24px; }
.modal-body p { font-size: 14px; line-height: 22px; color: #47464c; margin: 0; }

/* Form grid */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-field { display: flex; flex-direction: column; gap: 6px; }
.span-2 { grid-column: span 2; }
.form-field label { font-size: 13px; font-weight: 600; color: #47464c; }
.form-field input,
.form-field select {
  height: 40px; padding: 0 12px; border: 1px solid #c8c5cd;
  border-radius: 6px; font-family: 'Inter', sans-serif; font-size: 14px;
  color: #1c1b1d; outline: none; transition: border 0.15s; background: #fff;
}
.form-field input:focus,
.form-field select:focus { border-color: #1a1a2e; box-shadow: 0 0 0 1px #1a1a2e; }
.form-field input::placeholder { color: #78767d; }
.form-field input:disabled { background: #f6f2f4; color: #78767d; cursor: not-allowed; }

.form-error {
  display: flex; align-items: center; gap: 8px; padding: 12px;
  background: #ffdad6; border-radius: 8px; color: #93000a;
  font-size: 14px; margin-top: 16px;
}
.form-error .material-symbols-outlined { font-size: 18px; flex-shrink: 0; }

.modal-footer {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 20px 24px; border-top: 1px solid #e5e1e3;
}
form .modal-footer { margin-top: 24px; padding: 0; border-top: none; }

.btn-cancel {
  padding: 8px 16px; border: 1px solid #c8c5cd; border-radius: 6px;
  background: #fff; font-family: 'Inter', sans-serif; font-size: 14px;
  color: #1c1b1d; cursor: pointer;
}
.btn-cancel:hover { background: #f1edef; }
.btn-submit {
  padding: 8px 20px; border: none; border-radius: 6px;
  background: #1a1a2e; color: #fff; font-family: 'Inter', sans-serif;
  font-size: 14px; font-weight: 600; cursor: pointer; transition: opacity 0.15s;
}
.btn-submit:hover:not(:disabled) { opacity: 0.9; }
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger {
  padding: 8px 20px; border: none; border-radius: 6px;
  background: #ba1a1a; color: #fff; font-family: 'Inter', sans-serif;
  font-size: 14px; font-weight: 600; cursor: pointer; transition: opacity 0.15s;
}
.btn-danger:hover:not(:disabled) { opacity: 0.9; }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }

.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}
</style>
