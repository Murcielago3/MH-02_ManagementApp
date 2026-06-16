<template>
  <AppLayout>

    <!-- ── Page Header ── -->
    <div class="dash-header">
      <div>
        <h1 class="dash-title">Dashboard</h1>
        <p class="dash-sub">Studio MH02 · Financial Overview · {{ currentYear }}</p>
      </div>
      <div class="dash-actions">
        <button class="btn-ghost" @click="$router.push('/admin/projects')">All Projects</button>
        <button class="btn-primary" @click="$router.push('/admin/projects')">
          <span class="material-symbols-outlined">add</span>New Project
        </button>
      </div>
    </div>

    <!-- ── KPI Strip ── -->
    <div class="kpi-strip">
      <div class="kpi-card accent-teal">
        <span class="kpi-icon material-symbols-outlined">trending_up</span>
        <div class="kpi-body">
          <span class="kpi-label">FY Turnover</span>
          <span class="kpi-value">{{ formatCurrency(stats.total_fy_turnover) }}</span>
          <span class="kpi-hint">Invoices · {{ currentYear }}</span>
        </div>
      </div>
      <div class="kpi-card accent-green">
        <span class="kpi-icon material-symbols-outlined">payments</span>
        <div class="kpi-body">
          <span class="kpi-label">Total Billed</span>
          <span class="kpi-value">{{ formatCurrency(stats.total_billed) }}</span>
          <span class="kpi-hint">All projects · all time</span>
        </div>
      </div>
      <div
        class="kpi-card accent-red clickable"
        :class="{ 'no-data': !stats.total_unbilled }"
        @click="stats.total_unbilled > 0 && openDeficitModal()"
        :title="stats.total_unbilled > 0 ? 'Click to see deficit projects' : ''"
      >
        <span class="kpi-icon material-symbols-outlined">warning</span>
        <div class="kpi-body">
          <span class="kpi-label">Unbilled Deficit</span>
          <span class="kpi-value">{{ formatCurrency(stats.total_unbilled) }}</span>
          <span class="kpi-hint" v-if="stats.total_unbilled > 0">
            Click to view projects ↗
          </span>
          <span class="kpi-hint" v-else>No deficit</span>
        </div>
      </div>
      <div class="kpi-card accent-indigo">
        <span class="kpi-icon material-symbols-outlined">savings</span>
        <div class="kpi-body">
          <span class="kpi-label">Profit Reserve</span>
          <span class="kpi-value">{{ formatCurrency(stats.total_profit) }}</span>
          <span class="kpi-hint">Positive reserve surplus</span>
        </div>
      </div>
    </div>

    <!-- ── Charts Grid ── -->
    <div class="charts-grid">

      <!-- Monthly Profit (full width) -->
      <div class="chart-card span-2">
        <div class="chart-card-head">
          <div>
            <h3 class="chart-card-title">Monthly Revenue</h3>
            <p class="chart-card-sub">Invoice subtotals · {{ currentYear }}</p>
          </div>
        </div>
        <div class="chart-card-body chart-body-line">
          <div v-if="loading" class="chart-placeholder">Loading…</div>
          <div v-else-if="!hasMonthlyData" class="chart-placeholder">
            <span class="material-symbols-outlined">show_chart</span>
            No data for {{ currentYear }}
          </div>
          <div v-else class="line-canvas-wrap">
            <canvas ref="salesChartRef" height="200" />
          </div>
        </div>
      </div>

      <!-- Project Status -->
      <div class="chart-card">
        <div class="chart-card-head">
          <div>
            <h3 class="chart-card-title">Project Status</h3>
            <p class="chart-card-sub">Billed vs deficit · all projects</p>
          </div>
        </div>
        <div class="chart-card-body chart-body-pie">
          <div v-if="loading" class="chart-placeholder">Loading…</div>
          <div v-else-if="!hasBillingData" class="chart-placeholder">
            <span class="material-symbols-outlined">donut_large</span>No billing data
          </div>
          <template v-else>
            <canvas ref="billingChartRef" width="180" height="180" />
            <ul class="pie-legend">
              <li v-for="r in billingLegend" :key="r.label">
                <span class="swatch" :style="{ background: r.color }" />
                <span class="leg-label">{{ r.label }}</span>
                <span class="leg-right">
                  <span class="leg-val">{{ formatCurrency(r.value) }}</span>
                  <span class="leg-pct">{{ r.pct }}%</span>
                </span>
              </li>
            </ul>
          </template>
        </div>
      </div>

      <!-- Remuneration & Profit -->
      <div class="chart-card">
        <div class="chart-card-head">
          <div>
            <h3 class="chart-card-title">Remuneration &amp; Profit</h3>
            <p class="chart-card-sub">Employee · partner · profit · all projects</p>
          </div>
        </div>
        <div class="chart-card-body chart-body-pie">
          <div v-if="loading" class="chart-placeholder">Loading…</div>
          <div v-else-if="!hasDistData" class="chart-placeholder">
            <span class="material-symbols-outlined">donut_large</span>No data yet
          </div>
          <template v-else>
            <canvas ref="distChartRef" width="180" height="180" />
            <ul class="pie-legend">
              <li v-for="r in distLegend" :key="r.label">
                <span class="swatch" :style="{ background: r.color }" />
                <span class="leg-label">{{ r.label }}</span>
                <span class="leg-right">
                  <span class="leg-val">{{ formatCurrency(r.value) }}</span>
                  <span class="leg-pct">{{ r.pct }}%</span>
                </span>
              </li>
            </ul>
          </template>
        </div>
      </div>

      <!-- Operating Expenses -->
      <div class="chart-card">
        <div class="chart-card-head">
          <div>
            <h3 class="chart-card-title">Operating Expenses</h3>
            <p class="chart-card-sub">{{ currentMonthName }} · payroll + logged expenses</p>
          </div>
        </div>
        <div class="chart-card-body chart-body-pie">
          <div v-if="loading" class="chart-placeholder">Loading…</div>
          <div v-else-if="!hasExpenseData" class="chart-placeholder">
            <span class="material-symbols-outlined">receipt_long</span>No expenses
          </div>
          <template v-else>
            <canvas ref="expChartRef" width="180" height="180" />
            <ul class="pie-legend">
              <li v-for="r in expenseLegend" :key="r.label">
                <span class="swatch" :style="{ background: r.color }" />
                <span class="leg-label">{{ r.label }}</span>
                <span class="leg-right">
                  <span class="leg-val">{{ formatCurrency(r.value) }}</span>
                  <span class="leg-pct">{{ r.pct }}%</span>
                </span>
              </li>
            </ul>
          </template>
        </div>
      </div>

    </div>

    <!-- ── Recent Projects ── -->
    <div class="table-card">
      <div class="table-card-head">
        <h3 class="table-card-title">Recent Projects</h3>
        <button class="btn-ghost-sm" @click="$router.push('/admin/projects')">View All →</button>
      </div>
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th>Project No.</th>
              <th>Client</th>
              <th>Stage</th>
              <th>Revenue</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="5" class="cell-empty">Loading…</td></tr>
            <tr v-else-if="recentProjects.length === 0"><td colspan="5" class="cell-empty">No projects found</td></tr>
            <tr
              v-for="p in recentProjects"
              :key="p.id"
              class="table-row"
              @click="$router.push('/admin/projects')"
            >
              <td><span class="proj-num">{{ p.project_number }}</span></td>
              <td class="muted">{{ getClientName(p.client_id) }}</td>
              <td><span class="stage-pill">{{ p.current_stage || 'N/A' }}</span></td>
              <td class="mono">{{ formatCurrency(p.project_remuneration) }}</td>
              <td>
                <span class="status-pill" :class="p.is_billed">
                  {{ p.is_billed || '—' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── Deficit Drill-down Modal ── -->
    <Teleport to="body">
      <div v-if="deficitModalOpen" class="modal-backdrop" @click.self="deficitModalOpen = false">
        <div class="modal modal-lg">
          <div class="modal-head">
            <div>
              <h3 class="modal-title">Projects in Deficit</h3>
              <p class="modal-sub">Work costs exceed invoices raised — unbilled labour</p>
            </div>
            <button class="modal-close" @click="deficitModalOpen = false">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <div class="modal-body">
            <div v-if="deficitLoading" class="chart-placeholder">Loading…</div>
            <div v-else-if="deficitRows.length === 0" class="chart-placeholder">
              <span class="material-symbols-outlined">check_circle</span>
              No projects currently in deficit
            </div>
            <table v-else class="data-table">
              <thead>
                <tr>
                  <th>Project</th>
                  <th>Client</th>
                  <th class="text-right">Invoiced</th>
                  <th class="text-right">Deficit</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in deficitRows" :key="r.project_id" class="table-row">
                  <td>
                    <div class="proj-cell">
                      <span
                        class="color-dot"
                        :style="{ background: getProject(r.project_id)?.color || '#ef4444' }"
                      />
                      <span class="proj-num">{{ getProject(r.project_id)?.project_number || '—' }}</span>
                      <span class="proj-name-sm">{{ getProject(r.project_id)?.name || `Project #${r.project_id}` }}</span>
                    </div>
                  </td>
                  <td class="muted">{{ getClientName(getProject(r.project_id)?.client_id) }}</td>
                  <td class="mono text-right">{{ formatCurrency(r.total_invoiced) }}</td>
                  <td class="mono text-right deficit-val">{{ formatCurrency(Math.abs(r.reserve_balance)) }}</td>
                </tr>
              </tbody>
              <tfoot>
                <tr class="total-row">
                  <td colspan="3" class="text-right total-label">Total Deficit</td>
                  <td class="mono text-right deficit-val total-val">{{ formatCurrency(stats.total_unbilled) }}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </div>
    </Teleport>

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

const TEAL   = '#287475'
const RED    = '#ef4444'
const GREEN  = '#22c55e'
const INDIGO = '#6366f1'
const AMBER  = '#f59e0b'
const SKY    = '#0ea5e9'
const PURPLE = '#a855f7'
const CYAN   = '#06b6d4'
const SLATE  = '#94a3b8'

const loading = ref(true)
const currentYear = new Date().getFullYear()
const currentMonthName = new Date().toLocaleString('default', { month: 'long' })

const stats = ref({
  total_fy_turnover: 0,
  total_billed: 0,
  total_unbilled: 0,
  total_profit: 0,
  total_employee_remuneration: 0,
  total_partner_remuneration: 0,
  monthly_payroll: 0,
  fy_expenses: { salary: 0, office_rent: 0, electricity_bills: 0, software_licenses: 0, misc: 0, total: 0 },
  monthly_sales: {},
})
const projects = ref([])
const clients  = ref([])

const salesChartRef   = ref(null)
const billingChartRef = ref(null)
const distChartRef    = ref(null)
const expChartRef     = ref(null)
let salesChart = null, billingChart = null, distChart = null, expChart = null

// ── Deficit modal ──
const deficitModalOpen = ref(false)
const deficitLoading   = ref(false)
const deficitRows      = ref([])

async function openDeficitModal() {
  deficitModalOpen.value = true
  deficitLoading.value   = true
  try {
    const res = await projectsAPI.getReserveStatus()
    deficitRows.value = (res.data || [])
      .filter((r) => r.reserve_balance < 0 && r.total_invoiced > 0)
      .sort((a, b) => a.reserve_balance - b.reserve_balance)
  } catch (e) {
    console.error(e)
  } finally {
    deficitLoading.value = false
  }
}

function getProject(id) {
  return projects.value.find((p) => p.id === id)
}

// ── Data fetch ──
async function fetchAll() {
  loading.value = true
  try {
    const [sRes, pRes, cRes] = await Promise.all([
      dashboardAPI.getStats(),
      projectsAPI.getProjects(),
      clientsAPI.getClients(),
    ])
    stats.value    = sRes.data
    projects.value = pRes.data
    clients.value  = cRes.data
  } catch (e) {
    console.error('Dashboard fetch error:', e)
  } finally {
    loading.value = false
    queueRender()
  }
}
onMounted(fetchAll)

// ── Computeds ──
const monthLabels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
const fullMonths  = ['January','February','March','April','May','June','July','August','September','October','November','December']

const monthlyChartData = computed(() => {
  const sales = stats.value.monthly_sales || {}
  return monthLabels.map((m, i) => ({
    month:  m,
    revenue: Number(sales[fullMonths[i]] || 0),
  }))
})
const hasMonthlyData = computed(() =>
  monthlyChartData.value.some((d) => d.revenue > 0)
)

const billingLegend = computed(() => {
  const billed   = Number(stats.value.total_billed) || 0
  const unbilled = Number(stats.value.total_unbilled) || 0
  const rows = [
    { label: 'Billed',            value: billed,   color: TEAL },
    { label: 'Unbilled (deficit)', value: unbilled, color: RED  },
  ].filter((r) => r.value > 0)
  const total = rows.reduce((s, r) => s + r.value, 0)
  return rows.map((r) => ({ ...r, pct: total > 0 ? ((r.value / total) * 100).toFixed(1) : '0.0' }))
})
const hasBillingData = computed(() => billingLegend.value.length > 0)

const distLegend = computed(() => {
  const emp     = Number(stats.value.total_employee_remuneration) || 0
  const partner = Number(stats.value.total_partner_remuneration)  || 0
  const profit  = Number(stats.value.total_profit)                || 0
  const rows = [
    { label: 'Employee Remuneration', value: emp,     color: RED    },
    { label: 'Partner Remuneration',  value: partner, color: INDIGO },
    { label: 'Profit',                value: profit,  color: GREEN  },
  ].filter((r) => r.value > 0)
  const total = rows.reduce((s, r) => s + r.value, 0)
  return rows.map((r) => ({ ...r, pct: total > 0 ? ((r.value / total) * 100).toFixed(1) : '0.0' }))
})
const hasDistData = computed(() => distLegend.value.length > 0)

const expenseLegend = computed(() => {
  const e = stats.value.fy_expenses || {}
  const rows = [
    { label: 'Employee Salaries', value: Number(e.salary)            || 0, color: SKY    },
    { label: 'Office Rent',       value: Number(e.office_rent)       || 0, color: AMBER  },
    { label: 'Electricity',       value: Number(e.electricity_bills) || 0, color: PURPLE },
    { label: 'Software',          value: Number(e.software_licenses) || 0, color: CYAN   },
    { label: 'Misc',              value: Number(e.misc)              || 0, color: SLATE  },
  ].filter((r) => r.value > 0)
  const total = rows.reduce((s, r) => s + r.value, 0)
  return rows.map((r) => ({ ...r, pct: total > 0 ? ((r.value / total) * 100).toFixed(1) : '0.0' }))
})
const hasExpenseData = computed(() => expenseLegend.value.length > 0)

const recentProjects = computed(() => projects.value.slice(0, 5))

// ── Helpers ──
function getClientName(id) {
  if (!id) return '—'
  const c = clients.value.find((cl) => cl.id === id)
  return c ? c.name : `Client #${id}`
}

function formatCurrency(val) {
  const n = Number(val) || 0
  if (n >= 10000000) return `₹${(n / 10000000).toFixed(2)}Cr`
  if (n >= 100000)   return `₹${(n / 100000).toFixed(2)}L`
  if (n >= 1000)     return `₹${(n / 1000).toFixed(1)}K`
  return `₹${n.toLocaleString('en-IN')}`
}

// ── Chart rendering ──
function destroyAll() {
  [salesChart, billingChart, distChart, expChart].forEach((c) => c?.destroy())
  salesChart = billingChart = distChart = expChart = null
}

function renderSales() {
  if (salesChart) { salesChart.destroy(); salesChart = null }
  if (!hasMonthlyData.value || !salesChartRef.value) return
  const data     = monthlyChartData.value
  const revenues = data.map((d) => d.revenue)
  salesChart = new Chart(salesChartRef.value, {
    type: 'line',
    data: {
      labels: data.map((d) => d.month),
      datasets: [{
        label: 'Revenue',
        data:  revenues,
        borderColor:       TEAL,
        backgroundColor:   'rgba(40,116,117,0.07)',
        borderWidth:       2.5,
        pointBackgroundColor: TEAL,
        pointBorderColor:     TEAL,
        pointRadius:  5,
        pointHoverRadius: 7,
        fill:    true,
        tension: 0.35,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 400 },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: { label: (ctx) => `Revenue: ${formatCurrency(ctx.parsed.y)}` },
        },
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 11 }, color: '#94a3b8' } },
        y: {
          beginAtZero: true,
          ticks: { font: { size: 10 }, color: '#94a3b8', callback: (v) => formatCurrency(v) },
          grid:  { color: 'rgba(148,163,184,0.15)' },
          border: { display: false },
        },
      },
    },
  })
}

