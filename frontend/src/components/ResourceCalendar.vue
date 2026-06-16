<template>
  <div class="resource-calendar">
    <div class="rc-controls">
      <div class="rc-controls-left">
        <button class="rc-btn rc-today" @click="goToday" title="Scroll back to today (T)">
          <span class="material-symbols-outlined">today</span>
          Today
        </button>
        <span class="rc-period">{{ periodLabel }}</span>
        <span class="rc-hint">Scroll horizontally or roll the mouse wheel to navigate · Today is highlighted</span>
        <div class="rc-divider"></div>
        <button
          class="rc-tool-toggle"
          :class="{ active: isSplitMode }"
          @click="isSplitMode = !isSplitMode"
          title="Toggle Split/Cut Mode"
        >
          <span class="material-symbols-outlined">{{ isSplitMode ? 'close' : 'content_cut' }}</span>
          {{ isSplitMode ? 'Exit Cut Mode' : 'Split Task' }}
        </button>
      </div>
    </div>

    <div class="rc-container" ref="containerRef" :class="{ dragging: drag.mode }" @wheel="onWheel">
      <div class="rc-scroll" :style="{ width: scrollWidth + 'px', minWidth: scrollWidth + 'px' }">
        <!-- Header -->
        <div class="rc-header">
          <div class="rc-corner">Team</div>
          <div
            v-for="day in visibleDays"
            :key="day.dateStr"
            class="rc-day-header"
            :class="{ today: day.isToday, weekend: day.isWeekend, 'week-start': day.isMonday, 'month-start': day.isFirstOfMonth }"
            :style="{ width: COL_W + 'px' }"
          >
            <span v-if="day.isFirstOfMonth" class="dh-month">{{ new Date(day.dateStr).toLocaleDateString('en-GB', { month: 'short' }) }}</span>
            <span class="dh-name">{{ day.label }}</span>
            <span class="dh-num">{{ day.num }}</span>
          </div>
        </div>

        <!-- Body -->
        <div class="rc-body" v-if="displayEmployees.length > 0">
          <div v-for="emp in displayEmployees" :key="emp.id" class="rc-row" :style="{ minHeight: rowMinH(emp.id) + 'px' }">
            <div class="rc-emp-cell" :class="{ overloaded: isOverloaded(emp.id) }">
              <div class="emp-avatar" :style="{ background: avatarColor(emp.name) }">{{ initials(emp.name) }}</div>
              <div class="emp-meta">
                <span class="emp-name">{{ emp.name }}</span>
                <span class="emp-hours" :class="hrsClass(emp.id)">
                  <template v-if="isOverloaded(emp.id)">{{ Math.round((getAssignedHours(emp.id) - 8) * 10) / 10 }}h over</template>
                  <template v-else-if="getRemaining(emp.id) > 0">{{ getRemaining(emp.id) }}h left</template>
                  <template v-else>0h ✓</template>
                </span>
              </div>
            </div>
            <div class="rc-timeline" :style="{ gridTemplateColumns: `repeat(${visibleDays.length}, ${COL_W}px)` }">
              <div
                v-for="day in visibleDays"
                :key="day.dateStr"
                class="rc-cell"
                :class="{ today: day.isToday && !day.isWeekend, weekend: day.isWeekend, 'is-leave': isEmpLeave(emp.id, day.dateStr), 'drag-hl': isDragHL(day.dateStr, emp.id), 'week-start': day.isMonday, 'month-start': day.isFirstOfMonth }"
                :data-date="day.dateStr"
                :data-employee="emp.id"
                @mousedown.prevent="!day.isWeekend && onCellDown($event, day.dateStr, emp.id)"
              >
                <span v-if="isEmpLeave(emp.id, day.dateStr)" class="leave-tag">Leave</span>
              </div>
              <div class="rc-ribbon-layer">
                <div
                  v-for="rb in empRibbons(emp.id)"
                  :key="rb.task.id"
                  class="rc-ribbon"
                  :class="{ completed: rb.task.status === 'completed', delayed: isDelayed(rb.task) }"
                  :style="rbStyle(rb)"
                  @click.stop="$emit('ribbon-click', rb.task)"
                  @dblclick.stop="onSplit($event, rb.task)"
                  @mousedown.stop
                >
                  <div 
                    class="rb-handle rb-handle-start" 
                    @mousedown.stop.prevent="onHandleDown($event, rb.task, 'resize-start')"
                  ></div>
                  <div 
                    class="rb-content" 
                    @mousedown.stop.prevent="onRibbonDown($event, rb.task)"
                    @mousemove="onRibbonHover($event, rb.task)"
                    @mouseleave="hoverState.taskId = null"
                    :class="{ 'cut-ready': isSplitMode && hoverState.taskId === rb.task.id }"
                  >
                    <span class="rb-title">{{ rb.task.title }}</span>
                    <span v-if="rb.project" class="rb-project">{{ rb.project.name }}</span>
                  </div>
                  <div 
                    v-if="isSplitMode && hoverState.taskId === rb.task.id && canSplit(rb.task)"
                    class="rb-tools"
                    :style="{ left: hoverState.x + 'px' }"
                  >
                    <div class="rb-cut-line"></div>
                    <div class="rb-cut-indicator">
                      <span class="material-symbols-outlined">content_cut</span>
                    </div>
                  </div>
                  <span v-if="isDelayed(rb.task)" class="rb-delay">{{ taskDelay(rb.task) }}d</span>
                  <div 
                    class="rb-handle rb-handle-end" 
                    @mousedown.stop.prevent="onHandleDown($event, rb.task, 'resize-end')"
                  ></div>
                </div>
              </div>
              <div class="rc-leave-overlay-layer" :style="{ gridTemplateColumns: `repeat(${visibleDays.length}, ${COL_W}px)` }">
                <div v-for="(day, idx) in visibleDays" :key="'lo-'+day.dateStr" :style="{ gridColumn: idx + 1 }">
                  <div v-if="isEmpLeave(emp.id, day.dateStr)" class="leave-darken"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="rc-empty">No employees to display</div>
      </div>
    </div>

    <div class="rc-legend" v-if="legendItems.length">
      <div v-for="item in legendItems" :key="item.label" class="rc-legend-item">
        <span class="rc-legend-dot" :style="{ background: item.color }"></span>
        <span>{{ item.label }}</span>
      </div>
    </div>

    <div v-if="drag.mode" class="rc-tooltip" :style="{ left: drag.mx + 16 + 'px', top: drag.my - 32 + 'px' }">
      <template v-if="drag.mode === 'create'">{{ fmtShort(drag.startDate) }} → {{ fmtShort(drag.currentDate) }} · {{ dragDays }} days</template>
      <template v-else-if="drag.mode === 'resize-end'">Ends: {{ fmtShort(drag.currentDate) }}</template>
      <template v-else-if="drag.mode === 'resize-start'">Starts: {{ fmtShort(drag.currentDate) }}</template>
      <template v-else-if="drag.mode === 'move' || drag.mode === 'clone'">
        <span class="tooltip-mode">{{ drag.mode === 'clone' ? 'COPY' : 'MOVE' }}</span>
        {{ fmtShort(drag.currentDate) }} · {{ userMap[drag.empId]?.name }}
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, onUnmounted, watch, nextTick } from 'vue'

