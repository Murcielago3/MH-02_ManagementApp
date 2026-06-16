<template>
  <Teleport to="body">
    <div class="modal-backdrop" @click.self="$emit('close')">
      <div class="modal">
        <div class="modal-header">
          <div>
            <h3 class="modal-title">Assign Project</h3>
            <p class="modal-subtitle" v-if="project">{{ project.name }}</p>
          </div>
          <button class="modal-close" @click="$emit('close')">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <form @submit.prevent="handleSubmit" class="modal-body">
          <!-- Employee multi-select -->
          <div class="field">
            <label>Assign To <span class="req">*</span></label>
            <div class="emp-toolbar">
              <input
                v-model="search"
                type="text"
                class="emp-search"
                placeholder="Search employees…"
              />
              <button type="button" class="link-btn" @click="toggleAll">
                {{ allSelected ? 'Clear all' : 'Select all' }}
              </button>
            </div>
            <div class="emp-list">
              <label
                v-for="u in filteredUsers"
                :key="u.id"
                class="emp-row"
                :class="{ checked: selected.includes(u.id) }"
              >
                <input type="checkbox" :value="u.id" v-model="selected" />
                <span class="emp-avatar" :style="{ background: avatarColor(u.name) }">{{ initials(u.name) }}</span>
                <span class="emp-name">{{ u.name }}</span>
                <span class="emp-desig">{{ u.designation || '' }}</span>
              </label>
              <div v-if="filteredUsers.length === 0" class="emp-empty">No employees found.</div>
            </div>
            <p class="selected-count">{{ selected.length }} selected</p>
          </div>

          <div class="form-grid">
            <div class="field">
              <label>Start Date <span class="req">*</span></label>
              <input v-model="form.date" type="date" required />
            </div>
            <div class="field">
              <label>End Date</label>
              <input v-model="form.end_date" type="date" :min="form.date" />
            </div>
            <div class="field">
              <label>Priority</label>
              <select v-model="form.priority">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
            <div class="field">
              <label>Duration (hours)</label>
              <input v-model.number="form.duration_hours" type="number" min="0" placeholder="0" />
            </div>
            <div class="field span-2">
              <label>Description</label>
              <textarea v-model="form.description" rows="3" placeholder="What should they work on?"></textarea>
            </div>
          </div>

          <div v-if="formError" class="form-error">
            <span class="material-symbols-outlined">error</span>
            {{ formError }}
          </div>

          <div class="modal-footer">
            <button type="button" class="btn-cancel" @click="$emit('close')">Cancel</button>
            <button type="submit" class="btn-submit" :disabled="submitting">
              {{ submitting ? 'Assigning…' : `Assign to ${selected.length || 0} ${selected.length === 1 ? 'employee' : 'employees'}` }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { tasksAPI } from '../api/tasks'

const props = defineProps({
  project: { type: Object, required: true },
  users: { type: Array, default: () => [] },
})
const emit = defineEmits(['close', 'assigned'])

const search = ref('')
const selected = ref([])
const submitting = ref(false)
const formError = ref('')

const form = reactive({
  date: new Date().toISOString().split('T')[0],
  end_date: '',
  priority: 'medium',
  duration_hours: null,
  description: '',
})

const filteredUsers = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return props.users
  return props.users.filter(
    (u) => u.name.toLowerCase().includes(q) || (u.designation || '').toLowerCase().includes(q)
  )
})

const allSelected = computed(
  () => filteredUsers.value.length > 0 && filteredUsers.value.every((u) => selected.value.includes(u.id))
)

function toggleAll() {
  if (allSelected.value) {
    const ids = filteredUsers.value.map((u) => u.id)
    selected.value = selected.value.filter((id) => !ids.includes(id))
  } else {
    const ids = filteredUsers.value.map((u) => u.id)
    selected.value = [...new Set([...selected.value, ...ids])]
  }
}

function initials(n) {
  return (n || '').split(' ').map((x) => x[0]).join('').toUpperCase().slice(0, 2)
}
const palette = ['#287475', '#6366f1', '#ec4899', '#f59e0b', '#3b82f6', '#8b5cf6', '#ef4444', '#14b8a6']
function avatarColor(n) {
  let h = 0
  for (let i = 0; i < (n || '').length; i++) h = n.charCodeAt(i) + ((h << 5) - h)
  return palette[Math.abs(h) % palette.length]
}

