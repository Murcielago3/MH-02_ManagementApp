<template>
  <AppLayout>
    <!-- Page Header -->
    <div class="page-header">
      <div class="page-header__text">
        <h1 class="page-title">Project Reports</h1>
        <p class="page-sub">Visual breakdown of billing, hours, and remuneration distribution</p>
      </div>
    </div>

    <div class="split-layout">
      <aside class="col-left">
        <ProjectSelector v-model:selectedProjectId="selectedProjectId" />
      </aside>

      <section class="col-right">
        <transition name="fade-panel" mode="out-in">

          <!-- Empty state -->
          <div v-if="!selectedProjectId" key="empty" class="empty-center">
            <span class="material-symbols-outlined empty-ic">analytics</span>
            <p>Select a project to view its reports</p>
          </div>

          <!-- Loading skeleton -->
          <div v-else-if="loading" key="load" class="detail-skeleton">
            <div class="sk-h1" />
            <div class="sk-sub" />
            <div class="sk-grid">
              <div class="sk-cell" v-for="n in 4" :key="n" />
            </div>
          </div>

          <!-- Error -->
          <div v-else-if="loadError" key="err" class="empty-center text-error">
            <span class="material-symbols-outlined" style="font-size:36px;margin-bottom:8px;opacity:0.5;">error_outline</span>
            {{ loadError }}
          </div>

          <!-- Main content -->
          <div v-else key="content" class="detail-content">

            <!-- Project identity header -->
            <div class="project-header">
              <div class="project-header__left">
                <div class="project-color-dot" :style="{ background: projectMeta?.color || 'var(--color-primary)' }" />
                <div>
                  <h2 class="detail-title">{{ summary?.project_name || '—' }}</h2>
                  <p class="detail-sub">
                    {{ projectMeta?.project_number }}
                    <template v-if="projectMeta?.year"> · {{ projectMeta.year }}</template>
                  </p>
                </div>
              </div>
              <div class="project-header__badges">
                <span class="stage-badge" :class="stageClass(projectMeta?.current_stage)">
                  {{ projectMeta?.current_stage || 'N/A' }}
                </span>
                <span
                  v-if="summary?.reserve_depleted"
                  class="reserve-chip"
                  title="Reserve balance has gone negative"
                >
                  <span class="material-symbols-outlined">warning</span>
                  Reserve Depleted
                </span>
              </div>
            </div>

            <!-- 2×2 chart grid -->
            <div class="charts-grid">

              <!-- Card 1: Billed vs Unbilled -->
              <div class="report-card">
                <header class="card-head">
                  <div class="card-head__icon-wrap card-head__icon-wrap--teal">
                    <span class="material-symbols-outlined">payments</span>
                  </div>
                  <div>
                    <h3 class="card-title">Billed vs Unbilled</h3>
                    <p class="card-sub">Unbilled appears only when reserve runs below zero</p>
                  </div>
                </header>
                <div class="chart-body">
                  <div v-if="!hasBillingData" class="chart-empty">
                    <span class="material-symbols-outlined">payments</span>
                    <span>No billing or invoices yet</span>
                  </div>
                  <template v-else>
                    <div class="chart-canvas-wrap">
                      <canvas ref="billingChartRef" width="220" height="220" />
                    </div>
                    <ul class="legend">
                      <li v-for="row in billingLegend" :key="row.label" class="legend-row">
                        <span class="swatch" :style="{ background: row.color }" />
                        <span class="leg-label">{{ row.label }}</span>
                        <span class="leg-val">{{ formatInr(row.value, 0) }}</span>
                        <span class="leg-pct">{{ row.pct }}%</span>
                      </li>
                    </ul>
                  </template>
                </div>
              </div>

              <!-- Card 2: Hours & Cost per Employee -->
              <div class="report-card">
                <header class="card-head">
                  <div class="card-head__icon-wrap card-head__icon-wrap--amber">
                    <span class="material-symbols-outlined">groups</span>
                  </div>
                  <div>
                    <h3 class="card-title">Hours &amp; Cost per Employee</h3>
                    <p class="card-sub">From approved timesheets · cost = hours × rate</p>
                  </div>
                </header>
                <div class="chart-body chart-body--bar">
                  <div v-if="!hasEmpData" class="chart-empty">
                    <span class="material-symbols-outlined">groups</span>
                    <span>No approved timesheet hours yet</span>
                  </div>
                  <div v-else class="chart-canvas-wrap chart-canvas-hbar">
                    <canvas ref="empChartRef" />
                  </div>
                </div>
              </div>

              <!-- Card 3: Coming Soon -->
              <div class="report-card report-card--placeholder">
                <header class="card-head">
                  <div class="card-head__icon-wrap card-head__icon-wrap--slate">
                    <span class="material-symbols-outlined">insights</span>
                  </div>
                  <div>
                    <h3 class="card-title">Coming Soon</h3>
                    <p class="card-sub">A fourth chart will land here</p>
                  </div>
                </header>
                <div class="chart-body chart-empty">
                  <span class="material-symbols-outlined placeholder-icon">insights</span>
                  <span>More insights on the way</span>
                </div>
              </div>

              <!-- Card 4: Remuneration & Profit Distribution -->
              <div class="report-card">
                <header class="card-head">
                  <div class="card-head__icon-wrap card-head__icon-wrap--green">
                    <span class="material-symbols-outlined">donut_small</span>
                  </div>
                  <div>
                    <h3 class="card-title">Remuneration &amp; Profit Distribution</h3>
                    <p class="card-sub">Partner share, employees, and profit (when reserve is positive)</p>
                  </div>
                </header>
                <div class="chart-body">
                  <div v-if="!hasDistData" class="chart-empty">
                    <span class="material-symbols-outlined">donut_small</span>
                    <span>No remuneration to distribute yet</span>
                  </div>
                  <template v-else>
                    <div class="chart-canvas-wrap">
                      <canvas ref="distChartRef" width="220" height="220" />
                    </div>
                    <ul class="legend">
                      <li v-for="row in distLegend" :key="row.label" class="legend-row">
                        <span class="swatch" :style="{ background: row.color }" />
                        <span class="leg-label">{{ row.label }}</span>
                        <span class="leg-val">{{ formatInr(row.value, 0) }}</span>
                        <span class="leg-pct">{{ row.pct }}%</span>
                      </li>
                    </ul>
                  </template>
                </div>
              </div>

            </div>
          </div>
        </transition>
      </section>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import { Chart, registerables } from 'chart.js'
