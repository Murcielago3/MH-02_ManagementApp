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
        <select v-model="filterClient" class="year-select">
          <option value="">All Clients</option>
          <option v-for="c in clients" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </div>
      <button class="add-btn" @click="openAddModal">
        <span class="material-symbols-outlined">add</span>
        Add New Project
      </button>
    </div>

    <!-- Card Grid -->
    <div class="cards-grid">
      <div v-if="loading" class="cards-empty">
        <div class="loading-text">Loading projects…</div>
      </div>
      <div v-else-if="filtered.length === 0" class="cards-empty">
        No projects found.
      </div>
      <div v-else class="cards-wrap">
        <article
          v-for="p in filtered"
          :key="p.id"
          class="project-card"
          @click="goToSummary(p)"
        >
          <div class="project-card-top">
            <div class="name-cell">
              <span class="color-dot" :style="{ background: p.color || '#B5EAD7' }"></span>
              <div>
                <div class="proj-name">{{ p.name }}</div>
                <div class="proj-sub mono">{{ p.project_number }} <span v-if="p.year">· {{ p.year }}</span></div>
              </div>
            </div>
            <span class="stage-badge" :class="stageBadgeClass(p.current_stage)">
              {{ p.current_stage || 'N/A' }}
            </span>
          </div>

          <div class="proj-meta-row">
            <span class="muted">{{ getClientName(p.client_id) }}</span>
          </div>

          <div class="project-card-body">
            <div class="stat-row">
              <span class="stat-label">Total Project Cost</span>
              <span class="stat-val">₹{{ formatAmount(p.project_remuneration) }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">Billed</span>
              <span class="stat-val billed-val">₹{{ formatAmount(getFinancials(p.id).billed) }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">Employee Rem.</span>
              <span class="stat-val">₹{{ formatAmount(getFinancials(p.id).employeeRem) }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">Partner Rem.</span>
              <span class="stat-val">₹{{ formatAmount(getFinancials(p.id).partnerRem) }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">Reserve Balance</span>
              <span class="stat-val" :class="reserveClass(getFinancials(p.id).reserveBalance)">
                ₹{{ formatAmount(getFinancials(p.id).reserveBalance) }}
              </span>
            </div>
          </div>

          <div class="card-actions">
            <button type="button" class="btn-text btn-text-primary" @click.stop="openAssignModal(p)">Assign</button>
            <button type="button" class="btn-text" @click.stop="openEditModal(p)">Edit</button>
            <button type="button" class="btn-text btn-text-danger" @click.stop="confirmDelete(p)">Delete</button>
          </div>
        </article>
      </div>
    </div>

    <div class="table-footer">
      <span class="page-info">
        {{ filtered.length }} {{ filtered.length === 1 ? 'project' : 'projects' }}
      </span>
    </div>

    <!-- Add/Edit Modal -->
    <Teleport to="body">
      <div v-if="modalOpen" class="modal-backdrop">
        <div class="modal modal-wide">
          <div class="modal-header">
            <h3 class="modal-title">{{ isEditing ? 'Edit Project' : 'Add New Project' }}</h3>
            <button class="modal-close" @click="closeModal">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>

          <form @submit.prevent="handleSubmit" class="modal-body">
            <!-- Draft restore banner -->
            <div v-if="showDraftBanner" class="draft-banner">
              <span class="material-symbols-outlined">history</span>
              <span>You have an unsaved draft from a previous session.</span>
              <button type="button" class="draft-restore-btn" @click="restoreProjectDraft">Restore</button>
              <button type="button" class="draft-discard-btn" @click="discardProjectDraft">Discard</button>
            </div>

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
              <!-- Display Name (invoice) -->
              <div class="form-field">
                <label style="display:flex; align-items:center; justify-content:space-between;">
                  <span>Invoice Display Name</span>
                  <label style="display:inline-flex; align-items:center; gap:4px; text-transform:none; letter-spacing:0; font-weight:600; font-size:11px; cursor:pointer;">
                    <input type="checkbox" v-model="sameAsProjectName" style="width:auto; margin:0;" />
                    Same as project name
                  </label>
                </label>
                <input
                  v-model="form.display_name"
                  type="text"
                  :disabled="sameAsProjectName"
                  :placeholder="form.name || 'Name shown on invoices'"
                />
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
              <div class="form-field span-2">
                <label>Project Color / Brand</label>
                <div class="modern-color-picker">
                  <div class="presets-grid">
                    <button
                      v-for="c in projectPresets"
                      :key="c"
                      type="button"
                      class="color-preset-btn"
                      :class="{ active: form.color === c }"
                      :style="{ background: c }"
                      @click="form.color = c"
                    ></button>
                  </div>
                </div>
              </div>

              <!-- Total Assigned Hours -->
              <div class="form-field span-2">
                <label>Total Assigned Hours</label>
                <input v-model.number="form.total_assigned_hours" type="number" step="0.5" placeholder="e.g. 500" />
              </div>

              <!-- Remuneration Fields -->
              <div class="form-field">
                <label>Total Project Cost (₹)</label>
                <CurrencyInput v-model="form.project_remuneration" placeholder="₹ 0.00" />
              </div>
              <div class="form-field">
                <label>Employee Remuneration (₹)</label>
                <CurrencyInput v-model="form.employee_remuneration" placeholder="₹ 0.00" />
              </div>
              <div class="form-field span-2">
                <label>Partner Remuneration (₹)</label>
                <CurrencyInput v-model="form.partner_remuneration" placeholder="₹ 0.00" />
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
      <div v-if="deleteTarget" class="modal-backdrop">
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

    <!-- Assign Project Modal -->
    <AssignProjectModal
      v-if="assignTarget"
      :project="assignTarget"
      :users="users"
      @close="assignTarget = null"
      @assigned="onAssigned"
    />

    <ToastNotification
      v-if="toastMsg"
      :message="toastMsg"
      :type="toastType"
      @done="toastMsg = ''"
    />
  </component>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import EmployeeLayout from '../components/EmployeeLayout.vue'
import CurrencyInput from '../components/CurrencyInput.vue'
import ToastNotification from '../components/ToastNotification.vue'
import AssignProjectModal from '../components/AssignProjectModal.vue'
import { useAuthStore } from '../stores/auth'
import { projectsAPI } from '../api/projects'
import { clientsAPI } from '../api/clients'
import { usersAPI } from '../api/users'
import { weeklyTimesheetsAPI } from '../api/weekly_timesheets'
import { useDraftStorage } from '../composables/useDraftStorage'
import { previewHourlyFromBasePay } from '../utils/currency'

const route = useRoute()
const router = useRouter()


const authStore = useAuthStore()
const { draft: projectDraft, saveDraft: saveProjectDraft, clearDraft: clearProjectDraft, hasDraft: hasProjectDraft, load: loadProjectDraft } = useDraftStorage('project_create')

const layout = computed(() => {
  return authStore.role === 'admin' ? AppLayout : EmployeeLayout
})

const isAdmin = computed(() => authStore.role === 'admin')

const projects = ref([])
const clients = ref([])
const users = ref([])
const reserveMap = ref({})
const approvedTimesheets = ref([])
const loading = ref(true)
const searchQuery = ref('')
const filterYear = ref('')
const filterClient = ref('')

const modalOpen = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const submitting = ref(false)
const formError = ref('')
const deleteTarget = ref(null)
const assignTarget = ref(null)


const toastMsg = ref('')
const toastType = ref('success')

function toast(msg, type = 'success') {
  toastType.value = type
  toastMsg.value = msg
}



const stages = [
  'In Progress', 'Incomplete Beyond Deadline', 'Halted', 'Completed'
]

const form = reactive({
  project_number: '',
  name: '',
  display_name: '',
  location: '',
  gmap_link: '',
  year: new Date().getFullYear(),
  current_stage: '',
  is_billed: 'unbilled',
  client_id: null,
  total_assigned_hours: null,
  project_remuneration: null,
  employee_remuneration: null,
  partner_remuneration: null,
  color: '#60A5FA',
})

// Project color palette — medium-saturation, clearly visible on calendar
const projectPresets = [
  '#F87171', // red
  '#FB923C', // orange
  '#FBBF24', // amber
  '#FDE047', // yellow
  '#A3E635', // lime
  '#4ADE80', // green
  '#34D399', // emerald
  '#2DD4BF', // teal
  '#22D3EE', // cyan
  '#38BDF8', // sky blue
  '#60A5FA', // blue
  '#818CF8', // indigo
  '#A78BFA', // violet
  '#C084FC', // purple
  '#E879F9', // fuchsia
  '#F472B6', // pink
  '#94A3B8', // slate
  '#86EFAC', // light green
  '#7DD3FC', // light blue
  '#FCA5A5', // light red/coral
]

const showDraftBanner = ref(false)
const sameAsProjectName = ref(true)
watch(sameAsProjectName, (same) => { if (same) form.display_name = '' })
watch(() => form.name, () => { if (sameAsProjectName.value) form.display_name = '' })

// Auto-save draft when form changes (only during add, not edit)
watch(() => ({ ...form }), (val) => {
  if (modalOpen.value && !isEditing.value) {
    saveProjectDraft({ ...val })
  }
}, { deep: true })

function restoreProjectDraft() {
  if (!projectDraft.value) return
  const d = projectDraft.value
  Object.keys(form).forEach(k => {
    if (d[k] !== undefined) form[k] = d[k]
  })
  showDraftBanner.value = false
}

function discardProjectDraft() {
  clearProjectDraft()
  showDraftBanner.value = false
}

async function fetchAll() {
  loading.value = true
  try {
    const results = await Promise.allSettled([
      projectsAPI.getProjects(),
      clientsAPI.getClients(),
      usersAPI.getUsers(),
      projectsAPI.getReserveStatus(),
      weeklyTimesheetsAPI.getTimesheets({ status: 'approved' }),
    ])

    if (results[0].status === 'fulfilled') projects.value = results[0].value.data
    else console.error('Projects fetch failed', results[0].reason)

    if (results[1].status === 'fulfilled') clients.value = results[1].value.data
    else console.error('Clients fetch failed', results[1].reason)

    if (results[2].status === 'fulfilled') users.value = results[2].value.data
    else console.error('Users fetch failed', results[2].reason)

    if (results[3].status === 'fulfilled') {
      const map = {}
      for (const r of results[3].value.data) map[r.project_id] = r
      reserveMap.value = map
    } else {
      console.error('Reserve status fetch failed', results[3].reason)
    }

    if (results[4].status === 'fulfilled') {
      approvedTimesheets.value = await ensureTimesheetEntries(results[4].value.data || [])
    } else {
      console.error('Timesheets fetch failed', results[4].reason)
    }

  } catch (e) {
    console.error('FetchAll failed', e)
  } finally {
    loading.value = false
  }
}

// Some timesheets come back from the list endpoint without their `entries`
// populated — fetch the missing ones individually (same pattern used on the
// project summary page), capped so a huge backlog can't blow up requests.
async function ensureTimesheetEntries(timesheets) {
  const list = [...(timesheets || [])]
  const missing = list.filter((t) => !t.entries || t.entries.length === 0)
  const slice = missing.slice(0, 80)
  if (!slice.length) return list
  const detailed = await Promise.all(
    slice.map((t) => weeklyTimesheetsAPI.getTimesheet(t.id).then((r) => r.data).catch(() => t))
  )
  const byId = new Map(detailed.map((d) => [d.id, d]))
  return list.map((t) => byId.get(t.id) || t)
}

// Per-project: total hours worked by each employee, from approved timesheets.
// Map<projectId, Map<employeeId, hours>>
const hoursByProjectAndEmployee = computed(() => {
  const out = new Map()
  for (const ts of approvedTimesheets.value || []) {
    if (ts.status !== 'approved') continue
    const uid = ts.employee_id ?? ts.user_id
    if (!uid) continue
    for (const e of ts.entries || []) {
      const pid = Number(e.project_id)
      const h = Number(e.hours) || 0
      if (!pid || h <= 0) continue
      if (!out.has(pid)) out.set(pid, new Map())
      const empMap = out.get(pid)
      empMap.set(uid, (empMap.get(uid) || 0) + h)
    }
  }
  return out
})

// Billed / unbilled / employee & partner remuneration per project. Employee
// and partner remuneration are ALWAYS calculated live from approved
// timesheet hours — total hours × each employee's hourly pay, and total
// hours × the project's partner hourly rate — never the static budgeted
// fields on the project record.
function getFinancials(projectId) {
  const r = reserveMap.value[projectId]
  const billed = r ? Number(r.total_invoiced) || 0 : 0
  const reserveBalance = r ? Number(r.reserve_balance) || 0 : 0
  const p = projects.value.find(proj => proj.id === projectId)
  const totalCost = Number(p?.project_remuneration) || 0
  const unbilled = totalCost - billed

  const empHours = hoursByProjectAndEmployee.value.get(projectId) || new Map()
  let employeeRem = 0
  let totalHours = 0
  for (const [uid, hours] of empHours) {
    totalHours += hours
    const u = users.value.find((x) => x.id === uid)
    const hourly = previewHourlyFromBasePay(u?.salary_month) || 0
    employeeRem += hourly * hours
  }
  const partnerHourly = Number(p?.partner_hourly_rate) || 0
  const partnerRem = partnerHourly * totalHours

  return { billed, unbilled, reserveBalance, employeeRem, partnerRem }
}

function reserveClass(val) {
  if (val < 0) return 'unbilled-val'
  if (val > 0) return 'billed-val'
  return ''
}

onMounted(async () => {
  await fetchAll()
  const editId = route.query.edit
  if (editId) {
    const p = projects.value.find(proj => proj.id === Number(editId))
    if (p) openEditModal(p)
    router.replace({ query: {} })
  }
})

const yearOptions = computed(() => {
  const years = [...new Set(projects.value.map(p => p.year).filter(Boolean))].sort((a, b) => b - a)
  return years
})

const filtered = computed(() => {
  let list = [...projects.value]
  // Sort alphabetically by project name (case-insensitive)
  list.sort((a, b) => (a.name || '').localeCompare(b.name || '', undefined, { sensitivity: 'base' }))
  
  if (filterYear.value) list = list.filter(p => p.year === Number(filterYear.value))
  if (filterClient.value) list = list.filter(p => p.client_id === Number(filterClient.value))
  const q = searchQuery.value.toLowerCase()
  if (q) list = list.filter(p =>
    p.name.toLowerCase().includes(q) ||
    p.project_number.toLowerCase().includes(q) ||
    (p.location || '').toLowerCase().includes(q)
  )
  return list
})


function resetForm() {
  form.project_number = ''
  form.name = ''
  form.display_name = ''
  sameAsProjectName.value = true
  form.location = ''
  form.gmap_link = ''
  form.year = new Date().getFullYear()
  form.current_stage = ''
  form.is_billed = 'unbilled'
  form.client_id = null
  form.total_assigned_hours = null
  form.project_remuneration = null
  form.employee_remuneration = null
  form.partner_remuneration = null
  form.color = '#B5EAD7'
  formError.value = ''
}

async function openAddModal() {
  resetForm()
  isEditing.value = false
  editingId.value = null
  modalOpen.value = true

  try {
    const res = await projectsAPI.getNextNumber()
    if (res.data?.next_number) {
      form.project_number = res.data.next_number
    }
  } catch (e) {
    console.error('Failed to fetch next project number', e)
  }

  // Show draft banner if a saved draft exists (latest for this account).
  await loadProjectDraft()
  if (hasProjectDraft.value) {
    showDraftBanner.value = true
  }
}

function openEditModal(p) {
  isEditing.value = true
  editingId.value = p.id
  form.project_number = p.project_number
  form.name = p.name
  form.display_name = p.display_name || ''
  sameAsProjectName.value = !p.display_name
  form.location = p.location || ''
  form.gmap_link = p.gmap_link || ''
  form.year = p.year || new Date().getFullYear()
  form.current_stage = p.current_stage || ''
  form.is_billed = p.is_billed || 'unbilled'
  form.client_id = p.client_id || null
  form.total_assigned_hours = p.total_assigned_hours ? Number(p.total_assigned_hours) : null
  form.project_remuneration = p.project_remuneration ? Number(p.project_remuneration) : null
  form.employee_remuneration = p.employee_remuneration ? Number(p.employee_remuneration) : null
  form.partner_remuneration = p.partner_remuneration ? Number(p.partner_remuneration) : null
  form.color = p.color || '#B5EAD7'
  formError.value = ''
  modalOpen.value = true
}

function closeModal() { modalOpen.value = false }

function goToSummary(p) {
  router.push(`/admin/projects/summary/${p.id}`)
}

function openAssignModal(p) {
  assignTarget.value = p
}

function onAssigned({ count }) {
  assignTarget.value = null
  toast(`Project assigned to ${count} ${count === 1 ? 'employee' : 'employees'}.`)
}


async function handleSubmit() {
  formError.value = ''
  submitting.value = true
  try {
    const payload = {
      project_number: form.project_number,
      name: form.name,
      display_name: sameAsProjectName.value ? null : (form.display_name || null),
      location: form.location || null,
      gmap_link: form.gmap_link || null,
      year: form.year || null,
      current_stage: form.current_stage || null,
      is_billed: form.is_billed,
      client_id: form.client_id || null,
      total_assigned_hours: form.total_assigned_hours,
      project_remuneration: form.project_remuneration,
      employee_remuneration: form.employee_remuneration,
      partner_remuneration: form.partner_remuneration,
      color: form.color,
    }
    if (isEditing.value) {
      await projectsAPI.updateProject(editingId.value, payload)
    } else {
      await projectsAPI.createProject(payload)
    }
    if (!isEditing.value) clearProjectDraft()
    closeModal()
    toast(isEditing.value ? 'Project updated.' : 'Project created.')
    await fetchAll()
  } catch (err) {
    formError.value = err.response?.data?.detail || 'Operation failed. Please try again.'
    toast(formError.value, 'error')
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
    toast('Project deleted.')
    await fetchAll()
  } catch (err) {
    toast(err.response?.data?.detail || 'Delete failed.', 'error')
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

function getClientName(clientId) {
  if (!clientId) return '—'
  const c = clients.value.find(client => client.id === clientId)
  return c ? c.name : `Client #${clientId}`
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

/* Search */
.search-box { position: relative; }
.search-icon {
  position: absolute; left: 10px; top: 50%;
  transform: translateY(-50%); color: var(--color-on-surface-variant); font-size: 16px;
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

/* Year filter */
.year-select {
  height: 38px;
  padding: 0 12px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  background: var(--color-surface);
  outline: none;
  cursor: pointer;
  transition: border-color var(--transition);
}
.year-select:focus { border-color: var(--color-primary); }

/* Add button */
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

/* ─── Project Card Grid ─── */
.cards-grid { min-height: 220px; }

.cards-empty {
  padding: 48px 16px;
  text-align: center;
  color: var(--color-on-surface-variant);
  font-size: 13px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-xl);
}
.loading-text { animation: pulse 1.4s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }

.cards-wrap {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.project-card {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: 20px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  cursor: pointer;
  transition: transform .16s ease, border-color .16s ease, box-shadow .16s ease;
}
.project-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-primary);
  box-shadow: var(--shadow-sm);
}

.project-card-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}
.name-cell { display: flex; align-items: flex-start; gap: 8px; min-width: 0; }
.color-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-top: 4px;
  flex-shrink: 0;
}
.proj-name {
  font-weight: 700;
  font-size: 14px;
  color: var(--color-on-surface);
  line-height: 1.3;
}
.proj-sub {
  font-size: 11px;
  color: var(--color-on-surface-variant);
  margin-top: 2px;
}
.proj-meta-row {
  font-size: 12px;
  color: var(--color-on-surface-variant);
  margin-top: -6px;
}

.mono { font-variant-numeric: tabular-nums; }
.muted { color: var(--color-on-surface-variant); }

/* Stage badges */
.stage-badge {
  display: inline-block;
  padding: 3px 9px;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}
.stage-active  { background: #dbeafe; color: #1d4ed8; }
.stage-done    { background: #dcfce7; color: #15803d; }
.stage-const   { background: #fef3c7; color: #92400e; }
.stage-na      { background: var(--color-outline-variant); color: var(--color-on-surface-variant); }

.project-card-body {
  display: grid;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--color-outline-variant);
}
.stat-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 12.5px;
}
.stat-label { color: var(--color-on-surface-variant); }
.stat-val { font-weight: 700; color: var(--color-on-surface); font-variant-numeric: tabular-nums; }
.billed-val { color: #15803d; }
.unbilled-val { color: #b91c1c; }

.card-actions {
  display: flex;
  gap: 14px;
  justify-content: flex-end;
  margin-top: 2px;
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
.btn-text:hover { text-decoration: underline; }
.btn-text-danger { color: var(--color-error); }
.btn-text-primary { color: var(--color-primary); margin-right: auto; }

/* ─── Table Footer / Pagination ─── */
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
.modal-wide { width: 760px; }
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
.span-2 { grid-column: span 2; }

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
.form-field input:disabled {
  background: var(--color-outline-variant);
  color: var(--color-on-surface-variant);
  cursor: not-allowed;
}

/* Color picker */
.modern-color-picker {
  background: var(--color-surface-dim);
  padding: 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-outline);
}
.presets-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
}
.color-preset-btn {
  width: 100%;
  aspect-ratio: 1;
  border: 2px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: transform 0.15s, border-color 0.15s, box-shadow 0.15s;
}
.color-preset-btn:hover { transform: scale(1.12); }
.color-preset-btn.active {
  border-color: var(--color-on-surface);
  box-shadow: 0 0 0 2px var(--color-surface) inset;
}

/* Form error */
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

/* ─── Detail Modal ─── */
.modal-xl {
  width: 1100px;
  max-width: 98vw;
  height: 94vh;
  display: flex;
  flex-direction: column;
}
.modal-xl .modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 28px 32px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 28px;
}
.detail-section { margin-bottom: 0; }

.section-title {
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--color-on-surface-variant);
  margin: 0 0 14px;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.info-item label {
  font-family: var(--font-body);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: var(--color-on-surface-variant);
}
.info-item span {
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
}
.info-item input,
.info-item select {
  height: 34px;
  padding: 0 10px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 13px;
  outline: none;
  background: var(--color-surface-dim);
  transition: border-color var(--transition), box-shadow var(--transition);
}
.info-item input:focus,
.info-item select:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light);
  background: var(--color-surface);
}

/* Work orders */
.workorders-list { margin-bottom: 12px; }
.workorder-item {
  padding: 8px 12px;
  background: var(--color-surface-dim);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  margin-bottom: 6px;
}
.workorder-item a {
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 600;
}
.workorder-item a:hover { text-decoration: underline; }

.upload-form {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-top: 8px;
}
.upload-form input {
  flex: 1;
  padding: 7px 10px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 12px;
  outline: none;
}
.btn-upload {
  padding: 8px 14px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity var(--transition);
  white-space: nowrap;
}
.btn-upload:hover:not(:disabled) { opacity: 0.88; }
.btn-upload:disabled { opacity: 0.45; cursor: not-allowed; }

.empty-state {
  padding: 20px;
  text-align: center;
  color: var(--color-on-surface-variant);
  font-family: var(--font-body);
  font-size: 13px;
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

/* Utility */
.mt-4 { margin-top: 16px; }
.text-primary { color: var(--color-primary); }
.text-success  { color: var(--color-success); }
.text-danger   { color: var(--color-error); }

/* Progress bar */
.progress-container { display: flex; flex-direction: column; gap: 6px; }
.progress-bar {
  height: 8px;
  background: var(--color-outline-variant);
  border-radius: var(--radius-full);
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}
.progress-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-on-surface-variant);
}

@media (max-width: 768px) {
  .page-actions { flex-direction: column; align-items: stretch; gap: 10px; }
  .actions-left { flex-wrap: wrap; }
  .search-input { width: 100%; }
  .cards-wrap { grid-template-columns: 1fr; }
  .modal { max-width: 100%; width: 100%; }
  .modal-backdrop { padding: 8px; }
  .info-grid { grid-template-columns: 1fr; }
}
</style>
