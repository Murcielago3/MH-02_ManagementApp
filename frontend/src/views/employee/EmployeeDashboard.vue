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
        
        <div class="stat-pill checkin-pill" :class="{ active: checkedInToday }">
          <span class="material-symbols-outlined icon">{{ checkedInToday ? 'how_to_reg' : 'sensor_door' }}</span>
          <div class="stat-text">
            <span class="stat-val">{{ checkInText }}</span>
            <span class="stat-lbl">Attendance</span>
          </div>
        </div>

        <div class="stat-pill leave-pill">
          <span class="material-symbols-outlined icon">event_available</span>
          <div class="stat-text">
            <span class="stat-val">{{ leavesRemaining }}</span>
            <span class="stat-lbl">Leaves Remaining</span>
          </div>
        </div>

        <div class="stat-pill tasks-pill">
          <span class="material-symbols-outlined icon">task</span>
          <div class="stat-text">
            <span class="stat-val">{{ pendingTasksToday }}</span>
            <span class="stat-lbl">Pending Tasks Today</span>
          </div>
        </div>
      </div>

      <!-- Main Columns -->
      <div class="main-content">
        
        <!-- Left: Calendar -->
        <div class="calendar-column">
          <CalendarGrid
            :tasks="allTasks"
            :projectMap="projectMap"
            :userMap="{}"
            :leaves="approvedLeaves"
            :isAdmin="false"
            @ribbon-click="openTaskDrawer"
          />
        </div>

        <!-- Right: Today's Tasks -->
        <div class="today-tasks-column">
          <div class="column-header">
            <h2 class="column-title">Today's Tasks</h2>
          </div>
          
          <div class="today-tasks-list">
            <div v-if="loadingTasks" class="loading-state">
              <span class="material-symbols-outlined spinner">refresh</span>
            </div>
            
            <div v-else-if="todayTasks.length === 0" class="empty-state">
              <span class="material-symbols-outlined">celebration</span>
              <p>No tasks assigned for today 🎉</p>
            </div>

            <div v-else class="task-card" v-for="task in todayTasks" :key="'today-'+task.id" :class="task.status">
              <div class="task-header">
                <span class="priority-badge" :class="task.priority">{{ task.priority }}</span>
                <span class="duration-badge" v-if="task.duration_hours">{{ task.duration_hours }} hrs</span>
              </div>
              <h4 class="task-title">{{ task.title }}</h4>
              <p v-if="task.project_id && projectMap[task.project_id]" class="task-project">
                <span class="project-dot" :style="{ background: projectMap[task.project_id].color }"></span>
                {{ projectMap[task.project_id].name }}
              </p>
              
              <div class="task-actions">
                <button 
                  v-if="task.status === 'pending'" 
                  class="btn-action start" 
                  @click="updateTaskStatus(task.id, 'in-progress')"
                  :disabled="statusUpdating === task.id"
                >Start</button>
                <button 
                  v-if="task.status === 'in-progress'" 
                  class="btn-action complete" 
                  @click="updateTaskStatus(task.id, 'completed')"
                  :disabled="statusUpdating === task.id"
                >Complete</button>
                <span v-if="task.status === 'completed'" class="completed-text">
                  <span class="material-symbols-outlined">check_circle</span> Done
                </span>
              </div>
            </div>
          </div>
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

const user = ref(null)
const attendanceToday = ref(null)
const leaves = ref([])
const allTasks = ref([])
const projectsList = ref([])
const loadingTasks = ref(true)
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
    const [uRes, aRes, lRes, tRes, pRes] = await Promise.all([
      usersAPI.getMe(),
      attendanceAPI.getMyAttendance(),
      leavesAPI.getMyLeaves(),
      tasksAPI.getMyTasks(),
      projectsAPI.getProjects().catch(() => ({ data: [] })), // may fail for employee role
    ])
    
    user.value = uRes.data
    attendanceToday.value = aRes.data.find(a => a.date === todayStr) || null
    leaves.value = lRes.data
    allTasks.value = tRes.data
    projectsList.value = pRes.data || []
  } catch (err) {
    console.error('Failed to load dashboard data', err)
  } finally {
    loadingTasks.value = false
  }
}

// ── Computed ──
const approvedLeaves = computed(() => leaves.value.filter(l => l.status === 'approved'))

const projectMap = computed(() => {
  const map = {}
  for (const p of projectsList.value) {
    map[p.id] = { name: p.name, color: p.color || '#287475' }
  }
  return map
})

const checkedInToday = computed(() => !!attendanceToday.value)
const checkInText = computed(() => {
  if (attendanceToday.value?.check_in) return `Checked In ${attendanceToday.value.check_in}`
  return 'Not Checked In'
})

const leavesRemaining = computed(() => {
  if (!user.value) return 0
  const allowed = user.value.leaves_allowed || 0
  const used = approvedLeaves.value.reduce((acc, l) => acc + countWorkingDays(l.start_date, l.end_date), 0)
  return Math.max(0, allowed - used)
})

const pendingTasksToday = computed(() => {
  return allTasks.value.filter(t => t.date <= todayStr && t.status !== 'completed').length
})

const todayTasks = computed(() => {
  return allTasks.value
    .filter(t => {
      const tEnd = t.end_date || t.date
      return t.date <= todayStr && tEnd >= todayStr
    })
    .sort((a, b) => {
      const pMap = { high: 0, medium: 1, low: 2 }
      return pMap[a.priority] - pMap[b.priority]
    })
})

// ── Task interactions ──
function openTaskDrawer(task) {
  selectedTask.value = task
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
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
@media (max-width: 1024px) {
  .stats-strip { grid-template-columns: repeat(2, 1fr); }
}

.stat-pill {
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
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
  min-height: 500px;
}
@media (max-width: 1200px) {
  .main-content { grid-template-columns: 1fr; }
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

/* ── Today's Tasks Right Column ── */
.today-tasks-list {
  background: var(--color-surface);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 400px;
  overflow-y: auto;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--color-outline);
  text-align: center;
  padding: 32px;
}
.empty-state .material-symbols-outlined { font-size: 48px; margin-bottom: 16px; }

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
}

.task-card {
  padding: 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-outline-variant);
  background: var(--color-surface-container-lowest);
  transition: border-color 0.2s;
}
.task-card:hover { border-color: var(--color-outline); }
.task-card.completed { opacity: 0.6; }

.task-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}
.priority-badge {
  padding: 2px 8px;
  border-radius: 2px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.priority-badge.high { background: #fee2e2; color: #b91c1c; }
.priority-badge.medium { background: #fef3c7; color: #b45309; }
.priority-badge.low { background: #ecfdf5; color: #059669; }

.duration-badge {
  font-size: 11px;
  color: var(--color-outline);
  font-weight: 600;
}

.task-title {
  font-family: var(--font-display);
  font-size: 14px;
  margin: 0 0 4px 0;
  color: var(--color-on-surface);
}

.task-project {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--color-primary);
  margin: 0 0 16px 0;
  font-weight: 600;
}
.project-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.task-actions {
  display: flex;
  justify-content: flex-end;
}
.btn-action {
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  border: none;
  cursor: pointer;
  transition: opacity 0.2s;
}
.btn-action:hover:not(:disabled) { opacity: 0.9; }
.btn-action:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-action.start { background: var(--color-primary); color: white; }
.btn-action.complete { background: #059669; color: white; }

.completed-text {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 700;
  color: #059669;
}
.completed-text .material-symbols-outlined { font-size: 16px; }

@keyframes spin { 100% { transform: rotate(360deg); } }
.spinner { animation: spin 1s linear infinite; }
</style>