import AppLayout from '../components/AppLayout.vue'
import ProjectSelector from '../components/projects/ProjectSelector.vue'
import { projectsAPI } from '../api/projects'
import { usersAPI } from '../api/users'
import { weeklyTimesheetsAPI } from '../api/weekly_timesheets'
import { formatInr, previewHourlyFromBasePay } from '../utils/currency'

Chart.register(...registerables)

// Palette
const TEAL = '#287475'
const RED = '#ef4444'
const AMBER = '#f59e0b'
const GREEN = '#22c55e'
const INDIGO = '#6366f1'
const SLATE = '#94a3b8'

const selectedProjectId = ref(null)
const loading = ref(false)
const loadError = ref('')
const summary = ref(null)
const projectMeta = ref(null)
const approvedTimesheets = ref([])
const allUsers = ref([])

const billingChartRef = ref(null)
const empChartRef = ref(null)
const distChartRef = ref(null)
let billingChart = null
let empChart = null
let distChart = null

function apiErr(e) {
  const d = e.response?.data?.detail
  if (Array.isArray(d)) return d.map((x) => x.msg || JSON.stringify(x)).join(' ')
  if (typeof d === 'object' && d !== null) return JSON.stringify(d)
  return d || e.message || 'Request failed'
}

function stageClass(stage) {
  if (!stage) return 'stage-na'
  if (stage === 'Completed') return 'stage-done'
  if (stage === 'Incomplete Beyond Deadline' || stage === 'Halted') return 'stage-warn'
  return 'stage-active'
}

// ───────── Derived chart inputs ─────────

