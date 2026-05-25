<template>
  <AppLayout>
    <!-- Page header -->
    <div class="page-header">
      <div>
        <h2 class="page-title">Dashboard</h2>
        <p class="page-subtitle">Studio MH02 Financial Overview</p>
      </div>
      <div class="header-actions">
        <button class="btn-outline" @click="$router.push('/admin/projects')">All Projects</button>
        <button class="btn-primary" @click="$router.push('/admin/projects')">New Project</button>
      </div>
    </div>

    <!-- Top metric strip -->
    <div class="metric-strip">
      <div class="metric-tile">
        <span class="m-label">Total Turnover (FY)</span>
        <span class="m-val">{{ formatCurrency(stats.total_fy_turnover) }}</span>
        <span class="m-sub">Invoices + advance for {{ currentYear }}</span>
      </div>
      <div class="metric-tile">
        <span class="m-label">Billed (All Time)</span>
        <span class="m-val text-green">{{ formatCurrency(stats.total_billed) }}</span>
        <span class="m-sub">Advance + invoices generated</span>
      </div>
      <div class="metric-tile">
        <span class="m-label">Unbilled Deficit</span>
        <span class="m-val" :class="stats.total_unbilled > 0 ? 'text-red' : 'text-grey'">
          {{ formatCurrency(stats.total_unbilled) }}
        </span>
        <span class="m-sub">Sum of negative reserves</span>
      </div>
      <div class="metric-tile">
        <span class="m-label">Profit Reserve</span>
        <span class="m-val text-teal">{{ formatCurrency(stats.total_profit) }}</span>
        <span class="m-sub">Sum of positive reserves</span>
      </div>
    </div>

    <!-- Dashboard Grid 2x2 -->
    <div class="dashboard-grid">
      <!-- (1,1) Monthly Sales (Bar) -->
      <div class="dashboard-card">
        <header class="card-head">
          <h3 class="card-title">Monthly Sales · {{ currentYear }}</h3>
          <p class="card-sub">Sum of invoice totals by month</p>
        </header>
        <div class="chart-body">
          <div v-if="loading" class="chart-empty">Loading…</div>
          <div v-else-if="!hasMonthlyData" class="chart-empty">
            <span class="material-symbols-outlined">bar_chart</span>
            No invoices for {{ currentYear }} yet
          </div>
          <div v-else class="chart-canvas-bar">
            <canvas ref="salesChartRef" width="520" height="240" />
          </div>
        </div>
      </div>

      <!-- (1,2) Billed vs Unbilled (Pie) -->
      <div class="dashboard-card">
        <header class="card-head">
          <h3 class="card-title">Project Status</h3>
          <p class="card-sub">Billed total vs deficit across all projects</p>
        </header>
        <div class="chart-body">
          <div v-if="loading" class="chart-empty">Loading…</div>
          <div v-else-if="!hasBillingData" class="chart-empty">
            <span class="material-symbols-outlined">payments</span>
            No billing data yet
          </div>
          <template v-else>
            <canvas ref="billingChartRef" width="220" height="220" />
            <ul class="legend">
              <li v-for="row in billingLegend" :key="row.label" class="legend-row">
                <span class="swatch" :style="{ background: row.color }" />
                <span class="leg-label">{{ row.label }}</span>
                <span class="leg-val">{{ formatCurrency(row.value) }}</span>
                <span class="leg-pct">{{ row.pct }}%</span>
              </li>
            </ul>
          </template>
        </div>
      </div>

      <!-- (2,1) Distribution: Employee / Partner / Profit -->
      <div class="dashboard-card">
        <header class="card-head">
          <h3 class="card-title">Remuneration &amp; Profit</h3>
          <p class="card-sub">Where the reserve gets distributed across projects</p>
        </header>
        <div class="chart-body">
          <div v-if="loading" class="chart-empty">Loading…</div>
          <div v-else-if="!hasDistData" class="chart-empty">
            <span class="material-symbols-outlined">donut_small</span>
            No remuneration computed yet
          </div>
          <template v-else>
            <canvas ref="distChartRef" width="220" height="220" />
            <ul class="legend">
              <li v-for="row in distLegend" :key="row.label" class="legend-row">
                <span class="swatch" :style="{ background: row.color }" />
                <span class="leg-label">{{ row.label }}</span>
                <span class="leg-val">{{ formatCurrency(row.value) }}</span>
                <span class="leg-pct">{{ row.pct }}%</span>
              </li>
            </ul>
          </template>
        </div>
      </div>

      <!-- (2,2) Operating Expenses pie -->
      <div class="dashboard-card">
        <header class="card-head">
          <h3 class="card-title">Operating Expenses · {{ currentYear }}</h3>
          <p class="card-sub">From the expenses ledger, with annualised payroll</p>
        </header>
        <div class="chart-body">
          <div v-if="loading" class="chart-empty">Loading…</div>
          <div v-else-if="!hasExpenseData" class="chart-empty">
            <span class="material-symbols-outlined">receipt_long</span>
            No expenses recorded
          </div>
          <template v-else>
            <canvas ref="expChartRef" width="220" height="220" />
            <ul class="legend">
              <li v-for="row in expenseLegend" :key="row.label" class="legend-row">
                <span class="swatch" :style="{ background: row.color }" />
                <span class="leg-label">{{ row.label }}</span>
                <span class="leg-val">{{ formatCurrency(row.value) }}</span>
                <span class="leg-pct">{{ row.pct }}%</span>
              </li>
            </ul>
          </template>
        </div>
      </div>
    </div>

    <!-- Recent Project Activity -->
    <div class="table-card">
      <div class="table-header">
        <h3 class="card-title">Recent Projects</h3>
        <button class="view-all-btn" @click="$router.push('/admin/projects')">View All</button>
      </div>
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th>Project ID</th>
              <th>Client Name</th>
              <th>Stage</th>
              <th>Revenue</th>
              <th>Status</th>
              <th class="text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading" class="empty-row">
              <td colspan="6" class="text-center">Loading…</td>
            </tr>
            <tr v-else-if="recentProjects.length === 0" class="empty-row">
              <td colspan="6" class="text-center">No projects found</td>
            </tr>
            <tr v-for="p in recentProjects" :key="p.id">
              <td class="mono">{{ p.project_number }}</td>
              <td>{{ getClientName(p.client_id) }}</td>
              <td><span class="stage-badge">{{ p.current_stage || 'N/A' }}</span></td>
              <td class="mono">{{ formatCurrency(p.project_remuneration) }}</td>
              <td><span class="status-badge" :class="p.is_billed">{{ p.is_billed || '—' }}</span></td>
              <td class="text-right">
                <button class="more-btn" @click="$router.push('/admin/projects/summary')">
                  <span class="material-symbols-outlined">more_vert</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { Chart, registerables } from 'chart.js'