const props = defineProps({
  tasks: { type: Array, default: () => [] },
  employees: { type: Array, default: () => [] },
  projectMap: { type: Object, default: () => ({}) },
  leaves: { type: Array, default: () => [] },
  filterEmployeeId: { type: Number, default: null },
})
const emit = defineEmits(['ribbon-click', 'cell-drag-create', 'ribbon-drag-extend', 'ribbon-move', 'ribbon-clone', 'ribbon-split', 'range-change'])

const COL_W = 120
const EMP_W = 200
// Infinite scroll: render a wide window, extend dynamically on edge approach.
const INITIAL_PAD_DAYS = 90      // days rendered on each side of today at first
const EXTEND_BY = 60             // how many days to add when an edge is reached
const EDGE_THRESHOLD_PX = 600    // start extending when within this many px of an edge

const containerRef = ref(null)
const todayStr = (() => {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
})()

// Range refs: rangeStart is the leftmost day rendered; rangeEnd is the rightmost.
function makeDate(offset = 0) {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  d.setDate(d.getDate() + offset)
  return d
}
const rangeStart = ref(makeDate(-INITIAL_PAD_DAYS))
const rangeEnd = ref(makeDate(INITIAL_PAD_DAYS))

// "anchorDate" kept for backward compat with parent that reads it.
// Now exposed as the date currently in the centre of the viewport.
const anchorDate = ref(new Date())

const visibleDays = computed(() => {
  const labels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  const days = []
  const total = daysBetween(toStr(rangeStart.value), toStr(rangeEnd.value)) + 1
  for (let i = 0; i < total; i++) {
    const d = new Date(rangeStart.value)
    d.setDate(d.getDate() + i)
    const ds = toStr(d)
    const dow = d.getDay()
    days.push({
      label: labels[dow],
      num: d.getDate(),
      dateStr: ds,
      isToday: ds === todayStr,
      isWeekend: dow === 0 || dow === 6,
      isMonday: dow === 1,
      isFirstOfMonth: d.getDate() === 1,
    })
  }
  return days
})

