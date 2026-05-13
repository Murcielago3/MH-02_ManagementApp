<template>
  <component :is="layout">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h2 class="page-title">Task Calendar</h2>
        <p class="page-subtitle">Manage and assign team tasks</p>
      </div>
      <div class="header-actions">
        <select v-model="filterEmployee" class="filter-select">
          <option :value="null">All Employees</option>
          <option v-for="u in usersList" :key="u.id" :value="u.id">{{ u.name }}</option>
        </select>
      </div>
    </div>

    <!-- Calendar Grid -->
    <ResourceCalendar
      ref="calGrid"
      :tasks="tasks"
      :employees="usersList"
      :projectMap="projectMap"
      :leaves="allLeaves"
      :filterEmployeeId="filterEmployee"
      @ribbon-click="openDrawer"
      @cell-drag-create="onDragCreate"
      @ribbon-drag-extend="onDragExtend"
    />

    <!-- Task Detail Drawer -->
    <TaskDetailDrawer
      v-if="selectedTask"
      :task="selectedTask"
      :projectMap="projectMap"
      :userMap="userMap"
      :isAdmin="true"
      @close="selectedTask = null"
      @edit="onEditTask"
      @delete="onDeleteTask"
    />

    <!-- Add / Edit Task Modal -->
    <AddTaskModal
      v-if="modalOpen"
      :users="usersList"
      :projects="projectsList"
      :prefillDate="prefillDate"
      :prefillEndDate="prefillEndDate"
      :prefillAssignedTo="prefillAssignedTo"
      :editTask="editingTask"
      @close="closeModal"
      @submit="handleModalSubmit"
      @delete-task="handleDeleteFromModal"
    />

    <!-- Delete Confirmation -->
    <Teleport to="body">
      <div v-if="deleteTarget" class="modal-backdrop" @click.self="deleteTarget = null">
        <div class="modal-sm">
          <div class="modal-header">
            <h3 class="modal-title">Delete Task</h3>
            <button class="modal-close" @click="deleteTarget = null">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <div class="modal-body">
            <p>Are you sure you want to delete <strong>{{ deleteTarget.title }}</strong>?<br/>This cannot be undone.</p>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="deleteTarget = null">Cancel</button>
            <button class="btn-danger" :disabled="deleting" @click="confirmDelete">
              {{ deleting ? 'Deleting…' : 'Delete Task' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Weekend Warning -->
    <Teleport to="body">
      <div v-if="weekendWarning" class="modal-backdrop" @click.self="dismissWeekendWarning">
        <div class="modal-sm">
          <div class="modal-header weekend-warn-header">
            <div class="weekend-warn-title">
              <span class="material-symbols-outlined warn-icon">warning</span>
              <h3 class="modal-title">Weekend Conflict</h3>
            </div>
            <button class="modal-close" @click="dismissWeekendWarning">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <div class="modal-body">
            <p class="weekend-warn-msg">
              <strong>{{ weekendWarning.weekendDays }}</strong> day{{ weekendWarning.weekendDays > 1 ? 's' : '' }} in the selected range fall{{ weekendWarning.weekendDays === 1 ? 's' : '' }} on a weekend.
            </p>
            <p v-if="weekendWarning.empName" class="weekend-warn-emp">
              <strong>{{ weekendWarning.empName }}</strong>
            </p>
            <p class="weekend-warn-note">
              Task will be assigned to weekend/non-working days. If this is not your intention, please go back and change the dates.
            </p>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="dismissWeekendWarning">Go Back</button>
            <button class="btn-submit" @click="confirmWeekendAction">Confirm Anyway</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Toast -->
    <ToastNotification
      v-if="toastMsg"
      :message="toastMsg"
      :type="toastType"
      @done="toastMsg = ''"
    />
  </component>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import EmployeeLayout from '../components/EmployeeLayout.vue'
import ResourceCalendar from '../components/ResourceCalendar.vue'
import TaskDetailDrawer from '../components/TaskDetailDrawer.vue'
import AddTaskModal from '../components/AddTaskModal.vue'
import ToastNotification from '../components/ToastNotification.vue'
import { useAuthStore } from '../stores/auth'
import { tasksAPI } from '../api/tasks'
import { projectsAPI } from '../api/projects'
import { usersAPI } from '../api/users'
import { leavesAPI } from '../api/leaves'

const authStore = useAuthStore()
const layout = computed(() => authStore.role === 'admin' ? AppLayout : EmployeeLayout)

const calGrid = ref(null)

// Data
const tasks = ref([])
const projectsList = ref([])
const usersList = ref([])
const allLeaves = ref([])

const projectMap = computed(() => {
  const map = {}
  for (const p of projectsList.value) {
    map[p.id] = { name: p.name, color: p.color || '#287475' }
  }
  return map
})

const userMap = computed(() => {
  const map = {}
  for (const u of usersList.value) {
    map[u.id] = { name: u.name }
  }
  return map
})

// Filters
const filterEmployee = ref(null)

// State
const selectedTask = ref(null)
const modalOpen = ref(false)
const prefillDate = ref('')
const prefillEndDate = ref('')
const prefillAssignedTo = ref(null)
const editingTask = ref(null)
const deleteTarget = ref(null)
const deleting = ref(false)
const weekendWarning = ref(null) // { action, payload, weekendDays, empName }

// Toast
const toastMsg = ref('')
const toastType = ref('success')

function showToast(msg, type = 'success') {
  toastMsg.value = msg
  toastType.value = type
}

// ── Fetch ──
async function fetchAll() {
  try {
    const [pRes, uRes, lRes] = await Promise.all([
      projectsAPI.getProjects(),
      usersAPI.getUsers(),
      leavesAPI.getLeaves(),
    ])
    projectsList.value = pRes.data
    usersList.value = uRes.data
    allLeaves.value = (lRes.data || []).filter(l => l.status === 'approved')
  } catch (e) {
    console.error('Failed to fetch base data', e)
  }
}

async function fetchTasks() {
  try {
    const anchor = calGrid.value?.anchorDate || new Date()
    const year = anchor.getFullYear()
    const month = anchor.getMonth() + 1
    const res = await tasksAPI.getCalendarTasks(year, month, filterEmployee.value)
    tasks.value = res.data
  } catch (e) {
    console.error('Failed to fetch tasks', e)
  }
}

onMounted(async () => {
  await fetchAll()
  await fetchTasks()
})

// Re-fetch on calendar navigation or filter change
watch(filterEmployee, fetchTasks)
// Watch for calendar anchor changes
watch(() => calGrid.value?.anchorDate, fetchTasks)
watch(() => calGrid.value?.viewMode, fetchTasks)

// ── Drawer ──
function openDrawer(task) {
  selectedTask.value = task
}

function onEditTask(task) {
  selectedTask.value = null
  editingTask.value = task
  prefillDate.value = ''
  prefillEndDate.value = ''
  modalOpen.value = true
}

function onDeleteTask(task) {
  selectedTask.value = null
  deleteTarget.value = task
}

// ── Weekend helpers ──
function isWeekendDate(dateStr) {
  const day = new Date(dateStr).getDay()
  return day === 0 || day === 6
}

function countWeekendDays(startDate, endDate) {
  let count = 0
  const d = new Date(startDate)
  const end = new Date(endDate)
  while (d <= end) {
    const day = d.getDay()
    if (day === 0 || day === 6) count++
    d.setDate(d.getDate() + 1)
  }
  return count
}

function dismissWeekendWarning() {
  // Revert optimistic update if it was an extend
  if (weekendWarning.value?.action === 'extend') {
    const t = tasks.value.find(x => x.id === weekendWarning.value.payload.taskId)
    if (t) t.end_date = weekendWarning.value.payload.originalEnd
  }
  weekendWarning.value = null
}

async function confirmWeekendAction() {
  const w = weekendWarning.value
  weekendWarning.value = null
  if (w.action === 'create') {
    doOpenCreateModal(w.payload)
  } else if (w.action === 'extend') {
    await doExtendTask(w.payload.taskId, w.payload.newEndDate)
  }
}

// ── Modal ──
function onDragCreate({ startDate, endDate, employeeId }) {
  const wDays = countWeekendDays(startDate, endDate)
  const empName = userMap.value[employeeId]?.name || ''
  if (wDays > 0) {
    weekendWarning.value = {
      action: 'create',
      payload: { startDate, endDate, employeeId },
      weekendDays: wDays,
      empName,
    }
    return
  }
  doOpenCreateModal({ startDate, endDate, employeeId })
}

function doOpenCreateModal({ startDate, endDate, employeeId }) {
  editingTask.value = null
  prefillDate.value = startDate
  prefillEndDate.value = startDate === endDate ? '' : endDate
  prefillAssignedTo.value = employeeId || null
  modalOpen.value = true
}

function closeModal() {
  modalOpen.value = false
  editingTask.value = null
  prefillAssignedTo.value = null
}

async function handleModalSubmit({ payload, isEditing, taskId }) {
  try {
    if (isEditing) {
      await tasksAPI.updateTask(taskId, payload)
      showToast('Task updated successfully')
    } else {
      await tasksAPI.createTask(payload)
      const empName = userMap.value[payload.assigned_to]?.name || 'employee'
      showToast(`Task assigned to ${empName}`)
    }
    closeModal()
    await fetchTasks()
  } catch (err) {
    showToast(err.response?.data?.detail || 'Failed to save task', 'error')
  }
}

function handleDeleteFromModal(taskId) {
  closeModal()
  const task = tasks.value.find(t => t.id === taskId)
  if (task) deleteTarget.value = task
}

async function confirmDelete() {
  deleting.value = true
  try {
    await tasksAPI.deleteTask(deleteTarget.value.id)
    showToast('Task deleted')
    deleteTarget.value = null
    await fetchTasks()
  } catch (err) {
    showToast('Failed to delete task', 'error')
  } finally {
    deleting.value = false
  }
}

// ── Drag extend ──
function onDragExtend({ taskId, newEndDate }) {
  const task = tasks.value.find(t => t.id === taskId)
  if (!task) return
  const originalEnd = task.end_date

  // Check weekend
  if (isWeekendDate(newEndDate)) {
    // Optimistic update for visual, will revert on dismiss
    task.end_date = newEndDate
    const empName = userMap.value[task.assigned_to]?.name || ''
    weekendWarning.value = {
      action: 'extend',
      payload: { taskId, newEndDate, originalEnd },
      weekendDays: 1,
      empName,
    }
    return
  }

  // No weekend conflict
  task.end_date = newEndDate
  doExtendTask(taskId, newEndDate, originalEnd)
}

async function doExtendTask(taskId, newEndDate, originalEnd) {
  const task = tasks.value.find(t => t.id === taskId)
  const prevEnd = originalEnd || task?.end_date
  try {
    await tasksAPI.patchTask(taskId, { end_date: newEndDate })
    const formatted = new Date(newEndDate).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
    showToast(`Task extended to ${formatted}`)
    await fetchTasks()
  } catch (err) {
    if (task) task.end_date = prevEnd
    showToast('Failed to extend task', 'error')
  }
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.page-title {
  font-family: 'Integral CF', sans-serif;
  font-size: 24px;
  font-weight: 700;
  color: var(--color-on-surface);
  margin: 0;
}
.page-subtitle {
  font-size: 13px;
  color: var(--color-on-surface-variant);
  margin: 4px 0 0 0;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.filter-select {
  height: 36px;
  padding: 0 12px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-family: var(--font-body);
  font-size: 13px;
  background: var(--color-surface);
  outline: none;
  min-width: 180px;
}
.filter-select:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(40, 116, 117, 0.1);
}

/* Delete Modal */
.modal-backdrop {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.5); display: flex; align-items: center;
  justify-content: center; z-index: 1000;
}
.modal-sm {
  background: #fff; border-radius: 8px; max-width: 420px; width: 92%;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 20px 24px; border-bottom: 1px solid var(--color-outline-variant);
}
.modal-title {
  font-family: 'Integral CF', sans-serif; font-size: 16px; margin: 0;
}
.modal-close {
  background: none; border: none; cursor: pointer; padding: 4px; border-radius: 4px;
}
.modal-close:hover { background: var(--color-surface-container); }
.modal-close .material-symbols-outlined { font-size: 20px; color: var(--color-on-surface-variant); }
.modal-body { padding: 24px; font-size: 14px; color: var(--color-on-surface-variant); }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 12px;
  padding: 16px 24px; border-top: 1px solid var(--color-outline-variant);
}
.btn-cancel {
  padding: 10px 16px; background: #fff; border: 1px solid var(--color-outline-variant);
  border-radius: 4px; font-size: 13px; font-weight: 600;
  color: var(--color-on-surface-variant); cursor: pointer;
}
.btn-danger {
  padding: 10px 16px; background: #dc2626; color: #fff; border: none;
  border-radius: 4px; font-size: 13px; font-weight: 600; cursor: pointer;
}
.btn-danger:hover:not(:disabled) { background: #b91c1c; }
.btn-danger:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-submit {
  padding: 10px 20px; background: var(--color-primary); color: #fff; border: none;
  border-radius: 4px; font-size: 13px; font-weight: 600; cursor: pointer;
}
.btn-submit:hover { background: #1a4e4f; }

/* Weekend warning */
.weekend-warn-header { gap: 8px; }
.weekend-warn-title {
  display: flex; align-items: center; gap: 8px;
}
.warn-icon { font-size: 22px; color: #f59e0b; }
.weekend-warn-msg { margin: 0 0 12px 0; font-size: 14px; color: var(--color-on-surface); line-height: 1.5; }
.weekend-warn-emp {
  margin: 0 0 12px 0; font-size: 14px; color: var(--color-on-surface);
}
.weekend-warn-note {
  margin: 0; font-size: 13px; color: #dc2626; line-height: 1.5;
}
</style>