async function handleSubmit() {
  formError.value = ''
  if (selected.value.length === 0) {
    formError.value = 'Select at least one employee.'
    return
  }
  if (!form.date) {
    formError.value = 'Start date is required.'
    return
  }
  submitting.value = true
  try {
    await tasksAPI.bulkAssign({
      title: props.project.name,
      description: form.description || null,
      date: form.date,
      end_date: form.end_date || null,
      duration_hours: form.duration_hours || null,
      priority: form.priority,
      project_id: props.project.id,
      assigned_to: [...selected.value],
    })
    emit('assigned', { count: selected.value.length })
  } catch (err) {
    formError.value = err.response?.data?.detail || 'Failed to assign project.'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000; padding: 16px;
}
.modal {
  background: #fff; border-radius: var(--radius-xl);
  max-width: 640px; width: 100%;
  max-height: 92vh; overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.18);
}
.modal-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding: 20px 24px; border-bottom: 1px solid var(--color-outline-variant);
}
.modal-title { font-family: var(--font-display); font-size: 18px; font-weight: 700; color: var(--color-on-surface); margin: 0; }
.modal-subtitle { margin: 2px 0 0; font-size: 13px; color: var(--color-on-surface-variant); }
.modal-close { background: none; border: none; cursor: pointer; padding: 4px; border-radius: 4px; }
.modal-close:hover { background: var(--color-surface-container); }
.modal-close .material-symbols-outlined { font-size: 20px; color: var(--color-on-surface-variant); }

.modal-body { padding: 24px; }

.field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 18px; }
.field label {
  font-size: 12px; font-weight: 600;
  color: var(--color-on-surface-variant);
  text-transform: uppercase; letter-spacing: 0.03em;
}
.req { color: var(--color-error); }
.field input, .field select, .field textarea {
  width: 100%; padding: 10px 12px; border: 1px solid var(--color-outline);
  border-radius: var(--radius-md); font-family: var(--font-body); font-size: 14px;
  color: var(--color-on-surface); outline: none; background: var(--color-surface);
  box-sizing: border-box;
}
.field input:focus, .field select:focus, .field textarea:focus {
  border-color: var(--color-primary); box-shadow: 0 0 0 2px rgba(40,116,117,0.1);
}
.field textarea { resize: vertical; }

/* Employee picker */
.emp-toolbar { display: flex; gap: 10px; align-items: center; }
.emp-search { flex: 1; }
.link-btn {
  background: none; border: none; color: var(--color-primary);
  font-size: 12px; font-weight: 700; cursor: pointer; white-space: nowrap;
}
.link-btn:hover { text-decoration: underline; }
.emp-list {
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  max-height: 220px; overflow-y: auto;
  margin-top: 4px;
}
.emp-row {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 12px; cursor: pointer;
  border-bottom: 1px solid var(--color-outline-variant);
}
.emp-row:last-child { border-bottom: none; }
.emp-row:hover { background: var(--color-surface-dim); }
.emp-row.checked { background: var(--color-primary-light); }
.emp-row input { width: 16px; height: 16px; accent-color: var(--color-primary); cursor: pointer; flex-shrink: 0; }
.emp-avatar {
  width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 10px; font-weight: 700;
}
.emp-name { font-size: 13px; font-weight: 600; color: var(--color-on-surface); }
.emp-desig { font-size: 12px; color: var(--color-on-surface-variant); margin-left: auto; }
.emp-empty { padding: 20px; text-align: center; font-size: 13px; color: var(--color-on-surface-variant); }
.selected-count { margin: 6px 0 0; font-size: 12px; color: var(--color-on-surface-variant); }

.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-grid .field { margin-bottom: 0; }
.span-2 { grid-column: span 2; }

.form-error {
  display: flex; align-items: center; gap: 8px;
  padding: 12px; background: #fef2f2; border: 1px solid #fecaca;
  border-radius: var(--radius-md); margin-top: 16px;
  font-size: 13px; color: var(--color-error);
}
.form-error .material-symbols-outlined { font-size: 16px; }

.modal-footer {
  display: flex; justify-content: flex-end; gap: 12px;
  padding: 18px 0 0; margin-top: 20px;
  border-top: 1px solid var(--color-outline-variant);
}
.btn-cancel {
  padding: 10px 16px; background: #fff; border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg); font-size: 13px; font-weight: 600;
  color: var(--color-on-surface-variant); cursor: pointer;
}
.btn-cancel:hover { background: var(--color-surface-container); }
.btn-submit {
  padding: 10px 20px; background: var(--color-primary); color: #fff; border: none;
  border-radius: var(--radius-lg); font-size: 13px; font-weight: 600; cursor: pointer;
}
.btn-submit:hover:not(:disabled) { background: #1a4e4f; }
.btn-submit:disabled { opacity: 0.6; cursor: not-allowed; }

@media (max-width: 768px) {
  .modal { max-width: 100%; }
  .form-grid { grid-template-columns: 1fr; }
  .span-2 { grid-column: span 1; }
}
</style>