const scrollWidth = computed(() => EMP_W + visibleDays.value.length * COL_W)

// Month label shown in the toolbar, based on whatever date sits at the viewport centre.
const periodLabel = computed(() => {
  const a = anchorDate.value
  return a.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })
})

// ───────── Scroll behaviour ─────────
// Centers `today` in the viewport accounting for the sticky employee column
// on the left. We want today's column-center to land at the centre of the
// visible *day* area (i.e. the viewport minus the sticky emp column).
let initialCenterDone = false
let centerObserver = null
function computeCenterScrollLeft(c) {
  const days = visibleDays.value
  const todayIdx = days.findIndex(d => d.isToday)
  if (todayIdx < 0) return null
  const todayCenter = EMP_W + todayIdx * COL_W + COL_W / 2
  // Centre of the day-area in scroll coords:
  //   scrollLeft + EMP_W + (clientWidth - EMP_W) / 2
  // Solve for scrollLeft so todayCenter sits there.
  return todayCenter - EMP_W - (c.clientWidth - EMP_W) / 2
}
function tryCenterToday() {
  const c = containerRef.value
  if (!c) return false
  if (c.clientWidth === 0) return false
  const target = computeCenterScrollLeft(c)
  if (target == null) return false
  // Use the JS-computed scrollWidth as the source of truth (the DOM may not have
  // applied the inline width yet, but we know what it *will* be).
  const effectiveScrollWidth = Math.max(c.scrollWidth, scrollWidth.value)
  const max = Math.max(0, effectiveScrollWidth - c.clientWidth)
  suppressEdgeChecks = true
  c.scrollLeft = Math.max(0, Math.min(target, max))
  initialCenterDone = true
  requestAnimationFrame(() => { suppressEdgeChecks = false })
  return true
}
function scrollToToday() {
  if (tryCenterToday()) return
  // Container not laid out yet — observe size changes and center the first time
  // we get a real width. Cleaner than polling RAF for fixed N attempts.
  if (centerObserver) return
  centerObserver = new ResizeObserver(() => {
    if (tryCenterToday()) {
      centerObserver.disconnect()
      centerObserver = null
    }
  })
  if (containerRef.value) centerObserver.observe(containerRef.value)
}

const goToday = () => {
  const today = makeDate(0)
  if (today < rangeStart.value || today > rangeEnd.value) {
    rangeStart.value = makeDate(-INITIAL_PAD_DAYS)
    rangeEnd.value = makeDate(INITIAL_PAD_DAYS)
  }
  initialCenterDone = false
  nextTick(() => scrollToToday())
}

// Mouse-wheel → horizontal scroll. Bound from the template via @wheel
// (Vue 3 default is non-passive, so preventDefault works).
const WHEEL_MAX = COL_W * 1.5  // 180 px per event max
function onWheel(e) {
  const c = containerRef.value
  if (!c) return
  const dx = e.deltaX
  const dy = e.deltaY
  // Pure horizontal trackpad swipes: let them through natively
  if (Math.abs(dx) > Math.abs(dy)) return
  if (dy === 0) return
  // Always claim the event — calendar always has overflow, so vertical wheel = horizontal calendar scroll
  e.preventDefault()
  let delta = dy
  if (e.deltaMode === 1) delta = dy * 16
  else if (e.deltaMode === 2) delta = dy * c.clientHeight
  if (delta > WHEEL_MAX) delta = WHEEL_MAX
  else if (delta < -WHEEL_MAX) delta = -WHEEL_MAX
  c.scrollLeft += delta
}

function updateAnchorFromScroll() {
  const c = containerRef.value
  if (!c) return
  // The date in the centre of the visible day-area
  const centerX = c.scrollLeft + EMP_W + (c.clientWidth - EMP_W) / 2
  const idx = Math.max(0, Math.floor((centerX - EMP_W) / COL_W))
  const days = visibleDays.value
  if (days[idx]) {
    const d = new Date(days[idx].dateStr)
    if (toStr(d) !== toStr(anchorDate.value)) anchorDate.value = d
  }
}

let extending = false
let suppressEdgeChecks = true   // True until initial centring completes
function onScroll() {
  const c = containerRef.value
  if (!c) return
  updateAnchorFromScroll()
  if (extending || suppressEdgeChecks || !initialCenterDone) return

  if (c.scrollLeft < EDGE_THRESHOLD_PX) {
    extending = true
    const prev = new Date(rangeStart.value)
    prev.setDate(prev.getDate() - EXTEND_BY)
    rangeStart.value = prev
    nextTick(() => {
      if (containerRef.value) containerRef.value.scrollLeft += EXTEND_BY * COL_W
      requestAnimationFrame(() => { extending = false })
      emit('range-change', { startDate: toStr(rangeStart.value), endDate: toStr(rangeEnd.value) })
    })
    return
  }
  const remaining = c.scrollWidth - (c.scrollLeft + c.clientWidth)
  if (remaining < EDGE_THRESHOLD_PX) {
    extending = true
    const nxt = new Date(rangeEnd.value)
    nxt.setDate(nxt.getDate() + EXTEND_BY)
    rangeEnd.value = nxt
    nextTick(() => {
      requestAnimationFrame(() => { extending = false })
      emit('range-change', { startDate: toStr(rangeStart.value), endDate: toStr(rangeEnd.value) })
    })
  }
}

