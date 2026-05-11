<template>
  <AppLayout>
    <div class="profile-header">
      <div class="profile-info">
        <div class="avatar">
          <img v-if="employee.photo_url" :src="employee.photo_url" alt="Profile" />
          <span v-else class="avatar-initials">{{ initials }}</span>
        </div>
        <div class="profile-details">
          <h1 class="profile-name">{{ employee.name }}</h1>
          <p class="profile-role">{{ employee.role }}</p>
          <p class="profile-email">{{ employee.email }}</p>
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
            <label>Email</label>
            <span>{{ employee.email }}</span>
          </div>
          <div class="info-item">
            <label>Phone</label>
            <span>{{ employee.phone || '—' }}</span>
          </div>
          <div class="info-item">
            <label>Role</label>
            <span>{{ employee.role }}</span>
          </div>
          <div class="info-item">
            <label>Department</label>
            <span>{{ employee.department || '—' }}</span>
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
            <label>Salary</label>
            <span>{{ employee.salary ? `₹${employee.salary.toLocaleString()}` : '—' }}</span>
          </div>
          <div class="info-item">
            <label>Salary Month</label>
            <span>{{ employee.salary_month || '—' }}</span>
          </div>
          <div class="info-item">
            <label>Leaves Allowed</label>
            <span>{{ employee.leaves_allowed }}</span>
          </div>
          <div class="info-item">
            <label>Manager</label>
            <span>{{ employee.manager?.name || '—' }}</span>
          </div>
        </div>
      </div>

      <!-- Timesheet Tab -->
      <div v-if="activeTab === 'timesheet'" class="timesheet-section">
        <div class="table-card">
          <table class="proj-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Check In</th>
                <th>Check Out</th>
                <th>Site Visit</th>
                <th>Site Name</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loadingAttendance">
                <td colspan="5" class="empty-cell">Loading attendance...</td>
              </tr>
              <tr v-else-if="attendance.length === 0">
                <td colspan="5" class="empty-cell">No attendance records.</td>
              </tr>
              <tr v-for="a in attendance" :key="a.id" class="proj-row">
                <td class="mono">{{ formatDate(a.date) }}</td>
                <td class="mono">{{ a.check_in || '—' }}</td>
                <td class="mono">{{ a.check_out || '—' }}</td>
                <td>
                  <span v-if="a.is_site_visit" class="site-badge">Yes</span>
                  <span v-else class="muted">No</span>
                </td>
                <td class="muted">{{ a.site_name || '—' }}</td>
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
                <th>Reason</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loadingLeaves">
                <td colspan="5" class="empty-cell">Loading leave requests...</td>
              </tr>
              <tr v-else-if="leaves.length === 0">
                <td colspan="5" class="empty-cell">No leave requests.</td>
              </tr>
              <tr v-for="l in leaves" :key="l.id" class="proj-row">
                <td class="mono">{{ formatDate(l.start_date) }}</td>
                <td class="mono">{{ formatDate(l.end_date) }}</td>
                <td class="mono">{{ l.days_count }}</td>
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
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import { usersAPI } from '../api/users'
import { attendanceAPI } from '../api/attendance'
import { leavesAPI } from '../api/leaves'
import { tasksAPI } from '../api/tasks'

const route = useRoute()
const employeeId = route.params.id

const employee = ref({})
const attendance = ref([])
const leaves = ref([])
const tasks = ref([])
const loadingAttendance = ref(false)
const loadingLeaves = ref(false)
const loadingTasks = ref(false)
const activeTab = ref('profile')

const tabs = [
  { key: 'profile', label: 'Profile' },
  { key: 'timesheet', label: 'Timesheet' },
  { key: 'leaves', label: 'Leave Requests' },
  { key: 'tasks', label: 'Assigned Tasks' },
]

const initials = computed(() => {
  const name = employee.value.name || ''
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
})

async function fetchEmployee() {
  try {
    const res = await usersAPI.getUser(employeeId)
    employee.value = res.data
  } catch (e) {
    console.error(e)
  }
}

async function fetchAttendance() {
  loadingAttendance.value = true
  try {
    const res = await attendanceAPI.getAttendance({ employee_id: employeeId })
    attendance.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loadingAttendance.value = false
  }
}