import AppLayout from '../components/AppLayout.vue'
import { dashboardAPI } from '../api/dashboard'
import { projectsAPI } from '../api/projects'
import { clientsAPI } from '../api/clients'

Chart.register(...registerables)

// Palette — mirrors the reports view for consistency
const TEAL = '#287475'
const RED = '#ef4444'
const GREEN = '#22c55e'
const INDIGO = '#6366f1'
const AMBER = '#f59e0b'
const SKY = '#0ea5e9'
const PURPLE = '#a855f7'
const CYAN = '#06b6d4'
const SLATE = '#94a3b8'

const loading = ref(true)
const currentYear = new Date().getFullYear()

const stats = ref({
  total_fy_turnover: 0,
  total_billed: 0,
  total_unbilled: 0,
  total_profit: 0,
  total_employee_remuneration: 0,
  total_partner_remuneration: 0,
  fy_expenses: {
    salary: 0,
    office_rent: 0,
    electricity_bills: 0,
    software_licenses: 0,
    misc: 0,
    total: 0,
    employee_remuneration: 0,
    partner_remuneration: 0,
  },
  monthly_sales: {},
})

const projects = ref([])
const clients = ref([])

const salesChartRef = ref(null)
const billingChartRef = ref(null)
const distChartRef = ref(null)
const expChartRef = ref(null)
let salesChart = null
let billingChart = null
let distChart = null
let expChart = null

async function fetchAll() {
  loading.value = true
  try {
    const [statsRes, projectsRes, clientsRes] = await Promise.all([
      dashboardAPI.getStats(),
      projectsAPI.getProjects(),
      clientsAPI.getClients(),
    ])
    stats.value = statsRes.data
    projects.value = projectsRes.data
    clients.value = clientsRes.data
  } catch (err) {
    console.error('Dashboard fetch error:', err)
  } finally {
    loading.value = false
    queueRender()
  }
}

onMounted(fetchAll)

// ── Computeds ──
const monthlyChartData = computed(() => {
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const fullNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
  const sales = stats.value.monthly_sales || {}
  return monthNames.map((m, i) => ({
    month: m,
    value: Number(sales[fullNames[i]] || 0),
  }))
})
const hasMonthlyData = computed(() => monthlyChartData.value.some((d) => d.value > 0))

const billingLegend = computed(() => {
  const billed = Number(stats.value.total_billed) || 0
  const unbilled = Number(stats.value.total_unbilled) || 0
  const rows = [
    { label: 'Billed', value: billed, color: TEAL },
    { label: 'Unbilled (deficit)', value: unbilled, color: RED },
  ].filter((r) => r.value > 0)
  const total = rows.reduce((s, r) => s + r.value, 0)
  return rows.map((r) => ({ ...r, pct: total > 0 ? ((r.value / total) * 100).toFixed(1) : '0.0' }))
})
const hasBillingData = computed(() => billingLegend.value.length > 0)