onMounted(async () => {
  if (containerRef.value) {
    containerRef.value.addEventListener('scroll', onScroll, { passive: true })
  }
  // Wait for the DOM to flush so the .rc-scroll inline width is applied
  await nextTick()
  scrollToToday()
  emit('range-change', { startDate: toStr(rangeStart.value), endDate: toStr(rangeEnd.value) })
})
onUnmounted(() => {
  if (centerObserver) { centerObserver.disconnect(); centerObserver = null }
  if (containerRef.value) {
    containerRef.value.removeEventListener('scroll', onScroll)
  }
})

// Employees
const displayEmployees = computed(() => props.filterEmployeeId ? props.employees.filter(e => e.id === props.filterEmployeeId) : props.employees)

// Hours
function getAssignedHours(eid) {
  if (isEmpLeave(eid, todayStr)) return 0
  let h = 0
  for (const t of props.tasks) {
    if (t.assigned_to === eid && t.status !== 'completed') {
      const e = t.end_date || t.date
      // Does this task cover today?
      if (t.date <= todayStr && e >= todayStr) {
        // duration_hours = daily hours for this task (e.g. 2 = 2h/day)
        // If not set, assume full 8-hour day
        h += (t.duration_hours != null && t.duration_hours > 0) ? t.duration_hours : 8
      }
    }
  }
  return Math.round(h * 10) / 10
}
function getRemaining(eid) { return Math.round(Math.max(0, 8 - getAssignedHours(eid)) * 10) / 10 }
function isOverloaded(eid) { return getAssignedHours(eid) > 8 }
function hrsClass(eid) { if (isOverloaded(eid)) return 'hrs-over'; const r = getRemaining(eid); if (r === 0) return 'hrs-done'; if (r <= 3) return 'hrs-busy'; return 'hrs-ok' }

// Ribbons
const priorityColors = { high: '#ef4444', medium: '#f59e0b', low: '#22c55e' }
function rbColor(t) { if (t.project_id && props.projectMap[t.project_id]?.color) return props.projectMap[t.project_id].color; return priorityColors[t.priority] ?? '#287475' }
function taskDelay(t) { if (t.status === 'completed') return 0; const dl = t.end_date || t.date; if (!dl) return 0; const d = daysBetween(dl, todayStr); return d > 0 ? d : 0 }
function isDelayed(t) { return taskDelay(t) > 0 }

function empRibbons(eid) {
  const days = visibleDays.value, vStart = days[0].dateStr, vEnd = days[days.length - 1].dateStr
  const empTasks = props.tasks.filter(t => t.assigned_to === eid && t.date <= vEnd && (t.end_date || t.date) >= vStart)
  const lanes = Array.from({ length: days.length }, () => new Set())
  const result = []
  for (const task of empTasks) {
    const tEnd = task.end_date || task.date
    const rS = task.date < vStart ? vStart : task.date, rE = tEnd > vEnd ? vEnd : tEnd
    const left = daysBetween(vStart, rS), width = daysBetween(rS, rE) + 1
    let lane = 0, ok = false
    while (!ok) { ok = true; for (let c = left; c < left + width; c++) if (lanes[c]?.has(lane)) { ok = false; break }; if (!ok) lane++ }
    for (let c = left; c < left + width; c++) if (lanes[c]) lanes[c].add(lane)
    result.push({ task, left, width, lane, project: task.project_id ? props.projectMap[task.project_id] : null })
  }
  return result
}

function rowMinH(eid) { const rbs = empRibbons(eid); const ml = rbs.length ? Math.max(...rbs.map(r => r.lane)) : -1; return Math.max(56, 28 + (ml + 1) * 28) }

function rbStyle(rb) {
  return { left: `${rb.left * COL_W + 2}px`, width: `${rb.width * COL_W - 4}px`, top: `${4 + rb.lane * 28}px`, background: rbColor(rb.task), height: '26px', borderRadius: '4px', opacity: rb.task.status === 'completed' ? '0.45' : '1', border: '1px solid rgba(0,0,0,0.18)', boxShadow: '0 1px 3px rgba(0,0,0,0.15)' }
}

