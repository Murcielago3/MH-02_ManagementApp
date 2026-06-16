<template>
  <div class="daily-grid-container">
    <!-- Day-by-day grid: same layout employees fill in, read-only -->
    <div v-if="hasDailyBreakdown" class="grid-table-wrapper">
      <table class="grid-table">
        <thead>
          <tr>
            <th class="col-project">Project</th>
            <th v-for="(d, di) in weekDays" :key="di" class="col-day" :class="{ 'is-weekend': di >= 5 }">
              <div class="day-header">
                <span class="day-name">{{ d.short }}</span>
                <span class="day-date">{{ d.dateLabel }}</span>
              </div>
            </th>
            <th class="col-total">Total</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in entriesWithDaily" :key="entry.id">
            <td>
              <span class="project-tag">{{ getProjectName(entry.project_id) }}</span>
            </td>
            <td v-for="(d, di) in weekDays" :key="di" class="day-cell" :class="{ 'is-weekend': di >= 5 }">
              <span class="day-val" :class="{ 'has-hours': Number(entry.daily_hours[di]) > 0 }">
                {{ Number(entry.daily_hours[di]) > 0 ? entry.daily_hours[di] + 'h' : '—' }}
              </span>
            </td>
            <td class="row-total has-hours">{{ entry.hours }}h</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td class="total-label">Daily Total</td>
            <td v-for="(d, di) in weekDays" :key="di" class="day-total" :class="{ 'over-8': dayTotal(di) > 8, 'is-weekend': di >= 5 }">
              {{ dayTotal(di) }}h
            </td>
            <td class="grand-total">{{ grandTotal }}h</td>
          </tr>
        </tfoot>
      </table>
    </div>

    <!-- Fallback for timesheets submitted before daily breakdown was tracked -->
    <div v-else class="table-wrapper">
      <table class="entries-table">
        <thead>
          <tr>
            <th class="col-project">Project</th>
            <th class="col-desc">Task Description</th>
            <th class="col-hours text-right">Hours</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in entries" :key="entry.id">
            <td><span class="project-tag">{{ getProjectName(entry.project_id) }}</span></td>
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
      <p class="legacy-note">
        <span class="material-symbols-outlined">info</span>
        Submitted before daily breakdown tracking — only weekly totals per project are available.
      </p>
    </div>

    <!-- Task descriptions per project -->
    <div v-if="hasDailyBreakdown && entriesWithDaily.some((e) => e.description)" class="desc-section">
      <label class="section-label">Task Descriptions</label>
      <div class="desc-rows">
        <div v-for="entry in entriesWithDaily" :key="entry.id" class="desc-row" v-show="entry.description">
          <span class="desc-project-name">{{ getProjectName(entry.project_id) }}</span>
          <span class="desc-text">{{ entry.description }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  timesheet: { type: Object, required: true },
  projects: { type: Array, required: true },
})

const entries = computed(() => props.timesheet.entries || [])

const entriesWithDaily = computed(() =>
  entries.value.filter((e) => Array.isArray(e.daily_hours) && e.daily_hours.length === 7)
)

const hasDailyBreakdown = computed(() => entriesWithDaily.value.length > 0)

const weekDays = computed(() => {
  const start = new Date(props.timesheet.week_start + 'T00:00:00')
  const shortNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  const days = []
  for (let i = 0; i < 7; i++) {
    const d = new Date(start)
    d.setDate(start.getDate() + i)
    days.push({
      short: shortNames[i],
      dateLabel: d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }),
    })
  }
  return days
})

function dayTotal(di) {
  const sum = entriesWithDaily.value.reduce((s, e) => s + (Number(e.daily_hours[di]) || 0), 0)
  return Math.round(sum * 10) / 10
}

const grandTotal = computed(() => {
  const sum = entriesWithDaily.value.reduce((s, e) => s + (Number(e.hours) || 0), 0)
  return Math.round(sum * 10) / 10
})

function getProjectName(id) {
  const p = props.projects.find((proj) => proj.id === id)
  return p ? p.name : 'Unknown Project'
}
</script>

<style scoped>
.daily-grid-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ─── Day-by-day grid (read-only) ─── */
.grid-table-wrapper {
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-md);
  overflow-x: auto;
}
.grid-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}
.grid-table th {
  background: var(--color-surface-container-low);
  padding: 8px 4px;
  text-align: center;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
  border-bottom: 1px solid var(--color-outline-variant);
}
.grid-table th.col-project { text-align: left; padding-left: 10px; width: 26%; }
.grid-table th.col-day.is-weekend { background: #f8f5f0; }
.grid-table td.day-cell.is-weekend { background: #faf8f5; }
.grid-table th.col-total { width: 56px; font-weight: 800; color: var(--color-on-surface); }

.day-header { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.day-name { font-size: 10px; font-weight: 700; letter-spacing: 0.03em; }
.day-date { font-size: 9px; font-weight: 500; color: var(--color-on-surface-variant); text-transform: none; letter-spacing: 0; }

.grid-table td {
  padding: 8px 4px;
  border-bottom: 1px solid var(--color-surface-container-high);
  vertical-align: middle;
}
.grid-table td:first-child { padding-left: 10px; }

.day-cell { text-align: center; }
.day-val {
  display: inline-block;
  min-width: 30px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-outline);
}
.day-val.has-hours { color: var(--color-on-surface); }

.row-total {
  text-align: center;
  font-weight: 700;
  font-size: 12px;
  color: var(--color-on-surface-variant);
  background: var(--color-surface-container-lowest);
}
.row-total.has-hours { color: var(--color-primary); }

.grid-table tfoot td {
  background: var(--color-surface-container-low);
  border-top: 2px solid var(--color-outline-variant);
  border-bottom: none;
}
.total-label {
  text-align: right;
  font-weight: 700;
  font-size: 12px;
  padding-right: 12px !important;
  color: var(--color-on-surface-variant);
}
.day-total { text-align: center; font-weight: 700; font-size: 13px; color: var(--color-on-surface); }
.day-total.over-8 { color: #dc2626; }
.grand-total { text-align: center; font-weight: 800; font-size: 15px; color: var(--color-primary); }

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

/* ─── Legacy fallback table ─── */
.table-wrapper {
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.entries-table { width: 100%; border-collapse: collapse; }
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
.col-hours { width: 100px; }
.text-right { text-align: right; }
.total-value { font-weight: 700; font-size: 16px; color: var(--color-primary); background: var(--color-surface-container-low); }
.legacy-note {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--color-on-surface-variant);
}
.legacy-note .material-symbols-outlined { font-size: 16px; }

/* ─── Task descriptions ─── */
.desc-section { display: flex; flex-direction: column; gap: 10px; }
.section-label {
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-on-surface-variant);
}
.desc-rows { display: flex; flex-direction: column; gap: 8px; }
.desc-row { display: flex; align-items: flex-start; gap: 12px; }
.desc-project-name {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-on-surface);
  min-width: 140px;
  max-width: 180px;
  flex-shrink: 0;
}
.desc-text { font-size: 13px; color: var(--color-on-surface-variant); line-height: 1.5; }
</style>
