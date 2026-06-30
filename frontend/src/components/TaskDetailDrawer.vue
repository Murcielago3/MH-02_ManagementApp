<template>
  <div class="drawer-overlay" @click="$emit('close')">
    <div class="drawer-panel" @click.stop>
      <div class="drawer-header">
        <h3>Task Details</h3>
        <button class="icon-btn" @click="$emit('close')">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>

      <div class="drawer-content">
        <!-- Badges -->
        <div class="drawer-badges">
          <span class="priority-badge" :class="task.priority">{{ task.priority }}</span>
          <span class="status-badge" :class="task.status">{{ formatStatus(task.status) }}</span>
        </div>

        <!-- Title -->
        <h2 class="drawer-title">{{ task.title }}</h2>

        <!-- Project -->
        <div v-if="project" class="drawer-project">
          <span class="project-dot" :style="{ background: project.color }"></span>
          {{ project.name }}
        </div>

        <!-- Description -->
        <p class="drawer-desc">{{ task.description || 'No description provided.' }}</p>

        <!-- Meta -->
        <div class="drawer-meta">
          <div class="meta-item" v-if="assigneeName">
            <span class="material-symbols-outlined">person</span>
            <span>{{ assigneeName }}</span>
          </div>
          <div class="meta-item">
            <span class="material-symbols-outlined">date_range</span>
            <span>
              {{ formatDate(task.date) }}
              <template v-if="task.end_date && task.end_date !== task.date"> → {{ formatDate(task.end_date) }}</template>
            </span>
          </div>
          <div class="meta-item" v-if="task.duration_hours">
            <span class="material-symbols-outlined">schedule</span>
            <span>{{ task.duration_hours }} hours</span>
          </div>
        </div>

        <!-- Subtasks -->
        <div class="subtasks-section">
          <div class="subtasks-header">
            <h4>
              <span class="material-symbols-outlined">checklist</span>
              Subtasks <span class="subtasks-count" v-if="subtasks.length">{{ subtasks.length }}</span>
            </h4>
            <button v-if="!addingSubtask" type="button" class="add-subtask-btn" @click="startAddSubtask">
              <span class="material-symbols-outlined">add</span> Add
            </button>
          </div>

          <ul v-if="subtasks.length" class="subtasks-list">
            <li v-for="s in subtasks" :key="s.id" class="subtask-item" :class="{ done: s.status === 'completed' }">
              <button class="subtask-check" :class="{ checked: s.status === 'completed' }" @click="toggleSubtask(s)" :title="s.status === 'completed' ? 'Mark as pending' : 'Mark as complete'">
                <span v-if="s.status === 'completed'" class="material-symbols-outlined">check</span>
              </button>
              <div class="subtask-body">
                <div class="subtask-title">{{ s.title }}</div>
                <div class="subtask-meta">
                  <span v-if="s.duration_hours" class="subtask-duration">
                    <span class="material-symbols-outlined">schedule</span>{{ s.duration_hours }}h
                  </span>
                  <span v-if="s.description" class="subtask-desc">{{ s.description }}</span>
                </div>
              </div>
              <button class="subtask-remove" @click="removeSubtask(s)" title="Delete">
                <span class="material-symbols-outlined">close</span>
              </button>
            </li>
          </ul>
          <div v-else-if="!addingSubtask && !subtasksLoading" class="subtasks-empty">No subtasks yet.</div>
          <div v-if="subtasksLoading" class="subtasks-empty">Loading…</div>

          <div v-if="addingSubtask" class="subtask-add-form">
            <input
              v-model="newSubtask.title"
              type="text"
              placeholder="Subtask title"
              class="subtask-input"
              @keyup.enter="submitSubtask"
              ref="subtaskTitleRef"
            />
            <div class="subtask-add-row">
              <input
                v-model.number="newSubtask.duration_hours"
                type="number"
                min="0"
                step="0.5"
                placeholder="Hours"
                class="subtask-input subtask-input-hours"
              />
              <input
                v-model="newSubtask.description"
                type="text"
                placeholder="Description (optional)"
                class="subtask-input"
              />
            </div>
            <div class="subtask-add-actions">
              <button type="button" class="subtask-cancel" @click="cancelAddSubtask">Cancel</button>
              <button type="button" class="subtask-save" :disabled="!newSubtask.title || subtaskSubmitting" @click="submitSubtask">
                {{ subtaskSubmitting ? 'Saving…' : 'Save' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Admin: Edit / Delete -->
        <div v-if="isAdmin" class="drawer-actions admin-actions">
          <button class="btn-edit" @click="$emit('edit', task)">
            <span class="material-symbols-outlined">edit</span> Edit Task
          </button>
          <button class="btn-delete" @click="$emit('delete', task)">
            <span class="material-symbols-outlined">delete</span> Delete
          </button>
        </div>

        <!-- Employee: Status update -->
        <div v-else class="drawer-actions">
          <button
            v-if="task.status === 'pending'"
            class="btn-status start"
            @click="$emit('update-status', task.id, 'in-progress')"
            :disabled="loading"
          >Mark as In Progress</button>
          <button
            v-if="task.status === 'in-progress'"
            class="btn-status complete"
            @click="$emit('update-status', task.id, 'completed')"
            :disabled="loading"
          >Mark as Complete</button>
          <div v-if="task.status === 'completed'" class="completed-badge">
            <span class="material-symbols-outlined">check_circle</span> Completed
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'
import { subtasksAPI } from '../api/subtasks'

const props = defineProps({
  task: { type: Object, required: true },
  projectMap: { type: Object, default: () => ({}) },
  userMap: { type: Object, default: () => ({}) },
  isAdmin: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
})

defineEmits(['close', 'edit', 'delete', 'update-status'])

const project = computed(() => props.task.project_id ? props.projectMap[props.task.project_id] : null)
const assigneeName = computed(() => props.userMap[props.task.assigned_to]?.name || '')

const formatDate = (d) => {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

const formatStatus = (s) => {
  if (!s) return ''
  return s.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
}

// ── Subtasks ──
const subtasks = ref([])
const subtasksLoading = ref(false)
const addingSubtask = ref(false)
const subtaskSubmitting = ref(false)
const subtaskTitleRef = ref(null)
const newSubtask = ref({ title: '', description: '', duration_hours: null })

async function loadSubtasks() {
  if (!props.task?.id) return
  subtasksLoading.value = true
  try {
    const { data } = await subtasksAPI.list(props.task.id)
    subtasks.value = data || []
  } catch (err) {
    // silently — surface a toast outside this component if needed
  } finally {
    subtasksLoading.value = false
  }
}

watch(() => props.task?.id, loadSubtasks, { immediate: true })

function startAddSubtask() {
  newSubtask.value = { title: '', description: '', duration_hours: null }
  addingSubtask.value = true
  nextTick(() => subtaskTitleRef.value?.focus())
}

function cancelAddSubtask() {
  addingSubtask.value = false
  newSubtask.value = { title: '', description: '', duration_hours: null }
}

async function submitSubtask() {
  if (!newSubtask.value.title || subtaskSubmitting.value) return
  subtaskSubmitting.value = true
  try {
    const { data } = await subtasksAPI.create(props.task.id, {
      title: newSubtask.value.title.trim(),
      description: newSubtask.value.description?.trim() || null,
      duration_hours: newSubtask.value.duration_hours || null,
    })
    subtasks.value.push(data)
    cancelAddSubtask()
  } catch (err) {
    // Could emit an error event; keeping silent for now
  } finally {
    subtaskSubmitting.value = false
  }
}

async function toggleSubtask(s) {
  const next = s.status === 'completed' ? 'pending' : 'completed'
  const prev = s.status
  s.status = next
  try {
    await subtasksAPI.patch(s.id, { status: next })
  } catch (err) {
    s.status = prev
  }
}

async function removeSubtask(s) {
  const idx = subtasks.value.findIndex(x => x.id === s.id)
  if (idx === -1) return
  const removed = subtasks.value.splice(idx, 1)[0]
  try {
    await subtasksAPI.remove(s.id)
  } catch (err) {
    subtasks.value.splice(idx, 0, removed)
  }
}
</script>

<style scoped>
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
}
.drawer-panel {
  width: 380px;
  max-width: 100vw;
  background: var(--color-surface);
  height: 100%;
  display: flex;
  flex-direction: column;
  box-shadow: -4px 0 24px rgba(0,0,0,0.1);
  animation: slideIn 0.25s ease-out forwards;
}
@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--color-outline-variant);
}
.drawer-header h3 {
  margin: 0;
  font-family: 'Integral CF', sans-serif;
  font-size: 16px;
}
.icon-btn {
  width: 32px; height: 32px;
  border-radius: 4px;
  border: 1px solid var(--color-outline-variant);
  background: var(--color-surface);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
}