// Leave
function isEmpLeave(eid, ds) { return props.leaves.some(l => (l.employee_id ?? l.user_id) === eid && ds >= l.start_date && ds <= l.end_date) }

// Legend
const legendItems = computed(() => {
  const items = [], seen = new Set(); let hasNone = false
  for (const t of props.tasks) { if (t.project_id && props.projectMap[t.project_id] && !seen.has(t.project_id)) { seen.add(t.project_id); const p = props.projectMap[t.project_id]; items.push({ color: p.color || '#287475', label: p.name }) }; if (!t.project_id) hasNone = true }
  if (hasNone) { items.push({ color: '#ef4444', label: 'High' }, { color: '#f59e0b', label: 'Medium' }, { color: '#22c55e', label: 'Low' }) }
  return items
})

// Drag
const drag = reactive({ 
  mode: null, 
  taskId: null, 
  empId: null, 
  startDate: null, 
  currentDate: null, 
  origEnd: null, 
  origStart: null,
  offsetDays: 0,
  mx: 0, 
  my: 0 
})
const dragDays = computed(() => (!drag.startDate || !drag.currentDate) ? 0 : Math.abs(daysBetween(drag.startDate, drag.currentDate)) + 1)

const hoverState = reactive({ taskId: null, date: null, x: 0 })
const isSplitMode = ref(false)

function canSplit(task) {
  const dur = daysBetween(task.date, task.end_date || task.date)
  return dur >= 1 // Must be at least 2 days long to split
}
let scrollRAF = null

function isDragHL(ds, eid) {
  if (drag.mode !== 'create' || drag.empId !== eid) return false
  const mn = drag.startDate < drag.currentDate ? drag.startDate : drag.currentDate
  const mx = drag.startDate > drag.currentDate ? drag.startDate : drag.currentDate
  return ds >= mn && ds <= mx
}

function onCellDown(e, ds, eid) { drag.mode = 'create'; drag.empId = eid; drag.startDate = ds; drag.currentDate = ds; drag.mx = e.clientX; drag.my = e.clientY; document.body.style.userSelect = 'none'; startAutoScroll() }

function onRibbonDown(e, task) {
  if (isSplitMode.value) {
    onSplit(e, task)
    return
  }
  // Use elementsFromPoint to find the cell UNDER the ribbon
  const elements = document.elementsFromPoint(e.clientX, e.clientY)
  const cell = elements.find(el => el.dataset?.date)
  const ds = cell?.dataset.date
  
  if (!ds) return
  
  drag.mode = e.shiftKey ? 'clone' : 'move'
  drag.taskId = task.id
  drag.empId = task.assigned_to
  drag.startDate = task.date
  drag.currentDate = ds
  drag.origStart = task.date
  drag.origEnd = task.end_date || task.date
  drag.offsetDays = daysBetween(task.date, ds)
  drag.mx = e.clientX
  drag.my = e.clientY
  document.body.style.userSelect = 'none'
  startAutoScroll()
}

function onHandleDown(e, task, mode) { 
  drag.mode = mode // 'resize-start' or 'resize-end'
  drag.taskId = task.id
  drag.empId = task.assigned_to
  drag.origStart = task.date
  drag.origEnd = task.end_date || task.date
  drag.startDate = task.date
  drag.currentDate = mode === 'resize-start' ? task.date : (task.end_date || task.date)
  drag.mx = e.clientX
  drag.my = e.clientY
  document.body.style.userSelect = 'none'
  startAutoScroll()
}

function onRibbonHover(e, task) {
  if (drag.mode || !isSplitMode.value) { hoverState.taskId = null; return }
  
  const elements = document.elementsFromPoint(e.clientX, e.clientY)
  const cell = elements.find(el => el.dataset?.date)
  const ds = cell?.dataset.date
  
  if (ds && ds > task.date) {
    const rect = e.currentTarget.getBoundingClientRect()
    hoverState.taskId = task.id
    hoverState.date = ds
    // Position relative to ribbon start
    const dayOffset = daysBetween(task.date, ds)
    hoverState.x = dayOffset * COL_W
  } else {
    hoverState.taskId = null
  }
}

function onSplit(e, task) {
  const ds = hoverState.date
  if (ds && ds > task.date && ds <= (task.end_date || task.date)) {
    emit('ribbon-split', { taskId: task.id, splitDate: ds })
    hoverState.taskId = null
  }
}

