<template>
  <div class="form-container">
    <div v-if="week.status === 'rejected'" class="rejected-alert">
      <div class="alert-header">
        <span class="material-symbols-outlined">error</span>
        <h4>This timesheet was rejected</h4>
      </div>
      <p class="rejection-reason">{{ week.rejection_reason || 'No reason provided by admin.' }}</p>
    </div>

    <form @submit.prevent="handleSubmit" class="timesheet-form">
      <div v-if="store.loading" class="loading-overlay">
        <span class="material-symbols-outlined rotating">sync</span>
        <p>Fetching assigned tasks...</p>
      </div>

      <div class="form-section">
        <div class="section-header">
          <div>
            <label>Detailed Tasks</label>
            <p class="section-desc">Assigned tasks for this week are auto-pulled below. You can add more as needed.</p>
          </div>
          <button type="button" class="btn-add-task" @click="addTask">
            <span class="material-symbols-outlined">add</span>
            Add Task
          </button>
        </div>

        <div class="tasks-table-wrapper">
          <table class="tasks-table">
            <thead>
              <tr>
                <th class="col-project">Project</th>
                <th class="col-hours">Hours</th>
                <th class="col-desc">Task Description</th>
                <th class="col-action"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(entry, index) in entries" :key="index" :class="{ 'is-auto': entry.is_auto }">
                <td>
                  <select v-model="entry.project_id" required class="form-select">
                    <option :value="null" disabled>Select Project</option>
                    <option v-for="p in projects" :key="p.id" :value="p.id">
                      {{ p.name }}
                    </option>
                  </select>
                </td>
                <td>
                  <input 
                    v-model.number="entry.hours" 
                    type="number" 
                    step="0.5" 
                    min="0" 
                    max="80"
                    required 
                    class="form-input hours-input"
                  />
                </td>
                <td>
                  <div class="input-wrapper">
                    <input 
                      v-model="entry.description" 
                      type="text" 
                      placeholder="Describe your task..." 
                      required 
                      class="form-input"
                    />
                    <span v-if="entry.is_auto" class="auto-badge" title="Auto-pulled from assigned tasks">Auto</span>
                  </div>
                </td>
                <td>
                  <button 
                    type="button" 
                    class="btn-remove" 
                    @click="removeTask(index)" 
                    :disabled="entries.length === 1"
                  >
                    <span class="material-symbols-outlined">delete</span>
                  </button>
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td class="total-label">Total Hours</td>
                <td class="total-value" :class="{ 'text-success': totalHours > 0 }">
                  {{ totalHours }}h
                </td>
                <td colspan="2"></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      <div class="form-section">
        <label>Weekly Overview <span class="required">*</span></label>
        <p class="section-desc">Summarize your overall progress and blockers for the week (Required).</p>
        <textarea 
          v-model="description" 
          rows="3" 
          placeholder="Overall progress and highlights..."
          required
        ></textarea>
        <div class="char-count" v-if="description.length < 20">
          Min 20 characters ({{ description.length }}/20)
        </div>
      </div>

      <div class="form-actions">
        <button 
          type="submit" 
          class="btn-submit" 
          :disabled="!isValid || submitting"
        >
          <span class="material-symbols-outlined" v-if="!submitting">send</span>
          <span class="material-symbols-outlined rotating" v-else>sync</span>
          {{ submitLabel }}
        </button>
      </div>
    </form>

  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useTimesheetStore } from '../../stores/timesheet'

const props = defineProps({
  week: { type: Object, required: true },
  projects: { type: Array, required: true }
})

const emit = defineEmits(['submit'])
const store = useTimesheetStore()

const description = ref('')
const entries = ref([])
const submitting = ref(false)

// Sync from store
watch(() => props.week, () => {
  description.value = store.form.description || ''
  entries.value = JSON.parse(JSON.stringify(store.form.entries))
}, { immediate: true })

