<template>
  <AppLayout>
    <!-- Header -->
    <div class="page-header">
      <div>
        <h2 class="page-title">Task Management</h2>
        <p class="page-subtitle">Calendar view of all tasks</p>
      </div>
      <div class="header-actions">
        <button class="btn-outline" @click="prevMonth">Prev</button>
        <span class="month-year">{{ currentMonthName }} {{ currentYear }}</span>
        <button class="btn-outline" @click="nextMonth">Next</button>
      </div>
    </div>

    <!-- Calendar -->
    <div class="calendar-container">
      <!-- Days of week -->
      <div class="calendar-header">
        <div v-for="day in daysOfWeek" :key="day" class="day-header">{{ day }}</div>
      </div>

      <!-- Calendar grid -->
      <div class="calendar-grid">
        <div
          v-for="day in calendarDays"
          :key="day.date"
          class="calendar-day"
          :class="{ 'other-month': !day.isCurrentMonth, 'today': day.isToday }"
          @click="openAddModal(day.date)"
        >
          <div class="day-number">{{ day.day }}</div>
          <div class="day-tasks">
            <div
              v-for="task in day.tasks"
              :key="task.id"
              class="task-block"
              :class="`priority-${task.priority}`"
              @click.stop="openEditModal(task)"
            >
              <span class="task-title">{{ task.title }}</span>
              <span class="task-duration" v-if="task.duration_hours">{{ task.duration_hours }}h</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <Teleport to="body">
      <div v-if="modalOpen" class="modal-backdrop" @click.self="closeModal">
        <div class="modal modal-wide">
          <div class="modal-header">
            <h3 class="modal-title">{{ isEditing ? 'Edit Task' : 'Add New Task' }}</h3>
            <button class="modal-close" @click="closeModal">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>

          <form @submit.prevent="handleSubmit" class="modal-body">
            <div class="form-grid">
              <!-- Title -->
              <div class="form-field">
                <label>Title *</label>
                <input v-model="form.title" type="text" required placeholder="Task title" />
              </div>
              <!-- Due Date -->
              <div class="form-field">
                <label>Due Date *</label>
                <input v-model="form.date" type="date" required />
              </div>
              <!-- Description -->
              <div class="form-field span-2">
                <label>Description</label>
                <textarea v-model="form.description" placeholder="Task description..." rows="3"></textarea>
              </div>
              <!-- Duration -->
              <div class="form-field">
                <label>Duration (hours)</label>
                <input v-model.number="form.duration_hours" type="number" placeholder="0" min="0" />
              </div>
              <!-- Priority -->
              <div class="form-field">
                <label>Priority *</label>
                <select v-model="form.priority" required>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              <!-- Assigned To -->
              <div class="form-field">
                <label>Assigned To *</label>
                <select v-model="form.assigned_to" required>
                  <option :value="null">— Select Employee —</option>
                  <option v-for="u in users" :key="u.id" :value="u.id">{{ u.name }} ({{ u.designation }})</option>
                </select>
              </div>
              <!-- Project -->
              <div class="form-field">
                <label>Project</label>
                <select v-model="form.project_id">
                  <option :value="null">— No Project —</option>
                  <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
                </select>
              </div>
            </div>

            <div v-if="formError" class="form-error">
              <span class="material-symbols-outlined">error</span>
              {{ formError }}
            </div>

            <div class="modal-footer">
              <button type="button" class="btn-cancel" @click="closeModal">Cancel</button>
              <button v-if="isEditing" type="button" class="btn-danger" @click="confirmDelete">Delete</button>
              <button type="submit" class="btn-submit" :disabled="submitting">
                {{ submitting ? 'Saving…' : (isEditing ? 'Save Changes' : 'Add Task') }}
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
            <h3 class="modal-title">Delete Task</h3>
            <button class="modal-close" @click="deleteTarget = null">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <div class="modal-body">
            <p>Are you sure you want to delete <strong>{{ deleteTarget.title }}</strong>?<br/>This action cannot be undone.</p>
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
  </AppLayout>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import { tasksAPI } from '../api/tasks'
import { usersAPI } from '../api/users'
import { projectsAPI } from '../api/projects'

const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth()) // 0-based

const calendarData = ref({})
const users = ref([])
const projects = ref([])
const loading = ref(true)

const modalOpen = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const submitting = ref(false)
const formError = ref('')
const deleteTarget = ref(null)

const form = reactive({
  title: '',
  description: '',
  date: '',
  duration_hours: null,
  priority: 'medium',
  assigned_to: null,
  project_id: null,
})

const daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

const currentMonthName = computed(() => {
  return new Date(currentYear.value, currentMonth.value).toLocaleString('default', { month: 'long' })
})

const calendarDays = computed(() => {
  const year = currentYear.value
  const month = currentMonth.value
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const startDate = new Date(firstDay)
  startDate.setDate(startDate.getDate() - firstDay.getDay())

  const days = []
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  for (let i = 0; i < 42; i++) { // 6 weeks
    const date = new Date(startDate)
    date.setDate(startDate.getDate() + i)
    const dateStr = date.toISOString().split('T')[0]
    const isCurrentMonth = date.getMonth() === month
    const isToday = date.toDateString() === today.toDateString()

    days.push({
      date: dateStr,
      day: date.getDate(),
      isCurrentMonth,
      isToday,
      tasks: calendarData.value[dateStr] || []
    })
  }
  return days
})

async function fetchCalendar() {
  loading.value = true
  try {
    const res = await tasksAPI.getCalendarTasks(currentYear.value, currentMonth.value + 1)
    calendarData.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function fetchUsersAndProjects() {
  try {
    const [uRes, pRes] = await Promise.all([usersAPI.getUsers(), projectsAPI.getProjects()])
    users.value = uRes.data
    projects.value = pRes.data
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  fetchUsersAndProjects()
  fetchCalendar()
})

watch([currentYear, currentMonth], fetchCalendar)

function prevMonth() {
  if (currentMonth.value === 0) {
    currentMonth.value = 11
    currentYear.value--
  } else {
    currentMonth.value--
  }
}

function nextMonth() {
  if (currentMonth.value === 11) {
    currentMonth.value = 0
    currentYear.value++
  } else {
    currentMonth.value++
  }
}

function resetForm() {
  form.title = ''
  form.description = ''
  form.date = ''
  form.duration_hours = null
  form.priority = 'medium'
  form.assigned_to = null
  form.project_id = null
  formError.value = ''
}

function openAddModal(dateStr) {
  resetForm()
  form.date = dateStr
  isEditing.value = false
  editingId.value = null
  modalOpen.value = true
}

function openEditModal(task) {
  isEditing.value = true
  editingId.value = task.id
  form.title = task.title
  form.description = task.description || ''
  form.date = task.date
  form.duration_hours = task.duration_hours
  form.priority = task.priority
  form.assigned_to = task.assigned_to
  form.project_id = task.project_id
  formError.value = ''
  modalOpen.value = true
}

function closeModal() { modalOpen.value = false }

async function handleSubmit() {
  formError.value = ''
  submitting.value = true
  try {
    const payload = {
      title: form.title,
      description: form.description || null,
      date: form.date,
      duration_hours: form.duration_hours,
      priority: form.priority,
      assigned_to: form.assigned_to,
      project_id: form.project_id || null,
    }
    if (isEditing.value) {
      await tasksAPI.updateTask(editingId.value, payload)
    } else {
      await tasksAPI.createTask(payload)
    }
    closeModal()
    await fetchCalendar()
  } catch (err) {
    formError.value = err.response?.data?.detail || 'Operation failed. Please try again.'
  } finally {
    submitting.value = false
  }
}

function confirmDelete() {
  deleteTarget.value = { id: editingId.value, title: form.title }
  closeModal()
}

async function handleDelete() {
  submitting.value = true
  try {
    await tasksAPI.deleteTask(deleteTarget.value.id)
    deleteTarget.value = null
    await fetchCalendar()
  } catch (err) {
    console.error(err)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.page-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 24px;
}
.page-title {
  font-family: 'Integral CF', sans-serif; font-size: 24px; font-weight: 600;
  color: #1c1b1d; margin: 0;
}
.page-subtitle {
  font-family: 'Integral CF', sans-serif; font-size: 14px; color: #64748b; margin: 4px 0 0 0;
}
.header-actions {
  display: flex; align-items: center; gap: 12px;
}
.btn-outline {
  padding: 8px 16px; background: #fff; border: 1px solid #e2e8f0;
  border-radius: 4px; font-family: 'Integral CF', sans-serif; font-size: 13px;
  color: #334155; cursor: pointer; transition: all 0.15s;
}
.btn-outline:hover { background: #f1f5f9; }
.month-year {
  font-family: 'Integral CF', sans-serif; font-size: 16px; font-weight: 600;
  color: #1c1b1d;
}

.calendar-container {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
  overflow: hidden;
}
.calendar-header {
  display: grid; grid-template-columns: repeat(7, 1fr);
  background: #f8fafc; border-bottom: 1px solid #e2e8f0;
}
.day-header {
  padding: 12px; text-align: center; font-family: 'Integral CF', sans-serif;
  font-size: 12px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.05em; color: #64748b;
}
.calendar-grid {
  display: grid; grid-template-columns: repeat(7, 1fr);
}
.calendar-day {
  min-height: 120px; padding: 8px; border-right: 1px solid #f1f5f9;
  border-bottom: 1px solid #f1f5f9; cursor: pointer; transition: background 0.15s;
}
.calendar-day:hover { background: #f8fafc; }
.calendar-day.other-month { background: #fafafa; color: #9ca3af; }
.calendar-day.today { background: #fefce8; }
.day-number {
  font-family: 'Integral CF', sans-serif; font-size: 14px; font-weight: 500;
  margin-bottom: 4px;
}
.day-tasks { display: flex; flex-direction: column; gap: 2px; }
.task-block {
  padding: 4px 6px; border-radius: 3px; font-size: 11px; line-height: 1.2;
  cursor: pointer; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.task-block.priority-low { background: #dcfce7; color: #166534; }
.task-block.priority-medium { background: #fef3c7; color: #92400e; }
.task-block.priority-high { background: #fee2e2; color: #991b1b; }
.task-title { font-weight: 500; }
.task-duration { margin-left: 4px; opacity: 0.8; }

/* Modal styles similar to others */
.modal-backdrop {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.5); display: flex; align-items: center;
  justify-content: center; z-index: 1000;
}
.modal {
  background: #fff; border-radius: 8px; max-width: 600px; width: 90%;
  max-height: 90vh; overflow-y: auto; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}
.modal-wide { max-width: 800px; }
.modal-sm { max-width: 400px; }
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 20px 24px; border-bottom: 1px solid #e2e8f0;
}
.modal-title {
  font-family: 'Integral CF', sans-serif; font-size: 18px; font-weight: 600;
  color: #1c1b1d; margin: 0;
}
.modal-close {
  background: none; border: none; cursor: pointer; padding: 4px;
  border-radius: 4px; transition: background 0.15s;
}
.modal-close:hover { background: #f1f5f9; }
.modal-close .material-symbols-outlined { font-size: 20px; color: #64748b; }
.modal-body { padding: 24px; }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 12px;
  padding: 20px 24px; border-top: 1px solid #e2e8f0; background: #f8fafc;
}

.form-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
  margin-bottom: 24px;
}
.form-field span-2 { grid-column: span 2; }
.form-field label {
  display: block; font-family: 'Integral CF', sans-serif; font-size: 13px;
  font-weight: 600; color: #334155; margin-bottom: 6px;
}
.form-field input,
.form-field select,
.form-field textarea {
  width: 100%; padding: 8px 12px; border: 1px solid #e2e8f0;
  border-radius: 4px; font-family: 'Integral CF', sans-serif; font-size: 13px;
  color: #1c1b1d; outline: none; transition: border 0.15s;
}
.form-field input:focus,
.form-field select:focus,
.form-field textarea:focus { border-color: #0d9488; }
.form-field textarea { resize: vertical; }

.form-error {
  display: flex; align-items: center; gap: 8px;
  padding: 12px; background: #fef2f2; border: 1px solid #fecaca;
  border-radius: 4px; margin-bottom: 16px;
}
.form-error .material-symbols-outlined { color: #dc2626; font-size: 16px; }
.form-error {
  font-family: 'Integral CF', sans-serif; font-size: 13px; color: #dc2626;
}

.btn-cancel {
  padding: 8px 16px; background: #fff; border: 1px solid #e2e8f0;
  border-radius: 4px; font-family: 'Integral CF', sans-serif; font-size: 13px;
  color: #334155; cursor: pointer; transition: all 0.15s;
}
.btn-cancel:hover { background: #f1f5f9; }
.btn-submit {
  padding: 8px 16px; background: #1a1a2e; color: #fff; border: none;
  border-radius: 4px; font-family: 'Integral CF', sans-serif; font-size: 13px;
  font-weight: 500; cursor: pointer; transition: background 0.15s;
}
.btn-submit:hover:not(:disabled) { background: #2a2a3e; }
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger {
  padding: 8px 16px; background: #dc2626; color: #fff; border: none;
  border-radius: 4px; font-family: 'Integral CF', sans-serif; font-size: 13px;
  font-weight: 500; cursor: pointer; transition: background 0.15s;
}
.btn-danger:hover:not(:disabled) { background: #b91c1c; }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }
</style>