function onMove(e) {
  if (!drag.mode) return
  drag.mx = e.clientX; drag.my = e.clientY
  
  const elements = document.elementsFromPoint(e.clientX, e.clientY)
  const cell = elements.find(el => el.dataset?.date)
  
  if (cell) {
    const hd = cell.dataset.date
    const eid = parseInt(cell.dataset.employee)
    
    if (drag.mode === 'resize-end') {
      if (hd >= drag.origStart) drag.currentDate = hd
    } else if (drag.mode === 'resize-start') {
      if (hd <= drag.origEnd) drag.currentDate = hd
    } else if (drag.mode === 'move' || drag.mode === 'clone') {
      drag.currentDate = hd
      drag.empId = eid
    } else {
      drag.currentDate = hd
    }
  }
}

function startAutoScroll() {
  function tick() {
    if (!drag.mode || !containerRef.value) return
    const rect = containerRef.value.getBoundingClientRect()
    const threshold = 80
    if (drag.mx > rect.right - threshold) containerRef.value.scrollLeft += 10
    else if (drag.mx < rect.left + EMP_W + threshold && containerRef.value.scrollLeft > 0) containerRef.value.scrollLeft -= 10
    scrollRAF = requestAnimationFrame(tick)
  }
  scrollRAF = requestAnimationFrame(tick)
}
function stopAutoScroll() { if (scrollRAF) { cancelAnimationFrame(scrollRAF); scrollRAF = null } }

function onUp() {
  if (!drag.mode) return
  document.body.style.userSelect = ''; stopAutoScroll()
  
  if (drag.mode === 'create' && drag.startDate && drag.currentDate) {
    const mn = drag.startDate < drag.currentDate ? drag.startDate : drag.currentDate
    const mx = drag.startDate > drag.currentDate ? drag.startDate : drag.currentDate
    emit('cell-drag-create', { startDate: mn, endDate: mx, employeeId: drag.empId })
  } else if (drag.mode === 'resize-end' && drag.currentDate !== drag.origEnd) {
    emit('ribbon-drag-extend', { taskId: drag.taskId, newEndDate: drag.currentDate })
  } else if (drag.mode === 'resize-start' && drag.currentDate !== drag.origStart) {
    // Re-use extend event or emit new
    emit('ribbon-move', { taskId: drag.taskId, newDate: drag.currentDate, newEndDate: drag.origEnd, newEmployeeId: drag.empId })
  } else if ((drag.mode === 'move' || drag.mode === 'clone') && drag.currentDate) {
    const task = props.tasks.find(t => t.id === drag.taskId)
    if (task) {
      const dur = daysBetween(task.date, task.end_date || task.date)
      const d = new Date(drag.currentDate)
      d.setDate(d.getDate() - drag.offsetDays)
      const newStart = toStr(d)
      const d2 = new Date(d)
      d2.setDate(d2.getDate() + dur)
      const newEnd = toStr(d2)
      
      if (drag.mode === 'move') {
        emit('ribbon-move', { taskId: drag.taskId, newDate: newStart, newEndDate: newEnd, newEmployeeId: drag.empId })
      } else {
        emit('ribbon-clone', { taskId: drag.taskId, newDate: newStart, newEndDate: newEnd, newEmployeeId: drag.empId })
      }
    }
  }
  
  Object.assign(drag, { mode: null, taskId: null, empId: null, startDate: null, currentDate: null, origEnd: null, origStart: null, offsetDays: 0 })
}

onMounted(() => { document.addEventListener('mousemove', onMove); document.addEventListener('mouseup', onUp) })
onUnmounted(() => { document.removeEventListener('mousemove', onMove); document.removeEventListener('mouseup', onUp); stopAutoScroll() })

// Helpers
function toStr(d) {
  // Local-time YYYY-MM-DD (avoids UTC offset off-by-one)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}
function daysBetween(a, b) { return Math.round((new Date(b) - new Date(a)) / 864e5) }
function fmtShort(s) { if (!s) return ''; return new Date(s).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) }
const ap = ['#287475', '#6366f1', '#ec4899', '#f59e0b', '#3b82f6', '#8b5cf6', '#ef4444', '#14b8a6']
function avatarColor(n) { let h = 0; for (let i = 0; i < n.length; i++) h = n.charCodeAt(i) + ((h << 5) - h); return ap[Math.abs(h) % ap.length] }
function initials(n) { return n.split(' ').map(x => x[0]).join('').toUpperCase().slice(0, 2) }

defineExpose({ anchorDate, rangeStart, rangeEnd, scrollToToday: goToday })
</script>

<style scoped>
/* min-width: 0 + width: 100% so this flex item doesn't expand to its content's (21920px) width.
   Without this, the whole page becomes 21920px wide, the inner container never overflows,
   and wheel events fall through to vertical page scroll. */
