<template>
  <div class="calendar-wrapper">
    <!-- Controls -->
    <div class="calendar-controls">
      <div class="controls-left">
        <button class="ctrl-btn" @click="prev"><span class="material-symbols-outlined">chevron_left</span></button>
        <button class="ctrl-btn today-btn" @click="goToday">Today</button>
        <button class="ctrl-btn" @click="next"><span class="material-symbols-outlined">chevron_right</span></button>
        <span class="ctrl-label">{{ periodLabel }}</span>
      </div>
      <div class="controls-right">
        <button class="ctrl-btn" :class="{ active: viewMode === 'week' }" @click="viewMode = 'week'">Week</button>
        <button class="ctrl-btn" :class="{ active: viewMode === 'month' }" @click="viewMode = 'month'">Month</button>
      </div>
    </div>

    <!-- Calendar -->
    <div class="calendar-container">
      <!-- Header Row -->
      <div class="cal-header">
        <div v-for="d in headerDays" :key="d.label" class="cal-header-cell">{{ d.label }}</div>
      </div>

      <!-- Weeks -->
      <div class="cal-body">
        <div
          v-for="(week, wi) in weeks"
          :key="wi"
          class="cal-week-row"
          :style="{ minHeight: weekMinHeight(wi) + 'px' }"
        >
          <!-- Timesheet Week Shading -->
          <div 
            v-if="getWeekTimesheet(wi)" 
            class="timesheet-week-bg" 
            :class="getWeekTimesheet(wi).status"
          >
            <div 
              class="timesheet-pill" 
              @click.stop="$emit('timesheet-click', getWeekTimesheet(wi))"
            >
              {{ timesheetLabel(getWeekTimesheet(wi).status) }}
            </div>
          </div>

          <!-- Day cells -->
          <div
            v-for="day in week"
            :key="day.dateStr"
            class="cal-day-cell"
            :class="{
              'other-month': !day.isCurrentMonth,
              'is-today': day.isToday,
              'is-leave': isLeaveDay(day.dateStr),
              'is-drag-highlight': isDragHighlight(day.dateStr),
            }"
            :data-date="day.dateStr"
            @mousedown.prevent="onCellMouseDown($event, day.dateStr)"
          >
            <span class="day-number">{{ day.num }}</span>
            <span v-if="isLeaveDay(day.dateStr)" class="leave-chip">On Leave</span>
          </div>

          <!-- Ribbon layer for this week -->
          <div class="ribbon-layer">
            <div
              v-for="ribbon in weekRibbons(wi)"
              :key="ribbon.task.id + '-' + wi"
              class="task-ribbon"
              :class="{ 'completed': ribbon.task.status === 'completed', 'drag-preview': ribbon.task._isDragPreview, 'delayed': isDelayed(ribbon.task) }"
              :style="ribbonStyle(ribbon)"
              @click.stop="$emit('ribbon-click', ribbon.task)"
              @mousedown.stop
            >
              <div class="ribbon-content">
                <span class="ribbon-title">{{ ribbon.task.title }}</span>
                <span v-if="isAdmin && userMap[ribbon.task.assigned_to]" class="ribbon-assignee">→ {{ userMap[ribbon.task.assigned_to].name }}</span>
                <span v-if="!isAdmin && ribbon.project" class="ribbon-project">{{ ribbon.project.name }}</span>
              </div>
              <!-- Delay badge -->
              <span v-if="isDelayed(ribbon.task)" class="delay-badge">
                {{ getTaskDelay(ribbon.task) }}d late
              </span>
              <!-- Drag handle (admin only) -->
              <div
                v-if="isAdmin && !ribbon.task._isDragPreview"
                class="drag-handle"
                title="Drag to extend"
                @mousedown.stop.prevent="onHandleMouseDown($event, ribbon.task)"
              ></div>
            </div>
          </div>

          <!-- Leave overlay layer -->
          <div class="leave-overlay-layer">
            <div v-for="(day, idx) in week" :key="'lo-'+day.dateStr" :style="{ gridColumn: idx + 1 }">
              <div v-if="isLeaveDay(day.dateStr)" class="leave-darken"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Legend -->
    <div class="calendar-legend" v-if="legendItems.length > 0">
      <div v-for="item in legendItems" :key="item.label" class="legend-item">
        <span class="legend-dot" :style="{ background: item.color }"></span>
        <span class="legend-label">{{ item.label }}</span>
      </div>
    </div>

    <!-- Drag tooltip -->
    <div v-if="dragState.mode" class="drag-tooltip" :style="tooltipStyle">
      <template v-if="dragState.mode === 'create'">
        {{ formatShort(dragState.startDate) }} → {{ formatShort(dragState.currentDate) }} · {{ dragDayCount }} days
      </template>
      <template v-if="dragState.mode === 'extend'">
        Ends: {{ formatShort(dragState.currentDate) }}
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, reactive } from 'vue'