async function fetchLeaves() {
  loadingLeaves.value = true
  try {
    // Note: This assumes leaves API can filter by employee_id, but backend may need adjustment
    const res = await leavesAPI.getLeaves()
    leaves.value = res.data.filter(l => l.employee_id == employeeId)
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
    tasks.value = res.data.filter(t => t.assigned_to == employeeId)
  } catch (e) {
    console.error(e)
  } finally {
    loadingTasks.value = false
  }
}

onMounted(async () => {
  await fetchEmployee()
  await fetchAttendance()
  await fetchLeaves()
  await fetchTasks()
})

// Helpers
function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('en-IN')
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
  background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 24px; margin-bottom: 24px; display: flex; align-items: center;
}
.profile-info { display: flex; align-items: center; gap: 16px; }
.avatar {
  width: 64px; height: 64px; border-radius: 50%; background: #0d9488;
  display: flex; align-items: center; justify-content: center;
  font-size: 24px; font-weight: 600; color: #fff;
}
.avatar img {
  width: 100%; height: 100%; border-radius: 50%; object-fit: cover;
}
.avatar-initials { color: #fff; }
.profile-details { flex: 1; }
.profile-name {
  font-size: 24px; font-weight: 600; color: #1c1b1d; margin: 0 0 4px 0;
}
.profile-role {
  font-size: 14px; color: #64748b; margin: 0 0 4px 0;
}
.profile-email {
  font-size: 14px; color: #64748b; margin: 0;
}

.profile-tabs {
  display: flex; gap: 0; margin-bottom: 24px;
  border-bottom: 1px solid #e2e8f0;
}
.tab-btn {
  padding: 12px 24px; background: none; border: none; border-bottom: 2px solid transparent;
  font-family: 'Integral CF', sans-serif; font-size: 14px; font-weight: 500;
  color: #64748b; cursor: pointer; transition: all 0.15s;
}
.tab-btn:hover { color: #334155; }
.tab-btn.active {
  color: #0d9488; border-bottom-color: #0d9488;
}

.tab-content {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
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
  letter-spacing: 0.05em; color: #64748b;
}
.info-item span {
  font-size: 14px; color: #1c1b1d; font-weight: 500;
}

.table-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
  overflow: hidden;
}
.proj-table {
  width: 100%; border-collapse: collapse;
}
.proj-table th {
  padding: 12px 16px; text-align: left; font-family: 'Integral CF', sans-serif;
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.05em; color: #334155; border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}
.proj-table td {
  padding: 12px 16px; border-bottom: 1px solid #f1f5f9;
  font-family: 'Integral CF', sans-serif; font-size: 13px; color: #1c1b1d;
}
.proj-row:hover { background: #f8fafc; }
.proj-name { font-weight: 500; }
.muted { color: #64748b; }
.mono { font-variant-numeric: tabular-nums; }

.empty-cell {
  text-align: center; padding: 48px 16px; color: #64748b;
  font-family: 'Integral CF', sans-serif; font-size: 13px;
}

.site-badge {
  padding: 4px 8px; background: #dbeafe; color: #1e40af;
  border-radius: 12px; font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.05em;
}

.due-status {
  margin-top: 4px;
  font-size: 12px;
  color: #475569;
}
.due-status.late {
  color: #b91c1c;
}
.due-status.dueToday {
  color: #0c4a6e;
}

.status-badge {
  padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.05em;
}
.status-badge.status-pending { background: #fef3c7; color: #92400e; }
.status-badge.status-approved { background: #dcfce7; color: #166534; }
.status-badge.status-rejected { background: #fee2e2; color: #991b1b; }
.status-badge.status-completed { background: #dcfce7; color: #166534; }
.status-badge.status-in_progress { background: #dbeafe; color: #1e40af; }
.status-badge.status-todo { background: #f3f4f6; color: #374151; }

.priority-badge {
  padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.05em;
}
.priority-badge.priority-high { background: #fee2e2; color: #991b1b; }
.priority-badge.priority-medium { background: #fef3c7; color: #92400e; }
.priority-badge.priority-low { background: #dcfce7; color: #166534; }
</style>