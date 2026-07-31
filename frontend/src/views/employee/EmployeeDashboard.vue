<template>
  <EmployeeLayout>
    <div class="dashboard-view">

      <!-- Stats strip -->
      <div class="stats-strip">
        <div class="stat-card">
          <div class="stat-icon-wrap">
            <span class="material-symbols-outlined">calendar_today</span>
          </div>
          <div class="stat-body">
            <span class="stat-val">{{ formattedToday }}</span>
            <span class="stat-lbl">Today's Date</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon-wrap accent">
            <span class="material-symbols-outlined">event_available</span>
          </div>
          <div class="stat-body">
            <span class="stat-val">{{ leavesRemaining }}</span>
            <span class="stat-lbl">Leaves Remaining</span>
          </div>
        </div>
      </div>

      <!-- Calendar -->
      <div class="calendar-wrap">
        <CalendarGrid
          :tasks="allTasks"
          :projectMap="projectMap"
          :userMap="{}"
          :leaves="approvedLeaves"
          :holidays="holidays"
          :isAdmin="false"
          :timesheetWeeks="combinedTimesheetWeeks"
          :subtaskDeadlines="subtaskDeadlines"
          @ribbon-click="openTaskDrawer"
          @timesheet-click="onTimesheetClick"
          @subtask-deadline-click="openDeadline"
        />
      </div>

      <!-- Subtask deadline detail -->
      <div v-if="selectedDeadline" class="dl-overlay" @click.self="selectedDeadline = null">
        <div class="dl-card">
          <div class="dl-head">
            <span class="dl-badge" :class="{ late: selectedDeadline.is_overdue, done: selectedDeadline.status === 'completed' }">
              {{ selectedDeadline.status === 'completed' ? 'Completed'
                 : selectedDeadline.is_overdue ? 'Overdue' : 'Subtask deadline' }}
            </span>
            <button class="dl-close" @click="selectedDeadline = null">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <h3 class="dl-title">{{ selectedDeadline.title }}</h3>
          <div class="dl-rows">
            <div class="dl-row">
              <span class="material-symbols-outlined">architecture</span>
              <span><strong>{{ selectedDeadline.project_name }}</strong></span>
            </div>
            <div class="dl-row">
              <span class="material-symbols-outlined">flag</span>
              <span>Stage: {{ selectedDeadline.stage_name }}</span>
            </div>
            <div class="dl-row">
              <span class="material-symbols-outlined">event</span>
              <span>Due {{ formatDeadlineDate(selectedDeadline.due_date) }}</span>
            </div>
          </div>
          <button class="dl-cta" @click="goToTimesheet">
            <span class="material-symbols-outlined">schedule</span> Log hours in my timesheet
          </button>
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
        @subtasks-changed="fetchDashboardData"
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
import { tasksAPI } from '../../api/tasks'
import { leavesAPI } from '../../api/leaves'
import { projectsAPI } from '../../api/projects'
import { holidaysAPI } from '../../api/holidays'
import { stagesAPI } from '../../api/stages'
import { toLocalDateStr } from '../../utils/date'
import { useTimesheetStore } from '../../stores/timesheet'

const router = useRouter()
const timesheetStore = useTimesheetStore()
const user = ref(null)
const leaves = ref([])
const allTasks = ref([])
const projectsList = ref([])
// Was referenced by the template and assigned in fetchDashboardData but never
// declared - every dashboard load threw "holidays is not defined" partway
// through, so holidays never rendered and anything assigned after it (the
// subtask deadlines) was silently skipped.
const holidays = ref([])
const subtaskDeadlines = ref([])
const selectedDeadline = ref(null)

