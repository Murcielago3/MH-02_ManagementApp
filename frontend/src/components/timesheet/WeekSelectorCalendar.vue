<template>
  <div class="calendar-container">
    <div v-if="pendingCount > 0" class="pending-alert" @click="selectOldestPending">
      <span class="material-symbols-outlined">warning</span>
      <span>You have {{ pendingCount }} pending timesheet(s)</span>
    </div>

    <div class="calendar-header">
      <button class="nav-btn" @click="changeMonth(-1)">
        <span class="material-symbols-outlined">chevron_left</span>
      </button>
      <h3 class="month-title">{{ currentMonthName }} {{ currentYear }}</h3>
      <button class="nav-btn" @click="changeMonth(1)">
        <span class="material-symbols-outlined">chevron_right</span>
      </button>
    </div>

    <div class="calendar-grid">
      <!-- Weekdays Header -->
      <div class="weekdays-row">
        <div class="weekday-cell" v-for="day in ['M', 'T', 'W', 'T', 'F', 'S', 'S']" :key="day">
          {{ day }}
        </div>
      </div>

      <!-- Calendar Weeks -->
      <div 
        v-for="(week, index) in weeks" 
        :key="index"
        class="week-row"
        :class="getWeekClasses(week)"
        @click="handleWeekClick(week)"
      >
        <div class="week-status-pill" v-if="getWeekStatus(week) && !isFuture(week)">
          {{ getStatusLabel(getWeekStatus(week)) }}
        </div>
        
        <div 
          v-for="day in week.days" 
          :key="day.dateString"
          class="day-cell"
          :class="{ 'is-weekend': day.isWeekend, 'is-other-month': day.isOtherMonth, 'is-today': day.isToday }"
        >
          {{ day.dayOfMonth }}
        </div>
      </div>
    </div>

    <div class="calendar-legend">
      <div class="legend-item"><span class="legend-dot pending"></span> Pending</div>
      <div class="legend-item"><span class="legend-dot submitted"></span> Submitted</div>
      <div class="legend-item"><span class="legend-dot approved"></span> Approved</div>
      <div class="legend-item"><span class="legend-dot rejected"></span> Rejected</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useTimesheetStore } from '../../stores/timesheet'

const timesheetStore = useTimesheetStore()

const props = defineProps({
  pendingCount: { type: Number, default: 0 }
})

// Current view state (month/year)
const today = new Date()
const currentMonth = ref(today.getMonth())
const currentYear = ref(today.getFullYear())

// Map pendingWeeks array to a map for quick lookup
// key: 'YYYY-MM-DD' (Monday), value: status
const weekStatusMap = computed(() => {
  const map = {}
  timesheetStore.pendingWeeks.forEach(pw => {
    map[pw.week_start] = pw.status
  })
  timesheetStore.submittedTimesheets.forEach(ts => {
    map[ts.week_start] = ts.status
  })
  return map
})

const currentMonthName = computed(() => {
  return new Date(currentYear.value, currentMonth.value, 1).toLocaleString('default', { month: 'long' })
})

function changeMonth(delta) {
  let m = currentMonth.value + delta
  let y = currentYear.value
  if (m > 11) { m = 0; y++ }
  if (m < 0) { m = 11; y-- }
  currentMonth.value = m
  currentYear.value = y
}

// Generate weeks for the currently selected month
const weeks = computed(() => {
  const firstDayOfMonth = new Date(currentYear.value, currentMonth.value, 1)
  const lastDayOfMonth = new Date(currentYear.value, currentMonth.value + 1, 0)
  
  // Find the Monday of the week containing the 1st of the month
  let startDate = new Date(firstDayOfMonth)
  let dayOfWeek = startDate.getDay() // 0 is Sunday, 1 is Monday
  let diff = startDate.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1) // Adjust when day is Sunday
  startDate.setDate(diff)

  const weeksArray = []
  
  // Create 6 weeks (max possible in a month view)
  let currentDay = new Date(startDate)
  
  for (let w = 0; w < 6; w++) {
    const week = {
      days: [],
      mondayDate: null,
      fridayDate: null
    }
    
    for (let d = 0; d < 7; d++) {
      const dateString = formatDate(currentDay)
      const isWeekend = d === 5 || d === 6 // Sat, Sun
      const isOtherMonth = currentDay.getMonth() !== currentMonth.value
      
      // Check if it's actual today
      const isToday = currentDay.toDateString() === today.toDateString()
      
      if (d === 0) week.mondayDate = dateString
      if (d === 4) week.fridayDate = dateString
      
      week.days.push({
        dayOfMonth: currentDay.getDate(),
        dateString,
        isWeekend,
        isOtherMonth,
        isToday
      })
      
      // Move to next day
      currentDay.setDate(currentDay.getDate() + 1)
    }
    
    weeksArray.push(week)
    
    // Break if the next week starts in a completely new month
    // (We only need to show weeks that contain days of the current month)
    if (w > 3 && currentDay.getMonth() !== currentMonth.value) {
      break
    }
  }
  
  return weeksArray
})

function isFuture(week) {
  const weekStart = new Date(week.mondayDate)
  weekStart.setHours(0, 0, 0, 0)
  const todayOnly = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  return weekStart > todayOnly
}