.drawer-content {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.drawer-badges {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.priority-badge, .status-badge {
  padding: 3px 10px;
  border-radius: 2px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.priority-badge.high { background: #fee2e2; color: #b91c1c; }
.priority-badge.medium { background: #fef3c7; color: #b45309; }
.priority-badge.low { background: #ecfdf5; color: #059669; }

.status-badge { background: var(--color-surface-container); color: var(--color-on-surface-variant); }
.status-badge.completed { background: #ecfdf5; color: #059669; }
.status-badge.in-progress { background: #dbeafe; color: #1d4ed8; }

.drawer-title {
  font-family: 'Integral CF', sans-serif;
  font-size: 22px;
  margin: 0 0 8px 0;
  color: var(--color-on-surface);
}

.drawer-project {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-primary);
  margin-bottom: 20px;
}
.project-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.drawer-desc {
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-on-surface-variant);
  margin-bottom: 24px;
}

.drawer-meta {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: var(--color-surface-container-lowest);
  padding: 16px;
  border-radius: 4px;
  border: 1px solid var(--color-outline-variant);
  margin-bottom: 32px;
}
.meta-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--color-on-surface);
}
.meta-item .material-symbols-outlined {
  color: var(--color-outline);
  font-size: 18px;
}

.drawer-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.admin-actions {
  flex-direction: row;
}

.btn-edit, .btn-delete, .btn-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-edit {
  background: var(--color-primary);
  color: #fff;
  flex: 1;
}
.btn-edit:hover { background: #1a4e4f; }
.btn-delete {
  background: #fee2e2;
  color: #dc2626;
}
.btn-delete:hover { background: #fecaca; }
.btn-status.start {
  background: var(--color-primary);
  color: #fff;
}
.btn-status.start:hover { background: #1a4e4f; }
.btn-status.complete {
  background: #059669;
  color: #fff;
}
.btn-status.complete:hover { background: #047857; }
.btn-status:disabled { opacity: 0.6; cursor: not-allowed; }

.completed-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: #059669;
}
.completed-badge .material-symbols-outlined { font-size: 20px; }

/* ── Subtasks ── */
.subtasks-section {
  margin-bottom: 24px;
  padding-top: 4px;
}
.subtasks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.subtasks-header h4 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-on-surface-variant);
}
.subtasks-header h4 .material-symbols-outlined { font-size: 16px; }
.subtasks-count {
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-size: 11px;
  padding: 1px 7px;
  border-radius: 999px;
  font-weight: 700;
  text-transform: none;
}
.add-subtask-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: 1px solid var(--color-outline-variant);
  border-radius: 4px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-primary);
  cursor: pointer;
}
.add-subtask-btn:hover { background: var(--color-primary-light); border-color: var(--color-primary); }
.add-subtask-btn .material-symbols-outlined { font-size: 14px; }

.subtasks-list { list-style: none; padding: 0; margin: 0 0 10px; }
.subtask-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 8px;
  border-bottom: 1px solid var(--color-outline-variant);
}
.subtask-item:last-child { border-bottom: none; }
.subtask-item.done .subtask-title { text-decoration: line-through; color: var(--color-on-surface-variant); }

.subtask-check {
  flex-shrink: 0;
  width: 18px; height: 18px;
  border: 2px solid var(--color-outline);
  border-radius: 4px;
  background: var(--color-surface);
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  margin-top: 2px;
  padding: 0;
}
.subtask-check.checked {
  background: var(--color-primary);
  border-color: var(--color-primary);
}
.subtask-check .material-symbols-outlined { color: #fff; font-size: 12px; }

.subtask-body { flex: 1; min-width: 0; }
.subtask-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-surface);
  line-height: 1.4;
}
.subtask-meta {
  display: flex;
  gap: 10px;
  font-size: 11px;
  color: var(--color-on-surface-variant);
  margin-top: 3px;
  align-items: center;
}
.subtask-duration {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-weight: 600;
}
.subtask-duration .material-symbols-outlined { font-size: 12px; }
.subtask-desc { line-height: 1.4; }

.subtask-remove {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-on-surface-variant);
  padding: 2px;
  border-radius: 3px;
  opacity: 0;
  transition: opacity 0.15s, background 0.15s;
}
.subtask-item:hover .subtask-remove { opacity: 1; }
.subtask-remove:hover { background: #fee2e2; color: var(--color-error); }
.subtask-remove .material-symbols-outlined { font-size: 16px; }

.subtasks-empty {
  font-size: 12px;
  color: var(--color-on-surface-variant);
  padding: 8px 0;
  font-style: italic;
}

.subtask-add-form {
  background: var(--color-surface-container-lowest);
  border: 1px solid var(--color-outline-variant);
  border-radius: 6px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.subtask-add-row { display: flex; gap: 8px; }
.subtask-input {
  flex: 1;
  padding: 7px 10px;
  border: 1px solid var(--color-outline);
  border-radius: 4px;
  font-size: 13px;
  outline: none;
  background: var(--color-surface);
}
.subtask-input:focus { border-color: var(--color-primary); }
.subtask-input-hours { flex: 0 0 80px; }
.subtask-add-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 2px; }
.subtask-cancel {
  background: none;
  border: 1px solid var(--color-outline);
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  color: var(--color-on-surface-variant);
}
.subtask-save {
  background: var(--color-primary);
  color: #fff;
  border: none;
  padding: 6px 14px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
.subtask-save:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
