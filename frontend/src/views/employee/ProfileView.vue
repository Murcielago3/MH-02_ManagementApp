<template>
  <EmployeeLayout>
    <div class="profile-view">

      <div v-if="loading" class="loading-state">
        <span class="material-symbols-outlined spinner">refresh</span>
      </div>

      <template v-else-if="user">
        <!-- Top section -->
        <div class="top-section">
          <!-- Profile card -->
          <div class="profile-card">
            <div class="photo-container">
              <div class="photo-wrapper" @click="triggerPhotoUpload">
                <img v-if="avatarUrl" :src="avatarUrl" alt="Profile Photo" class="profile-photo" />
                <div v-else class="initials-avatar">{{ userInitials }}</div>
                <div class="photo-overlay">
                  <span class="material-symbols-outlined">photo_camera</span>
                </div>
              </div>
              <input type="file" ref="photoInput" @change="handlePhotoChange" accept="image/*" style="display: none" />
            </div>
            <h2 class="profile-name">{{ user.name }}</h2>
            <p class="profile-designation">{{ user.designation || 'Employee' }}</p>
            <div class="profile-badges">
              <span class="role-badge">{{ formatRole(user.role) }}</span>
              <span class="status-dot" :class="user.is_active ? 'active' : 'inactive'">
                {{ user.is_active ? 'Active' : 'Inactive' }}
              </span>
            </div>
            <button class="edit-profile-btn" @click="showEditModal = true">
              <span class="material-symbols-outlined">edit</span>
              Edit Profile
            </button>
          </div>

          <!-- Details card -->
          <div class="details-card">
            <div class="card-header">
              <h3 class="card-title">Personal Information</h3>
            </div>
            <div class="details-grid">
              <div class="detail-item">
                <span class="detail-label">Studio Email</span>
                <span class="detail-value">{{ user.studio_email || '—' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Personal Email</span>
                <span class="detail-value">{{ user.personal_mail || '—' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Phone Number</span>
                <span class="detail-value">{{ user.phone_number || '—' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Emergency Contact</span>
                <span class="detail-value">{{ user.emergency_contact_number || '—' }} ({{ user.emergency_contact_relationship || '—' }})</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">PAN Number</span>
                <span class="detail-value">{{ user.pan_number || '—' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Aadhar Number</span>
                <span class="detail-value">{{ user.aadhar_number || '—' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Manager</span>
                <span class="detail-value">{{ user.manager_id ? `Manager #${user.manager_id}` : '—' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Joining Date</span>
                <span class="detail-value">{{ formatDate(user.joining_date) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">End Date</span>
                <span class="detail-value">{{ formatDate(user.end_date) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Leaves Allowed</span>
                <span class="detail-value">{{ user.leaves_allowed || 0 }} days / year</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Identity Documents -->
        <div class="details-card documents-card">
          <div class="card-header">
            <h3 class="card-title">Identity Documents</h3>
          </div>
          <div class="doc-body">
            <div v-for="dt in DOC_TYPES" :key="dt.type" class="doc-row">
              <div class="doc-row-left">
                <span class="material-symbols-outlined doc-icon" :class="{ 'has-doc': docFor(dt.type) }">
                  {{ docFor(dt.type) ? 'task' : 'description' }}
                </span>
                <div class="doc-info">
                  <div class="doc-name">{{ dt.label }}</div>
                  <div v-if="docFor(dt.type)" class="doc-sub" :title="docFor(dt.type).filename">{{ docFor(dt.type).filename }}</div>
                  <div v-else class="doc-sub muted">Not uploaded yet</div>
                </div>
              </div>
              <div class="doc-row-right">
                <a v-if="docFor(dt.type)" :href="docUrl(docFor(dt.type))" target="_blank" rel="noopener" class="btn-doc">
                  <span class="material-symbols-outlined">visibility</span> View
                </a>
                <span v-if="docFor(dt.type)" class="locked-tag" title="Contact an admin to change this">
                  <span class="material-symbols-outlined">lock</span> Locked
                </span>
                <button v-else class="btn-doc btn-doc-primary" @click="triggerUpload(dt.type)" :disabled="uploadingType === dt.type">
                  <span class="material-symbols-outlined">{{ uploadingType === dt.type ? 'progress_activity' : 'upload' }}</span>
                  {{ uploadingType === dt.type ? 'Uploading…' : 'Upload' }}
                </button>
              </div>
            </div>
          </div>
          <p class="doc-note">
            <span class="material-symbols-outlined">info</span>
            Once uploaded, a document is locked and can only be changed by an admin. Accepted: PDF or image.
          </p>
          <input ref="fileInput" type="file" accept="application/pdf,image/*" style="display:none" @change="onFileSelected" />
        </div>

        <!-- Activity section -->
        <div class="activity-section">
          <div class="tabs-header">
            <button class="tab-btn" :class="{ active: activeTab === 'tasks' }" @click="activeTab = 'tasks'">Tasks</button>
            <button class="tab-btn" :class="{ active: activeTab === 'timesheets' }" @click="activeTab = 'timesheets'">Timesheets</button>
            <button class="tab-btn" :class="{ active: activeTab === 'attendance' }" @click="activeTab = 'attendance'">Attendance</button>
            <button class="tab-btn" :class="{ active: activeTab === 'leaves' }" @click="activeTab = 'leaves'">Leaves</button>
          </div>

          <div class="tab-content">
            <!-- Tasks Tab -->
            <div v-if="activeTab === 'tasks'">
              <div v-if="tasks.length === 0" class="empty-state">
                <span class="material-symbols-outlined">task_alt</span>
                <p>No recent tasks</p>
              </div>
              <table v-else class="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Title</th>
                    <th>Priority</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="t in tasks" :key="t.id">
                    <td class="mono">{{ formatDateShort(t.date) }}</td>
                    <td>{{ t.title }}</td>
                    <td><span class="priority-badge" :class="t.priority">{{ t.priority }}</span></td>
                    <td>{{ t.status }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Timesheets Tab -->
            <div v-if="activeTab === 'timesheets'">
              <div v-if="timesheets.length === 0" class="empty-state">
                <span class="material-symbols-outlined">pending_actions</span>
                <p>No recent timesheets</p>
              </div>
              <table v-else class="data-table">
                <thead>
                  <tr>
                    <th>Week Starting</th>
                    <th>Description</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="t in timesheets" :key="t.id">
                    <td class="mono">{{ formatDateShort(t.week_start) }}</td>
                    <td class="desc-cell">{{ t.description || '—' }}</td>
                    <td>
                      <span class="status-badge" :class="t.status">{{ t.status }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Attendance Tab -->
            <div v-if="activeTab === 'attendance'">
              <div v-if="attendance.length === 0" class="empty-state">
                <span class="material-symbols-outlined">person_check</span>
                <p>No recent attendance records</p>
              </div>
              <table v-else class="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Check In</th>
                    <th>Check Out</th>
                    <th>Type</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="a in attendance" :key="a.id">
                    <td class="mono">{{ formatDateShort(a.date) }}</td>
                    <td>{{ a.check_in || '—' }}</td>
                    <td>{{ a.check_out || '—' }}</td>
                    <td>
                      <span v-if="a.is_site_visit" class="site-badge">Site: {{ a.site_name }}</span>
                      <span v-else class="type-label">Office</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Leaves Tab -->
            <div v-if="activeTab === 'leaves'">
              <div v-if="leaves.length === 0" class="empty-state">
                <span class="material-symbols-outlined">event_busy</span>
                <p>No leave records found</p>
              </div>
              <table v-else class="data-table">
                <thead>
                  <tr>
                    <th>Date Range</th>
                    <th>Reason</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="l in leaves" :key="l.id">
                    <td class="mono">{{ formatDateShort(l.start_date) }} – {{ formatDateShort(l.end_date) }}</td>
                    <td>{{ l.reason || '—' }}</td>
                    <td><span class="status-badge" :class="l.status">{{ l.status }}</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

      </template>
    </div>

    <!-- Edit Profile Modal -->
    <div v-if="showEditModal" class="modal-overlay">
      <div class="modal-card">
        <div class="modal-header">
          <h3 class="modal-title">Edit Profile</h3>
          <button class="modal-close" @click="showEditModal = false">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <form @submit.prevent="handleUpdateProfile" class="modal-form">
          <div class="form-group">
            <label>Phone Number</label>
            <input v-model="editForm.phone_number" type="text" placeholder="+91 98765 43210" class="field-input" />
          </div>
          <div class="form-group">
            <label>Emergency Contact Number</label>
            <input v-model="editForm.emergency_contact_number" type="text" placeholder="+91 98765 43210" class="field-input" />
          </div>
          <div class="form-group">
            <label>Relationship with Emergency Contact</label>
            <input v-model="editForm.emergency_contact_relationship" type="text" placeholder="Spouse / Parent" class="field-input" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>PAN Number <span class="readonly-note">(View Only)</span></label>
              <input v-model="editForm.pan_number" type="text" readonly class="field-input readonly-input" />
            </div>
            <div class="form-group">
              <label>Aadhar Number <span class="readonly-note">(View Only)</span></label>
              <input v-model="editForm.aadhar_number" type="text" readonly class="field-input readonly-input" />
            </div>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-ghost" @click="showEditModal = false">Cancel</button>
            <button type="submit" class="btn-primary" :disabled="updating">
              {{ updating ? 'Saving…' : 'Save Changes' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </EmployeeLayout>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import EmployeeLayout from '../../components/EmployeeLayout.vue'
import { usersAPI } from '../../api/users'
import { tasksAPI } from '../../api/tasks'
import { weeklyTimesheetsAPI } from '../../api/weekly_timesheets'
import { attendanceAPI } from '../../api/attendance'
import { leavesAPI } from '../../api/leaves'
import { notifySuccess } from '../../stores/notifier'

const loading = ref(true)
const user = ref(null)
const photoInput = ref(null)

const activeTab = ref('tasks')
const tasks = ref([])
const timesheets = ref([])
const attendance = ref([])
const leaves = ref([])

// ── Identity documents (employee uploads own PAN / Aadhaar; locked after) ──
const DOC_TYPES = [
  { type: 'pan', label: 'PAN Card' },
  { type: 'aadhar', label: 'Aadhaar Card' },
]
const documents = ref([])
const uploadingType = ref(null)
const pendingType = ref(null)
const fileInput = ref(null)
function docFor(type) { return documents.value.find(d => d.doc_type === type) }
function docUrl(doc) { return usersAPI.resolveFileUrl(doc.url) }

const showEditModal = ref(false)
const updating = ref(false)
const editForm = ref({
  phone_number: '',
  emergency_contact_number: '',
  emergency_contact_relationship: '',
  pan_number: '',
  aadhar_number: ''
})

onMounted(async () => {
  await fetchUserData()
  fetchTabData(activeTab.value)
})

watch(activeTab, (newTab) => {
  fetchTabData(newTab)
})

const fetchDocuments = async () => {
  if (!user.value?.id) return
  try {
    const res = await usersAPI.getDocuments(user.value.id)
    documents.value = Array.isArray(res.data) ? res.data : []
  } catch (err) {
    console.error('Failed to load documents', err)
  }
}

function triggerUpload(type) {
  pendingType.value = type
  fileInput.value?.click()
}

const onFileSelected = async (e) => {
  const file = e.target.files?.[0]
  const type = pendingType.value
  e.target.value = ''
  if (!file || !type) return
  uploadingType.value = type
  try {
    await usersAPI.uploadDocument(user.value.id, file, type)
    await fetchDocuments()
    notifySuccess('Document uploaded.')
  } catch (err) {
    alert(err.response?.data?.detail || 'Upload failed')
  } finally {
    uploadingType.value = null
    pendingType.value = null
  }
}

const fetchUserData = async () => {
  try {
    const res = await usersAPI.getMe()
    user.value = res.data
    fetchDocuments()
    // Sync edit form
    editForm.value = {
      phone_number: res.data.phone_number || '',
      emergency_contact_number: res.data.emergency_contact_number || '',
      emergency_contact_relationship: res.data.emergency_contact_relationship || '',
      pan_number: res.data.pan_number || '',
      aadhar_number: res.data.aadhar_number || ''
    }
  } catch (err) {
    console.error('Failed to load user', err)
  } finally {
    loading.value = false
  }
}

const fetchTabData = async (tab) => {
  try {
    if (tab === 'tasks' && tasks.value.length === 0) {
      const res = await tasksAPI.getMyTasks()
      tasks.value = res.data.sort((a,b) => new Date(b.date) - new Date(a.date)).slice(0,10)
    } else if (tab === 'timesheets') {
      const res = await weeklyTimesheetsAPI.getMyTimesheets()
      timesheets.value = res.data.sort((a,b) => new Date(b.week_start) - new Date(a.week_start)).slice(0,10)
    } else if (tab === 'attendance' && attendance.value.length === 0) {
      const res = await attendanceAPI.getMyAttendance()
      attendance.value = res.data.sort((a,b) => new Date(b.date) - new Date(a.date)).slice(0,30)
    } else if (tab === 'leaves' && leaves.value.length === 0) {
      const res = await leavesAPI.getMyLeaves()
      leaves.value = res.data.sort((a,b) => new Date(b.start_date) - new Date(a.start_date))
    }
  } catch (err) {
    console.error(`Failed to load ${tab}`, err)
  }
}

const triggerPhotoUpload = () => {
  if (photoInput.value) photoInput.value.click()
}

const handlePhotoChange = async (e) => {
  if (!e.target.files.length) return
  const file = e.target.files[0]

  try {
    const res = await usersAPI.uploadPhoto(user.value.id, file)
    user.value = res.data
    notifySuccess('Profile photo updated.')
  } catch (err) {
    console.error(err)
  }
}
const handleUpdateProfile = async () => {
  updating.value = true
  try {
    const res = await usersAPI.updateUser(user.value.id, editForm.value)
    user.value = res.data
    showEditModal.value = false
    notifySuccess('Profile updated.')
  } catch (err) {
    console.error(err)
  } finally {
    updating.value = false
  }
}
// Helpers
const avatarUrl = computed(() => {
  return user.value?.photo_url ? usersAPI.resolveFileUrl(user.value.photo_url) : null
})

const userInitials = computed(() => {
  const name = user.value?.name || 'Employee'
  return name.split(' ').map(p => p[0]).join('').toUpperCase().slice(0,2)
})

const formatRole = (role) => {
  if (!role) return ''
  return role.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
}

const formatDate = (d) => {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'long', year: 'numeric' })
}

const formatDateShort = (d) => {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

const formatCurrency = (val) => {
  if (!val) return '—'
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val)
}
</script>

<style scoped>
.profile-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Loading */
.loading-state {
  display: flex;
  justify-content: center;
  padding: 80px;
}
.spinner {
  font-size: 32px;
  color: var(--color-on-surface-variant);
  animation: spin 1s linear infinite;
}

/* ── Top section ── */
.top-section {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 20px;
}
@media (max-width: 768px) {
  .top-section { grid-template-columns: 1fr; }
}

/* Profile card */
.profile-card {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  padding: 32px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 8px;
  box-shadow: var(--shadow-sm);
}

.photo-container { margin-bottom: 8px; }
.photo-wrapper {
  width: 112px; height: 112px;
  border-radius: 50%;
  position: relative;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  background: var(--color-primary-light);
}
.profile-photo { width: 100%; height: 100%; object-fit: cover; }
.initials-avatar {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  font-size: 38px; font-weight: 800;
  color: var(--color-primary);
  font-family: var(--font-display);
}
.photo-overlay {
  position: absolute; bottom: 0; left: 0; right: 0; height: 36px;
  background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center;
  opacity: 0;
  transition: opacity var(--transition);
}
.photo-wrapper:hover .photo-overlay { opacity: 1; }
.photo-overlay span { color: #fff; font-size: 18px; }

.profile-name {
  font-family: var(--font-display);
  font-size: 20px; margin: 4px 0 0 0;
  color: var(--color-on-surface);
  letter-spacing: -0.01em;
}
.profile-designation {
  font-size: 13px;
  color: var(--color-on-surface-variant);
  margin: 0;
}
.profile-badges {
  display: flex; align-items: center; gap: 8px;
  flex-wrap: wrap; justify-content: center;
  margin-top: 4px;
}
.role-badge {
  display: inline-block;
  padding: 3px 10px;
  background: var(--color-primary-light);
  color: var(--color-primary);
  border-radius: var(--radius-full);
  font-size: 11px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.04em;
}
.status-dot {
  display: inline-block;
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-size: 11px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.04em;
}
.status-dot.active { background: #dcfce7; color: #15803d; }
.status-dot.inactive { background: #fee2e2; color: #b91c1c; }

.edit-profile-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  font-size: 13px; font-weight: 600;
  color: var(--color-primary);
  cursor: pointer;
  transition: all var(--transition);
  margin-top: 8px;
}
.edit-profile-btn:hover {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}
.edit-profile-btn .material-symbols-outlined { font-size: 16px; }

/* Details card */
.details-card {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}
.card-header {
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--color-outline);
  background: var(--color-surface-dim);
}
.card-title {
  font-family: var(--font-display);
  font-size: 14px; font-weight: 700;
  color: var(--color-on-surface);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  padding: 0;
}
@media (max-width: 640px) {
  .details-grid { grid-template-columns: 1fr; }
}
.detail-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 16px 24px;
  border-bottom: 1px solid var(--color-outline);
}
.detail-item:nth-child(odd) { border-right: 1px solid var(--color-outline); }
.detail-label {
  font-size: 11px;
  color: var(--color-on-surface-variant);
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 0.04em;
}
.detail-value {
  font-size: 14px;
  color: var(--color-on-surface);
  font-weight: 500;
}

/* ── Identity documents ── */
.documents-card { padding-bottom: 8px; }
.doc-body { display: flex; flex-direction: column; }
.doc-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 24px;
  border-bottom: 1px solid var(--color-outline);
}
.doc-row-left { display: flex; align-items: center; gap: 12px; min-width: 0; }
.doc-icon {
  font-size: 24px;
  color: var(--color-on-surface-variant);
  background: var(--color-surface-dim);
  border-radius: var(--radius-md);
  padding: 7px;
}
.doc-icon.has-doc { color: var(--color-primary); background: var(--color-primary-light); }
.doc-info { min-width: 0; }
.doc-name { font-size: 14px; font-weight: 600; color: var(--color-on-surface); }
.doc-sub {
  font-size: 12px;
  color: var(--color-on-surface-variant);
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.doc-sub.muted { font-style: italic; }
.doc-row-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.btn-doc {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 7px 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-on-surface);
  cursor: pointer;
  text-decoration: none;
  transition: all var(--transition);
}
.btn-doc:hover:not(:disabled) { border-color: var(--color-primary); color: var(--color-primary); }
.btn-doc:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-doc .material-symbols-outlined { font-size: 15px; }
.btn-doc-primary { background: var(--color-primary); border-color: var(--color-primary); color: #fff; }
.btn-doc-primary:hover:not(:disabled) { background: #1a5657; border-color: #1a5657; color: #fff; }
.locked-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border-radius: var(--radius-md);
  background: var(--color-surface-dim);
  color: var(--color-on-surface-variant);
  font-size: 12px;
  font-weight: 600;
}
.locked-tag .material-symbols-outlined { font-size: 14px; }
.doc-note {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  padding: 14px 24px;
  font-size: 12px;
  color: var(--color-on-surface-variant);
}
.doc-note .material-symbols-outlined { font-size: 16px; }

/* ── Activity section ── */
.activity-section {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.tabs-header {
  display: flex;
  border-bottom: 1px solid var(--color-outline);
  background: var(--color-surface-dim);
}
.tab-btn {
  flex: 1;
  padding: 14px 16px;
  background: none; border: none;
  border-bottom: 2px solid transparent;
  font-family: var(--font-body);
  font-size: 13px; font-weight: 600;
  color: var(--color-on-surface-variant);
  cursor: pointer;
  transition: all var(--transition);
}
.tab-btn:hover {
  background: var(--color-background);
  color: var(--color-on-surface);
}
.tab-btn.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
  background: var(--color-surface);
}

.tab-content { overflow-x: auto; }

.empty-state {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 56px 0;
  gap: 12px;
  color: var(--color-on-surface-variant);
}
.empty-state .material-symbols-outlined { font-size: 36px; color: var(--color-outline); }
.empty-state p { margin: 0; font-size: 14px; }

/* Table */
.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  text-align: left;
  padding: 12px 20px;
  font-size: 11px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.05em;
  color: var(--color-on-surface-variant);
  border-bottom: 1px solid var(--color-outline);
  background: var(--color-surface-dim);
}
.data-table td {
  padding: 14px 20px;
  font-size: 13.5px;
  color: var(--color-on-surface);
  border-bottom: 1px solid var(--color-outline);
}
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: var(--color-surface-dim); }

.mono { font-variant-numeric: tabular-nums; }

.desc-cell {
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.priority-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-md);
  font-size: 11px; font-weight: 700;
  text-transform: uppercase;
}
.priority-badge.high { background: #fee2e2; color: #b91c1c; }
.priority-badge.medium { background: #fef3c7; color: #b45309; }
.priority-badge.low { background: #dcfce7; color: #15803d; }

.site-badge {
  display: inline-block;
  padding: 2px 8px;
  background: var(--color-primary-light);
  color: var(--color-primary);
  border-radius: var(--radius-md);
  font-size: 12px; font-weight: 600;
}
.type-label { font-size: 13px; color: var(--color-on-surface-variant); }

.status-badge {
  display: inline-block;
  padding: 3px 9px;
  border-radius: var(--radius-full);
  font-size: 11px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.04em;
}
.status-badge.pending { background: #fef3c7; color: #b45309; }
.status-badge.submitted { background: #dbeafe; color: #1d4ed8; }
.status-badge.approved { background: #dcfce7; color: #15803d; }
.status-badge.rejected { background: #fee2e2; color: #dc2626; }

/* ── Modal ── */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}
.modal-card {
  background: var(--color-surface);
  width: 100%; max-width: 520px;
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0,0,0,0.15);
}
.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-outline);
  display: flex; justify-content: space-between; align-items: center;
  background: var(--color-surface-dim);
}
.modal-title { margin: 0; font-family: var(--font-display); font-size: 16px; color: var(--color-on-surface); }
.modal-close {
  background: none; border: none; cursor: pointer;
  color: var(--color-on-surface-variant);
  width: 30px; height: 30px;
  display: flex; align-items: center; justify-content: center;
  border-radius: var(--radius-md);
  transition: background var(--transition);
}
.modal-close:hover { background: var(--color-outline); }
.modal-close .material-symbols-outlined { font-size: 18px; }

.modal-form { padding: 24px; display: flex; flex-direction: column; gap: 18px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-group label {
  font-size: 12px; font-weight: 700;
  color: var(--color-on-surface-variant);
  text-transform: uppercase; letter-spacing: 0.04em;
}
.readonly-note { font-weight: 400; text-transform: none; letter-spacing: 0; opacity: .7; }
.field-input {
  padding: 10px 12px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  font-family: var(--font-body); font-size: 14px;
  color: var(--color-on-surface);
  background: var(--color-surface);
  transition: border-color var(--transition);
}
.field-input:focus { outline: none; border-color: var(--color-primary); box-shadow: 0 0 0 3px rgba(40,116,117,.10); }
.readonly-input { background: var(--color-surface-dim); color: var(--color-on-surface-variant); cursor: not-allowed; }

.modal-actions {
  display: flex; justify-content: flex-end; gap: 12px;
  padding-top: 8px;
}
.btn-ghost {
  padding: 9px 18px;
  background: none;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  font-family: var(--font-body); font-size: 13px; font-weight: 600;
  color: var(--color-on-surface-variant);
  cursor: pointer;
  transition: all var(--transition);
}
.btn-ghost:hover { background: var(--color-surface-dim); }
.btn-primary {
  padding: 9px 20px;
  background: var(--color-primary); color: #fff;
  border: none; border-radius: var(--radius-md);
  font-family: var(--font-body); font-size: 13px; font-weight: 600;
  cursor: pointer;
  transition: background var(--transition);
}
.btn-primary:hover:not(:disabled) { background: #1a5657; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

@keyframes spin { 100% { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .profile-layout { flex-direction: column; }
  .profile-sidebar { width: 100%; }
  .profile-main { min-width: 0; }
  .info-grid { grid-template-columns: 1fr; }
  .doc-grid { grid-template-columns: 1fr; }
  .modal { max-width: 100%; width: 100%; }
  .modal-backdrop { padding: 8px; }
}
</style>