.resource-calendar { display: flex; flex-direction: column; gap: 16px; min-width: 0; width: 100%; max-width: 100%; }
.rc-controls { display: flex; justify-content: space-between; align-items: center; }
.rc-controls-left { display: flex; align-items: center; gap: 4px; }
.rc-btn { height: 32px; padding: 0 12px; border: 1px solid var(--color-outline-variant); border-radius: 4px; background: var(--color-surface); font-family: var(--font-body); font-size: 12px; font-weight: 600; color: var(--color-on-surface-variant); cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all .15s; }
.rc-btn:hover { background: var(--color-surface-container); }
.rc-btn .material-symbols-outlined { font-size: 18px; }
.rc-period { font-family: 'Integral CF', sans-serif; font-size: 16px; font-weight: 600; color: var(--color-on-surface); margin-left: 12px; min-width: 140px; }
.rc-hint { font-size: 11px; color: var(--color-on-surface-variant); margin-left: 16px; font-style: italic; }
.rc-today { display: inline-flex; gap: 4px; }
.rc-today .material-symbols-outlined { font-size: 16px; }

.rc-container { background: var(--color-surface); border: 1px solid var(--color-outline-variant); border-radius: 8px; overflow-x: auto; overflow-y: visible; width: 100%; max-width: 100%; min-width: 0; }
.rc-scroll { min-width: 100%; }