// Sync back to store
watch(description, (v) => store.form.description = v)
watch(entries, (v) => store.form.entries = v, { deep: true })

const totalHours = computed(() => {
  return entries.value.reduce((sum, e) => sum + (Number(e.hours) || 0), 0)
})

const isValid = computed(() => {
  if (entries.value.length === 0) return false
  const entriesValid = entries.value.every(e => e.project_id && e.hours > 0 && e.description.trim().length > 3)
  const descValid = description.value.trim().length >= 20
  return entriesValid && descValid
})

const submitLabel = computed(() => {
  if (submitting.value) return 'Submitting...'
  return props.week.status === 'rejected' ? 'Resubmit Timesheet' : 'Submit Timesheet'
})

function addTask() {
  entries.value.push({ project_id: null, hours: 0, description: '' })
}

function removeTask(index) {
  if (entries.value.length > 1) {
    entries.value.splice(index, 1)
  }
}

async function handleSubmit() {
  if (!isValid.value) return
  submitting.value = true
  try {
    await store.submitTimesheet()
    emit('submit')
  } catch (err) {
    // Error handled in store
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.form-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.rejected-alert {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: var(--radius-md);
  padding: 16px;
}

.alert-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #dc2626;
  margin-bottom: 8px;
}

.alert-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}

.rejection-reason {
  margin: 0;
  font-size: 14px;
  color: #b91c1c;
  font-style: italic;
}

.timesheet-form {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

label {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  color: var(--color-on-surface);
}

.section-desc {
  font-size: 13px;
  color: var(--color-on-surface-variant);
  margin: 4px 0 0 0;
}

.btn-add-task {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: var(--color-surface-container);
  color: var(--color-primary);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-add-task:hover {
  background: var(--color-surface-container-high);
  border-color: var(--color-primary);
}

.tasks-table-wrapper {
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.tasks-table {
  width: 100%;
  border-collapse: collapse;
}

.tasks-table th {
  background: var(--color-surface-container-low);
  padding: 10px 12px;
  text-align: left;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
  border-bottom: 1px solid var(--color-outline-variant);
}

.tasks-table td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--color-surface-container-high);
}

.col-hours { width: 80px; }
.col-action { width: 48px; }

.form-select, .form-input {
  width: 100%;
  padding: 8px;
  border: 1px solid var(--color-outline-variant);
  border-radius: 4px;
  font-size: 14px;
  color: var(--color-on-surface);
  background: var(--color-surface);
}

.form-select:focus, .form-input:focus {
  border-color: var(--color-primary);
  outline: none;
}

.hours-input {
  text-align: center;
}

.btn-remove {
  padding: 4px;
  background: none;
  border: none;
  color: var(--color-on-surface-variant);
  cursor: pointer;
}

.btn-remove:hover:not(:disabled) {
  color: #dc2626;
}

.btn-remove:disabled {
  opacity: 0.3;
}

.total-label {
  text-align: right;
  font-weight: 700;
  font-size: 13px;
  background: var(--color-surface-container-low);
}

.total-value {
  font-weight: 700;
  font-size: 15px;
  text-align: center;
  background: var(--color-surface-container-low);
}

textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-on-surface);
  background: var(--color-surface);
  resize: vertical;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px dashed var(--color-outline-variant);
}

.btn-submit {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-submit:hover:not(:disabled) {
  background: #1a4e4f;
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(255,255,255,0.8);
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--color-primary);
  font-weight: 600;
}

.is-auto {
  background: var(--color-surface-container-lowest);
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.auto-badge {
  position: absolute;
  right: 8px;
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
  font-size: 10px;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
}

.required {
  color: #dc2626;
}

.char-count {
  font-size: 11px;
  color: #dc2626;
  margin-top: 4px;
  text-align: right;
}

.rotating {
  animation: spin 1.5s linear infinite;
}

@keyframes spin { 100% { transform: rotate(360deg); } }
</style>

