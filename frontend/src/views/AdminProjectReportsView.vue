<template>
  <AppLayout>
    <div class="page-header">
      <div>
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
          <div v-if="!selectedProjectId" key="empty" class="empty-center">
            <span class="material-symbols-outlined empty-ic">analytics</span>
            <p>Select a project to view its reports</p>
          </div>

          <div v-else-if="loading" key="load" class="detail-skeleton">
            <div class="sk-h1" />
            <div class="sk-sub" />
            <div class="sk-grid">
              <div class="sk-cell" v-for="n in 4" :key="n" />
            </div>
          </div>

          <div v-else-if="loadError" key="err" class="empty-center text-error">{{ loadError }}</div>

          <div v-else key="content" class="detail-content">
            <div class="header-block">
              <h2 class="detail-title">{{ summary?.project_name || '—' }}</h2>
              <p class="detail-sub">
                {{ projectMeta?.project_number }} · {{ projectMeta?.year || '—' }}
              </p>
              <div class="header-meta">
                <span class="dot" :style="{ background: projectMeta?.color || '#287475' }" />
                <span class="stage-badge" :class="stageClass(projectMeta?.current_stage)">
                  {{ projectMeta?.current_stage || 'N/A' }}
                </span>
                <span
                  v-if="summary?.reserve_depleted"
                  class="reserve-chip depleted"
                  title="Reserve balance has gone negative"
                >
                  <span class="material-symbols-outlined">warning</span>
                  Reserve Depleted
                </span>
              </div>
            </div>

            <!-- 2x2 Grid -->
            <div class="grid-2x2">
              <!-- (1,1) Billed vs Unbilled -->
              <div class="report-card">
                <header class="card-head">
                  <h3 class="card-title">Billed vs Unbilled</h3>
                  <p class="card-sub">
                    Unbilled appears only when reserve runs below zero
                  </p>
                </header>
                <div class="chart-body">
                  <div v-if="!hasBillingData" class="chart-empty">
                    <span class="material-symbols-outlined">payments</span>
                    No billing or invoices yet
                  </div>
                  <template v-else>
                    <div class="chart-canvas-wrap">
                      <canvas ref="billingChartRef" width="240" height="240" />
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

              <!-- (1,2) Hours / Cost per employee -->
              <div class="report-card">
                <header class="card-head">
                  <h3 class="card-title">Hours &amp; Cost per Employee</h3>
                  <p class="card-sub">
                    From approved timesheets · cost = hours × rate
                  </p>
                </header>
                <div class="chart-body">
                  <div v-if="!hasEmpData" class="chart-empty">
                    <span class="material-symbols-outlined">groups</span>
                    No approved timesheet hours yet
                  </div>
                  <div v-else class="chart-canvas-wrap chart-canvas-bar">
                    <canvas ref="empChartRef" width="420" height="240" />
                  </div>
                </div>
              </div>

              <!-- (2,1) Reserved for later -->
              <div class="report-card placeholder-card">
                <header class="card-head">
                  <h3 class="card-title">Coming Soon</h3>
                  <p class="card-sub">A fourth chart will land here</p>
                </header>
                <div class="chart-body placeholder">
                  <span class="material-symbols-outlined">insights</span>
                </div>
              </div>

              <!-- (2,2) Distribution: Partner / Profit / Employees -->
              <div class="report-card">
                <header class="card-head">
                  <h3 class="card-title">Remuneration &amp; Profit Distribution</h3>
                  <p class="card-sub">
                    Partner share, employees to pay out, and profit (only when reserve is positive)
                  </p>
                </header>
                <div class="chart-body">
                  <div v-if="!hasDistData" class="chart-empty">
                    <span class="material-symbols-outlined">donut_small</span>
                    No remuneration to distribute yet
                  </div>
                  <template v-else>
                    <div class="chart-canvas-wrap">
                      <canvas ref="distChartRef" width="240" height="240" />
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
import { formatInr } from '../utils/currency'

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
  return Math.max(0, Number(s.advance_amount || 0) + Number(s.total_invoiced || 0))
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

const empRows = computed(() => {
  const rows = summary.value?.employee_rows || []
  // Only include employees with logged hours
  return rows
    .filter((r) => Number(r.hours_worked) > 0)
    .slice()
    .sort((a, b) => Number(b.total_spent) - Number(a.total_spent))
})
const hasEmpData = computed(() => empRows.value.length > 0)

const partnerCost = computed(() => Number(summary.value?.partner?.partner_cost || 0))
const employeeCost = computed(() => Number(summary.value?.totals?.total_spent || 0))
const profit = computed(() => Math.max(0, Number(summary.value?.reserve_balance || 0)))

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
  const labels = rows.map((r) => r.name)
  const costs = rows.map((r) => Number(r.total_spent))
  const hours = rows.map((r) => Number(r.hours_worked))

  empChart = new Chart(el, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Cost (₹)',
          data: costs,
          backgroundColor: TEAL,
          borderRadius: 4,
          borderWidth: 0,
          yAxisID: 'y',
        },
        {
          label: 'Hours',
          data: hours,
          backgroundColor: AMBER,
          borderRadius: 4,
          borderWidth: 0,
          yAxisID: 'y1',
        },
      ],
    },
    options: {
      responsive: false,
      animation: { duration: 350 },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { size: 11 } },
        },
        y: {
          type: 'linear',
          position: 'left',
          title: { display: true, text: 'Cost (₹)', font: { size: 10 } },
          ticks: {
            font: { size: 10 },
            callback: (v) => formatInr(v, 0),
          },
          grid: { color: 'rgba(148,163,184,0.18)' },
        },
        y1: {
          type: 'linear',
          position: 'right',
          title: { display: true, text: 'Hours', font: { size: 10 } },
          ticks: { font: { size: 10 } },
          grid: { drawOnChartArea: false },
        },
      },
      plugins: {
        legend: { display: true, position: 'top', labels: { boxWidth: 12, font: { size: 11 } } },
        tooltip: {
          callbacks: {
            label(ctx) {
              const v = ctx.parsed.y
              if (ctx.dataset.label === 'Cost (₹)') return `Cost: ${formatInr(v, 0)}`
              return `Hours: ${v} hrs`
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

async function loadAll(projectId) {
  loadError.value = ''
  summary.value = null
  projectMeta.value = null
  destroyAll()
  loading.value = true
  try {
    const [sumRes, projRes] = await Promise.all([
      projectsAPI.getProjectSummary(projectId),
      projectsAPI.getProject(projectId),
    ])
    summary.value = sumRes.data
    projectMeta.value = projRes.data
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
.chart-canvas-bar { width: 100%; overflow-x: auto; }
.chart-canvas-bar canvas { max-width: 100%; }
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