function openDeadline(d) { selectedDeadline.value = d }
function formatDeadlineDate(d) {
  return d ? new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : ''
}
function goToTimesheet() {
  selectedDeadline.value = null
  router.push('/employee/timesheet')
}
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
const todayStr = toLocalDateStr(today)
const formattedToday = today.toLocaleDateString('en-GB', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' })

onMounted(async () => {
  await fetchDashboardData()
})

async function fetchDashboardData() {
  try {
    // Also fetch timesheet data
    timesheetStore.fetchPendingWeeks()
    timesheetStore.fetchMyTimesheets()

    const [uRes, lRes, tRes, pRes, hRes, dRes] = await Promise.all([
      usersAPI.getMe(),
      leavesAPI.getMyLeaves(),
      tasksAPI.getMyTasks(),
      projectsAPI.getProjects().catch(() => ({ data: [] })), // may fail for employee role
      holidaysAPI.getHolidays().catch(() => ({ data: [] })),
      stagesAPI.myDeadlines().catch(() => ({ data: [] })),
    ])

    user.value = uRes.data
    leaves.value = lRes.data
    allTasks.value = tRes.data
    projectsList.value = pRes.data || []
    holidays.value = hRes.data || []
    subtaskDeadlines.value = dRes.data || []
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

// The running paid-leave balance is the single source of truth: it accrues
// +1.5/month and is already drawn down when a leave is approved. (The old
// `leaves_allowed − days taken` maths double-counted and ignored accrual.)
const leavesRemaining = computed(() => Number(user.value?.paid_leave_balance || 0))

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
/* ── Subtask deadline detail ── */
.dl-overlay {
  position: fixed; inset: 0; background: rgba(15,23,42,.5);
  display: flex; align-items: center; justify-content: center; z-index: 1200; padding: 16px;
}
.dl-card {
  background: var(--color-surface); border-radius: var(--radius-xl);
  width: 100%; max-width: 380px; padding: 20px; box-shadow: 0 20px 50px rgba(0,0,0,.25);
}
.dl-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.dl-badge {
  font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: .06em;
  background: #ede9fe; color: #5b21b6; padding: 3px 10px; border-radius: 999px;
}
.dl-badge.late { background: #fee2e2; color: #991b1b; }
.dl-badge.done { background: #dcfce7; color: #166534; }
.dl-close { background: none; border: none; cursor: pointer; color: var(--color-on-surface-variant); padding: 2px; }
.dl-title { font-size: 17px; font-weight: 800; margin: 0 0 14px; color: var(--color-on-surface); }
.dl-rows { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
.dl-row { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--color-on-surface); }
.dl-row .material-symbols-outlined { font-size: 17px; color: var(--color-primary); }
.dl-cta {
  display: flex; align-items: center; justify-content: center; gap: 6px; width: 100%;
  padding: 11px; border: none; border-radius: var(--radius-lg);
  background: var(--color-primary); color: #fff; font-size: 13px; font-weight: 700; cursor: pointer;
}
.dl-cta .material-symbols-outlined { font-size: 17px; }

.dashboard-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ── Stats strip ── */
.stats-strip {
  display: flex;
  gap: 16px;
}

.stat-card {
  flex: 1;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  padding: 18px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: var(--shadow-sm);
}

.stat-icon-wrap {
  width: 42px; height: 42px;
  border-radius: var(--radius-md);
  background: var(--color-surface-dim);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.stat-icon-wrap .material-symbols-outlined {
  font-size: 22px;
  color: var(--color-on-surface-variant);
}
.stat-icon-wrap.accent {
  background: var(--color-primary-light);
}
.stat-icon-wrap.accent .material-symbols-outlined {
  color: var(--color-primary);
}

.stat-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-val {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 700;
  color: var(--color-on-surface);
  line-height: 1.2;
}

.stat-lbl {
  font-size: 11px;
  color: var(--color-on-surface-variant);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

/* ── Calendar ── */
.calendar-wrap {
  flex: 1;
}

@keyframes spin { 100% { transform: rotate(360deg); } }
.spinner { animation: spin 1s linear infinite; }

@media (max-width: 768px) {
  .stats-strip { flex-direction: column; }
  .calendar-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
}
</style>