const props = defineProps({
  tasks: { type: Array, default: () => [] },
  projectMap: { type: Object, default: () => ({}) },
  userMap: { type: Object, default: () => ({}) },
  leaves: { type: Array, default: () => [] },
  isAdmin: { type: Boolean, default: false },
  timesheetWeeks: { type: Array, default: () => [] } // { week_start, status }
})

const emit = defineEmits(['ribbon-click', 'cell-drag-create', 'ribbon-drag-extend', 'timesheet-click'])

const viewMode = ref('week')
const anchorDate = ref(new Date())

const todayStr = new Date().toISOString().split('T')[0]

// ── Delay detection ──
function getTaskDelay(task) {
  if (task.status === 'completed') return 0
  const deadline = task.end_date || task.date
  if (!deadline) return 0
  const diff = daysBetween(deadline, todayStr)
  return diff > 0 ? diff : 0
}

function isDelayed(task) {
  return getTaskDelay(task) > 0
}

// Priority fallback colors
const priorityColors = { high: '#ef4444', medium: '#f59e0b', low: '#22c55e' }

function getRibbonColor(task) {
  if (task.project_id && props.projectMap[task.project_id]?.color) {
    return props.projectMap[task.project_id].color
  }
  return priorityColors[task.priority] ?? '#287475'
}

// ── Navigation ──
function getMonday(d) {
  d = new Date(d)
  const day = d.getDay()
  const diff = d.getDate() - day + (day === 0 ? -6 : 1)
  return new Date(d.setDate(diff))
}

const prev = () => {
  const d = new Date(anchorDate.value)
  d.setDate(d.getDate() - (viewMode.value === 'week' ? 7 : 30))
  anchorDate.value = d
}
const next = () => {
  const d = new Date(anchorDate.value)
  d.setDate(d.getDate() + (viewMode.value === 'week' ? 7 : 30))
  anchorDate.value = d
}
const goToday = () => { anchorDate.value = new Date() }

const periodLabel = computed(() => {
  if (viewMode.value === 'week') {
    const mon = getMonday(anchorDate.value)
    const sun = new Date(mon)
    sun.setDate(sun.getDate() + 6)
    return `${formatShort(toStr(mon))} – ${formatShort(toStr(sun))}`
  }
  return new Date(anchorDate.value).toLocaleString('default', { month: 'long', year: 'numeric' })
})

// ── Header days ──
const headerDays = computed(() => {
  const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  return labels.map(l => ({ label: l }))
})

// ── Week rows ──
const weeks = computed(() => {
  if (viewMode.value === 'week') {
    const mon = getMonday(anchorDate.value)
    return [buildWeek(mon, -1)] // -1 = no month filter
  }
  // Month view
  const year = anchorDate.value.getFullYear()
  const month = anchorDate.value.getMonth()
  const first = new Date(year, month, 1)
  // Start from Monday on or before the 1st
  const start = getMonday(first)
  const rows = []
  for (let w = 0; w < 6; w++) {
    const weekStart = new Date(start)
    weekStart.setDate(start.getDate() + w * 7)
    rows.push(buildWeek(weekStart, month))
  }
  return rows
})

function buildWeek(monday, filterMonth) {
  const days = []
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday)
    d.setDate(d.getDate() + i)
    const dateStr = toStr(d)
    days.push({
      dateStr,
      num: d.getDate(),
      isCurrentMonth: filterMonth === -1 || d.getMonth() === filterMonth,
      isToday: dateStr === todayStr,
    })
  }
  return days
}

