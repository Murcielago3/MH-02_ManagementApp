<template>
  <div class="panel-container">
    <div v-if="!selectedWeek" class="empty-state">
      <div class="empty-icon-wrap">
        <span class="material-symbols-outlined empty-icon">calendar_month</span>
      </div>
      <h3>No Week Selected</h3>
      <p>Select a week from the calendar to view or submit your timesheet.</p>
    </div>

    <div v-else class="panel-content">
      <div class="panel-header">
        <div class="header-main">
          <h2 class="week-title">{{ formattedWeekRange }}</h2>
          <span class="status-badge" :class="selectedWeek.status">
            {{ formatStatus(selectedWeek.status) }}
          </span>
        </div>
        <p class="week-subtitle">Mon – Sun · 7 days</p>
      </div>

      <div class="panel-body">
        <TimesheetPendingForm 
          v-if="['pending', 'rejected'].includes(selectedWeek.status)"
          :week="selectedWeek"
          :projects="projects"
          @submit="handleSuccess"
        />
        
        <TimesheetReadOnly 
          v-else-if="['submitted', 'approved'].includes(selectedWeek.status)"
          :timesheet="selectedTimesheet"
          :projects="projects"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import TimesheetPendingForm from './TimesheetPendingForm.vue'
import TimesheetReadOnly from './TimesheetReadOnly.vue'
import { useTimesheetStore } from '../../stores/timesheet'

const store = useTimesheetStore()

const props = defineProps({
  projects: { type: Array, required: true }
})

const selectedWeek = computed(() => store.selectedWeek)
const selectedTimesheet = computed(() => store.selectedTimesheet || selectedWeek.value)

const formattedWeekRange = computed(() => {
  if (!selectedWeek.value) return ''
  const start = new Date(selectedWeek.value.week_start)
  const end = new Date(selectedWeek.value.week_end)
  
  const optionsShort = { day: '2-digit', month: 'short' }
  const optionsLong = { day: '2-digit', month: 'short', year: 'numeric' }
  
  return `Week of Mon ${start.toLocaleDateString('en-GB', optionsShort)} – Sun ${end.toLocaleDateString('en-GB', optionsLong)}`
})

function formatStatus(status) {
  if (!status) return ''
  if (status === 'submitted') return 'Awaiting Review'
  return status.charAt(0).toUpperCase() + status.slice(1)
}

function handleSuccess() {
  // Can trigger toast or animations here
  console.log('Timesheet submitted successfully')
}
</script>

<style scoped>
.panel-container {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-outline-variant);
  height: 100%;
  min-height: 600px;
  display: flex;
  flex-direction: column;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 48px;
  color: var(--color-on-surface-variant);
}

.empty-icon-wrap {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--color-surface-container);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
}

.empty-icon {
  font-size: 40px;
  color: var(--color-outline);
}

.empty-state h3 {
  font-family: var(--font-display);
  font-size: 20px;
  color: var(--color-on-surface);
  margin: 0 0 12px 0;
}

.empty-state p {
  font-size: 15px;
  max-width: 300px;
  line-height: 1.5;
  margin: 0;
}

.panel-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.panel-header {
  padding: 32px 32px 24px;
  border-bottom: 1px solid var(--color-outline-variant);
}

.header-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.week-title {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--color-on-surface);
  margin: 0;
}

.week-subtitle {
  font-size: 14px;
  color: var(--color-on-surface-variant);
  margin: 0;
}

.status-badge {
  padding: 6px 12px;
  border-radius: 99px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.status-badge.pending { background: #fee2e2; color: #ef4444; }
.status-badge.submitted { background: #fef3c7; color: #d97706; }
.status-badge.approved { background: #dcfce7; color: #15803d; }
.status-badge.rejected { background: #fee2e2; color: #ef4444; }

.panel-body {
  padding: 32px;
  flex: 1;
  overflow-y: auto;
}
</style>