const billed = computed(() => {
  const s = summary.value
  if (!s) return 0
  return Math.max(0, Number(s.total_invoiced || 0))
})

const unbilled = computed(() => {
  // Only show unbilled when reserve has gone negative (the deficit amount).
  const s = summary.value
  if (!s) return 0
  return Math.max(0, -Number(s.reserve_balance || 0))
})

const hasBillingData = computed(() => billed.value > 0 || unbilled.value > 0)

const billingLegend = computed(() => {
  const vals = [
    { label: 'Billed', value: billed.value, color: TEAL },
    { label: 'Unbilled (deficit)', value: unbilled.value, color: RED },
  ].filter((r) => r.value > 0)
  const total = vals.reduce((s, r) => s + r.value, 0)
  return vals.map((r) => ({
    ...r,
    pct: total > 0 ? ((r.value / total) * 100).toFixed(1) : '0.0',
  }))
})

// Hours per employee from approved timesheets (same approach as AdminProjectSummaryView)
const hoursFromTimesheets = computed(() => {
  const pid = selectedProjectId.value
  const map = new Map()
  if (!pid) return map
  for (const ts of approvedTimesheets.value) {
    if (ts.status !== 'approved') continue
    const uid = ts.employee_id ?? ts.user_id
    if (!uid) continue
    for (const e of (ts.entries || [])) {
      if (Number(e.project_id) !== Number(pid)) continue
      const h = Number(e.hours) || 0
      if (h > 0) map.set(uid, (map.get(uid) || 0) + h)
    }
  }
  return map
})

const empRows = computed(() => {
  // Server returns one row per (employee × salary period) with frozen cost.
  // Aggregate back to one row per person for the reports distribution, keeping
  // the point-in-time totals; the per-person rate shown is the blended average.
  const apiRows = summary.value?.employee_rows || []
  const byUid = new Map()
  for (const r of apiRows) {
    const hours = Number(r.hours_worked) || 0
    if (hours <= 0) continue
    const cur = byUid.get(r.employee_id) || {
      employee_id: r.employee_id,
      name: r.name,
      hours_worked: 0,
      total_spent: 0,
    }
    cur.hours_worked += hours
    cur.total_spent += Number(r.total_spent) || 0
    byUid.set(r.employee_id, cur)
  }
  return [...byUid.values()]
    .map((r) => ({ ...r, hourly_rate: r.hours_worked > 0 ? r.total_spent / r.hours_worked : 0 }))
    .sort((a, b) => b.total_spent - a.total_spent)
})
const hasEmpData = computed(() => empRows.value.length > 0)

const partnerHourlyRate = computed(() => Number(projectMeta.value?.partner_hourly_rate || 0))
const totalHours = computed(() => empRows.value.reduce((s, r) => s + r.hours_worked, 0))
const employeeCost = computed(() => empRows.value.reduce((s, r) => s + r.total_spent, 0))
const partnerCost = computed(() => partnerHourlyRate.value * totalHours.value)
const profit = computed(() => {
  const inv = Number(summary.value?.total_invoiced || 0)
  return Math.max(0, inv - employeeCost.value - partnerCost.value)
})

const hasDistData = computed(
  () => partnerCost.value > 0 || employeeCost.value > 0 || profit.value > 0
)

const distLegend = computed(() => {
  const vals = [
    { label: 'Employee Remuneration', value: employeeCost.value, color: RED },
    { label: 'Partner Remuneration', value: partnerCost.value, color: INDIGO },
    { label: 'Profit', value: profit.value, color: GREEN },
  ].filter((r) => r.value > 0)
  const total = vals.reduce((s, r) => s + r.value, 0)
  return vals.map((r) => ({
    ...r,
    pct: total > 0 ? ((r.value / total) * 100).toFixed(1) : '0.0',
  }))
})

// ───────── Chart render / destroy ─────────

function destroyAll() {
  if (billingChart) { billingChart.destroy(); billingChart = null }
  if (empChart) { empChart.destroy(); empChart = null }
  if (distChart) { distChart.destroy(); distChart = null }
}