function renderPie(chartRef, rows, existing) {
  existing?.destroy()
  if (!rows.length || !chartRef.value) return null
  return new Chart(chartRef.value, {
    type: 'doughnut',
    data: {
      labels: rows.map((r) => r.label),
      datasets: [{
        data:            rows.map((r) => r.value),
        backgroundColor: rows.map((r) => r.color),
        borderWidth: 0,
        hoverOffset: 4,
      }],
    },
    options: {
      responsive: false,
      cutout: '60%',
      animation: { duration: 350 },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label(ctx) {
              const total = rows.reduce((s, r) => s + r.value, 0)
              const pct = total > 0 ? ((ctx.parsed / total) * 100).toFixed(1) : '0.0'
              return `${ctx.label}: ${formatCurrency(ctx.parsed)} (${pct}%)`
            },
          },
        },
      },
    },
  })
}

function queueRender() {
  let attempts = 0
  const tryOnce = () => {
    attempts++
    const ready = (
      (!hasMonthlyData.value || salesChartRef.value) &&
      (!hasBillingData.value || billingChartRef.value) &&
      (!hasDistData.value    || distChartRef.value) &&
      (!hasExpenseData.value || expChartRef.value)
    )
    if (ready) {
      renderSales()
      billingChart = renderPie(billingChartRef, billingLegend.value, billingChart)
      distChart    = renderPie(distChartRef,    distLegend.value,    distChart)
      expChart     = renderPie(expChartRef,     expenseLegend.value, expChart)
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
</script>

<style scoped>
/* ── Page shell ── */
.dash-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 28px;
}
.dash-title {
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 800;
  color: var(--color-on-surface);
  margin: 0 0 4px;
  letter-spacing: -0.03em;
}
.dash-sub {
  margin: 0;
  font-size: 13px;
  color: var(--color-on-surface-variant);
}
.dash-actions { display: flex; gap: 10px; align-items: center; }

.btn-primary {
  display: flex; align-items: center; gap: 4px;
  padding: 9px 16px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-lg);
  font-size: 13px; font-weight: 600;
  cursor: pointer;
  transition: opacity .15s;
}
.btn-primary:hover { opacity: .88; }
.btn-primary .material-symbols-outlined { font-size: 18px; }

.btn-ghost {
  padding: 9px 14px;
  background: transparent;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  font-size: 13px; font-weight: 600;
  color: var(--color-on-surface);
  cursor: pointer;
  transition: background .12s;
}
.btn-ghost:hover { background: #f1f5f9; }

.btn-ghost-sm {
  padding: 5px 10px;
  background: transparent;
  border: none;
  font-size: 13px; font-weight: 600;
  color: var(--color-primary);
  cursor: pointer;
}

/* ── KPI strip ── */
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
.kpi-card {
  display: flex;
  align-items: center;
  gap: 14px;
  background: #fff;
  border: 1px solid var(--color-outline-variant);
  border-left: 4px solid transparent;
  border-radius: var(--radius-lg);
  padding: 18px 20px;
  box-shadow: 0 1px 4px rgba(0,0,0,.05);
  transition: box-shadow .15s, transform .15s;
}
.kpi-card.clickable { cursor: pointer; }
.kpi-card.clickable:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,.10);
  transform: translateY(-2px);
}
.kpi-card.no-data { opacity: .6; cursor: default; }
.kpi-card.no-data:hover { box-shadow: 0 1px 4px rgba(0,0,0,.05); transform: none; }

