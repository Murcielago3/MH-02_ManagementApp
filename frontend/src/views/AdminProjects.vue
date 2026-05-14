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
            <th>Client</th>
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
            <td><span class="muted">{{ getClientName(p.client_id) }}</span></td>
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
                  <div class="custom-color-wrap">
                    <input v-model="form.color" type="color" class="custom-color-input" />
                    <span class="color-hex">{{ form.color }}</span>
                  </div>
                </div>
              </div>
              <!-- Partner Hourly Rate -->
              <div class="form-field" v-if="isAdmin">
                <label>Partner Rate/hr (₹)</label>
                <input
                  v-model.number="form.partner_hourly_rate"
                  type="number"
                  min="0"
                  step="100"
                  placeholder="e.g. 1500"
                />
              </div>
              <!-- Budgets -->
              <div class="form-field" v-if="isAdmin">
                <label>Employee Budget (₹)</label>
                <CurrencyInput v-model="form.employee_budget" placeholder="e.g. 500000" />
              </div>
              <div class="form-field" v-if="isAdmin">
                <label>Partner Budget (₹)</label>
                <CurrencyInput v-model="form.partner_budget" placeholder="e.g. 200000" />
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
              <!-- Total Assigned Hours -->
              <div class="form-field span-2">
                <label>Total Assigned Hours</label>
                <input v-model.number="form.total_assigned_hours" type="number" step="0.5" placeholder="e.g. 500" />
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
            <!-- Budget Alerts -->
            <div v-if="isAdmin && (employeeBudgetPercent >= 90 || partnerBudgetPercent >= 90)" class="budget-alerts mb-4">
              <div v-if="employeeBudgetPercent >= 90" class="form-error" :style="{ background: employeeBudgetPercent > 100 ? '#ffdad6' : '#fef3c7', color: employeeBudgetPercent > 100 ? '#93000a' : '#92400e', marginTop: '0', marginBottom: '8px' }">
                <span class="material-symbols-outlined">{{ employeeBudgetPercent > 100 ? 'error' : 'warning' }}</span>
                Employee Budget is {{ employeeBudgetPercent }}% utilized. {{ employeeBudgetPercent > 100 ? 'Limit exceeded!' : 'Approaching limit.' }}
              </div>
              <div v-if="partnerBudgetPercent >= 90" class="form-error" :style="{ background: partnerBudgetPercent > 100 ? '#ffdad6' : '#fef3c7', color: partnerBudgetPercent > 100 ? '#93000a' : '#92400e', marginTop: '0', marginBottom: '8px' }">
                <span class="material-symbols-outlined">{{ partnerBudgetPercent > 100 ? 'error' : 'warning' }}</span>
                Partner Budget is {{ partnerBudgetPercent }}% utilized. {{ partnerBudgetPercent > 100 ? 'Limit exceeded!' : 'Approaching limit.' }}
              </div>
            </div>

            <div class="detail-grid">
              <!-- Project Info -->
              <div class="detail-section info-section">
                <h4 class="section-title">Project Information</h4>
                <div class="info-grid">
                  <div class="info-item">
                    <label>Project Number</label>
                    <input v-if="isAdmin" v-model="detailProject.project_number" type="text" />
                    <span v-else>{{ detailProject?.project_number }}</span>
                  </div>
                  <div class="info-item">
                    <label>Name</label>
                    <input v-if="isAdmin" v-model="detailProject.name" type="text" />
                    <span v-else>{{ detailProject?.name }}</span>
                  </div>
                  <div class="info-item">
                    <label>Location</label>
                    <input v-if="isAdmin" v-model="detailProject.location" type="text" />
                    <span v-else>{{ detailProject?.location || '—' }}</span>
                  </div>
                  <div class="info-item">
                    <label>Google Maps</label>
                    <input v-if="isAdmin" v-model="detailProject.gmap_link" type="url" placeholder="https://..." />
                    <span v-else-if="detailProject?.gmap_link">
                      <a :href="detailProject.gmap_link" target="_blank">View Map</a>
                    </span>
                    <span v-else>—</span>
                  </div>
                  <div class="info-item">
                    <label>Year</label>
                    <input v-if="isAdmin" v-model.number="detailProject.year" type="number" />
                    <span v-else>{{ detailProject?.year || '—' }}</span>
                  </div>
                  <div class="info-item">
                    <label>Stage</label>
                    <select v-if="isAdmin" v-model="detailProject.current_stage">
                      <option v-for="s in stages" :key="s" :value="s">{{ s }}</option>
                    </select>
                    <span v-else>{{ detailProject?.current_stage || '—' }}</span>
                  </div>
                  <div class="info-item">
                    <label>Billing Status</label>
                    <select v-if="isAdmin" v-model="detailProject.is_billed">
                      <option value="unbilled">Unbilled</option>
                      <option value="billed">Billed</option>
                      <option value="partial">Partial</option>
                    </select>
                    <span v-else>{{ detailProject?.is_billed }}</span>
                  </div>
                  <div class="info-item">
                    <label>Client</label>
                    <select v-if="isAdmin" v-model="detailProject.client_id">
                      <option :value="null">No Client</option>
                      <option v-for="c in clients" :key="c.id" :value="c.id">{{ c.name }}</option>
                    </select>
                    <span v-else>{{ getClientName(detailProject?.client_id) }}</span>
                  </div>
                </div>

                <div class="info-grid mt-4" v-if="isAdmin">
                  <div class="info-item">
                    <label>Partner Rate/hr</label>
                    <input v-model.number="detailProject.partner_hourly_rate" type="number" />
                  </div>
                  <div class="info-item">
                    <label>Partner Remuneration</label>
                    <CurrencyInput v-model="detailProject.partner_remuneration" />
                  </div>
                  <div class="info-item">
                    <label>Employee Remuneration</label>
                    <CurrencyInput v-model="detailProject.employee_remuneration" />
                  </div>
                  <div class="info-item">
                    <label>Total Remuneration</label>
                    <CurrencyInput v-model="detailProject.project_remuneration" />
                  </div>
                  <div class="info-item">
                    <label>Employee Budget</label>
                    <CurrencyInput v-model="detailProject.employee_budget" />
                  </div>
                  <div class="info-item">
                    <label>Partner Budget</label>
                    <CurrencyInput v-model="detailProject.partner_budget" />
                  </div>
                </div>
              </div>

              <!-- Budget Tracking -->
              <div class="detail-section highlight-section" v-if="isAdmin">
                <h4 class="section-title">Budget Tracking</h4>
                <!-- Employee Budget -->
                <div class="budget-block">
                  <div class="hours-track-grid">
                    <div class="track-item">
                      <label>Employee Budget</label>
                      <div class="track-val">₹{{ formatAmount(detailProject?.employee_budget || 0) }}</div>
                    </div>
                    <div class="track-item">
                      <label>Employee Cost</label>
                      <div class="track-val text-primary">₹{{ formatAmount(detailProject?.employee_remuneration || 0) }}</div>
                    </div>
                    <div class="track-item">
                      <label>Remaining</label>
                      <div class="track-val" :class="(detailProject?.employee_budget || 0) - (detailProject?.employee_remuneration || 0) < 0 ? 'text-danger' : 'text-success'">
                        ₹{{ formatAmount((detailProject?.employee_budget || 0) - (detailProject?.employee_remuneration || 0)) }}
                      </div>
                    </div>
                  </div>
                  <div class="progress-container">
                    <div class="progress-bar">
                      <div 
                        class="progress-fill" 
                        :style="{ width: Math.min(100, employeeBudgetPercent) + '%', background: employeeBudgetPercent > 100 ? '#dc2626' : (employeeBudgetPercent >= 90 ? '#f59e0b' : 'var(--color-primary)') }"
                      ></div>
                    </div>
                    <div class="progress-labels">
                      <span>{{ employeeBudgetPercent }}% Utilized</span>
                      <span v-if="employeeBudgetPercent >= 90" :style="{ color: employeeBudgetPercent > 100 ? '#ba1a1a' : '#f59e0b', fontWeight: '700' }">
                        {{ employeeBudgetPercent > 100 ? 'Budget Exceeded!' : 'Nearing Budget Limit!' }}
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Partner Budget -->
                <div class="budget-block" style="margin-top: 24px;">
                  <div class="hours-track-grid">
                    <div class="track-item">
                      <label>Partner Budget</label>
                      <div class="track-val">₹{{ formatAmount(detailProject?.partner_budget || 0) }}</div>
                    </div>
                    <div class="track-item">
                      <label>Partner Cost</label>
                      <div class="track-val text-primary">₹{{ formatAmount(detailProject?.partner_remuneration || 0) }}</div>
                    </div>
                    <div class="track-item">
                      <label>Remaining</label>
                      <div class="track-val" :class="(detailProject?.partner_budget || 0) - (detailProject?.partner_remuneration || 0) < 0 ? 'text-danger' : 'text-success'">
                        ₹{{ formatAmount((detailProject?.partner_budget || 0) - (detailProject?.partner_remuneration || 0)) }}
                      </div>
                    </div>
                  </div>
                  <div class="progress-container">
                    <div class="progress-bar">
                      <div 
                        class="progress-fill" 
                        :style="{ width: Math.min(100, partnerBudgetPercent) + '%', background: partnerBudgetPercent > 100 ? '#dc2626' : (partnerBudgetPercent >= 90 ? '#f59e0b' : 'var(--color-primary)') }"
                      ></div>
                    </div>
                    <div class="progress-labels">
                      <span>{{ partnerBudgetPercent }}% Utilized</span>
                      <span v-if="partnerBudgetPercent >= 90" :style="{ color: partnerBudgetPercent > 100 ? '#ba1a1a' : '#f59e0b', fontWeight: '700' }">
                        {{ partnerBudgetPercent > 100 ? 'Budget Exceeded!' : 'Nearing Budget Limit!' }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Assigned Employees -->
              <div class="detail-section">
                <h4 class="section-title">Assigned Employees</h4>
                <div v-if="detailProject?.assignments?.length" class="assignments-list">
                  <div v-for="a in detailProject.assignments" :key="a.id" class="assignment-item">
                    <div class="assign-main">
                      <div class="assign-info">
                        <span class="assign-name">{{ a.user?.name }}</span>
                        <span class="assign-role">{{ a.user?.designation }}</span>
                      </div>
                      <div class="assign-stats">
                        <div class="stat-item">
                          <label>Hours Spent</label>
                          <span class="stat-val">{{ a.hours_worked || 0 }}h</span>
                        </div>
                        <div class="stat-item">
                          <label>Base Pay</label>
                          <span class="stat-val">₹{{ formatAmount(a.base_pay) }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else class="empty-state">No employees assigned yet.</div>

                <!-- Assign Employee -->
                <div class="assign-form">
                  <select v-model="assignUserId">
                    <option :value="null">— Select Employee —</option>
                    <option v-for="u in assignableUsers" :key="u.id" :value="u.id">
                      {{ u.name }} ({{ u.designation }})
                    </option>
                  </select>
                  <div class="assign-pay-block">
                    <label class="assign-pay-label">Base Pay (₹/month)</label>
                    <input
                      v-model.number="assignBasePay"
                      type="number"
                      min="0"
                      step="100"
                      class="assign-base-input"
                      placeholder="e.g. 80000"
                    />
                    <p v-if="assignPreviewHourly != null" class="assign-hourly-preview">
                      Hourly Rate: {{ formatInrPerHour(assignPreviewHourly) }}
                    </p>
                  </div>
                  <button
                    class="btn-assign"
                    :disabled="!assignUserId || assignBasePay == null || assignBasePay === '' || Number(assignBasePay) <= 0 || assignSubmitting"
                    @click="assignUser"
                  >
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
          <div class="modal-footer" v-if="isAdmin">
            <button class="btn-cancel" @click="closeDetailModal">Cancel</button>
            <button class="btn-submit" :disabled="submitting" @click="saveDetailChanges">
              {{ submitting ? 'Saving...' : 'Save All Changes' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

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
import AppLayout from '../components/AppLayout.vue'
import EmployeeLayout from '../components/EmployeeLayout.vue'
import CurrencyInput from '../components/CurrencyInput.vue'
import ToastNotification from '../components/ToastNotification.vue'
import { useAuthStore } from '../stores/auth'
import { projectsAPI } from '../api/projects'
import { clientsAPI } from '../api/clients'
import { usersAPI } from '../api/users'
import { formatInrPerHour, previewHourlyFromBasePay } from '../utils/currency'

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
const assignBasePay = ref(null)
const assignSubmitting = ref(false)
const uploadFile = ref(null)
const uploadSubmitting = ref(false)
const uploadInput = ref(null)

const toastMsg = ref('')
const toastType = ref('success')

function toast(msg, type = 'success') {
  toastType.value = type
  toastMsg.value = msg
}

const assignableUsers = computed(() => {
  const assignments = detailProject.value?.assignments || []
  const taken = new Set(
    assignments.map((a) => a.user_id ?? a.user?.id).filter((id) => id != null)
  )
  return users.value.filter((u) => !taken.has(u.id))
})

const assignPreviewHourly = computed(() => previewHourlyFromBasePay(assignBasePay.value))

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
  total_assigned_hours: null,
  color: '#287475',
  partner_hourly_rate: null,
  employee_budget: null,
  partner_budget: null,
})

const projectPresets = [
  '#287475', '#1e5d5e', '#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f59e0b',
  '#10b981', '#06b6d4', '#3b82f6', '#475569', '#1e293b'
]

async function fetchAll() {
  loading.value = true
  try {
    const results = await Promise.allSettled([
      projectsAPI.getProjects(),
      clientsAPI.getClients(),
      usersAPI.getUsers()
    ])
    
    if (results[0].status === 'fulfilled') projects.value = results[0].value.data
    else console.error('Projects fetch failed', results[0].reason)
    
    if (results[1].status === 'fulfilled') clients.value = results[1].value.data
    else console.error('Clients fetch failed', results[1].reason)
    
    if (results[2].status === 'fulfilled') users.value = results[2].value.data
    else console.error('Users fetch failed', results[2].reason)
    
  } catch (e) {
    console.error('FetchAll failed', e)
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
  let list = [...projects.value]
  // Sort: Year desc, Number desc (Newer first)
  list.sort((a, b) => {
    if (b.year !== a.year) return (b.year || 0) - (a.year || 0)
    return (b.project_number || '').localeCompare(a.project_number || '')
  })
  
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
  form.total_assigned_hours = null
  form.color = '#287475'
  form.partner_hourly_rate = null
  form.employee_budget = null
  form.partner_budget = null
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
  form.total_assigned_hours = p.total_assigned_hours ? Number(p.total_assigned_hours) : null
  form.color = p.color || '#287475'
  form.partner_hourly_rate =
    p.partner_hourly_rate != null && p.partner_hourly_rate !== ''
      ? Number(p.partner_hourly_rate)
      : null
  form.employee_budget = p.employee_budget ? Number(p.employee_budget) : null
  form.partner_budget = p.partner_budget ? Number(p.partner_budget) : null
  formError.value = ''
  modalOpen.value = true
}

function closeModal() { modalOpen.value = false }

// Automatic Calculations in Detail Modal
watch(() => detailProject.value?.partner_hourly_rate, (newVal) => {
  if (!detailProject.value || newVal === null || newVal === undefined) return
  const hrs = Number(detailProject.value.total_worked_hours) || 0
  detailProject.value.partner_remuneration = Number(newVal) * hrs
})

watch([() => detailProject.value?.partner_remuneration, () => detailProject.value?.employee_remuneration], ([newP, newE]) => {
  if (!detailProject.value) return
  const pRem = Number(newP) || 0
  const eRem = Number(newE) || 0
  detailProject.value.project_remuneration = pRem + eRem
})

async function openDetailModal(p) {
  try {
    const res = await projectsAPI.getProject(p.id)
    detailProject.value = res.data
    assignUserId.value = null
    assignBasePay.value = null
    detailModalOpen.value = true
  } catch (e) {
    toast(e.response?.data?.detail || 'Could not load project.', 'error')
    console.error(e)
  }
}

function closeDetailModal() {
  detailModalOpen.value = false
  assignUserId.value = null
  assignBasePay.value = null
}

async function assignUser() {
  if (!assignUserId.value || assignBasePay.value == null || assignBasePay.value === '') return
  const bp = Number(assignBasePay.value)
  if (bp <= 0) return
  assignSubmitting.value = true
  try {
    await projectsAPI.assignEmployee(detailProject.value.id, {
      user_id: assignUserId.value,
      base_pay: bp,
    })
    assignUserId.value = null
    assignBasePay.value = null
    toast('Employee assigned.')
    const res = await projectsAPI.getProject(detailProject.value.id)
    detailProject.value = res.data
  } catch (e) {
    toast(e.response?.data?.detail || 'Assignment failed.', 'error')
    console.error(e)
  } finally {
    assignSubmitting.value = false
  }
}

async function saveDetailChanges() {
  if (!detailProject.value) return
  submitting.value = true
  try {
    const payload = {
      project_number: detailProject.value.project_number,
      name: detailProject.value.name,
      location: detailProject.value.location || null,
      gmap_link: detailProject.value.gmap_link || null,
      year: detailProject.value.year || null,
      current_stage: detailProject.value.current_stage || null,
      is_billed: detailProject.value.is_billed,
      client_id: detailProject.value.client_id || null,
      start_date: detailProject.value.start_date || null,
      end_date: detailProject.value.end_date || null,
      employee_budget: detailProject.value.employee_budget,
      partner_budget: detailProject.value.partner_budget,
      project_remuneration: detailProject.value.project_remuneration,
      color: detailProject.value.color,
      partner_hourly_rate: detailProject.value.partner_hourly_rate,
    }
    await projectsAPI.updateProject(detailProject.value.id, payload)
    toast('Project details saved.')
    await fetchAll()
  } catch (err) {
    toast(err.response?.data?.detail || 'Save failed.', 'error')
  } finally {
    submitting.value = false
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
    toast('Work order uploaded.')
  } catch (e) {
    toast(e.response?.data?.detail || 'Upload failed.', 'error')
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
      total_assigned_hours: form.total_assigned_hours,
      color: form.color,
      partner_hourly_rate: form.partner_hourly_rate,
      employee_budget: form.employee_budget,
      partner_budget: form.partner_budget,
    }
    if (isEditing.value) {
      await projectsAPI.updateProject(editingId.value, payload)
    } else {
      await projectsAPI.createProject(payload)
    }
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


const remainingHours = computed(() => {
  const assigned = Number(detailProject.value?.total_assigned_hours) || 0
  const worked = Number(detailProject.value?.total_worked_hours) || 0
  return (assigned - worked).toFixed(1)
})

const progressPercent = computed(() => {
  const assigned = Number(detailProject.value?.total_assigned_hours) || 0
  if (assigned <= 0) return 0
  const worked = Number(detailProject.value?.total_worked_hours) || 0
  return Math.round((worked / assigned) * 100)
})
const employeeBudgetPercent = computed(() => {
  const budget = Number(detailProject.value?.employee_budget) || 0
  if (budget <= 0) return 0
  const cost = Number(detailProject.value?.employee_remuneration) || 0
  return Math.round((cost / budget) * 100)
})

const partnerBudgetPercent = computed(() => {
  const budget = Number(detailProject.value?.partner_budget) || 0
  if (budget <= 0) return 0
  const cost = Number(detailProject.value?.partner_remuneration) || 0
  return Math.round((cost / budget) * 100)
})
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

/* Modern Color Picker */
.modern-color-picker {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: var(--color-background);
  padding: 16px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-outline-variant);
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
  border-radius: 6px;
  cursor: pointer;
  transition: transform 0.15s, border-color 0.15s;
}

.color-preset-btn:hover { transform: scale(1.1); }
.color-preset-btn.active { border-color: #000; box-shadow: 0 0 0 2px #fff inset; }

.custom-color-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-top: 8px;
  border-top: 1px dashed var(--color-outline-variant);
}

.custom-color-input {
  width: 32px;
  height: 32px;
  padding: 0;
  border: none;
  background: none;
  cursor: pointer;
}

.color-hex {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-surface-variant);
  text-transform: uppercase;
}

.color-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 8px;
  flex-shrink: 0;
}

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
.modal-xl { width: 1200px; max-width: 98vw; height: 95vh; display: flex; flex-direction: column; }
.modal-xl .modal-body { flex: 1; overflow-y: auto; padding: 32px; }
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
  font-family: var(--font-body); font-size: 14px; color: var(--color-on-surface);
}
.info-item input, .info-item select {
  height: 36px; padding: 0 8px; border: 1px solid var(--color-outline-variant);
  border-radius: 4px; font-family: var(--font-body); font-size: 13px; outline: none;
  background: var(--color-surface-dim);
}
.info-item input:focus, .info-item select:focus {
  border-color: var(--color-primary); background: #fff;
}
.mt-4 { margin-top: 16px; }
.assignments-list {
  margin-bottom: 16px;
}
.assignment-item {
  padding: 12px 16px; background: var(--color-surface-dim); border-radius: var(--radius-lg);
  margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;
  border: 1px solid var(--color-outline-variant);
}
.assign-main { flex: 1; display: flex; justify-content: space-between; align-items: center; }
.assign-info { display: flex; flex-direction: column; gap: 2px; }
.assign-name { font-family: var(--font-display); font-size: 14px; font-weight: 600; color: var(--color-on-surface); }
.assign-role { font-size: 11px; color: var(--color-on-surface-variant); text-transform: uppercase; letter-spacing: 0.02em; }
.assign-stats { display: flex; gap: 24px; }
.stat-item { display: flex; flex-direction: column; gap: 2px; }
.stat-item label { font-size: 9px; text-transform: uppercase; color: var(--color-on-surface-variant); font-weight: 700; }
.stat-val { font-family: var(--font-body); font-size: 13px; font-weight: 600; color: var(--color-on-surface); }
.assign-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: stretch;
  margin-top: 16px;
}
.assign-form select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius);
  font-family: var(--font-display);
  font-size: 13px;
}
.assign-pay-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.assign-pay-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-on-surface-variant);
}
.assign-base-input {
  width: 100%;
  height: 40px;
  padding: 0 12px;
  border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius-lg);
  font-size: 14px;
}
.assign-hourly-preview {
  margin: 0;
  font-size: 13px;
  color: var(--color-on-surface-variant);
}
.btn-assign {
  align-self: flex-start;
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
/* Highlight Section (Tracking) */
.highlight-section {
  background: var(--color-surface-container-lowest);
  padding: 20px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-outline-variant);
  grid-column: span 2;
}

.hours-track-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.track-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.track-item label {
  font-size: 11px;
  text-transform: uppercase;
  font-weight: 700;
  color: var(--color-on-surface-variant);
  letter-spacing: 0.05em;
}

.track-val {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  color: var(--color-on-surface);
}

.progress-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.progress-bar {
  height: 10px;
  background: var(--color-surface-container-high);
  border-radius: 5px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.progress-labels {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-on-surface-variant);
}

.text-primary { color: var(--color-primary); }
.text-success { color: #145a23; }
.text-danger { color: #ba1a1a; }
</style>
