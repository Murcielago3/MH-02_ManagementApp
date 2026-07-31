<template>
  <div class="qdr">
    <!-- Controls: quarter + scope -->
    <div class="qdr-controls">
      <select v-model="selectedQuarter" class="qdr-select" @change="load">
        <option v-for="q in quarters" :key="q.label" :value="`${q.fy_year}-${q.quarter}`">
          {{ q.label }}{{ q.is_current ? ' (current)' : '' }}
        </option>
      </select>

      <div class="qdr-scope">
        <button
          type="button"
          class="scope-btn"
          :class="{ active: scope === 'employee' }"
          @click="setScope('employee')"
        >{{ employeeName || 'This employee' }}</button>
        <button
          type="button"
          class="scope-btn"
          :class="{ active: scope === 'org' }"
          @click="setScope('org')"
        >Studio-wide</button>
      </div>
    </div>

    <!-- Capsules: tasks | subtasks -->
    <div class="qdr-capsules">
      <button
        v-for="c in ['tasks', 'subtasks']"
        :key="c"
        type="button"
        class="capsule"
        :class="{ active: capsule === c }"
        @click="capsule = c"
      >
        <span class="material-symbols-outlined">{{ c === 'tasks' ? 'task_alt' : 'checklist' }}</span>
        {{ c === 'tasks' ? 'Tasks' : 'Subtasks' }}
        <span v-if="data" class="capsule-count">{{ data[c].total }}</span>
      </button>
    </div>

    <div v-if="loading" class="qdr-msg">Loading…</div>
    <div v-else-if="error" class="qdr-msg qdr-err">{{ error }}</div>
    <div v-else-if="!data || active.total === 0" class="qdr-msg">
      No {{ capsule }} fell due in {{ data?.label || 'this quarter' }}.
    </div>

    <template v-else>
      <p class="qdr-range">
        {{ active.total }} {{ capsule }} due {{ fmt(data.range.start) }} – {{ fmt(data.range.end) }}
      </p>

      <!-- Headline rates -->
      <div class="qdr-rates">
        <div class="rate">
          <span class="rate-val" :class="rateClass(active.on_time_rate)">
            {{ active.on_time_rate === null ? '-' : active.on_time_rate + '%' }}
          </span>
          <span class="rate-lbl">On time</span>
        </div>
        <div class="rate">
          <span class="rate-val" :class="rateClass(active.completion_rate)">
            {{ active.completion_rate === null ? '-' : active.completion_rate + '%' }}
          </span>
          <span class="rate-lbl">Completed</span>
        </div>
      </div>

      <!-- Proportional bar -->
      <div class="qdr-bar">
        <div
          v-for="b in bars"
          :key="b.key"
          v-show="b.n > 0"
          class="bar-seg"
          :class="b.key"
          :style="{ width: (b.n / active.total * 100) + '%' }"
          :title="`${b.label}: ${b.n}`"
        ></div>
      </div>

      <ul class="qdr-legend">
        <li v-for="b in bars" :key="b.key" v-show="b.n > 0">
          <span class="dot" :class="b.key"></span>{{ b.label }}
          <strong>{{ b.n }}</strong>
        </li>
      </ul>

      <!-- never_started overlaps the buckets above, so it stands apart -->
      <div v-if="active.never_started > 0" class="qdr-flag">
        <span class="material-symbols-outlined">error</span>
        <strong>{{ active.never_started }}</strong>
        {{ active.never_started === 1 ? 'was' : 'were' }} never started -
        still untouched since being assigned.
      </div>

      <!-- Per-employee breakdown (studio-wide only) -->
      <table v-if="scope === 'org' && data.by_employee.length" class="qdr-table">
        <thead>
          <tr>
            <th>Employee</th><th>Due</th><th>On time</th><th>Late</th>
            <th>Overdue</th><th>Not started</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rankedRows" :key="r.employee_id">
            <td class="nm">{{ r.name }}</td>
            <td>{{ r[capsule].total }}</td>
            <td class="ok">{{ r[capsule].completed_on_time }}</td>
            <td class="late">{{ r[capsule].completed_late || '·' }}</td>
            <td class="bad">{{ r[capsule].overdue || '·' }}</td>
            <td class="bad">{{ r[capsule].never_started || '·' }}</td>
          </tr>
        </tbody>
      </table>

      <p v-if="active.completed_untimed > 0" class="qdr-note">
        {{ active.completed_untimed }} completed before delivery tracking began -
        counted as done, but their timing isn't known.
      </p>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { reportsAPI } from '../api/reports'

const props = defineProps({
  employeeId: { type: Number, default: null },
  employeeName: { type: String, default: '' },
  // Week the timesheet covers - picks the quarter to open on.
  weekStart: { type: String, default: '' },
})

const quarters = ref([])
const selectedQuarter = ref('')
const scope = ref('employee')
const capsule = ref('subtasks')
const data = ref(null)
const loading = ref(false)
const error = ref('')

const active = computed(() => data.value?.[capsule.value] || {})

const bars = computed(() => {
  const a = active.value
  return [
    { key: 'on-time', label: 'On time', n: a.completed_on_time || 0 },
    { key: 'late', label: 'Completed late', n: a.completed_late || 0 },
    { key: 'untimed', label: 'Completed (untimed)', n: a.completed_untimed || 0 },
    { key: 'overdue', label: 'Overdue', n: a.overdue || 0 },
    { key: 'open', label: 'Still open', n: a.open || 0 },
  ]
})

// Worst performers first - the report exists to surface problems.
const rankedRows = computed(() =>
  [...(data.value?.by_employee || [])]
    .filter(r => r[capsule.value].total > 0)
    .sort((a, b) =>
      (b[capsule.value].overdue + b[capsule.value].never_started) -
      (a[capsule.value].overdue + a[capsule.value].never_started))
)