function renderBillingChart() {
  if (billingChart) { billingChart.destroy(); billingChart = null }
  if (!hasBillingData.value) return
  const el = billingChartRef.value
  if (!el) return
  const rows = billingLegend.value
  billingChart = new Chart(el, {
    type: 'doughnut',
    data: {
      labels: rows.map((r) => r.label),
      datasets: [{
        data: rows.map((r) => r.value),
        backgroundColor: rows.map((r) => r.color),
        borderWidth: 0,
      }],
    },
    options: {
      responsive: false,
      cutout: '55%',
      animation: { duration: 350 },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label(ctx) {
              const v = ctx.parsed
              const total = rows.reduce((s, r) => s + r.value, 0)
              const pct = total > 0 ? ((v / total) * 100).toFixed(1) : '0.0'
              return `${ctx.label}: ${formatInr(v, 0)} (${pct}%)`
            },
          },
        },
      },
    },
  })
}

function renderEmpChart() {
  if (empChart) { empChart.destroy(); empChart = null }
  if (!hasEmpData.value) return
  const el = empChartRef.value
  if (!el) return
  const rows = empRows.value

  // Dynamic height: 52px per employee + 40px padding
  const canvasH = rows.length * 52 + 40
  el.style.width = '100%'
  el.style.height = canvasH + 'px'
  el.width = el.offsetWidth || 400
  el.height = canvasH

  empChart = new Chart(el, {
    type: 'bar',
    data: {
      labels: rows.map((r) => r.name),
      datasets: [
        {
          label: 'Cost (₹)',
          data: rows.map((r) => Number(r.total_spent)),
          backgroundColor: TEAL,
          borderRadius: { topRight: 4, bottomRight: 4 },
          borderSkipped: false,
          borderWidth: 0,
          xAxisID: 'x',
        },
        {
          label: 'Hours',
          data: rows.map((r) => Number(r.hours_worked)),
          backgroundColor: AMBER + 'cc',
          borderRadius: { topRight: 4, bottomRight: 4 },
          borderSkipped: false,
          borderWidth: 0,
          xAxisID: 'x1',
        },
      ],
    },
    options: {
      indexAxis: 'y',
      responsive: false,
      animation: { duration: 400 },
      layout: { padding: { right: 8 } },
      scales: {
        y: {
          grid: { display: false },
          border: { display: false },
          ticks: { font: { size: 12 }, color: '#475569' },
        },
        x: {
          position: 'bottom',
          title: { display: true, text: 'Cost (₹)', font: { size: 10 }, color: TEAL },
          ticks: { font: { size: 10 }, color: '#94a3b8', callback: (v) => formatInr(v, 0) },
          grid: { color: 'rgba(148,163,184,0.12)' },
          border: { display: false },
        },
        x1: {
          position: 'top',
          title: { display: true, text: 'Hours', font: { size: 10 }, color: '#b45309' },
          ticks: { font: { size: 10 }, color: '#94a3b8' },
          grid: { drawOnChartArea: false },
          border: { display: false },
        },
      },
      plugins: {
        legend: {
          display: true,
          position: 'bottom',
          labels: { boxWidth: 10, boxHeight: 10, borderRadius: 2, font: { size: 11 }, padding: 16 },
        },
        tooltip: {
          callbacks: {
            label(ctx) {
              const v = ctx.parsed.x
              if (ctx.dataset.label === 'Cost (₹)') return `  Cost: ${formatInr(v, 0)}`
              return `  Hours: ${v} hrs`
            },
          },
        },
      },
    },
  })
}

function renderDistChart() {
  if (distChart) { distChart.destroy(); distChart = null }
  if (!hasDistData.value) return
  const el = distChartRef.value
  if (!el) return
  const rows = distLegend.value
  distChart = new Chart(el, {
    type: 'doughnut',
    data: {
      labels: rows.map((r) => r.label),
      datasets: [{
        data: rows.map((r) => r.value),
        backgroundColor: rows.map((r) => r.color),
        borderWidth: 0,
      }],
    },
    options: {
      responsive: false,
      cutout: '55%',
      animation: { duration: 350 },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label(ctx) {
              const v = ctx.parsed
              const total = rows.reduce((s, r) => s + r.value, 0)
              const pct = total > 0 ? ((v / total) * 100).toFixed(1) : '0.0'
              return `${ctx.label}: ${formatInr(v, 0)} (${pct}%)`
            },
          },
        },
      },
    },
  })
}

