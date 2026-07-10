<template>
  <AppLayout>
    <div class="profile-header">
      <div class="profile-info">
        <div class="avatar">
          <img v-if="employee.photo_url" :src="employee.photo_url" alt="Profile" />
          <span v-else class="avatar-initials">{{ initials }}</span>
        </div>
        <div class="profile-details">
          <h1 class="profile-name">{{ employee.name || 'Loading...' }}</h1>
          <p class="profile-role">{{ employee.designation || formatRole(employee.role) || '—' }}</p>
          <p class="profile-email">{{ employee.studio_email || '—' }}</p>
        </div>
      </div>
    </div>

    <div class="profile-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="tab-content">
      <!-- Profile Tab -->
      <div v-if="activeTab === 'profile'" class="profile-section">
        <div class="info-grid">
          <div class="info-item">
            <label>Employee ID</label>
            <span>{{ employee.id }}</span>
          </div>
          <div class="info-item">
            <label>Name</label>
            <span>{{ employee.name }}</span>
          </div>
          <div class="info-item">
            <label>Studio Email</label>
            <span>{{ employee.studio_email || '—' }}</span>
          </div>
          <div class="info-item">
            <label>Personal Email</label>
            <span>{{ employee.personal_mail || '—' }}</span>
          </div>
          <div class="info-item">
            <label>Phone Number</label>
            <span>{{ employee.phone_number || '—' }}</span>
          </div>
          <div class="info-item">
            <label>Role</label>
            <span>{{ formatRole(employee.role) }}</span>
          </div>
          <div class="info-item">
            <label>Designation</label>
            <span>{{ employee.designation || '—' }}</span>
          </div>
          <div class="info-item">
            <label>Joining Date</label>
            <span>{{ formatDate(employee.joining_date) }}</span>
          </div>
          <div class="info-item">
            <label>End Date</label>
            <span>{{ employee.end_date ? formatDate(employee.end_date) : '—' }}</span>
          </div>
          <div class="info-item">
            <label>Monthly Salary</label>
            <span>{{ employee.salary_month ? `₹${Number(employee.salary_month).toLocaleString()}` : '—' }}</span>
          </div>
          <div class="info-item">
            <label>Hourly Rate</label>
            <span>{{ employee.salary_hour ? `₹${employee.salary_hour}` : '—' }}</span>
          </div>
          <div class="info-item">
            <label>Leaves Allowed</label>
            <span>{{ employee.leaves_allowed }}</span>
          </div>
          <div class="info-item">
            <label>Paid Leave Balance</label>
            <span>{{ Number(employee.paid_leave_balance || 0) }} days</span>
          </div>
          <div class="info-item">
            <label>Probation</label>
            <span>
              <span class="status-badge" :class="onProbation ? 'status-pending' : 'status-approved'">
                {{ onProbation ? `Until ${probationEndLabel}` : 'Completed' }}
              </span>
            </span>
          </div>
          <div class="info-item">
            <label>Manager</label>
            <span>{{ employee.manager?.name || '—' }}</span>
          </div>
        </div>
      </div>

      <!-- Timesheets Tab -->
      <div v-if="activeTab === 'timesheet'" class="timesheet-section">
        <div class="table-card">
          <table class="proj-table">
            <thead>
              <tr>
                <th>Week</th>
                <th>Description</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loadingTimesheets">
                <td colspan="4" class="empty-cell">Loading timesheets...</td>
              </tr>
              <tr v-else-if="timesheets.length === 0">
                <td colspan="4" class="empty-cell">No timesheets submitted.</td>
              </tr>
              <tr v-for="ts in timesheets" :key="ts.id" class="proj-row">
                <td class="mono">
                  {{ formatDateShort(ts.week_start) }} – {{ formatDateShort(ts.week_end) }}
                </td>
                <td class="text-center">
                  <span class="hours-badge">{{ ts.total_hours || 0 }}h</span>
                </td>
                <td>
                  <span class="status-badge" :class="`status-${ts.status}`">
                    {{ formatTimesheetStatus(ts.status) }}
                  </span>
                </td>
                <td class="action-cell">
                  <div class="ts-actions">
                    <button class="btn-outline" @click="viewDetail(ts)">
                      <span class="material-symbols-outlined">visibility</span>
                      Details
                    </button>
                    <template v-if="ts.status === 'submitted'">
                      <button class="btn-approve" @click="handleAction(ts.id, 'approved')" :disabled="actionLoading === ts.id">
                        <span class="material-symbols-outlined">check</span>
                      </button>
                      <button class="btn-reject" @click="openRejectModal(ts.id)" :disabled="actionLoading === ts.id">
                        <span class="material-symbols-outlined">close</span>
                      </button>
                    </template>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Leave Requests Tab -->
      <div v-if="activeTab === 'leaves'" class="leaves-section">
        <div class="table-card">
          <table class="proj-table">
            <thead>
              <tr>
                <th>Start Date</th>
                <th>End Date</th>
                <th>Days</th>
                <th>Paid</th>
                <th>Unpaid</th>
                <th>Reason</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loadingLeaves">
                <td colspan="7" class="empty-cell">Loading leave requests...</td>
              </tr>
              <tr v-else-if="leaves.length === 0">
                <td colspan="7" class="empty-cell">No leave requests.</td>
              </tr>
              <tr v-for="l in leaves" :key="l.id" class="proj-row">
                <td class="mono">{{ formatDate(l.start_date) }}</td>
                <td class="mono">{{ formatDate(l.end_date) }}</td>
                <td class="mono">{{ l.days_count }}</td>
                <td class="mono">{{ l.status === 'approved' ? l.paid_days : '—' }}</td>
                <td class="mono">
                  <span :class="{ 'unpaid-flag': l.status === 'approved' && l.unpaid_days > 0 }">
                    {{ l.status === 'approved' ? l.unpaid_days : '—' }}
                  </span>
                </td>
                <td class="muted">{{ l.reason }}</td>
                <td>
                  <span class="status-badge" :class="`status-${l.status}`">
                    {{ l.status }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Assigned Tasks Tab -->
      <div v-if="activeTab === 'tasks'" class="tasks-section">
        <div class="table-card">
          <table class="proj-table">
            <thead>
              <tr>
                <th>Task</th>
                <th>Project</th>
                <th>Priority</th>
                <th>Due Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loadingTasks">
                <td colspan="5" class="empty-cell">Loading tasks...</td>
              </tr>
              <tr v-else-if="tasks.length === 0">
                <td colspan="5" class="empty-cell">No assigned tasks.</td>
              </tr>
              <tr v-for="t in tasks" :key="t.id" class="proj-row">
                <td><span class="proj-name">{{ t.title }}</span></td>
                <td class="muted">{{ t.project?.name || '—' }}</td>
                <td>
                  <span class="priority-badge" :class="`priority-${t.priority}`">
                    {{ t.priority }}
                  </span>
                </td>
                <td class="mono">
                  {{ t.date ? formatDate(t.date) : '—' }}
                  <div v-if="t.date" :class="['due-status', { late: isLate(t), dueToday: isDueToday(t) }]">
                    {{ taskDueStatus(t) }}
                  </div>
                </td>
                <td>
                  <span class="status-badge" :class="`status-${t.status}`">
                    {{ t.status }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Documents Tab (admin only) -->
      <div v-if="activeTab === 'documents'" class="documents-section">
        <div class="info-grid id-grid">
          <div class="info-item">
            <label>PAN Number</label>
            <span class="mono-id">{{ employee.pan_number || '—' }}</span>
          </div>
          <div class="info-item">
            <label>Aadhaar Number</label>
            <span class="mono-id">{{ employee.aadhar_number || '—' }}</span>
          </div>
        </div>

        <div class="doc-cards">
          <div v-for="dt in DOC_TYPES" :key="dt.type" class="doc-card">
            <div class="doc-card-head">
              <span class="material-symbols-outlined doc-icon" :class="{ 'has-doc': docFor(dt.type) }">
                {{ docFor(dt.type) ? 'task' : 'description' }}
              </span>
              <div class="doc-meta">
                <div class="doc-label">{{ dt.label }}</div>
                <div v-if="docFor(dt.type)" class="doc-file" :title="docFor(dt.type).filename">{{ docFor(dt.type).filename }}</div>
                <div v-else class="doc-file muted">Not uploaded</div>
              </div>
            </div>
            <div class="doc-actions">
              <a v-if="docFor(dt.type)" :href="docUrl(docFor(dt.type))" target="_blank" rel="noopener" class="btn-doc">
                <span class="material-symbols-outlined">visibility</span> View
              </a>
              <button class="btn-doc" @click="triggerUpload(dt.type)" :disabled="uploadingType === dt.type">
                <span class="material-symbols-outlined">{{ uploadingType === dt.type ? 'progress_activity' : 'upload' }}</span>
                {{ uploadingType === dt.type ? 'Uploading…' : (docFor(dt.type) ? 'Replace' : 'Upload') }}
              </button>
              <button v-if="docFor(dt.type)" class="btn-doc btn-doc-danger" @click="removeDoc(dt.type)" title="Remove">
                <span class="material-symbols-outlined">delete</span>
              </button>
            </div>
          </div>
        </div>
        <p class="doc-hint">Accepted formats: PDF or image (JPG/PNG). Uploading replaces any existing file of the same type.</p>
        <input ref="fileInput" type="file" accept="application/pdf,image/*" style="display:none" @change="onFileSelected" />
      </div>
    </div>

    <!-- Detail Modal -->
    <div v-if="showDetailModal" class="modal-backdrop">
      <div class="modal-content detail-modal">
        <div class="modal-header">
          <div class="header-info">
            <h3>Timesheet Breakdown</h3>
            <p>{{ employee.name }} · {{ formatDateShort(selectedTimesheet.week_start) }} - {{ formatDateShort(selectedTimesheet.week_end) }}</p>
          </div>
          <button class="btn-close" @click="closeDetailModal">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <div class="modal-body">
          <div class="detail-section">
            <label>Daily Hours Log</label>
            <TimesheetDailyGrid :timesheet="selectedTimesheet" :projects="projects" />
          </div>

          <div v-if="selectedTimesheet.description" class="detail-section">
            <label>Weekly Overview</label>
            <div class="overview-box">{{ selectedTimesheet.description }}</div>
          </div>
        </div>

        <div class="modal-footer" v-if="selectedTimesheet.status === 'submitted'">
          <div class="footer-actions">
            <button class="btn-reject-large" @click="openRejectModal(selectedTimesheet.id)">Reject</button>
            <button class="btn-approve-large" @click="handleAction(selectedTimesheet.id, 'approved')">Approve Timesheet</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Reject Modal -->
    <div v-if="rejectModalOpen" class="modal-backdrop">
      <div class="modal-content">
        <h3>Reject Timesheet</h3>
        <p>Please provide a reason for rejecting this timesheet.</p>
        <textarea v-model="rejectReason" rows="3" placeholder="Reason..."></textarea>
        <div class="modal-actions">
          <button class="btn-cancel" @click="closeRejectModal">Cancel</button>
          <button class="btn-reject-confirm" @click="confirmReject" :disabled="!rejectReason.trim() || actionLoading === rejectModalTarget">
            Reject Timesheet
          </button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import TimesheetDailyGrid from '../components/timesheet/TimesheetDailyGrid.vue'
import { usersAPI } from '../api/users'
import { weeklyTimesheetsAPI } from '../api/weekly_timesheets'
import { leavesAPI } from '../api/leaves'
import { tasksAPI } from '../api/tasks'
import { projectsAPI } from '../api/projects'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const employeeId = route.params.id
const authStore = useAuthStore()
const isAdmin = computed(() => authStore.role === 'admin')

const employee = ref({})
const timesheets = ref([])
const leaves = ref([])
const tasks = ref([])
const loadingTimesheets = ref(false)
const loadingLeaves = ref(false)
const loadingTasks = ref(false)
const activeTab = ref('profile')

const actionLoading = ref(null)
const rejectModalOpen = ref(false)
const rejectModalTarget = ref(null)
const rejectReason = ref('')

const showDetailModal = ref(false)
const selectedTimesheet = ref(null)
const projects = ref([])

const tabs = computed(() => {
  const t = [
    { key: 'profile', label: 'Profile' },
    { key: 'timesheet', label: 'Timesheet' },
    { key: 'leaves', label: 'Leave Requests' },
    { key: 'tasks', label: 'Assigned Tasks' },
  ]
  // PAN/Aadhaar are sensitive — documents are admin-only.
  if (isAdmin.value) t.push({ key: 'documents', label: 'Documents' })
  return t
})

// ── Documents (PAN / Aadhaar / other) ──
const DOC_TYPES = [
  { type: 'pan', label: 'PAN Card' },
  { type: 'aadhar', label: 'Aadhaar Card' },
  { type: 'other', label: 'Other Document' },
]
const documents = ref([])
const loadingDocs = ref(false)
const uploadingType = ref(null)
const pendingType = ref(null)
const fileInput = ref(null)

function docFor(type) {
  return documents.value.find(d => d.doc_type === type)
}
function docUrl(doc) {
  return usersAPI.resolveFileUrl(doc.url)
}

async function fetchDocuments() {
  loadingDocs.value = true
  try {
    const res = await usersAPI.getDocuments(employeeId)
    documents.value = Array.isArray(res.data) ? res.data : []
  } catch (e) {
    console.error(e)
  } finally {
    loadingDocs.value = false
  }
}

function triggerUpload(type) {
  pendingType.value = type
  fileInput.value?.click()
}

async function onFileSelected(e) {
  const file = e.target.files?.[0]
  const type = pendingType.value
  e.target.value = ''
  if (!file || !type) return
  uploadingType.value = type
  try {
    await usersAPI.uploadDocument(employeeId, file, type)
    await fetchDocuments()
  } catch (err) {
    alert(err.response?.data?.detail || 'Upload failed')
  } finally {
    uploadingType.value = null
    pendingType.value = null
  }
}

async function removeDoc(type) {
  if (!confirm('Remove this document?')) return
  try {
    await usersAPI.deleteDocument(employeeId, type)
    await fetchDocuments()
  } catch (err) {
    alert(err.response?.data?.detail || 'Delete failed')
  }
}

const initials = computed(() => {
  const name = employee.value.name || ''
  return name.split(' ').filter(Boolean).map(n => n[0]).join('').toUpperCase().slice(0, 2)
})

const probationEndDate = computed(() => {
  const j = employee.value?.joining_date
  if (!j) return null
  const d = new Date(j)
  d.setMonth(d.getMonth() + 3)
  return d
})
const onProbation = computed(() => probationEndDate.value && new Date() < probationEndDate.value)
const probationEndLabel = computed(() =>
  probationEndDate.value ? probationEndDate.value.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : ''
)

async function fetchEmployee() {
  try {
    const res = await usersAPI.getUser(employeeId)
    employee.value = res.data
  } catch (e) {
    console.error(e)
  }
}

async function fetchTimesheets() {
  loadingTimesheets.value = true
  try {
    const res = await weeklyTimesheetsAPI.getTimesheets({ employee_id: employeeId })
    if (res.data && Array.isArray(res.data)) {
      timesheets.value = res.data.sort((a, b) => new Date(b.week_start) - new Date(a.week_start))
    } else {
      timesheets.value = []
    }
  } catch (e) {
    console.error(e)
  } finally {
    loadingTimesheets.value = false
  }
}

async function fetchLeaves() {
  loadingLeaves.value = true
  try {
    // Note: This assumes leaves API can filter by employee_id, but backend may need adjustment
    const res = await leavesAPI.getLeaves()
    if (res.data && Array.isArray(res.data)) {
      leaves.value = res.data.filter(l => l.employee_id == employeeId)
    } else {
      leaves.value = []
    }
  } catch (e) {
    console.error(e)
  } finally {
    loadingLeaves.value = false
  }
}

async function fetchTasks() {
  loadingTasks.value = true
  try {
    const res = await tasksAPI.getTasks()
    if (res.data && Array.isArray(res.data)) {
      tasks.value = res.data.filter(t => t.assigned_to == employeeId)
    } else {
      tasks.value = []
    }
  } catch (e) {
    console.error(e)
  } finally {
    loadingTasks.value = false
  }
}

async function fetchProjects() {
  try {
    const res = await projectsAPI.getProjects()
    projects.value = res.data
  } catch (e) {
    console.error(e)
  }
}

onMounted(async () => {
  const jobs = [
    fetchEmployee(),
    fetchTimesheets(),
    fetchLeaves(),
    fetchTasks(),
    fetchProjects()
  ]
  if (isAdmin.value) jobs.push(fetchDocuments())
  await Promise.all(jobs)
})

// Helpers
function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('en-IN')
}

function formatDateShort(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
}

function truncateDesc(desc) {
  if (!desc) return 'No description'
  return desc.length > 50 ? desc.slice(0, 50) + '...' : desc
}

function formatTimesheetStatus(s) {
  if (s === 'submitted') return 'Pending Review'
  return s.charAt(0).toUpperCase() + s.slice(1)
}

function formatRole(role) {
  if (!role) return ''
  if (role === 'project_manager') return 'Project Manager'
  return role.charAt(0).toUpperCase() + role.slice(1)
}

async function handleAction(tsId, status, reason = null) {
  actionLoading.value = tsId
  try {
    await weeklyTimesheetsAPI.actionTimesheet(tsId, { status, rejection_reason: reason })
    // update locally
    const idx = timesheets.value.findIndex(t => t.id === tsId)
    if (idx !== -1) {
      timesheets.value[idx].status = status
      timesheets.value[idx].rejection_reason = reason
    }
  } catch (e) {
    console.error('Failed to update status', e)
  } finally {
    actionLoading.value = null
  }
}

function openRejectModal(tsId) {
  rejectModalTarget.value = tsId
  rejectReason.value = ''
  rejectModalOpen.value = true
}

function closeRejectModal() {
  rejectModalOpen.value = false
  rejectModalTarget.value = null
}

async function confirmReject() {
  if (rejectModalTarget.value) {
    await handleAction(rejectModalTarget.value, 'rejected', rejectReason.value)
    closeRejectModal()
    if (selectedTimesheet.value?.id === rejectModalTarget.value) {
      selectedTimesheet.value.status = 'rejected'
      selectedTimesheet.value.rejection_reason = rejectReason.value
    }
  }
}

function viewDetail(ts) {
  selectedTimesheet.value = ts
  showDetailModal.value = true
}

function closeDetailModal() {
  showDetailModal.value = false
  selectedTimesheet.value = null
}

function taskDueStatus(task) {
  if (!task?.date) return '—'
  const due = new Date(task.date)
  due.setHours(0, 0, 0, 0)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const diff = Math.round((due - today) / (1000 * 60 * 60 * 24))
  if (diff < 0) {
    return `${Math.abs(diff)} day${Math.abs(diff) === 1 ? '' : 's'} late`
  }
  if (diff === 0) {
    return 'Due today'
  }
  return `${diff} day${diff === 1 ? '' : 's'} to go`
}

function isLate(task) {
  if (!task?.date) return false
  const due = new Date(task.date)
  due.setHours(0, 0, 0, 0)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return due < today
}

function isDueToday(task) {
  if (!task?.date) return false
  const due = new Date(task.date)
  due.setHours(0, 0, 0, 0)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return due.getTime() === today.getTime()
}
</script>

<style scoped>
.profile-header {
  background: #fff; border: 1px solid var(--color-surface-container-high); border-radius: var(--radius-lg);
  padding: 24px; margin-bottom: 24px; display: flex; align-items: center;
}
.profile-info { display: flex; align-items: center; gap: 16px; }
.avatar {
  width: 64px; height: 64px; border-radius: 50%; background: var(--color-primary);
  display: flex; align-items: center; justify-content: center;
  font-size: 24px; font-weight: 600; color: #fff;
}
.avatar img {
  width: 100%; height: 100%; border-radius: 50%; object-fit: cover;
}
.avatar-initials { color: #fff; }
.profile-details { flex: 1; }
.profile-name {
  font-size: 24px; font-weight: 600; color: var(--color-on-surface); margin: 0 0 4px 0;
}
.profile-role {
  font-size: 14px; color: var(--color-on-surface-variant); margin: 0 0 4px 0;
}
.profile-email {
  font-size: 14px; color: var(--color-on-surface-variant); margin: 0;
}

.profile-tabs {
  display: flex; gap: 0; margin-bottom: 24px;
  border-bottom: 1px solid var(--color-surface-container-high);
}
.tab-btn {
  padding: 12px 24px; background: none; border: none; border-bottom: 2px solid transparent;
  font-family: var(--font-display); font-size: 14px; font-weight: 500;
  color: var(--color-on-surface-variant); cursor: pointer; transition: all 0.15s;
}
.tab-btn:hover { color: var(--color-on-surface-variant); }
.tab-btn.active {
  color: var(--color-primary); border-bottom-color: var(--color-primary);
}

.tab-content {
  background: #fff; border: 1px solid var(--color-surface-container-high); border-radius: var(--radius-lg);
  padding: 24px;
}

.profile-section .info-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px;
}
.info-item {
  display: flex; flex-direction: column; gap: 4px;
}
.info-item label {
  font-size: 12px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--color-on-surface-variant);
}
.info-item span {
  font-size: 14px; color: var(--color-on-surface); font-weight: 500;
}

