<template>
  <Teleport to="body">
    <div class="modal-backdrop">
      <div class="modal">
        <div class="modal-header">
          <h3 class="modal-title">{{ isEditing ? 'Edit Task' : 'Assign New Task' }}</h3>
          <button class="modal-close" @click="$emit('close')">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <form @submit.prevent="handleSubmit" class="modal-body">
          <div class="form-grid">
            <!-- Project -->
            <div class="form-field span-2">
              <label>Project</label>
              <select v-model="form.project_id">
                <option :value="null">— No Project —</option>
                <option v-for="p in projects" :key="p.id" :value="p.id">
                  ● {{ p.name }}
                </option>
              </select>
            </div>
            <!-- Assigned To -->
            <div class="form-field">
              <label>Assigned To *</label>
              <select v-model="form.assigned_to" required>
                <option :value="null">— Select Employee —</option>
                <option v-for="u in users" :key="u.id" :value="u.id">{{ u.name }}</option>
              </select>
            </div>
            <!-- Priority -->
            <div class="form-field">
              <label>Priority</label>
              <select v-model="form.priority">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
            <!-- Duration -->
            <div class="form-field">
              <label>Duration (hours)</label>
              <input v-model.number="form.duration_hours" type="number" placeholder="0" min="0" />
            </div>
            <!-- Date -->
            <div class="form-field">
              <label>Start Date *</label>
              <input v-model="form.date" type="date" required />
            </div>
            <!-- End Date -->
            <div class="form-field">
              <label>End Date</label>
              <input v-model="form.end_date" type="date" :min="form.date" />
            </div>
            <!-- Description -->
            <div class="form-field span-2">
              <label>Description</label>
              <textarea v-model="form.description" rows="3" placeholder="Optional details..."></textarea>
            </div>
          </div>

          <div v-if="formError" class="form-error">
            <span class="material-symbols-outlined">error</span>
            {{ formError }}
          </div>

          <div class="modal-footer">
            <button type="button" class="btn-cancel" @click="$emit('close')">Cancel</button>
            <button v-if="isEditing" type="button" class="btn-danger" @click="$emit('delete-task', editingId)">Delete</button>
            <button type="submit" class="btn-submit" :disabled="submitting">
              {{ submitting ? 'Saving…' : (isEditing ? 'Save Changes' : 'Assign Task') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'

const props = defineProps({
  users: { type: Array, default: () => [] },
  projects: { type: Array, default: () => [] },
  prefillDate: { type: String, default: '' },
  prefillEndDate: { type: String, default: '' },
  prefillAssignedTo: { type: Number, default: null },
  editTask: { type: Object, default: null }, // if set, we're editing
})

const emit = defineEmits(['close', 'submit', 'delete-task'])

const isEditing = ref(!!props.editTask)
const editingId = ref(props.editTask?.id || null)
const submitting = ref(false)
const formError = ref('')

const form = reactive({
  description: props.editTask?.description || '',
  date: props.editTask?.date || props.prefillDate || '',
  end_date: props.editTask?.end_date || props.prefillEndDate || '',
  duration_hours: props.editTask?.duration_hours || null,
  priority: props.editTask?.priority || 'medium',
  assigned_to: props.editTask?.assigned_to || props.prefillAssignedTo || null,
  project_id: props.editTask?.project_id || null,
})

async function handleSubmit() {
  formError.value = ''
  if (!form.date || !form.assigned_to) {
    formError.value = 'Date and assignee are required.'
    return
  }
  submitting.value = true
  try {
    const proj = props.projects.find(p => p.id === form.project_id)
    const derivedTitle = proj ? proj.name : 'General Task'

    const payload = {
      title: derivedTitle,
      description: form.description || null,
      date: form.date,
      end_date: form.end_date || null,
      duration_hours: form.duration_hours || null,
      priority: form.priority,
      assigned_to: form.assigned_to,
      project_id: form.project_id || null,
    }
    emit('submit', { payload, isEditing: isEditing.value, taskId: editingId.value })
  } catch (err) {
    formError.value = 'Failed to save task.'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.5); display: flex; align-items: center;
  justify-content: center; z-index: 1000;
}
.modal {
  background: #fff; border-radius: 8px; max-width: 720px; width: 92%;
  max-height: 90vh; overflow-y: auto;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 20px 24px; border-bottom: 1px solid var(--color-outline-variant);
}
.modal-title {
  font-family: 'Integral CF', sans-serif; font-size: 18px; font-weight: 700;
  color: var(--color-on-surface); margin: 0;
}
.modal-close {
  background: none; border: none; cursor: pointer; padding: 4px;
  border-radius: 4px; transition: background 0.15s;
}
.modal-close:hover { background: var(--color-surface-container); }
.modal-close .material-symbols-outlined { font-size: 20px; color: var(--color-on-surface-variant); }
.modal-body { padding: 24px; }

.form-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
  margin-bottom: 20px;
}
.form-field.span-2 { grid-column: span 2; }
.form-field label {
  display: block; font-size: 12px; font-weight: 600;
  color: var(--color-on-surface-variant); margin-bottom: 6px;
  text-transform: uppercase; letter-spacing: 0.03em;
}
.form-field input,
.form-field select,
.form-field textarea {
  width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1;
  border-radius: 4px; font-family: var(--font-body); font-size: 14px;
  color: var(--color-on-surface); outline: none; transition: border 0.15s;
  box-sizing: border-box; background: var(--color-surface);
}
.form-field input:focus,
.form-field select:focus,
.form-field textarea:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(40, 116, 117, 0.1);
}
.form-field textarea { resize: vertical; }

.form-error {
  display: flex; align-items: center; gap: 8px;
  padding: 12px; background: #fef2f2; border: 1px solid #fecaca;
  border-radius: 4px; margin-bottom: 16px;
  font-size: 13px; color: #dc2626;
}
.form-error .material-symbols-outlined { font-size: 16px; }

.modal-footer {
  display: flex; justify-content: flex-end; gap: 12px;
  padding: 16px 24px; border-top: 1px solid var(--color-outline-variant);
  background: var(--color-surface-container-lowest);
}
.btn-cancel {
  padding: 10px 16px; background: #fff; border: 1px solid var(--color-outline-variant);
  border-radius: 4px; font-size: 13px; font-weight: 600;
  color: var(--color-on-surface-variant); cursor: pointer;
}
.btn-cancel:hover { background: var(--color-surface-container); }
.btn-submit {
  padding: 10px 20px; background: var(--color-primary); color: #fff; border: none;
  border-radius: 4px; font-size: 13px; font-weight: 600; cursor: pointer;
}
.btn-submit:hover:not(:disabled) { background: #1a4e4f; }
.btn-submit:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-danger {
  padding: 10px 16px; background: #dc2626; color: #fff; border: none;
  border-radius: 4px; font-size: 13px; font-weight: 600; cursor: pointer;
}
.btn-danger:hover { background: #b91c1c; }

@media (max-width: 768px) {
  .modal { max-width: 100%; width: 100%; max-height: 92vh; }
  .modal-backdrop { padding: 8px; }
  .form-grid { grid-template-columns: 1fr !important; }
}
</style>
