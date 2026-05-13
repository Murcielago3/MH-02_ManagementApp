<template>
  <div class="readonly-container">
    <div class="read-section">
      <h3 class="section-title">Log Details</h3>
      <div class="table-wrapper">
        <table class="entries-table">
          <thead>
            <tr>
              <th class="col-project">Project</th>
              <th class="col-desc">Task Description</th>
              <th class="col-hours text-right">Hours</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entry in timesheet.entries" :key="entry.id">
              <td>
                <span class="project-tag">{{ getProjectName(entry.project_id) }}</span>
              </td>
              <td>{{ entry.description }}</td>
              <td class="text-right">{{ entry.hours }}h</td>
            </tr>
          </tbody>
          <tfoot>
            <tr>
              <td colspan="2" class="text-right total-label">Total Time</td>
              <td class="text-right total-value">{{ timesheet.total_hours }}h</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>

    <div v-if="timesheet.description" class="read-section">
      <h3 class="section-title">Weekly Overview</h3>
      <div class="overview-box">
        {{ timesheet.description }}
      </div>
    </div>

    <div class="status-notice" :class="timesheet.status">
      <span class="material-symbols-outlined icon" v-if="timesheet.status === 'submitted'">info</span>
      <span class="material-symbols-outlined icon" v-if="timesheet.status === 'approved'">check_circle</span>
      <span class="notice-text">
        {{ noticeText }}
      </span>
    </div>

    <div v-if="timesheet.status === 'rejected' && timesheet.rejection_reason" class="read-section">
      <h3 class="section-title text-error">Rejection Reason</h3>
      <div class="rejection-box">
        {{ timesheet.rejection_reason }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  timesheet: { type: Object, required: true },
  projects: { type: Array, required: true }
})

function getProjectName(id) {
  const p = props.projects.find(proj => proj.id === id)
  return p ? p.name : 'Unknown Project'
}

const noticeText = computed(() => {
  if (props.timesheet.status === 'submitted') {
    return 'This timesheet has been submitted and is awaiting admin review. You cannot edit it.'
  }
  if (props.timesheet.status === 'approved') {
    return '✓ This timesheet has been approved.'
  }
  return ''
})
</script>

<style scoped>
.readonly-container {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.read-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-on-surface-variant);
}

.table-wrapper {
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.entries-table {
  width: 100%;
  border-collapse: collapse;
}

.entries-table th {
  background: var(--color-surface-container-low);
  padding: 12px;
  text-align: left;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
  border-bottom: 1px solid var(--color-outline-variant);
}

.entries-table td {
  padding: 12px;
  border-bottom: 1px solid var(--color-surface-container-high);
  font-size: 14px;
}

.col-project { width: 180px; }
.col-hours { width: 100px; }

.project-tag {
  display: inline-block;
  padding: 4px 8px;
  background: var(--color-surface-container);
  border: 1px solid var(--color-outline-variant);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-primary);
}

.text-right { text-align: right; }

.total-label {
  font-weight: 700;
  color: var(--color-on-surface-variant);
  background: var(--color-surface-container-low);
}

.total-value {
  font-weight: 700;
  font-size: 16px;
  color: var(--color-primary);
  background: var(--color-surface-container-low);
}

.overview-box, .rejection-box {
  padding: 16px;
  background: var(--color-surface-container-low);
  border-radius: var(--radius-md);
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-on-surface);
  white-space: pre-wrap;
}

.rejection-box {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
}

.status-notice {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: var(--radius-md);
}

.status-notice.submitted {
  background: rgba(245, 158, 11, 0.1);
  color: #d97706;
}

.status-notice.approved {
  background: rgba(34, 197, 94, 0.1);
  color: #15803d;
}

.status-notice .icon {
  font-size: 24px;
}

.notice-text {
  font-size: 14px;
  font-weight: 600;
}

.text-error { color: #dc2626; }
</style>