const distLegend = computed(() => {
  const emp = Number(stats.value.total_employee_remuneration) || 0
  const partner = Number(stats.value.total_partner_remuneration) || 0
  const profit = Number(stats.value.total_profit) || 0
  const rows = [
    { label: 'Employee Remuneration', value: emp, color: RED },
    { label: 'Partner Remuneration', value: partner, color: INDIGO },
    { label: 'Profit', value: profit, color: GREEN },
  ].filter((r) => r.value > 0)
  const total = rows.reduce((s, r) => s + r.value, 0)
  return rows.map((r) => ({ ...r, pct: total > 0 ? ((r.value / total) * 100).toFixed(1) : '0.0' }))
})
const hasDistData = computed(() => distLegend.value.length > 0)

const expenseLegend = computed(() => {
  const e = stats.value.fy_expenses || {}
  const rows = [
    { label: 'Salary (annualised)', value: Number(e.salary) || 0, color: SKY },
    { label: 'Office Rent', value: Number(e.office_rent) || 0, color: AMBER },
    { label: 'Electricity', value: Number(e.electricity_bills) || 0, color: PURPLE },
    { label: 'Software', value: Number(e.software_licenses) || 0, color: CYAN },
    { label: 'Misc', value: Number(e.misc) || 0, color: SLATE },
  ].filter((r) => r.value > 0)
  const total = rows.reduce((s, r) => s + r.value, 0)
  return rows.map((r) => ({ ...r, pct: total > 0 ? ((r.value / total) * 100).toFixed(1) : '0.0' }))
})
const hasExpenseData = computed(() => expenseLegend.value.length > 0)

const recentProjects = computed(() => projects.value.slice(0, 5))

// ── Chart render ──
function destroyAll() {
  if (salesChart) { salesChart.destroy(); salesChart = null }
  if (billingChart) { billingChart.destroy(); billingChart = null }
  if (distChart) { distChart.destroy(); distChart = null }
  if (expChart) { expChart.destroy(); expChart = null }
}

function renderSales() {
  if (salesChart) { salesChart.destroy(); salesChart = null }
  if (!hasMonthlyData.value || !salesChartRef.value) return
  const data = monthlyChartData.value
  salesChart = new Chart(salesChartRef.value, {
    type: 'bar',
    data: {
      labels: data.map((d) => d.month),
      datasets: [{
        label: 'Sales',
        data: data.map((d) => d.value),
        backgroundColor: GREEN,
        borderRadius: 4,
        borderWidth: 0,
      }],
    },
    options: {
      responsive: false,
      animation: { duration: 350 },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `Sales: ${formatCurrency(ctx.parsed.y)}`,
          },
        },
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 11 } } },
        y: {
          ticks: { font: { size: 10 }, callback: (v) => formatCurrency(v) },
          grid: { color: 'rgba(148,163,184,0.18)' },
        },
      },
    },
  })
}

function renderPie(chartRef, rows, target) {
  if (target.chart) { target.chart.destroy(); target.chart = null }
  if (!rows.length || !chartRef.value) return
  target.chart = new Chart(chartRef.value, {
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
              return `${ctx.label}: ${formatCurrency(v)} (${pct}%)`
            },
          },
        },
      },
    },
  })
}

// Poll until canvases are ready, then render all four. Mirrors the pattern
// used in AdminProjectReportsView.vue.
function queueRender() {
  let attempts = 0
  const tryOnce = () => {
    attempts++
    const ready = (
      (!hasMonthlyData.value || salesChartRef.value) &&
      (!hasBillingData.value || billingChartRef.value) &&
      (!hasDistData.value || distChartRef.value) &&
      (!hasExpenseData.value || expChartRef.value)
    )
    if (ready) {
      renderSales()
      const billingTarget = { chart: billingChart }
      renderPie(billingChartRef, billingLegend.value, billingTarget)
      billingChart = billingTarget.chart
      const distTarget = { chart: distChart }
      renderPie(distChartRef, distLegend.value, distTarget)
      distChart = distTarget.chart
      const expTarget = { chart: expChart }
      renderPie(expChartRef, expenseLegend.value, expTarget)
      expChart = expTarget.chart
      return
    }
    if (attempts < 60) requestAnimationFrame(tryOnce)
  }
  requestAnimationFrame(tryOnce)
}

watch(
  () => [stats.value, hasMonthlyData.value, hasBillingData.value, hasDistData.value, hasExpenseData.value],
  () => queueRender(),
  { flush: 'post' },
)

onBeforeUnmount(destroyAll)