function rateClass(v) {
  if (v === null || v === undefined) return ''
  return v >= 80 ? 'good' : v >= 50 ? 'mid' : 'poor'
}

function fmt(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
}

function setScope(s) {
  if (scope.value === s) return
  scope.value = s
  load()
}

function quarterOf(dateStr) {
  const d = new Date(dateStr)
  const m = d.getMonth() + 1
  return m >= 4
    ? { fy: d.getFullYear(), q: Math.floor((m - 4) / 3) + 1 }
    : { fy: d.getFullYear() - 1, q: 4 }
}

async function loadQuarters() {
  try {
    const { data: qs } = await reportsAPI.availableQuarters()
    quarters.value = qs || []
    if (!selectedQuarter.value && quarters.value.length) {
      // Open on the quarter the timesheet's week belongs to, when we have it.
      let pick = quarters.value.find(q => q.is_current)
      if (props.weekStart) {
        const { fy, q } = quarterOf(props.weekStart)
        pick = quarters.value.find(x => x.fy_year === fy && x.quarter === q) || pick
      }
      selectedQuarter.value = pick
        ? `${pick.fy_year}-${pick.quarter}`
        : `${quarters.value[0].fy_year}-${quarters.value[0].quarter}`
    }
  } catch (e) {
    error.value = 'Could not load quarters.'
  }
}

async function load() {
  if (!selectedQuarter.value) return
  const [fyYear, quarter] = selectedQuarter.value.split('-').map(Number)
  loading.value = true
  error.value = ''
  try {
    const { data: res } = await reportsAPI.quarterly({
      fyYear,
      quarter,
      employeeId: scope.value === 'employee' ? props.employeeId : null,
    })
    data.value = res
  } catch (e) {
    error.value = e.response?.data?.detail || 'Could not load the report.'
  } finally {
    loading.value = false
  }
}

watch(() => props.employeeId, async () => {
  await loadQuarters()
  await load()
}, { immediate: true })
</script>

<style scoped>
.qdr { display: flex; flex-direction: column; gap: 14px; }

.qdr-controls { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.qdr-select {
  padding: 6px 10px;
  border: 1px solid var(--color-outline);
  border-radius: 4px;
  font-size: 13px;
  background: var(--color-surface);
  color: var(--color-on-surface);
}
.qdr-scope { display: flex; gap: 0; margin-left: auto; }
.scope-btn {
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid var(--color-outline-variant);
  background: var(--color-surface);
  color: var(--color-on-surface-variant);
  cursor: pointer;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.scope-btn:first-child { border-radius: 999px 0 0 999px; }
.scope-btn:last-child { border-radius: 0 999px 999px 0; border-left: none; }
.scope-btn.active { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }

.qdr-capsules { display: flex; gap: 8px; }
.capsule {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border-radius: 999px;
  border: 1px solid var(--color-outline-variant);
  background: var(--color-surface);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-surface-variant);
  cursor: pointer;
  transition: background .15s, border-color .15s;
}
.capsule .material-symbols-outlined { font-size: 16px; }
.capsule:hover { border-color: var(--color-primary); }
.capsule.active { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }
.capsule-count {
  background: rgba(0,0,0,.12);
  border-radius: 999px;
  padding: 0 7px;
  font-size: 11px;
}
.capsule.active .capsule-count { background: rgba(255,255,255,.25); }

.qdr-msg { font-size: 13px; color: var(--color-on-surface-variant); padding: 18px 0; font-style: italic; }
.qdr-err { color: var(--color-error); font-style: normal; }
.qdr-range { font-size: 12px; color: var(--color-on-surface-variant); margin: 0; }

.qdr-rates { display: flex; gap: 28px; }
.rate { display: flex; flex-direction: column; }
.rate-val { font-size: 26px; font-weight: 700; line-height: 1.1; color: var(--color-on-surface); }
.rate-val.good { color: #059669; }
.rate-val.mid  { color: #b45309; }
.rate-val.poor { color: #dc2626; }
.rate-lbl {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--color-on-surface-variant);
}

.qdr-bar {
  display: flex;
  height: 12px;
  border-radius: 999px;
  overflow: hidden;
  background: var(--color-surface-container);
}
.bar-seg { height: 100%; }
.bar-seg.on-time, .dot.on-time { background: #059669; }
.bar-seg.late,    .dot.late    { background: #f59e0b; }
.bar-seg.untimed, .dot.untimed { background: #94a3b8; }
.bar-seg.overdue, .dot.overdue { background: #dc2626; }
.bar-seg.open,    .dot.open    { background: #3b82f6; }

.qdr-legend {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
  font-size: 12px;
  color: var(--color-on-surface-variant);
}
.qdr-legend li { display: inline-flex; align-items: center; gap: 5px; }
.qdr-legend strong { color: var(--color-on-surface); }
.dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }

.qdr-flag {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 4px;
  padding: 9px 12px;
  font-size: 12px;
  color: #991b1b;
}
.qdr-flag .material-symbols-outlined { font-size: 17px; }

.qdr-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.qdr-table th {
  text-align: left;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: var(--color-on-surface-variant);
  padding: 6px 8px;
  border-bottom: 1px solid var(--color-outline-variant);
}
.qdr-table td { padding: 6px 8px; border-bottom: 1px solid var(--color-outline-variant); }
.qdr-table td.nm { font-weight: 600; color: var(--color-on-surface); }
.qdr-table td.ok { color: #059669; font-weight: 600; }
.qdr-table td.late { color: #b45309; font-weight: 600; }
.qdr-table td.bad { color: #dc2626; font-weight: 700; }

.qdr-note { font-size: 11px; color: var(--color-on-surface-variant); margin: 0; font-style: italic; }
</style>