.accent-teal   { border-left-color: #287475; }
.accent-green  { border-left-color: #22c55e; }
.accent-red    { border-left-color: #ef4444; }
.accent-indigo { border-left-color: #6366f1; }

.kpi-icon {
  font-size: 28px;
  opacity: .55;
  flex-shrink: 0;
}
.accent-teal   .kpi-icon { color: #287475; }
.accent-green  .kpi-icon { color: #22c55e; }
.accent-red    .kpi-icon { color: #ef4444; }
.accent-indigo .kpi-icon { color: #6366f1; }

.kpi-body { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.kpi-label {
  font-size: 10px; font-weight: 700;
  text-transform: uppercase; letter-spacing: .07em;
  color: var(--color-on-surface-variant);
}
.kpi-value {
  font-family: var(--font-display);
  font-size: 22px; font-weight: 800;
  color: var(--color-on-surface);
  letter-spacing: -0.02em;
  line-height: 1.1;
}
.kpi-hint { font-size: 11px; color: var(--color-on-surface-variant); }

/* ── Charts grid ── */
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}
.chart-card {
  background: #fff;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  box-shadow: 0 1px 4px rgba(0,0,0,.04);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.chart-card.span-2 { grid-column: span 2; }

.chart-card-head {
  padding: 16px 20px 12px;
  border-bottom: 1px solid var(--color-outline-variant);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.chart-card-title {
  margin: 0 0 2px;
  font-family: var(--font-display);
  font-size: 14px; font-weight: 700;
  color: var(--color-on-surface);
}
.chart-card-sub { margin: 0; font-size: 11px; color: var(--color-on-surface-variant); }

.chart-card-body {
  padding: 20px;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.chart-body-line {
  flex-direction: column;
  align-items: stretch;
  padding: 16px 20px 20px;
  min-height: 220px;
}
.chart-body-pie {
  gap: 20px;
  flex-wrap: wrap;
  justify-content: center;
  min-height: 200px;
}

.line-canvas-wrap {
  width: 100%;
  height: 200px;
  position: relative;
}
.line-canvas-wrap canvas { width: 100% !important; height: 100% !important; }

.chart-placeholder {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 10px;
  color: var(--color-on-surface-variant);
  font-size: 13px;
  text-align: center;
  padding: 24px;
  min-height: 160px;
}
.chart-placeholder .material-symbols-outlined { font-size: 36px; opacity: .35; }

/* ── Pie legend ── */
.pie-legend {
  list-style: none;
  margin: 0; padding: 0;
  display: flex; flex-direction: column; gap: 8px;
  min-width: 180px; flex: 1;
}
.pie-legend li {
  display: flex; align-items: center; gap: 8px;
  font-size: 12px;
}
.swatch {
  width: 10px; height: 10px;
  border-radius: 3px;
  flex-shrink: 0;
}
.leg-label { flex: 1; color: var(--color-on-surface); font-weight: 500; }
.leg-right { display: flex; flex-direction: column; align-items: flex-end; gap: 1px; }
.leg-val { font-variant-numeric: tabular-nums; font-weight: 700; color: var(--color-on-surface); font-size: 12px; }
.leg-pct { font-size: 10px; color: var(--color-on-surface-variant); }

/* ── Recent projects table ── */
.table-card {
  background: #fff;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  box-shadow: 0 1px 4px rgba(0,0,0,.04);
  overflow: hidden;
}
.table-card-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-outline-variant);
}
.table-card-title {
  font-family: var(--font-display);
  font-size: 14px; font-weight: 700;
  color: var(--color-on-surface);
  margin: 0;
}
.table-scroll { overflow-x: auto; }
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.data-table th {
  padding: 10px 16px;
  text-align: left;
  font-size: 10px; font-weight: 700;
  letter-spacing: .06em; text-transform: uppercase;
  color: var(--color-on-surface-variant);
  background: #f8fafc;
  border-bottom: 1px solid var(--color-outline-variant);
}
.data-table td {
  padding: 11px 16px;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}
.data-table tfoot td {
  border-bottom: none;
  padding-top: 14px;
  border-top: 1px solid var(--color-outline-variant);
}
.data-table tr:last-child td { border-bottom: none; }
.table-row { cursor: pointer; transition: background .1s; }
.table-row:hover { background: #f8fafc; }

.proj-num {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  font-size: 12px;
  color: var(--color-primary);
}
.muted { color: var(--color-on-surface-variant); }
.mono  { font-variant-numeric: tabular-nums; }
.text-right { text-align: right; }

.stage-pill {
  display: inline-block;
  padding: 2px 8px;
  background: #e0f0f0;
  color: #115657;
  border-radius: 20px;
  font-size: 11px; font-weight: 600;
}
.status-pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 20px;
  font-size: 11px; font-weight: 600;
  text-transform: capitalize;
}
.status-pill.billed   { background: #dcfce7; color: #166534; }
.status-pill.unbilled { background: #fee2e2; color: #b91c1c; }
.status-pill.partial  { background: #fef3c7; color: #92400e; }

.cell-empty {
  padding: 32px;
  text-align: center;
  color: var(--color-on-surface-variant);
}

/* ── Deficit modal ── */
.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.45);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
  padding: 24px;
}
.modal {
  background: #fff;
  border-radius: var(--radius-lg);
  box-shadow: 0 20px 60px rgba(0,0,0,.18);
  display: flex; flex-direction: column;
  max-height: 80vh;
  width: 100%;
  overflow: hidden;
}
.modal-lg { max-width: 680px; }
.modal-head {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--color-outline-variant);
  flex-shrink: 0;
}
.modal-title {
  margin: 0 0 3px;
  font-family: var(--font-display);
  font-size: 17px; font-weight: 700;
  color: var(--color-on-surface);
}
.modal-sub { margin: 0; font-size: 12px; color: var(--color-on-surface-variant); }
.modal-close {
  background: none; border: none; cursor: pointer;
  color: var(--color-on-surface-variant);
  padding: 2px;
  line-height: 1;
}
.modal-close:hover { color: var(--color-on-surface); }
.modal-body {
  overflow-y: auto;
  flex: 1;
}

.proj-cell { display: flex; align-items: center; gap: 8px; }
.color-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.proj-name-sm { color: var(--color-on-surface-variant); font-size: 12px; }
.deficit-val { color: #b91c1c; font-weight: 700; }
.total-label { font-weight: 700; color: var(--color-on-surface); }
.total-val { font-size: 14px; }
.total-row td { background: #fef2f2; }

/* ── Responsive ── */
@media (max-width: 1100px) {
  .kpi-strip { grid-template-columns: 1fr 1fr; }
  .charts-grid { grid-template-columns: 1fr; }
  .chart-card.span-2 { grid-column: span 1; }
}
@media (max-width: 600px) {
  .kpi-strip { grid-template-columns: 1fr; }
  .dash-header { flex-direction: column; align-items: flex-start; gap: 12px; }
}
</style>