function formatDate(d) {
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function getWeekStatus(week) {
  return weekStatusMap.value[week.mondayDate] || null
}

function getStatusLabel(status) {
  if (!status) return ''
  return status.charAt(0).toUpperCase() + status.slice(1)
}

function getWeekClasses(week) {
  const status = getWeekStatus(week)
  const isSelected = timesheetStore.selectedWeek?.week_start === week.mondayDate
  const future = isFuture(week)
  
  // Check if current week (contains today)
  const isCurrentWeek = week.days.some(d => d.isToday)
  
  return {
    'status-pending': status === 'pending',
    'status-submitted': status === 'submitted',
    'status-approved': status === 'approved',
    'status-rejected': status === 'rejected',
    'is-selected': isSelected,
    'is-future': future,
    'is-current': isCurrentWeek && !isSelected
  }
}

function handleWeekClick(week) {
  if (isFuture(week)) return
  
  // Find if it's in pendingWeeks or submittedTimesheets to pass full object
  let status = getWeekStatus(week) || 'pending' // Default to pending if not found but not future
  
  let weekObj = {
    week_start: week.mondayDate,
    week_end: week.fridayDate,
    status: status
  }
  
  // Try to find the exact object from store if available
  const pendingMatch = timesheetStore.pendingWeeks.find(pw => pw.week_start === week.mondayDate)
  if (pendingMatch) {
    weekObj = pendingMatch
  } else {
    const subMatch = timesheetStore.submittedTimesheets.find(ts => ts.week_start === week.mondayDate)
    if (subMatch) weekObj = subMatch
  }
  
  timesheetStore.selectWeek(weekObj)
}

function selectOldestPending() {
  const pendingOnly = timesheetStore.pendingWeeks.filter(pw => pw.status === 'pending')
  if (pendingOnly.length > 0) {
    // Sort oldest first (assuming they are in format YYYY-MM-DD)
    pendingOnly.sort((a, b) => new Date(a.week_start) - new Date(b.week_start))
    const oldest = pendingOnly[0]
    
    // Change calendar to show that month
    const oldestDate = new Date(oldest.week_start)
    currentMonth.value = oldestDate.getMonth()
    currentYear.value = oldestDate.getFullYear()
    
    timesheetStore.selectWeek(oldest)
  }
}
</script>

<style scoped>
.calendar-container {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-outline-variant);
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.pending-alert {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.pending-alert:hover {
  background: rgba(239, 68, 68, 0.15);
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.month-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  margin: 0;
  color: var(--color-on-surface);
}

.nav-btn {
  background: none;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-full);
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--color-on-surface-variant);
  transition: all 0.2s;
}

.nav-btn:hover {
  background: var(--color-surface-container);
  color: var(--color-on-surface);
}

.calendar-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.weekdays-row {
  display: flex;
  margin-left: 20px; /* Offset for border */
}

.weekday-cell {
  flex: 1;
  text-align: center;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-on-surface-variant);
  padding-bottom: 8px;
}

.week-row {
  position: relative;
  display: flex;
  border-radius: var(--radius-md);
  border-left: 3px solid transparent;
  padding: 4px 0;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--color-surface);
}

.week-row:not(.is-future):hover {
  background: var(--color-surface-container);
}

/* Status styles */
.week-row.status-pending {
  background: rgba(239, 68, 68, 0.05);
  border-left-color: #ef4444;
}
.week-row.status-submitted {
  background: rgba(245, 158, 11, 0.05);
  border-left-color: #f59e0b;
}
.week-row.status-approved {
  background: rgba(34, 197, 94, 0.05);
  border-left-color: #22c55e;
}
.week-row.status-rejected {
  background: rgba(239, 68, 68, 0.05);
  border-left-color: #ef4444;
}

/* Selected state overrides */
.week-row.is-selected {
  background: rgba(40, 116, 117, 0.15) !important;
  border: 2px solid #287475 !important;
  border-left-width: 4px !important;
}

/* Current week state */
.week-row.is-current {
  border: 1px dashed #287475;
}

/* Future state */
.week-row.is-future {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Label Pill */
.week-status-pill {
  position: absolute;
  top: -10px;
  left: 12px;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  z-index: 2;
}
.status-pending .week-status-pill { background: #fee2e2; color: #ef4444; }
.status-submitted .week-status-pill { background: #fef3c7; color: #f59e0b; }
.status-approved .week-status-pill { background: #dcfce7; color: #22c55e; }
.status-rejected .week-status-pill { background: #fee2e2; color: #ef4444; }

.day-cell {
  flex: 1;
  text-align: center;
  font-size: 14px;
  padding: 8px 0;
  color: var(--color-on-surface);
}

.day-cell.is-other-month {
  color: var(--color-outline);
}

.day-cell.is-weekend {
  color: var(--color-on-surface-variant);
  opacity: 0.7;
}

.day-cell.is-today {
  font-weight: 700;
  color: var(--color-primary);
  position: relative;
}

.day-cell.is-today::after {
  content: '';
  position: absolute;
  bottom: 2px;
  left: 50%;
  transform: translateX(-50%);
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--color-primary);
}

/* Legend */
.calendar-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed var(--color-outline-variant);
  justify-content: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-on-surface-variant);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.legend-dot.pending { background: #ef4444; }
.legend-dot.submitted { background: #f59e0b; }
.legend-dot.approved { background: #22c55e; }
.legend-dot.rejected { background: #ef4444; border: 2px solid #ef4444; } /* Just red */
</style>
