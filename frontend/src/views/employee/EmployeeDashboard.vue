<template>
  <EmployeeLayout>
    <div class="dashboard-view">
      
      <!-- Top Strip Stats -->
      <div class="stats-strip">
        <div class="stat-pill date-pill">
          <span class="material-symbols-outlined icon">calendar_today</span>
          <div class="stat-text">
            <span class="stat-val">{{ formattedToday }}</span>
            <span class="stat-lbl">Today's Date</span>
          </div>
        </div>
        
        <div class="stat-pill leave-pill">
          <span class="material-symbols-outlined icon">event_available</span>
          <div class="stat-text">
            <span class="stat-val">{{ leavesRemaining }}</span>
            <span class="stat-lbl">Leaves Remaining</span>
          </div>
        </div>
      </div>

      <!-- Main Content -->
      <div class="main-content">
        <div class="calendar-column">
          <CalendarGrid
            :tasks="allTasks"
            :projectMap="projectMap"
            :userMap="{}"
            :leaves="approvedLeaves"
            :isAdmin="false"
            :timesheetWeeks="combinedTimesheetWeeks"
            @ribbon-click="openTaskDrawer"
            @timesheet-click="onTimesheetClick"
          />
        </div>
      </div>

      <!-- Task Detail Drawer -->
      <TaskDetailDrawer
        v-if="selectedTask"
        :task="selectedTask"
        :projectMap="projectMap"
        :userMap="{}"
        :isAdmin="false"
        :loading="!!statusUpdating"
        @close="selectedTask = null"
        @update-status="onDrawerStatusUpdate"
      />

      <!-- Toast -->
      <ToastNotification
        v-if="toastMsg"
        :message="toastMsg"
        :type="toastType"
        @done="toastMsg = ''"
      />

    </div>
  </EmployeeLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import EmployeeLayout from '../../components/EmployeeLayout.vue'
import CalendarGrid from '../../components/CalendarGrid.vue'
import TaskDetailDrawer from '../../components/TaskDetailDrawer.vue'
import ToastNotification from '../../components/ToastNotification.vue'
import { usersAPI } from '../../api/users'
import { attendanceAPI } from '../../api/attendance'
import { tasksAPI } from '../../api/tasks'
import { leavesAPI } from '../../api/leaves'
import { projectsAPI } from '../../api/projects'
import { countWorkingDays } from '../../stores/estimate'
import { useTimesheetStore } from '../../stores/timesheet'

const router = useRouter()
const timesheetStore = useTimesheetStore()
const user = ref(null)
const leaves = ref([])
const allTasks = ref([])
const projectsList = ref([])
const statusUpdating = ref(null)
const selectedTask = ref(null)

// Toast
const toastMsg = ref('')
const toastType = ref('success')

function showToast(msg, type = 'success') {
  toastMsg.value = msg
  toastType.value = type
}

// Date logic
const today = new Date()
const todayStr = today.toISOString().split('T')[0]
const formattedToday = today.toLocaleDateString('en-GB', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' })

onMounted(async () => {
  await fetchDashboardData()
})

async function fetchDashboardData() {
  try {
    // Also fetch timesheet data
    timesheetStore.fetchPendingWeeks()
    timesheetStore.fetchMyTimesheets()

    const [uRes, aRes, lRes, tRes, pRes] = await Promise.all([
      usersAPI.getMe(),
      attendanceAPI.getMyAttendance(),
      leavesAPI.getMyLeaves(),
      tasksAPI.getMyTasks(),
      projectsAPI.getProjects().catch(() => ({ data: [] })), // may fail for employee role
    ])
    
    user.value = uRes.data
    leaves.value = lRes.data
    allTasks.value = tRes.data
    projectsList.value = pRes.data || []
  } catch (err) {
    console.error('Failed to load dashboard data', err)
  }
}

// ── Computed ──
const approvedLeaves = computed(() => leaves.value.filter(l => l.status === 'approved'))

const combinedTimesheetWeeks = computed(() => {
  const map = {}
  timesheetStore.pendingWeeks.forEach(pw => {
    map[pw.week_start] = { week_start: pw.week_start, status: pw.status }
  })
  timesheetStore.submittedTimesheets.forEach(ts => {
    // submitted timesheets overwrite pending if same week
    map[ts.week_start] = { week_start: ts.week_start, status: ts.status }
  })
  return Object.values(map)
})

const projectMap = computed(() => {
  const map = {}
  for (const p of projectsList.value) {
    map[p.id] = { name: p.name, color: p.color || '#287475' }
  }
  return map
})

const leavesRemaining = computed(() => {
  if (!user.value) return 0
  const allowed = user.value.leaves_allowed || 0
  const used = approvedLeaves.value.reduce((acc, l) => acc + countWorkingDays(l.start_date, l.end_date), 0)
  return Math.max(0, allowed - used)
})

// ── Task interactions ──
function openTaskDrawer(task) {
  selectedTask.value = task
}

function onTimesheetClick(weekObj) {
  timesheetStore.selectWeek(weekObj)
  router.push('/employee/timesheet')
}

async function onDrawerStatusUpdate(taskId, status) {
  await updateTaskStatus(taskId, status)
}

async function updateTaskStatus(taskId, status) {
  statusUpdating.value = taskId
  try {
    const res = await tasksAPI.updateTaskStatus(taskId, status)
    const index = allTasks.value.findIndex(t => t.id === taskId)
    if (index !== -1) {
      allTasks.value[index] = { ...allTasks.value[index], ...res.data }
    }
    if (selectedTask.value?.id === taskId) {
      selectedTask.value = { ...selectedTask.value, status }
    }
    showToast(status === 'completed' ? 'Task marked complete!' : 'Task updated')
  } catch (err) {
    showToast('Failed to update task status', 'error')
  } finally {
    statusUpdating.value = null
  }
}
</script>

<style scoped>
.dashboard-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ── Top Strip ── */
.stats-strip {
  display: flex;
  gap: 16px;
}
.stat-pill {
  flex: 1;
  background: var(--color-surface);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-pill .icon {
  font-size: 28px;
  color: var(--color-outline);
}

.stat-pill.checkin-pill.active {
  background: rgba(40, 116, 117, 0.05);
  border-color: var(--color-primary);
}
.stat-pill.checkin-pill.active .icon { color: var(--color-primary); }

.stat-text {
  display: flex;
  flex-direction: column;
}

.stat-val {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  color: var(--color-on-surface);
}

.stat-lbl {
  font-size: 11px;
  color: var(--color-on-surface-variant);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* ── Main Layout ── */
.main-content {
  display: block;
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.column-title {
  font-family: 'Integral CF', sans-serif;
  font-size: 18px;
  color: var(--color-on-surface);
  margin: 0;
}

@keyframes spin { 100% { transform: rotate(360deg); } }
.spinner { animation: spin 1s linear infinite; }
</style>