// ── Ribbon lane stacking per week ──
function weekRibbons(weekIndex) {
  const week = weeks.value[weekIndex]
  if (!week || week.length === 0) return []
  const weekStart = week[0].dateStr
  const weekEnd = week[6].dateStr

  // Filter tasks overlapping this week
  const overlapping = props.tasks.filter(t => {
    const tEnd = t.end_date || t.date
    return t.date <= weekEnd && tEnd >= weekStart
  })

  // Assign lanes (first-fit)
  const lanes = [] // lanes[dayIndex] = Set of lane indices occupied
  for (let i = 0; i < 7; i++) lanes.push(new Set())

  const result = []
  for (const task of overlapping) {
    const tEnd = task.end_date || task.date
    const rStart = task.date < weekStart ? weekStart : task.date
    const rEnd = tEnd > weekEnd ? weekEnd : tEnd
    const leftCells = daysBetween(weekStart, rStart)
    const widthCells = daysBetween(rStart, rEnd) + 1

    // Find first free lane
    let lane = 0
    let found = false
    while (!found) {
      found = true
      for (let c = leftCells; c < leftCells + widthCells; c++) {
        if (lanes[c].has(lane)) { found = false; break }
      }
      if (!found) lane++
    }
    // Occupy lane
    for (let c = leftCells; c < leftCells + widthCells; c++) {
      lanes[c].add(lane)
    }

    result.push({
      task,
      leftCells,
      widthCells,
      lane,
      project: task.project_id ? props.projectMap[task.project_id] : null,
    })
  }
  return result
}

function weekMinHeight(weekIndex) {
  const ribbons = weekRibbons(weekIndex)
  const maxLane = ribbons.length > 0 ? Math.max(...ribbons.map(r => r.lane)) : -1
  return Math.max(80, 32 + (maxLane + 1) * 28)
}

function ribbonStyle(ribbon) {
  const color = getRibbonColor(ribbon.task)
  return {
    left: `calc(${ribbon.leftCells} * (100% / 7) + 3px)`,
    width: `calc(${ribbon.widthCells} * (100% / 7) - 6px)`,
    top: `${28 + ribbon.lane * 28}px`,
    background: color,
    height: '24px',
    borderRadius: '4px',
    opacity: ribbon.task.status === 'completed' ? '0.5' : '0.88',
  }
}

// ── Timesheet Support ──
function getWeekTimesheet(wi) {
  const week = weeks.value[wi]
  if (!week || week.length === 0) return null
  const monday = week[0].dateStr
  return props.timesheetWeeks.find(tw => tw.week_start === monday)
}

function timesheetLabel(status) {
  if (status === 'pending') return 'Due'
  if (status === 'submitted') return 'Sent'
  if (status === 'approved') return 'OK'
  if (status === 'rejected') return 'Err'
  return ''
}

// ── Leave logic ──
function isLeaveDay(dateStr) {
  return props.leaves.some(l => dateStr >= l.start_date && dateStr <= l.end_date)
}

// ── Legend ──
const legendItems = computed(() => {
  const items = []
  const seenProjects = new Set()
  let hasNonProject = false
  for (const t of props.tasks) {
    if (t.project_id && props.projectMap[t.project_id] && !seenProjects.has(t.project_id)) {
      seenProjects.add(t.project_id)
      const p = props.projectMap[t.project_id]
      items.push({ color: p.color || '#287475', label: p.name })
    }
    if (!t.project_id) hasNonProject = true
  }
  if (hasNonProject) {
    items.push({ color: '#ef4444', label: 'High Priority' })
    items.push({ color: '#f59e0b', label: 'Medium Priority' })
    items.push({ color: '#22c55e', label: 'Low Priority' })
  }
  return items
})

// ── Drag State ──
const dragState = reactive({
  mode: null, // 'extend' | 'create' | null
  taskId: null,
  startDate: null,
  currentDate: null,
  originalEndDate: null,
  mouseX: 0,
  mouseY: 0,
})

const dragDayCount = computed(() => {
  if (!dragState.startDate || !dragState.currentDate) return 0
  return Math.abs(daysBetween(dragState.startDate, dragState.currentDate)) + 1
})

const tooltipStyle = computed(() => ({
  left: dragState.mouseX + 16 + 'px',
  top: dragState.mouseY - 32 + 'px',
}))

function isDragHighlight(dateStr) {
  if (dragState.mode !== 'create') return false
  if (!dragState.startDate || !dragState.currentDate) return false
  const min = dragState.startDate < dragState.currentDate ? dragState.startDate : dragState.currentDate
  const max = dragState.startDate > dragState.currentDate ? dragState.startDate : dragState.currentDate
  return dateStr >= min && dateStr <= max
}

