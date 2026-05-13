<template>
  <EmployeeLayout>
    <div class="profile-view">
      
      <div v-if="loading" class="loading-state">
        <span class="material-symbols-outlined spinner">refresh</span>
      </div>

      <template v-else-if="user">
        <div class="top-section">
          <!-- Left: Profile Card -->
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
            <div class="profile-info">
              <h2 class="profile-name">{{ user.name }}</h2>
              <p class="profile-designation">{{ user.designation || 'Employee' }}</p>
              <div class="profile-actions">
                <span class="role-badge">{{ formatRole(user.role) }}</span>
                <button class="edit-profile-btn" @click="showEditModal = true">
                  <span class="material-symbols-outlined">edit</span>
                  Edit Profile
                </button>
              </div>
            </div>
          </div>

          <!-- Right: Details Grid -->
          <div class="details-card">
            <h3 class="card-title">Personal Information</h3>
            <div class="details-grid">
              <div class="detail-item">
                <span class="label">Studio Email</span>
                <span class="value">{{ user.studio_email || '—' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Personal Email</span>
                <span class="value">{{ user.personal_mail || '—' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Phone Number</span>
                <span class="value">{{ user.phone_number || '—' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Emergency Contact</span>
                <span class="value">{{ user.emergency_contact_number || '—' }} ({{ user.emergency_contact_relationship || '—' }})</span>
              </div>
              <div class="detail-item">
                <span class="label">PAN Number</span>
                <span class="value">{{ user.pan_number || '—' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Aadhar Number</span>
                <span class="value">{{ user.aadhar_number || '—' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Manager</span>
                <span class="value">{{ user.manager_id ? `Manager #${user.manager_id}` : '—' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Joining Date</span>
                <span class="value">{{ formatDate(user.joining_date) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">End Date</span>
                <span class="value">{{ formatDate(user.end_date) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Stats Row -->
        <div class="stats-row">
          <div class="stat-pill">
            <span class="material-symbols-outlined icon">event_available</span>
            <div class="stat-text">
              <span class="stat-val">{{ user.leaves_allowed || 0 }}</span>
              <span class="stat-lbl">Leaves Allowed</span>
            </div>
          </div>
          <div class="stat-pill">
            <span class="material-symbols-outlined icon">calendar_month</span>
            <div class="stat-text">
              <span class="stat-val">{{ formatDateShort(user.joining_date) }}</span>
              <span class="stat-lbl">Joining Date</span>
            </div>
          </div>

          <div class="stat-pill">
            <span class="material-symbols-outlined icon" :class="{'text-green': user.is_active, 'text-red': !user.is_active}">
              {{ user.is_active ? 'check_circle' : 'cancel' }}
            </span>
            <div class="stat-text">
              <span class="stat-val">{{ user.is_active ? 'Active' : 'Inactive' }}</span>
              <span class="stat-lbl">Status</span>
            </div>
          </div>
        </div>

        <!-- Activity Tabs -->
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
              <div v-if="tasks.length === 0" class="empty-state">No recent tasks</div>
              <table v-else class="data-table">
                <thead><tr><th>Date</th><th>Title</th><th>Priority</th><th>Status</th></tr></thead>
                <tbody>
                  <tr v-for="t in tasks" :key="t.id">
                    <td>{{ formatDateShort(t.date) }}</td>
                    <td>{{ t.title }}</td>
                    <td><span class="priority-badge" :class="t.priority">{{ t.priority }}</span></td>
                    <td>{{ t.status }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Timesheets Tab -->
            <div v-if="activeTab === 'timesheets'">
              <div v-if="timesheets.length === 0" class="empty-state">No recent timesheets</div>
              <table v-else class="data-table">
                <thead><tr><th>Week Starting</th><th>Description</th><th>Status</th></tr></thead>
                <tbody>
                  <tr v-for="t in timesheets" :key="t.id">
                    <td>{{ formatDateShort(t.week_start) }}</td>
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
              <div v-if="attendance.length === 0" class="empty-state">No recent attendance</div>
              <table v-else class="data-table">
                <thead><tr><th>Date</th><th>Check In</th><th>Check Out</th><th>Type</th></tr></thead>
                <tbody>
                  <tr v-for="a in attendance" :key="a.id">
                    <td>{{ formatDateShort(a.date) }}</td>
                    <td>{{ a.check_in || '—' }}</td>
                    <td>{{ a.check_out || '—' }}</td>
                    <td>
                      <span v-if="a.is_site_visit" class="site-badge">Site: {{ a.site_name }}</span>
                      <span v-else>Office</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Leaves Tab -->
            <div v-if="activeTab === 'leaves'">
              <div v-if="leaves.length === 0" class="empty-state">No recent leaves</div>
              <table v-else class="data-table">
                <thead><tr><th>Date Range</th><th>Reason</th><th>Status</th></tr></thead>
                <tbody>
                  <tr v-for="l in leaves" :key="l.id">
                    <td>{{ formatDateShort(l.start_date) }} - {{ formatDateShort(l.end_date) }}</td>
                    <td>{{ l.reason || '—' }}</td>
                    <td>{{ l.status }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

      </template>
    </div>
    <!-- Edit Profile Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal-card">
        <div class="modal-header">
          <h3>Edit Profile</h3>
          <button class="close-btn" @click="showEditModal = false">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <form @submit.prevent="handleUpdateProfile" class="modal-form">
          <div class="form-group">
            <label>Phone Number</label>
            <input v-model="editForm.phone_number" type="text" placeholder="+91 98765 43210" />
          </div>
          <div class="form-group">
            <label>Emergency Contact Number</label>
            <input v-model="editForm.emergency_contact_number" type="text" placeholder="+91 98765 43210" />
          </div>
          <div class="form-group">
            <label>Relationship with Emergency Contact</label>
            <input v-model="editForm.emergency_contact_relationship" type="text" placeholder="Spouse / Parent" />
          </div>
          <div class="form-group-row">
            <div class="form-group">
              <label>PAN Number (View Only)</label>
              <input v-model="editForm.pan_number" type="text" readonly class="readonly-input" />
            </div>
            <div class="form-group">
              <label>Aadhar Number (View Only)</label>
              <input v-model="editForm.aadhar_number" type="text" readonly class="readonly-input" />
            </div>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showEditModal = false">Cancel</button>
            <button type="submit" class="btn-primary" :disabled="updating">
              {{ updating ? 'Saving...' : 'Save Changes' }}
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

const loading = ref(true)
const user = ref(null)
const photoInput = ref(null)

const activeTab = ref('tasks')
const tasks = ref([])
const timesheets = ref([])
const attendance = ref([])
const leaves = ref([])

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

const fetchUserData = async () => {
  try {
    const res = await usersAPI.getMe()
    user.value = res.data
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
    alert("Profile photo updated successfully!")
  } catch (err) {
    alert("Failed to upload photo: " + (err.response?.data?.detail || err.message))
  }
}
const handleUpdateProfile = async () => {
  updating.value = true
  try {
    const res = await usersAPI.updateUser(user.value.id, editForm.value)
    user.value = res.data
    showEditModal.value = false
    alert("Profile updated successfully!")
  } catch (err) {
    alert("Failed to update profile: " + (err.response?.data?.detail || err.message))
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
  max-width: 1000px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.loading-state {
  display: flex;
  justify-content: center;
  padding: 64px;
}
.spinner {
  font-size: 32px;
  color: var(--color-outline);
  animation: spin 1s linear infinite;
}

/* Top Section */
.top-section {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 24px;
}

@media (max-width: 768px) {
  .top-section { grid-template-columns: 1fr; }
}

.profile-card {
  background: var(--color-surface);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 32px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.photo-container {
  margin-bottom: 24px;
}

.photo-wrapper {
  width: 120px;
  height: 120px;
  border-radius: var(--radius-full);
  position: relative;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  background: var(--color-primary-container);
}

.profile-photo {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.initials-avatar {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  font-weight: 800;
  color: var(--color-primary);
  font-family: var(--font-display);
}

.photo-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.photo-wrapper:hover .photo-overlay {
  opacity: 1;
}

.photo-overlay span {
  color: white;
  font-size: 20px;
}

.profile-name {
  font-family: var(--font-display);
  font-size: 24px;
  margin: 0 0 4px 0;
  color: var(--color-on-surface);
}

.profile-designation {
  font-size: 14px;
  color: var(--color-on-surface-variant);
  margin: 0 0 16px 0;
}

.role-badge {
  display: inline-block;
  padding: 4px 12px;
  background: rgba(40, 116, 117, 0.1);
  color: var(--color-primary);
  border-radius: 12px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}

.profile-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
  margin-top: 8px;
}

.edit-profile-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline-variant);
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-primary);
  cursor: pointer;
  transition: all 0.2s;
}
.edit-profile-btn:hover {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}
.edit-profile-btn .material-symbols-outlined { font-size: 16px; }

.details-card {
  background: var(--color-surface);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 24px;
}

.card-title {
  font-family: var(--font-display);
  font-size: 18px;
  margin: 0 0 24px 0;
  color: var(--color-on-surface);
}

.details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (max-width: 640px) {
  .details-grid { grid-template-columns: 1fr; }
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item .label {
  font-size: 12px;
  color: var(--color-outline);
  text-transform: uppercase;
  font-weight: 600;
}

.detail-item .value {
  font-size: 14px;
  color: var(--color-on-surface);
  font-weight: 500;
}

/* Stats Row */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

@media (max-width: 768px) {
  .stats-row { grid-template-columns: repeat(2, 1fr); }
}

.stat-pill {
  background: var(--color-surface);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-md);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-pill .icon {
  font-size: 24px;
  color: var(--color-primary);
}

.stat-text {
  display: flex;
  flex-direction: column;
}

.stat-val {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--color-on-surface);
}

.stat-lbl {
  font-size: 11px;
  color: var(--color-on-surface-variant);
  text-transform: uppercase;
}

/* Activity Section */
.activity-section {
  background: var(--color-surface);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.tabs-header {
  display: flex;
  border-bottom: 1px solid var(--color-outline-variant);
  background: var(--color-surface-container-lowest);
}

.tab-btn {
  flex: 1;
  padding: 16px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-on-surface-variant);
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: var(--color-surface-container);
}

.tab-btn.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
  background: var(--color-surface);
}

.tab-content {
  padding: 0;
}

.empty-state {
  padding: 48px;
  text-align: center;
  color: var(--color-outline);
  font-size: 14px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  text-align: left;
  padding: 12px 24px;
  font-size: 12px;
  text-transform: uppercase;
  color: var(--color-outline);
  border-bottom: 1px solid var(--color-outline-variant);
  background: var(--color-surface-container-lowest);
}

.data-table td {
  padding: 16px 24px;
  font-size: 14px;
  color: var(--color-on-surface);
  border-bottom: 1px solid var(--color-outline-variant);
}

.priority-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}
.priority-badge.high { background: #fee2e2; color: #b91c1c; }
.priority-badge.medium { background: #fef3c7; color: #b45309; }
.priority-badge.low { background: #dcfce7; color: #15803d; }

.site-badge {
  padding: 2px 8px;
  background: rgba(40, 116, 117, 0.1);
  color: var(--color-primary);
  border-radius: 4px;
  font-size: 12px;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}
.status-badge.pending { background: #fee2e2; color: #ef4444; }
.status-badge.submitted { background: #fef3c7; color: #d97706; }
.status-badge.approved { background: #dcfce7; color: #15803d; }
.status-badge.rejected { background: #fee2e2; color: #ef4444; }

.desc-cell {
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}
.modal-card {
  background: var(--color-surface);
  width: 100%;
  max-width: 500px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1);
}
.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-outline-variant);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.modal-header h3 { margin: 0; font-family: var(--font-display); font-size: 18px; }
.close-btn { background: none; border: none; cursor: pointer; color: var(--color-outline); }

.modal-form { padding: 24px; display: flex; flex-direction: column; gap: 20px; }
.form-group { display: flex; flex-direction: column; gap: 8px; }
.form-group-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-group label { font-size: 12px; font-weight: 700; color: var(--color-outline); text-transform: uppercase; }
.form-group input {
  padding: 10px;
  border: 1px solid var(--color-outline-variant);
  border-radius: 8px;
  font-family: var(--font-body);
  font-size: 14px;
}
.form-group input:focus { outline: none; border-color: var(--color-primary); }

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
}
.btn-secondary { padding: 10px 20px; background: none; border: 1px solid var(--color-outline-variant); border-radius: 8px; cursor: pointer; }
.btn-primary { padding: 10px 20px; background: var(--color-primary); color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.text-green { color: #15803d !important; }
.text-red { color: #b91c1c !important; }

@keyframes spin { 100% { transform: rotate(360deg); } }
</style>
