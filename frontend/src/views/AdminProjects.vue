<template>
  <component :is="layout">
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
            <th v-if="isAdmin" class="text-right">Remuneration (₹)</th>
            <th class="text-center col-actions">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td :colspan="isAdmin ? 8 : 7" class="empty-cell"><div class="loading-text">Loading projects…</div></td>
          </tr>
          <tr v-else-if="paginated.length === 0">
            <td :colspan="isAdmin ? 8 : 7" class="empty-cell">No projects found.</td>
          </tr>
          <tr v-for="p in paginated" :key="p.id" class="proj-row" @click="openDetailModal(p)">
            <td class="mono"><span class="proj-num">{{ p.project_number }}</span></td>
            <td>
              <span class="proj-name">
                <span class="color-dot" :style="{ background: p.color || '#287475' }"></span>
                {{ p.name }}
              </span>
            </td>
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
            <td v-if="isAdmin" class="text-right mono">{{ formatAmount(p.project_remuneration) }}</td>
            <td @click.stop>
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
                <input v-model="form.project_number" type="text" required placeholder="e.g. MH - 001" />
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
              <!-- Project Color -->
              <div class="form-field">
                <label>Project Color</label>
                <div class="color-picker-row">
                  <span class="color-preview" :style="{ background: form.color }"></span>
                  <input v-model="form.color" type="color" class="color-input" />
                </div>
              </div>
              <!-- Partner Remuneration -->
              <div class="form-field" v-if="isAdmin">
                <label>Partner Remuneration (₹)</label>
                <CurrencyInput v-model="form.partner_remuneration" placeholder="0" />
              </div>
              <!-- Employee Remuneration -->
              <div class="form-field" v-if="isAdmin">
                <label>Employee Remuneration (₹)</label>
                <CurrencyInput v-model="form.employee_remuneration" placeholder="0" />
              </div>
              <!-- Project Remuneration -->
              <div class="form-field span-2" v-if="isAdmin">
                <label>Total Project Remuneration (₹)</label>
                <CurrencyInput v-model="form.project_remuneration" placeholder="0" />
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

    <!-- Project Detail Modal -->
    <Teleport to="body">
      <div v-if="detailModalOpen" class="modal-backdrop" @click.self="closeDetailModal">
        <div class="modal modal-xl">
          <div class="modal-header">
            <h3 class="modal-title">{{ detailProject?.name }}</h3>
            <button class="modal-close" @click="closeDetailModal">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>

          <div class="modal-body">
            <div class="detail-grid">
              <!-- Project Info -->
              <div class="detail-section">
                <h4 class="section-title">Project Information</h4>
                <div class="info-grid">
                  <div class="info-item">
                    <label>Project Number</label>
                    <span>{{ detailProject?.project_number }}</span>
                  </div>
                  <div class="info-item">
                    <label>Name</label>
                    <span>{{ detailProject?.name }}</span>
                  </div>
                  <div class="info-item">
                    <label>Location</label>
                    <span>{{ detailProject?.location || '—' }}</span>
                  </div>
                  <div class="info-item">
                    <label>Google Maps</label>
                    <span v-if="detailProject?.gmap_link">
                      <a :href="detailProject.gmap_link" target="_blank">View Map</a>
                    </span>
                    <span v-else>—</span>
                  </div>
                  <div class="info-item">
                    <label>Year</label>
                    <span>{{ detailProject?.year || '—' }}</span>
                  </div>
                  <div class="info-item">
                    <label>Stage</label>
                    <span>{{ detailProject?.current_stage || '—' }}</span>
                  </div>
                  <div class="info-item">
                    <label>Billing Status</label>
                    <span>{{ detailProject?.is_billed }}</span>
                  </div>
                  <div class="info-item">
                    <label>Client</label>
                    <span>{{ getClientName(detailProject?.client_id) }}</span>
                  </div>
                  <template v-if="isAdmin">
                    <div class="info-item">
                      <label>Partner Remuneration</label>
                      <span>{{ formatAmount(detailProject?.partner_remuneration) }}</span>
                    </div>
                    <div class="info-item">
                      <label>Employee Remuneration</label>
                      <span>{{ formatAmount(detailProject?.employee_remuneration) }}</span>
                    </div>
                    <div class="info-item">
                      <label>Total Remuneration</label>
                      <span>{{ formatAmount(detailProject?.project_remuneration) }}</span>
                    </div>
                  </template>
                </div>
              </div>

              <!-- Assigned Employees -->
              <div class="detail-section">
                <h4 class="section-title">Assigned Employees</h4>
                <div v-if="detailProject?.assignments?.length" class="assignments-list">
                  <div v-for="a in detailProject.assignments" :key="a.id" class="assignment-item">
                    {{ a.user?.name }} ({{ a.user?.designation }})
                  </div>
                </div>
                <div v-else class="empty-state">No employees assigned yet.</div>

                <!-- Assign Employee -->
                <div class="assign-form">
                  <select v-model="assignUserId">
                    <option :value="null">— Select Employee —</option>
                    <option v-for="u in users" :key="u.id" :value="u.id">{{ u.name }} ({{ u.designation }})</option>
                  </select>
                  <button class="btn-assign" :disabled="!assignUserId || assignSubmitting" @click="assignUser">
                    {{ assignSubmitting ? 'Assigning…' : 'Assign' }}
                  </button>
                </div>
              </div>

              <!-- Work Orders -->
              <div class="detail-section">
                <h4 class="section-title">Work Orders</h4>
                <div v-if="detailProject?.work_order_urls" class="workorders-list">
                  <div v-for="url in detailProject.work_order_urls.split(';')" :key="url" class="workorder-item">
                    <a :href="url" target="_blank">View Work Order</a>
                  </div>
                </div>
                <div v-else class="empty-state">No work orders uploaded yet.</div>

                <!-- Upload Work Order -->
                <div class="upload-form">
                  <input type="file" ref="uploadInput" @change="uploadFile = $event.target.files[0]" accept=".pdf,.jpg,.jpeg,.png" />
                  <button class="btn-upload" :disabled="!uploadFile || uploadSubmitting" @click="uploadWorkorder">
                    {{ uploadSubmitting ? 'Uploading…' : 'Upload' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </component>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import EmployeeLayout from '../components/EmployeeLayout.vue'
import { useAuthStore } from '../stores/auth'
import { projectsAPI } from '../api/projects'
import { clientsAPI } from '../api/clients'
import { usersAPI } from '../api/users'

const authStore = useAuthStore()

const layout = computed(() => {
  return authStore.role === 'admin' ? AppLayout : EmployeeLayout
})

const isAdmin = computed(() => authStore.role === 'admin')

const projects = ref([])
const clients = ref([])
const users = ref([])
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

const detailModalOpen = ref(false)
const detailProject = ref(null)
const assignUserId = ref(null)
const assignSubmitting = ref(false)
const uploadFile = ref(null)
const uploadSubmitting = ref(false)
const uploadInput = ref(null)

const stages = [
  'In Progress', 'Incomplete Beyond Deadline', 'Halted', 'Completed'
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
  color: '#287475',
})

async function fetchAll() {
  loading.value = true
  try {
    const [pr, cl, us] = await Promise.all([projectsAPI.getProjects(), clientsAPI.getClients(), usersAPI.getUsers()])
    projects.value = pr.data
    clients.value = cl.data
    users.value = us.data
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
  form.color = '#287475'
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
  form.color = p.color || '#287475'
  formError.value = ''
  modalOpen.value = true
}

function closeModal() { modalOpen.value = false }

async function openDetailModal(p) {
  try {
    const res = await projectsAPI.getProject(p.id)
    detailProject.value = res.data
    detailModalOpen.value = true
  } catch (e) {
    console.error(e)
  }
}

function closeDetailModal() { detailModalOpen.value = false }

async function assignUser() {
  if (!assignUserId.value) return
  assignSubmitting.value = true
  try {
    await projectsAPI.assignUser(detailProject.value.id, assignUserId.value)
    assignUserId.value = null
    // Refresh detail
    const res = await projectsAPI.getProject(detailProject.value.id)
    detailProject.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    assignSubmitting.value = false
  }
}

async function uploadWorkorder() {
  if (!uploadFile.value) return
  uploadSubmitting.value = true
  try {
    const formData = new FormData()
    formData.append('file', uploadFile.value)
    // Use client directly for upload
    const client = (await import('../api/client')).default
    await client.post(`/uploads/project/${detailProject.value.id}/workorder`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    uploadFile.value = null
    uploadInput.value.value = ''
    // Refresh detail
    const res = await projectsAPI.getProject(detailProject.value.id)
    detailProject.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    uploadSubmitting.value = false
  }
}

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
      color: form.color,
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
  if (stage === 'Incomplete Beyond Deadline' || stage === 'Halted') return 'stage-const'
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
  transform: translateY(-50%); color: var(--color-on-surface-variant); font-size: 18px;
}
.search-input {
  padding: 8px 8px 8px 32px; background: #fff; border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg); font-family: var(--font-display); font-size: 13px;
  color: var(--color-on-surface); width: 256px; outline: none; transition: border 0.15s;
}
.search-input:focus { border-color: var(--color-primary); box-shadow: 0 0 0 1px var(--color-primary); }
.search-input::placeholder { color: var(--color-on-surface-variant); }
.year-select {
  height: 36px; padding: 0 10px; border: 1px solid var(--color-outline); border-radius: var(--radius-lg);
  font-family: var(--font-display); font-size: 13px; color: var(--color-on-surface);
  background: #fff; outline: none; cursor: pointer;
}
.add-btn {
  display: flex; align-items: center; gap: 4px; padding: 8px 16px;
  background: var(--color-primary); color: #fff; border: none; border-radius: var(--radius-lg);
  font-family: var(--font-display); font-size: 14px; font-weight: 600;
  cursor: pointer; transition: opacity 0.15s;
}
.add-btn:hover { opacity: 0.9; }
.add-btn .material-symbols-outlined { font-size: 18px; }

/* ─── Table ─── */
.table-card {
  background: #fff; border: 1px solid var(--color-outline); border-radius: var(--radius-lg); overflow: hidden;
}
.proj-table { width: 100%; border-collapse: collapse; text-align: left; }
.proj-table thead { background: var(--color-surface-container); border-bottom: 1px solid var(--color-outline); }
.proj-table th {
  padding: 8px 16px; font-size: 11px; font-weight: 600;
  letter-spacing: 0.05em; text-transform: uppercase; color: var(--color-on-surface-variant);
}
.proj-table tbody tr { border-bottom: 1px solid #e5e1e3; transition: background 0.1s; }
.proj-table tbody tr:last-child { border-bottom: none; }
.proj-row:hover { background: var(--color-background); }
.proj-table td { padding: 8px 16px; font-size: 13px; color: var(--color-on-surface); }
.proj-num {
  font-family: 'Courier New', monospace; font-size: 12px;
  background: var(--color-surface-container-high); padding: 2px 6px; border-radius: var(--radius);
}
.proj-name { font-weight: 600; }
.mono { font-variant-numeric: tabular-nums; }
.muted { color: var(--color-on-surface-variant); }
.text-right { text-align: right; }
.text-center { text-align: center; }
.col-actions { width: 96px; }

/* Stage badges */
.stage-badge {
  display: inline-block; padding: 3px 8px; border-radius: var(--radius);
  font-size: 11px; font-weight: 600; text-transform: capitalize;
}
.stage-active { background: #d5e3fd; color: var(--color-primary); }
.stage-done { background: #c8f5d0; color: #145a23; }
.stage-const { background: #f2e1b7; color: #7a4f00; }
.stage-na { background: var(--color-surface-container-high); color: var(--color-on-surface-variant); }

/* Billing badges */
.billing-badge {
  display: inline-block; padding: 3px 8px; border-radius: var(--radius);
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
  border-radius: var(--radius); cursor: pointer; color: var(--color-on-surface-variant); transition: all 0.15s;
}
.action-btn .material-symbols-outlined { font-size: 18px; }
.edit-btn:hover { color: var(--color-primary); background: var(--color-surface-container); }
.delete-btn:hover { color: #ba1a1a; background: #ffdad6; }
.empty-cell { padding: 24px; text-align: center; color: var(--color-on-surface-variant); }
.loading-text { animation: pulse 1.5s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

/* Pagination */
.table-footer {
  padding: 8px 16px; border-top: 1px solid var(--color-outline); background: var(--color-surface-container);
  display: flex; justify-content: space-between; align-items: center;
}
.page-info { font-size: 13px; color: var(--color-on-surface-variant); }
.page-btns { display: flex; gap: 4px; }
.page-btn {
  padding: 4px 8px; border: 1px solid var(--color-outline); border-radius: var(--radius);
  background: #fff; font-family: var(--font-display); font-size: 13px;
  color: var(--color-on-surface); cursor: pointer; transition: background 0.15s;
}
.page-btn:hover:not(:disabled) { background: var(--color-surface-container); }
.page-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ─── Modal ─── */
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
  z-index: 100; animation: fadeIn 0.15s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.modal {
  background: #fff; border-radius: var(--radius-lg); width: 600px; max-width: 95vw;
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
.modal-title { font-size: 18px; font-weight: 600; color: var(--color-on-surface); margin: 0; }
.modal-close {
  background: none; border: none; color: var(--color-on-surface-variant); cursor: pointer;
  padding: 4px; border-radius: var(--radius);
}
.modal-close:hover { background: var(--color-surface-container); }
.modal-body { padding: 24px; }
.modal-body p { font-size: 14px; line-height: 22px; color: var(--color-on-surface-variant); margin: 0; }

/* Form grid */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-field { display: flex; flex-direction: column; gap: 6px; }
.span-2 { grid-column: span 2; }
.form-field label { font-size: 13px; font-weight: 600; color: var(--color-on-surface-variant); }
.form-field input,
.form-field select {
  height: 40px; padding: 0 12px; border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg); font-family: var(--font-display); font-size: 14px;
  color: var(--color-on-surface); outline: none; transition: border 0.15s; background: #fff;
}
.form-field input:focus,
.form-field select:focus { border-color: var(--color-primary); box-shadow: 0 0 0 1px var(--color-primary); }
.form-field input::placeholder { color: var(--color-on-surface-variant); }
.form-field input:disabled { background: var(--color-surface-container); color: var(--color-on-surface-variant); cursor: not-allowed; }

.form-error {
  display: flex; align-items: center; gap: 8px; padding: 12px;
  background: #ffdad6; border-radius: var(--radius-lg); color: #93000a;
  font-size: 14px; margin-top: 16px;
}
.form-error .material-symbols-outlined { font-size: 18px; flex-shrink: 0; }

.modal-footer {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 20px 24px; border-top: 1px solid #e5e1e3;
}
form .modal-footer { margin-top: 24px; padding: 0; border-top: none; }

.btn-cancel {
  padding: 8px 16px; border: 1px solid var(--color-outline); border-radius: var(--radius-lg);
  background: #fff; font-family: var(--font-display); font-size: 14px;
  color: var(--color-on-surface); cursor: pointer;
}
.btn-cancel:hover { background: var(--color-surface-container); }
.btn-submit {
  padding: 8px 20px; border: none; border-radius: var(--radius-lg);
  background: var(--color-primary); color: #fff; font-family: var(--font-display);
  font-size: 14px; font-weight: 600; cursor: pointer; transition: opacity 0.15s;
}
.btn-submit:hover:not(:disabled) { opacity: 0.9; }
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger {
  padding: 8px 20px; border: none; border-radius: var(--radius-lg);
  background: #ba1a1a; color: #fff; font-family: var(--font-display);
  font-size: 14px; font-weight: 600; cursor: pointer; transition: opacity 0.15s;
}
.btn-danger:hover:not(:disabled) { opacity: 0.9; }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }

.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

/* ─── Detail Modal ─── */
.modal-xl { max-width: 1200px; }
.detail-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 32px;
}
.detail-section { margin-bottom: 32px; }
.section-title {
  font-family: var(--font-display); font-size: 16px; font-weight: 600;
  color: var(--color-on-surface); margin-bottom: 16px;
}
.info-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
}
.info-item {
  display: flex; flex-direction: column; gap: 4px;
}
.info-item label {
  font-family: var(--font-display); font-size: 12px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-on-surface-variant);
}
.info-item span {
  font-family: var(--font-display); font-size: 14px; color: var(--color-on-surface);
}
.assignments-list {
  margin-bottom: 16px;
}
.assignment-item {
  padding: 8px 12px; background: var(--color-background); border-radius: var(--radius);
  font-family: var(--font-display); font-size: 13px; color: var(--color-on-surface);
  margin-bottom: 8px;
}
.assign-form {
  display: flex; gap: 12px; align-items: center;
}
.assign-form select {
  flex: 1; padding: 8px 12px; border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius); font-family: var(--font-display); font-size: 13px;
}
.btn-assign {
  padding: 8px 16px; background: var(--color-primary); color: #fff; border: none;
  border-radius: var(--radius); font-family: var(--font-display); font-size: 13px;
  cursor: pointer; transition: background 0.15s;
}
.btn-assign:hover:not(:disabled) { background: #2a2a3e; }
.btn-assign:disabled { opacity: 0.5; cursor: not-allowed; }
.workorders-list {
  margin-bottom: 16px;
}
.workorder-item {
  padding: 8px 12px; background: var(--color-background); border-radius: var(--radius);
  margin-bottom: 8px;
}
.workorder-item a {
  font-family: var(--font-display); font-size: 13px; color: var(--color-primary);
  text-decoration: none;
}
.workorder-item a:hover { text-decoration: underline; }
.upload-form {
  display: flex; gap: 12px; align-items: center;
}
.upload-form input {
  flex: 1; padding: 8px 12px; border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius); font-family: var(--font-display); font-size: 13px;
}
.btn-upload {
  padding: 8px 16px; background: var(--color-primary); color: #fff; border: none;
  border-radius: var(--radius); font-family: var(--font-display); font-size: 13px;
  cursor: pointer; transition: background 0.15s;
}
.btn-upload:hover:not(:disabled) { background: #0a7a6a; }
.btn-upload:disabled { opacity: 0.5; cursor: not-allowed; }
.empty-state {
  padding: 16px; text-align: center; color: var(--color-on-surface-variant);
  font-family: var(--font-display); font-size: 13px;
}

/* Color dot in table */
.color-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 6px;
  vertical-align: middle;
}

/* Color picker in form */
.color-picker-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.color-preview {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2px solid var(--color-outline-variant);
  flex-shrink: 0;
}
.color-input {
  width: 48px;
  height: 36px;
  padding: 0;
  border: 1px solid var(--color-outline-variant);
  border-radius: 4px;
  cursor: pointer;
  background: none;
}
</style>