.rc-header { display: flex; border-bottom: 2px solid var(--color-outline-variant); background: var(--color-surface-container-lowest, #fafafa); }
.rc-corner { width: 200px; flex-shrink: 0; padding: 12px 16px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; color: var(--color-on-surface-variant); border-right: 1px solid var(--color-outline-variant); display: flex; align-items: center; position: sticky; left: 0; z-index: 3; background: inherit; }
.rc-day-header { flex-shrink: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 8px 0; border-right: 1px solid var(--color-outline-variant); gap: 2px; }
.rc-day-header:last-child { border-right: none; }
.rc-day-header.today { background: rgba(40,116,117,.06); }
.rc-day-header.weekend { background: #f3f4f6; }
.rc-day-header.weekend .dh-name, .rc-day-header.weekend .dh-num { color: #9ca3af; }
.rc-day-header.week-start { border-left: 2px solid var(--color-outline-variant); }
.dh-name { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: .05em; color: var(--color-on-surface-variant); }
.dh-num { font-size: 16px; font-weight: 700; color: var(--color-on-surface); }
.dh-month { position: absolute; top: 2px; left: 4px; font-size: 9px; font-weight: 800; text-transform: uppercase; color: var(--color-primary); letter-spacing: .06em; }
.rc-day-header { position: relative; }
.rc-day-header.month-start { border-left: 2px solid var(--color-primary); }
.rc-day-header.today .dh-num { color: var(--color-primary); }
.rc-cell.month-start { border-left: 2px solid var(--color-primary); }

.rc-body { }
.rc-row { display: flex; border-bottom: 1px solid var(--color-outline-variant); position: relative; }
.rc-row:last-child { border-bottom: none; }
.rc-row:hover { background: rgba(40,116,117,.015); }

.rc-emp-cell { width: 200px; flex-shrink: 0; display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-right: 1px solid var(--color-outline-variant); background: var(--color-surface-container-lowest, #fafafa); position: sticky; left: 0; z-index: 2; transition: background .2s, box-shadow .2s; }
.rc-emp-cell.overloaded { background: #fef2f2; box-shadow: inset 3px 0 0 #dc2626; }
.emp-avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 11px; font-weight: 700; letter-spacing: .03em; flex-shrink: 0; }
.rc-emp-cell.overloaded .emp-avatar { box-shadow: 0 0 0 2px #dc2626; }
.emp-meta { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.emp-name { font-size: 13px; font-weight: 600; color: var(--color-on-surface); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rc-emp-cell.overloaded .emp-name { color: #dc2626; }
.emp-hours { font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 8px; width: fit-content; }
.hrs-done { background: #dcfce7; color: #15803d; }
.hrs-ok { background: #e0f2fe; color: #0369a1; }
.hrs-busy { background: #fef3c7; color: #b45309; }
.hrs-over { background: #fee2e2; color: #dc2626; }

.rc-timeline { display: grid; position: relative; }
.rc-cell { border-right: 1px solid var(--color-outline-variant); min-height: 48px; position: relative; transition: background .12s; }
.rc-cell:last-of-type { border-right: none; }
.rc-cell.today { background: rgba(40,116,117,.04); }
.rc-cell.weekend { background: #f3f4f6; cursor: not-allowed; }
.rc-cell.is-leave { background: rgba(229,231,235,.5); }
.rc-cell.drag-hl { background: rgba(40,116,117,.12); outline: 1px dashed #287475; outline-offset: -1px; }
.rc-cell.week-start { border-left: 2px solid var(--color-outline-variant); }
.leave-tag { position: absolute; bottom: 4px; left: 50%; transform: translateX(-50%); font-size: 8px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; color: #9ca3af; }

.rc-ribbon-layer { position: absolute; inset: 0; pointer-events: none; }
.rc-leave-overlay-layer { position: absolute; inset: 0; pointer-events: none; z-index: 6; display: grid; }
.leave-darken { width: 100%; height: 100%; background: rgba(0, 0, 0, 0.25); backdrop-filter: grayscale(80%); }
.rc-ribbon { position: absolute; display: flex; align-items: center; color: #fff; font-size: 11px; cursor: pointer; pointer-events: auto; overflow: hidden; z-index: 5; transition: opacity .12s; }
.rc-ribbon:hover { opacity: 1 !important; z-index: 10; filter: brightness(1.1); }
.rc-container.dragging .rc-ribbon { pointer-events: none; }
.rc-ribbon.completed { text-decoration: line-through; }
.rc-ribbon.delayed { border-left: 3px solid #dc2626; background-image: repeating-linear-gradient(-45deg, transparent, transparent 6px, rgba(220,38,38,.12) 6px, rgba(220,38,38,.12) 12px); animation: dl-pulse 2.5s ease-in-out infinite; }
@keyframes dl-pulse { 0%,100% { box-shadow: 0 0 0 0 rgba(220,38,38,0); } 50% { box-shadow: 0 0 0 2px rgba(220,38,38,.2); } }
.rb-handle { width: 8px; height: 100%; position: absolute; top: 0; cursor: col-resize; background: rgba(255,255,255,.2); transition: background .15s; z-index: 2; }
.rb-handle:hover { background: rgba(255,255,255,.5); }
.rb-handle-start { left: 0; border-radius: 4px 0 0 4px; }
.rb-handle-end { right: 0; border-radius: 0 4px 4px 0; }
.rb-content { display: flex; flex-direction: column; overflow: hidden; padding: 0 10px; line-height: 1.1; flex: 1; min-width: 0; height: 100%; justify-content: center; z-index: 1; cursor: grab; }
.rb-content:active { cursor: grabbing; }
.rb-tools { position: absolute; top: 0; bottom: 0; transform: translateX(-50%); display: flex; flex-direction: column; align-items: center; pointer-events: none; z-index: 10; }
.rb-cut-line { width: 0; height: 100%; border-left: 2px dashed #ef4444; position: absolute; top: 0; pointer-events: none; opacity: 0.8; }
.rb-cut-indicator { background: #ef4444; color: #fff; width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; position: absolute; top: -11px; box-shadow: 0 2px 6px rgba(0,0,0,0.2); }
.rb-cut-indicator .material-symbols-outlined { font-size: 14px; }
.cut-ready { cursor: cell !important; }

/* Tool Toggle Button */
.rc-divider { width: 1px; height: 20px; background: var(--color-outline); margin: 0 4px; }
.rc-tool-toggle {
  display: flex; align-items: center; gap: 6px; padding: 6px 12px;
  background: var(--color-surface); border: 1px solid var(--color-outline); border-radius: var(--radius-lg);
  font-family: var(--font-display); font-size: 12px; font-weight: 600; color: var(--color-on-surface);
  cursor: pointer; transition: all 0.2s;
}
.rc-tool-toggle:hover { background: var(--color-surface-container); }
.rc-tool-toggle.active { background: #fee2e2; border-color: #ef4444; color: #ef4444; }
.rc-tool-toggle .material-symbols-outlined { font-size: 18px; }
.rb-title { font-weight: 700; font-size: 11px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rb-project { font-size: 9px; opacity: .8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rb-delay { flex-shrink: 0; font-size: 8px; font-weight: 700; background: #dc2626; color: #fff; padding: 1px 4px; border-radius: 3px; margin-right: 10px; z-index: 2; }

.rc-legend { display: flex; flex-wrap: wrap; gap: 16px; padding: 4px 0; }
.rc-legend-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--color-on-surface-variant); font-weight: 500; }
.rc-legend-dot { width: 10px; height: 10px; border-radius: 50%; }

.rc-tooltip { position: fixed; background: var(--color-on-surface); color: #fff; padding: 6px 12px; border-radius: 4px; font-size: 12px; font-weight: 600; white-space: nowrap; z-index: 9999; pointer-events: none; box-shadow: 0 4px 12px rgba(0,0,0,.2); display: flex; flex-direction: column; gap: 2px; }
.tooltip-mode { font-size: 9px; font-weight: 900; color: var(--color-primary-container); letter-spacing: 0.05em; }
.rc-empty { padding: 48px; text-align: center; color: var(--color-on-surface-variant); font-size: 14px; }
</style>