// ── Helpers ──
function getClientName(clientId) {
  if (!clientId) return '—'
  const c = clients.value.find((cl) => cl.id === clientId)
  return c ? c.name : `Client #${clientId}`
}

function formatCurrency(val) {
  const n = Number(val) || 0
  if (n >= 10000000) return `₹${(n / 10000000).toFixed(2)}Cr`
  if (n >= 100000) return `₹${(n / 100000).toFixed(2)}L`
  if (n >= 1000) return `₹${(n / 1000).toFixed(1)}K`
  return `₹${n.toLocaleString('en-IN')}`
}
</script>

<style scoped>
.page-header {
  display: flex; justify-content: space-between; align-items: flex-end;
  margin-bottom: 24px;
}
.page-title {
  font-family: var(--font-display);
  font-size: 28px; font-weight: 700;
  color: var(--color-on-surface);
  margin: 0 0 4px; letter-spacing: -0.02em;
}
.page-subtitle { margin: 0; font-size: 14px; color: var(--color-on-surface-variant); }
.header-actions { display: flex; gap: 8px; }

.btn-primary, .btn-outline {
  padding: 10px 18px; border-radius: var(--radius-lg);
  font-family: var(--font-body); font-size: 14px; font-weight: 600;
  cursor: pointer; transition: opacity .15s;
}
.btn-primary { border: none; background: var(--color-primary); color: #fff; }
.btn-primary:hover { opacity: .92; }
.btn-outline { background: #fff; border: 1px solid var(--color-outline); color: var(--color-on-surface); }
.btn-outline:hover { background: #f8fafc; }

.metric-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
.metric-tile {
  background: #fff;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 18px 20px;
  display: flex; flex-direction: column; gap: 6px;
}
.m-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; color: var(--color-on-surface-variant); }
.m-val { font-family: var(--font-display); font-size: 24px; font-weight: 700; color: var(--color-on-surface); }
.m-sub { font-size: 11px; color: var(--color-on-surface-variant); }
.text-green { color: #15803d; }
.text-red { color: #b91c1c; }
.text-teal { color: var(--color-primary); }
.text-grey { color: var(--color-on-surface-variant); }

.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}
.dashboard-card {
  background: #fff;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  display: flex; flex-direction: column;
  min-height: 320px;
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
  display: flex; align-items: center; justify-content: center;
  gap: 16px;
  min-width: 0;
}
.chart-canvas-bar { width: 100%; overflow-x: auto; }
.chart-canvas-bar canvas { max-width: 100%; }
.chart-empty {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  color: var(--color-on-surface-variant); font-size: 13px; text-align: center; gap: 8px;
}
.chart-empty .material-symbols-outlined { font-size: 36px; opacity: 0.4; }

.legend {
  list-style: none; margin: 0; padding: 0;
  display: flex; flex-direction: column; gap: 4px;
  min-width: 0; flex: 1;
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

.table-card {
  background: #fff;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  overflow: hidden;
}
.table-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-outline-variant);
}
.view-all-btn {
  background: none; border: none; cursor: pointer;
  color: var(--color-primary); font-weight: 600; font-size: 13px;
}
.table-scroll { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th {
  text-align: left; padding: 10px 16px;
  font-size: 11px; font-weight: 600; letter-spacing: .05em; text-transform: uppercase;
  color: var(--color-on-surface-variant);
  background: #f8fafc;
  border-bottom: 1px solid var(--color-outline-variant);
}
.data-table td { padding: 10px 16px; border-bottom: 1px solid #e2e8f0; }
.data-table tr:last-child td { border-bottom: none; }
.mono { font-variant-numeric: tabular-nums; }
.text-right { text-align: right; }
.text-center { text-align: center; }
.empty-row td { padding: 24px; color: var(--color-on-surface-variant); }
.stage-badge {
  display: inline-block; padding: 2px 8px;
  background: #d4edee; color: #113b3c;
  border-radius: 2px; font-size: 11px; font-weight: 600;
}
.status-badge {
  display: inline-block; padding: 2px 8px;
  border-radius: 2px; font-size: 11px; font-weight: 600; text-transform: capitalize;
}
.status-badge.billed { background: #dcfce7; color: #166534; }
.status-badge.unbilled { background: #fee2e2; color: #b91c1c; }
.status-badge.partial { background: #fef3c7; color: #92400e; }
.more-btn {
  background: none; border: none; cursor: pointer;
  color: var(--color-on-surface-variant);
}
.more-btn:hover { color: var(--color-on-surface); }

@media (max-width: 1200px) {
  .metric-strip { grid-template-columns: 1fr 1fr; }
  .dashboard-grid { grid-template-columns: 1fr; }
}
@media (max-width: 600px) {
  .metric-strip { grid-template-columns: 1fr; }
}
</style>