/* ── Documents tab ── */
.id-grid { margin-bottom: 24px; }
.mono-id { font-variant-numeric: tabular-nums; letter-spacing: 0.04em; }
.doc-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}
.doc-card {
  border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius-lg);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  background: var(--color-background);
}
.doc-card-head { display: flex; align-items: center; gap: 12px; }
.doc-icon {
  font-size: 28px;
  color: var(--color-on-surface-variant);
  background: var(--color-surface-container);
  border-radius: var(--radius-md);
  padding: 6px;
}
.doc-icon.has-doc { color: var(--color-primary); background: var(--color-primary-light); }
.doc-meta { min-width: 0; }
.doc-label { font-size: 14px; font-weight: 600; color: var(--color-on-surface); }
.doc-file {
  font-size: 12px;
  color: var(--color-on-surface-variant);
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.doc-file.muted { font-style: italic; }
.doc-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.btn-doc {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: #fff;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-md);
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-on-surface);
  cursor: pointer;
  text-decoration: none;
  transition: all 0.15s;
}
.btn-doc:hover:not(:disabled) { border-color: var(--color-primary); color: var(--color-primary); }
.btn-doc:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-doc .material-symbols-outlined { font-size: 15px; }
.btn-doc-danger { color: #dc2626; }
.btn-doc-danger:hover { border-color: #dc2626; background: #fef2f2; color: #dc2626; }
.doc-hint { margin: 16px 0 0; font-size: 12px; color: var(--color-on-surface-variant); }

.table-card {
  background: #fff; border: 1px solid var(--color-surface-container-high); border-radius: var(--radius-lg);
  overflow: hidden;
}
.proj-table {
  width: 100%; border-collapse: collapse;
}
.proj-table th {
  padding: 12px 16px; text-align: left; font-family: var(--font-display);
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--color-on-surface-variant); border-bottom: 1px solid var(--color-surface-container-high);
  background: var(--color-background);
}
.proj-table td {
  padding: 12px 16px; border-bottom: 1px solid var(--color-surface-container);
  font-family: var(--font-display); font-size: 13px; color: var(--color-on-surface);
}
.proj-row:hover { background: var(--color-background); }
.proj-name { font-weight: 500; }
.muted { color: var(--color-on-surface-variant); }
.mono { font-variant-numeric: tabular-nums; }
.unpaid-flag { color: #b45309; font-weight: 700; }

.empty-cell {
  text-align: center; padding: 48px 16px; color: var(--color-on-surface-variant);
  font-family: var(--font-display); font-size: 13px;
}

.site-badge {
  padding: 4px 8px; background: #dbeafe; color: #1e40af;
  border-radius: var(--radius-lg); font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.05em;
}

.due-status {
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-on-surface-variant);
}
.due-status.late {
  color: #b91c1c;
}
.due-status.dueToday {
  color: #0c4a6e;
}

.status-badge {
  padding: 4px 8px; border-radius: var(--radius-lg); font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.05em;
}
.status-badge.status-pending { background: #fef3c7; color: #92400e; }
.status-badge.status-approved { background: #dcfce7; color: #166534; }
.status-badge.status-rejected { background: #fee2e2; color: #991b1b; }
.status-badge.status-completed { background: #dcfce7; color: #166534; }
.status-badge.status-in_progress { background: #dbeafe; color: #1e40af; }
.status-badge.status-todo { background: #f3f4f6; color: #374151; }

.priority-badge {
  padding: 4px 8px; border-radius: var(--radius-lg); font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.05em;
}
.priority-badge.priority-high { background: #fee2e2; color: #991b1b; }
.priority-badge.priority-medium { background: #fef3c7; color: #92400e; }
.priority-badge.priority-low { background: #dcfce7; color: #166534; }

.desc-cell {
  max-width: 250px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ts-actions {
  display: flex;
  gap: 8px;
}

.btn-approve, .btn-reject {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.btn-approve {
  background: var(--color-primary);
  color: #fff;
}
.btn-approve:hover:not(:disabled) {
  background: #1a4e4f;
}

.btn-reject {
  background: transparent;
  border-color: #ef4444;
  color: #ef4444;
}
.btn-reject:hover:not(:disabled) {
  background: #fef2f2;
}
.btn-approve:disabled, .btn-reject:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-backdrop {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.5); display: flex; align-items: center;
  justify-content: center; z-index: 1000;
}
.modal-content {
  background: #fff; padding: 24px; border-radius: var(--radius-lg);
  width: 100%; max-width: 400px;
  display: flex; flex-direction: column; gap: 16px;
}
.modal-content h3 { margin: 0; font-family: var(--font-display); }
.modal-content p { margin: 0; font-size: 14px; color: var(--color-on-surface-variant); }
.modal-content textarea {
  padding: 8px; border: 1px solid var(--color-outline-variant); border-radius: 4px;
  font-family: var(--font-body); resize: vertical;
}
.modal-actions {
  display: flex; justify-content: flex-end; gap: 8px;
}
.btn-cancel {
  padding: 8px 16px; background: transparent; border: 1px solid var(--color-outline-variant);
  border-radius: 4px; cursor: pointer;
}
.btn-reject-confirm {
  padding: 8px 16px; background: #ef4444; color: #fff; border: none;
  border-radius: 4px; cursor: pointer;
}
.btn-reject-confirm:disabled { opacity: 0.5; }
.text-center { text-align: center; }
.text-right { text-align: right; }
.font-bold { font-weight: 700; }

.hours-badge {
  padding: 4px 10px;
  background: var(--color-surface-container);
  border-radius: 99px;
  font-size: 13px;
  font-weight: 700;
  color: var(--color-primary);
}

/* Detail Modal Styles */
.detail-modal {
  max-width: 800px;
  width: 90%;
  padding: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 24px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-outline-variant);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-info h3 {
  margin: 0 0 4px 0;
  font-family: var(--font-display);
  font-size: 20px;
}

.header-info p {
  margin: 0;
  font-size: 14px;
  color: var(--color-on-surface-variant);
}

.btn-close {
  background: none;
  border: none;
  color: var(--color-on-surface-variant);
  cursor: pointer;
  padding: 4px;
}

.modal-body {
  padding: 24px;
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-section label {
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-on-surface-variant);
}

.detail-table-wrapper {
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.detail-table {
  width: 100%;
  border-collapse: collapse;
}

.detail-table th {
  background: var(--color-surface-container-low);
  padding: 12px;
  text-align: left;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
  border-bottom: 1px solid var(--color-outline-variant);
}

.detail-table td {
  padding: 12px;
  border-bottom: 1px solid var(--color-surface-container-high);
  font-size: 14px;
}

.col-proj { width: 180px; }
.col-desc { line-height: 1.5; }

.project-tag {
  display: inline-block;
  padding: 4px 8px;
  background: var(--color-surface-container);
  border: 1px solid var(--color-outline-variant);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-primary);
}

.total-val {
  font-size: 16px;
  color: var(--color-primary);
}

.overview-box {
  padding: 16px;
  background: var(--color-surface-container-low);
  border-radius: var(--radius-md);
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.modal-footer {
  padding: 20px 24px;
  background: var(--color-surface-container-low);
  border-top: 1px solid var(--color-outline-variant);
}

.footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn-approve-large {
  padding: 10px 20px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-weight: 700;
  cursor: pointer;
}

.btn-reject-large {
  padding: 10px 20px;
  background: #fff;
  color: #dc2626;
  border: 1px solid #dc2626;
  border-radius: var(--radius-md);
  font-weight: 700;
  cursor: pointer;
}

.btn-approve-large:hover { background: #1a4e4f; }
.btn-reject-large:hover { background: #fef2f2; }

@media (max-width: 768px) {
  .profile-header { flex-direction: column; gap: 12px; }
  .profile-tabs { overflow-x: auto; -webkit-overflow-scrolling: touch; flex-wrap: nowrap; white-space: nowrap; }
  .tab-btn { padding: 10px 14px; }
  .tab-content { padding: 14px; }
  .info-grid { grid-template-columns: 1fr; }
  .table-card { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .proj-table { min-width: 540px; }
  .ts-actions { flex-wrap: wrap; gap: 4px; }
  .modal-content { max-width: 100%; width: 100%; }
  .detail-modal { width: 100%; max-width: 100%; }
}
</style>