function onCellMouseDown(e, dateStr) {
  if (!props.isAdmin) return
  dragState.mode = 'create'
  dragState.startDate = dateStr
  dragState.currentDate = dateStr
  dragState.mouseX = e.clientX
  dragState.mouseY = e.clientY
  document.body.style.userSelect = 'none'
}

function onHandleMouseDown(e, task) {
  if (!props.isAdmin) return
  dragState.mode = 'extend'
  dragState.taskId = task.id
  dragState.originalEndDate = task.end_date || task.date
  dragState.currentDate = task.end_date || task.date
  dragState.mouseX = e.clientX
  dragState.mouseY = e.clientY
  document.body.style.userSelect = 'none'
}

function onDocMouseMove(e) {
  if (!dragState.mode) return
  dragState.mouseX = e.clientX
  dragState.mouseY = e.clientY
  const el = document.elementFromPoint(e.clientX, e.clientY)
  const cell = el?.closest?.('[data-date]')
  if (cell) {
    const hoverDate = cell.dataset.date
    if (dragState.mode === 'extend') {
      // Can't go before task start
      const task = props.tasks.find(t => t.id === dragState.taskId)
      if (task && hoverDate >= task.date) {
        dragState.currentDate = hoverDate
      }
    } else {
      dragState.currentDate = hoverDate
    }
  }
}

function onDocMouseUp() {
  if (!dragState.mode) return
  document.body.style.userSelect = ''

  if (dragState.mode === 'create' && dragState.startDate && dragState.currentDate) {
    const min = dragState.startDate < dragState.currentDate ? dragState.startDate : dragState.currentDate
    const max = dragState.startDate > dragState.currentDate ? dragState.startDate : dragState.currentDate
    if (min === max || min !== max) {
      emit('cell-drag-create', { startDate: min, endDate: max })
    }
  }

  if (dragState.mode === 'extend' && dragState.taskId && dragState.currentDate) {
    if (dragState.currentDate !== dragState.originalEndDate) {
      emit('ribbon-drag-extend', { taskId: dragState.taskId, newEndDate: dragState.currentDate })
    }
  }

  dragState.mode = null
  dragState.taskId = null
  dragState.startDate = null
  dragState.currentDate = null
  dragState.originalEndDate = null
}

onMounted(() => {
  document.addEventListener('mousemove', onDocMouseMove)
  document.addEventListener('mouseup', onDocMouseUp)
})
onUnmounted(() => {
  document.removeEventListener('mousemove', onDocMouseMove)
  document.removeEventListener('mouseup', onDocMouseUp)
})

// ── Helpers ──
function toStr(d) { return d.toISOString().split('T')[0] }
function daysBetween(a, b) {
  return Math.round((new Date(b) - new Date(a)) / (1000 * 60 * 60 * 24))
}
function formatShort(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
}

// Expose viewMode & anchorDate for parent to watch
defineExpose({ viewMode, anchorDate })
</script>

<style scoped>
.calendar-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Controls */
.calendar-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.controls-left, .controls-right {
  display: flex;
  align-items: center;
  gap: 4px;
}
.ctrl-btn {
  height: 32px;
  padding: 0 12px;
  border: 1px solid var(--color-outline-variant);
  border-radius: 4px;
  background: var(--color-surface);
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-on-surface-variant);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.ctrl-btn:hover { background: var(--color-surface-container); }
.ctrl-btn.active {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}
.ctrl-btn .material-symbols-outlined { font-size: 18px; }
.ctrl-label {
  font-family: 'Integral CF', sans-serif;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-on-surface);
  margin-left: 12px;
}

/* Calendar container */
.calendar-container {
  background: var(--color-surface);
  border: 1px solid var(--color-outline-variant);
  border-radius: 8px;
  overflow: hidden;
}

.cal-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  border-bottom: 2px solid var(--color-outline-variant);
}
.cal-header-cell {
  padding: 10px;
  text-align: center;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-on-surface-variant);
  border-right: 1px solid var(--color-outline-variant);
}
.cal-header-cell:last-child { border-right: none; }

.cal-body { }

.cal-week-row {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  position: relative;
  border-bottom: 1px solid var(--color-outline-variant);
}
.cal-week-row:last-child { border-bottom: none; }

