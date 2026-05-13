<template>
  <EmployeeLayout>
    <div class="timesheet-view">
      <!-- Loading State -->
      <div v-if="timesheetStore.loading && !isInitialized" class="loading-state">
        <span class="material-symbols-outlined rotating">sync</span>
        <p>Loading timesheets...</p>
      </div>

      <!-- Main Content -->
      <div v-else class="content-grid">
        <!-- Left Column: Calendar -->
        <div class="calendar-column">
          <WeekSelectorCalendar :pendingCount="timesheetStore.pendingCount" />
        </div>

        <!-- Right Column: Form/Details -->
        <div class="form-column">
          <TimesheetFormPanel :projects="timesheetStore.projects" />
        </div>
      </div>
    </div>
  </EmployeeLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import EmployeeLayout from '../../components/EmployeeLayout.vue'
import WeekSelectorCalendar from '../../components/timesheet/WeekSelectorCalendar.vue'
import TimesheetFormPanel from '../../components/timesheet/TimesheetFormPanel.vue'
import { useTimesheetStore } from '../../stores/timesheet'

const timesheetStore = useTimesheetStore()
const isInitialized = ref(false)

onMounted(async () => {
  await timesheetStore.initialize()
  isInitialized.value = true
})
</script>

<style scoped>
.timesheet-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--color-on-surface-variant);
  gap: 16px;
}

.rotating {
  animation: spin 1.5s linear infinite;
  font-size: 32px;
  color: var(--color-primary);
}

@keyframes spin { 100% { transform: rotate(360deg); } }

.content-grid {
  display: grid;
  grid-template-columns: 35% 1fr;
  gap: 32px;
  height: 100%;
  align-items: flex-start;
}

@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }
}
</style>