// Wait for the canvas refs to actually be mounted, then render. The
// <transition mode="out-in"> wrapper delays the content block by one leave
// cycle, so a single nextTick fires too early. We poll with rAF for up to ~1s.
function renderAll() {
  let attempts = 0
  function tryOnce() {
    attempts++
    const billingReady = !hasBillingData.value || billingChartRef.value
    const empReady = !hasEmpData.value || empChartRef.value
    const distReady = !hasDistData.value || distChartRef.value
    if (billingReady && empReady && distReady) {
      renderBillingChart()
      renderEmpChart()
      renderDistChart()
      return
    }
    if (attempts < 60) requestAnimationFrame(tryOnce)
  }
  requestAnimationFrame(tryOnce)
}

// Also re-render whenever data changes — covers the case where summary lands
// after the canvases have already been mounted (project switch, etc.).
watch(
  () => [summary.value, hasBillingData.value, hasEmpData.value, hasDistData.value],
  () => renderAll(),
  { flush: 'post' }
)

// ───────── Data loading ─────────

async function ensureEntries(timesheets) {
  const missing = timesheets.filter((t) => !t.entries || t.entries.length === 0)
  if (!missing.length) return timesheets
  const detailed = await Promise.all(
    missing.slice(0, 80).map((t) =>
      weeklyTimesheetsAPI.getTimesheet(t.id).then((r) => r.data).catch(() => t)
    )
  )
  const byId = new Map(detailed.map((d) => [d.id, d]))
  return timesheets.map((t) => byId.get(t.id) || t)
}

async function loadAll(projectId) {
  loadError.value = ''
  summary.value = null
  projectMeta.value = null
  approvedTimesheets.value = []
  allUsers.value = []
  destroyAll()
  loading.value = true
  try {
    const [sumRes, projRes, tsRes, usersRes] = await Promise.all([
      projectsAPI.getProjectSummary(projectId),
      projectsAPI.getProject(projectId),
      weeklyTimesheetsAPI.getTimesheets({ status: 'approved' }).catch(() => ({ data: [] })),
      usersAPI.getUsers().catch(() => ({ data: [] })),
    ])
    summary.value = sumRes.data
    projectMeta.value = projRes.data
    allUsers.value = usersRes.data || []
    let tsList = tsRes.data || []
    tsList = await ensureEntries(tsList)
    approvedTimesheets.value = tsList
  } catch (e) {
    loadError.value = apiErr(e) || 'Could not load reports.'
  } finally {
    loading.value = false
    renderAll()
  }
}

watch(selectedProjectId, (id) => {
  if (!id) {
    destroyAll()
    summary.value = null
    projectMeta.value = null
    approvedTimesheets.value = []
    allUsers.value = []
    return
  }
  loadAll(id)
})

onBeforeUnmount(() => destroyAll())
</script>

<style scoped>
.page-header { margin-bottom: 24px; }
.page-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--color-on-surface);
  margin: 0 0 4px;
  letter-spacing: -0.02em;
}
.page-sub { margin: 0; font-size: 14px; color: var(--color-on-surface-variant); }

.split-layout {
  display: flex;
  gap: 24px;
  align-items: stretch;
  min-height: calc(100vh - 220px);
}
.col-left { flex: 0 0 30%; max-width: 360px; min-width: 240px; }
.col-right { flex: 1; min-width: 0; }

.empty-center {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: 400px;
  background: #fff;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  color: var(--color-on-surface-variant);
  font-size: 14px;
}
.empty-ic { font-size: 48px; margin-bottom: 12px; opacity: 0.35; }