.cal-day-cell {
  padding: 6px 8px;
  border-right: 1px solid var(--color-outline-variant);
  position: relative;
  cursor: default;
  transition: background 0.15s;
  min-height: 32px;
}
.cal-day-cell:last-child { border-right: none; }
.cal-day-cell.other-month { background: #fafafa; }
.cal-day-cell.other-month .day-number { color: #9ca3af; }
.cal-day-cell.is-today {
  background: rgba(40, 116, 117, 0.04);
}
.cal-day-cell.is-today .day-number {
  background: var(--color-primary);
  color: #fff;
  border-radius: 50%;
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.cal-day-cell.is-leave {
  background: rgba(229, 231, 235, 0.6);
}
.cal-day-cell.is-drag-highlight {
  background: rgba(40, 116, 117, 0.12);
  outline: 1px dashed #287475;
  outline-offset: -1px;
}

.day-number {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-on-surface);
  font-variant-numeric: tabular-nums;
}

.leave-chip {
  display: block;
  font-size: 9px;
  color: #6b7280;
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 0.05em;
  margin-top: 2px;
}

/* Ribbon layer */
.ribbon-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.leave-overlay-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 6;
  display: grid;
  grid-template-columns: repeat(7, 1fr);
}

.leave-darken {
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.25);
  backdrop-filter: grayscale(80%);
}

.task-ribbon {
  position: absolute;
  display: flex;
  align-items: center;
  color: #fff;
  font-size: 11px;
  cursor: pointer;
  pointer-events: auto;
  overflow: hidden;
  z-index: 5;
  transition: opacity 0.15s;
}
.task-ribbon:hover { opacity: 1 !important; z-index: 10; filter: brightness(1.1); }
.task-ribbon.completed { text-decoration: line-through; }
.task-ribbon.drag-preview { opacity: 0.5; }
.task-ribbon.delayed {
  border-left: 3px solid #dc2626;
  background-image: repeating-linear-gradient(
    -45deg,
    transparent,
    transparent 6px,
    rgba(220, 38, 38, 0.12) 6px,
    rgba(220, 38, 38, 0.12) 12px
  );
  animation: delayed-pulse 2.5s ease-in-out infinite;
}
@keyframes delayed-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
  50% { box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.25); }
}

.delay-badge {
  flex-shrink: 0;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  background: #dc2626;
  color: #fff;
  padding: 1px 6px;
  border-radius: 3px;
  margin-right: 4px;
  white-space: nowrap;
  line-height: 1.4;
}

.ribbon-content {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0 6px;
  line-height: 1.1;
  flex: 1;
  min-width: 0;
}

.ribbon-title {
  font-weight: 700;
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ribbon-assignee, .ribbon-project {
  font-size: 10px;
  opacity: 0.8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Drag handle */
.drag-handle {
  width: 8px;
  height: 100%;
  position: absolute;
  right: 0;
  top: 0;
  cursor: col-resize;
  background: rgba(255,255,255,0.2);
  border-radius: 0 4px 4px 0;
  transition: background 0.15s;
}
.drag-handle:hover { background: rgba(255,255,255,0.5); }

/* Timesheet Support */
.timesheet-week-bg {
  position: absolute;
  top: 0; bottom: 0;
  left: calc(100% * 4 / 7);
  width: calc(100% / 7);
  z-index: 1;
  pointer-events: none;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 4px 2px;
}
.timesheet-week-bg.pending { background: rgba(239, 68, 68, 0.08); }
.timesheet-week-bg.rejected { background: rgba(239, 68, 68, 0.08); }
.timesheet-week-bg.submitted { background: rgba(245, 158, 11, 0.05); }
.timesheet-week-bg.approved { background: rgba(34, 197, 94, 0.05); }

.timesheet-pill {
  pointer-events: auto;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  cursor: pointer;
  z-index: 5;
}
.timesheet-week-bg.pending .timesheet-pill,
.timesheet-week-bg.rejected .timesheet-pill { background: #ef4444; color: #fff; }
.timesheet-week-bg.submitted .timesheet-pill { background: #f59e0b; color: #fff; }
.timesheet-week-bg.approved .timesheet-pill { background: #22c55e; color: #fff; }
.timesheet-pill:hover { filter: brightness(0.95); }

/* Legend */
.calendar-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 8px 0;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.legend-label {
  font-size: 12px;
  color: var(--color-on-surface-variant);
  font-weight: 500;
}

/* Drag tooltip */
.drag-tooltip {
  position: fixed;
  background: var(--color-on-surface);
  color: #fff;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  z-index: 9999;
  pointer-events: none;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
</style>
