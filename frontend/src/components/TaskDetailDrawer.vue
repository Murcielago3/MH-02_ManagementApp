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
import { computed } from 'vue'

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
</style>