.detail-skeleton {
  background: #fff;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 24px;
}
.sk-h1 { height: 28px; width: 55%; background: #e2e8f0; border-radius: 4px; margin-bottom: 12px; animation: pulse 1.2s ease-in-out infinite; }
.sk-sub { height: 16px; width: 30%; background: #f1f5f9; border-radius: 4px; margin-bottom: 24px; animation: pulse 1.2s ease-in-out infinite; }
.sk-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.sk-cell { height: 240px; background: #f8fafc; border-radius: 8px; animation: pulse 1.2s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.55; } }

.detail-content {
  background: #fff;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 24px;
}

.header-block { margin-bottom: 24px; }
.detail-title { font-family: var(--font-display); font-size: 22px; font-weight: 700; margin: 0 0 4px; color: var(--color-on-surface); }
.detail-sub { margin: 0 0 8px; font-size: 13px; color: var(--color-on-surface-variant); }
.header-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.dot { width: 12px; height: 12px; border-radius: 50%; }
.stage-badge { display: inline-block; padding: 3px 8px; border-radius: 2px; font-size: 11px; font-weight: 600; }
.stage-active { background: #d4edee; color: #113b3c; }
.stage-done { background: #dcfce7; color: #166534; }
.stage-warn { background: #fef3c7; color: #92400e; }
.stage-na { background: #f1f5f9; color: #64748b; }
.reserve-chip {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 8px; border-radius: 12px;
  font-size: 11px; font-weight: 700;
  background: #fee2e2; color: #b91c1c;
}
.reserve-chip .material-symbols-outlined { font-size: 14px; }

/* 2x2 grid */
.grid-2x2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.report-card {
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  background: #fff;
  display: flex;
  flex-direction: column;
  min-height: 340px;
  overflow: hidden;
}
.card-head {
  padding: 16px 18px 8px;
  border-bottom: 1px solid var(--color-outline-variant);
}
.card-title { font-family: var(--font-display); margin: 0 0 2px; font-size: 15px; font-weight: 700; color: var(--color-on-surface); }
.card-sub { margin: 0; font-size: 12px; color: var(--color-on-surface-variant); }

.chart-body {
  padding: 18px;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-width: 0;
}
.chart-canvas-wrap {
  display: flex; align-items: center; justify-content: center;
  min-width: 0;
}
.chart-canvas-hbar {
  width: 100%;
  overflow-y: auto;
}
.chart-canvas-hbar canvas {
  width: 100% !important;
}
.chart-body--bar {
  padding: 12px 18px 18px;
  align-items: stretch;
}
.chart-empty {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  flex: 1;
  color: var(--color-on-surface-variant);
  font-size: 13px;
  text-align: center;
  gap: 8px;
}
.chart-empty .material-symbols-outlined { font-size: 36px; opacity: 0.4; }

.legend {
  list-style: none; margin: 0; padding: 0;
  width: 100%;
  display: flex; flex-direction: column; gap: 4px;
}
.legend-row {
  display: grid;
  grid-template-columns: 14px 1fr auto auto;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 12px;
}
.swatch { width: 12px; height: 12px; border-radius: 3px; }
.leg-label { color: var(--color-on-surface); font-weight: 500; }
.leg-val { color: var(--color-on-surface); font-variant-numeric: tabular-nums; font-weight: 600; }
.leg-pct { color: var(--color-on-surface-variant); font-variant-numeric: tabular-nums; min-width: 44px; text-align: right; }

.placeholder-card { background: repeating-linear-gradient(45deg, #fafafa, #fafafa 8px, #f4f4f5 8px, #f4f4f5 16px); }
.placeholder { color: var(--color-on-surface-variant); }
.placeholder .material-symbols-outlined { font-size: 48px; opacity: 0.25; }

.fade-panel-enter-active, .fade-panel-leave-active { transition: opacity 0.2s ease; }
.fade-panel-enter-from, .fade-panel-leave-to { opacity: 0; }
.text-error { color: var(--color-error); }

@media (max-width: 1200px) {
  .grid-2x2 { grid-template-columns: 1fr; }
}
@media (max-width: 960px) {
  .split-layout { flex-direction: column; }
  .col-left { flex: none; max-width: none; width: 100%; }
}
</style>
