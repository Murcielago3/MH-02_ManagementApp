<template>
  <AppLayout>
    <!-- Page header -->
    <div class="page-header">
      <div>
        <h2 class="page-title">Overview</h2>
        <p class="page-subtitle">Studio MH02 Performance Metrics</p>
      </div>
      <div class="header-actions">
        <button class="btn-outline">Export Report</button>
        <button class="btn-primary">New Project</button>
      </div>
    </div>

    <!-- KPI Grid -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-top">
          <span class="kpi-label">Total Employees</span>
          <span class="material-symbols-outlined kpi-icon">group</span>
        </div>
        <div class="kpi-value">{{ stats.total_employees ?? '—' }}</div>
        <div class="kpi-note">Active employees</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-top">
          <span class="kpi-label">Active Projects</span>
          <span class="material-symbols-outlined kpi-icon">architecture</span>
        </div>
        <div class="kpi-value">{{ stats.total_projects ?? '—' }}</div>
        <div class="kpi-note">{{ stageNote }}</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-top">
          <span class="kpi-label">Monthly Expenditure (₹)</span>
          <span class="material-symbols-outlined kpi-icon">payments</span>
        </div>
        <div class="kpi-value">{{ formatCurrency(stats.monthly_salary_expenditure) }}</div>
        <div class="kpi-note">Salary expenditure</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-top">
          <span class="kpi-label">Billed Ratio</span>
          <span class="material-symbols-outlined kpi-icon">pie_chart</span>
        </div>
        <div class="kpi-value">{{ billedRatio }}%</div>
        <div class="kpi-note">Target: 90%</div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="charts-row">
      <!-- Donut Chart: Salary vs Revenue -->
      <div class="chart-card chart-card-wide">
        <h3 class="card-title">Salary Expenditure vs Revenue</h3>
        <div class="chart-content">
          <!-- SVG Donut -->
          <div class="donut-container">
            <svg class="donut-svg" viewBox="0 0 100 100">
              <!-- Background tracks -->
              <circle cx="50" cy="50" r="40" fill="transparent" stroke="#f1edef" stroke-width="8" />
              <circle cx="50" cy="50" r="30" fill="transparent" stroke="#f1edef" stroke-width="8" />
              <!-- Outer ring: Salary (teal) -->
              <circle
                cx="50" cy="50" r="40" fill="transparent"
                stroke="#0d9488" stroke-width="8"
                :stroke-dasharray="salaryDash"
                stroke-linecap="round"
                class="ring-transition"
              />
              <!-- Inner ring: Revenue (navy) -->
              <circle
                cx="50" cy="50" r="30" fill="transparent"
                stroke="#1a1a2e" stroke-width="8"
                :stroke-dasharray="revenueDash"
                stroke-linecap="round"
                class="ring-transition"
              />
            </svg>
            <div class="donut-center">
              <span class="donut-total">{{ formatCurrency(totalFinancial) }}</span>
              <span class="donut-label">TOTAL</span>
            </div>
          </div>

          <!-- Legend -->
          <div class="chart-legend">
            <div class="legend-item">
              <div class="legend-swatch" style="background-color: #1a1a2e;"></div>
              <div class="legend-text">
                <span class="legend-name">Revenue</span>
                <span class="legend-val">{{ formatCurrency(stats.total_billed) }} ({{ revenuePercent }}%)</span>
              </div>
            </div>
            <div class="legend-item">
              <div class="legend-swatch" style="background-color: #0d9488;"></div>
              <div class="legend-text">
                <span class="legend-name">Salary Expenditure</span>
                <span class="legend-val">{{ formatCurrency(stats.monthly_salary_expenditure) }} ({{ salaryPercent }}%)</span>
              </div>
            </div>
            <div class="legend-divider"></div>
            <p class="legend-note"><em>Margin: {{ revenuePercent }}% positive yield<br />vs previous quarter.</em></p>
          </div>
        </div>
      </div>

      <!-- Project Status Ratio -->
      <div class="chart-card">
        <h3 class="card-title">Project Status Ratio</h3>
        <div class="status-bars">
          <div v-for="stage in projectStages" :key="stage.name" class="status-item">
            <div class="status-row">
              <span class="status-name">{{ stage.name }}</span>
              <span class="status-pct">{{ stage.percent }}%</span>
            </div>
            <div class="progress-track">
              <div
                class="progress-fill"
                :style="{ width: stage.percent + '%', background: stage.color }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Project Activity -->
    <div class="table-card">
      <div class="table-header">
        <h3 class="card-title">Recent Project Activity</h3>
        <button class="view-all-btn" @click="$router.push('/admin/projects')">View All</button>
      </div>
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th>Project ID</th>
              <th>Client Name</th>
              <th>Stage</th>
              <th>Budget</th>
              <th>Last Update</th>
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
              <td class="mono muted">{{ p.year || '—' }}</td>
              <td class="text-right">
                <button class="more-btn">
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
import { ref, computed, onMounted } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import { dashboardAPI } from '../api/dashboard'
import { projectsAPI } from '../api/projects'
import { clientsAPI } from '../api/clients'

const loading = ref(true)

const stats = ref({
  total_employees: 0,
  total_projects: 0,
  total_billed: 0,
  total_unbilled: 0,
  monthly_salary_expenditure: 0,
  total_partner_remuneration: 0,
  total_expenditure: 0,
})

const projects = ref([])
const clients = ref([])

// ── Fetch data ──
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
  }
}

onMounted(fetchAll)

// ── Computed: KPI helpers ──
const billedRatio = computed(() => {
  const b = Number(stats.value.total_billed) || 0
  const u = Number(stats.value.total_unbilled) || 0
  const total = b + u
  if (total === 0) return 0
  return Math.round((b / total) * 100)
})

const stageNote = computed(() => {
  const designCount = projects.value.filter(p => p.current_stage === 'Design').length
  return designCount > 0 ? `${designCount} in design phase` : 'All stages'
})

// ── Computed: Donut chart ──
const totalFinancial = computed(() => {
  return (Number(stats.value.total_billed) || 0) + (Number(stats.value.monthly_salary_expenditure) || 0)
})

const revenuePercent = computed(() => {
  if (!totalFinancial.value) return 0
  return Math.round((Number(stats.value.total_billed) / totalFinancial.value) * 100)
})

const salaryPercent = computed(() => {
  if (!totalFinancial.value) return 0
  return Math.round((Number(stats.value.monthly_salary_expenditure) / totalFinancial.value) * 100)
})

// SVG stroke-dasharray: filled_length total_circumference
const revenueDash = computed(() => {
  const circ = 2 * Math.PI * 30 // inner ring r=30
  const fill = (revenuePercent.value / 100) * circ
  return `${fill.toFixed(2)} ${circ.toFixed(2)}`
})

const salaryDash = computed(() => {
  const circ = 2 * Math.PI * 40 // outer ring r=40
  const fill = (salaryPercent.value / 100) * circ
  return `${fill.toFixed(2)} ${circ.toFixed(2)}`
})

// ── Computed: Project status bars ──
const projectStages = computed(() => {
  const total = projects.value.length || 1
  const stages = {}
  for (const p of projects.value) {
    const s = p.current_stage || 'Other'
    stages[s] = (stages[s] || 0) + 1
  }

  const colorMap = {
    'Design': '#515f74',
    'Construction': '#78767d',
    'Review': '#c8c5cd',
  }

  return Object.entries(stages).map(([name, count]) => ({
    name,
    percent: Math.round((count / total) * 100),
    color: colorMap[name] || '#e5e1e3',
  }))
})

// ── Computed: Recent projects (last 3) ──
const recentProjects = computed(() => {
  return projects.value.slice(0, 3)
})

// ── Helpers ──
function getClientName(clientId) {
  if (!clientId) return '—'
  const c = clients.value.find(cl => cl.id === clientId)
  return c ? c.name : `Client #${clientId}`
}

function formatCurrency(val) {
  const n = Number(val) || 0
  if (n >= 10000000) return `₹${(n / 10000000).toFixed(1)}Cr`
  if (n >= 100000) return `₹${(n / 100000).toFixed(1)}L`
  if (n >= 1000) return `₹${(n / 1000).toFixed(1)}K`
  return `₹${n.toLocaleString('en-IN')}`
}
</script>

<style scoped>
/* ───────── Page header ───────── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  line-height: 24px;
  letter-spacing: -0.01em;
  color: #1c1b1d;
  margin: 0;
}

.page-subtitle {
  font-size: 13px;
  line-height: 18px;
  color: #47464c;
  margin: 4px 0 0;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.btn-outline {
  background: #ffffff;
  border: 1px solid #c8c5cd;
  color: #1c1b1d;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 13px;
  line-height: 18px;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-outline:hover {
  background: #f1edef;
}

.btn-primary {
  background: #1a1a2e;
  color: #ffffff;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 13px;
  line-height: 18px;
  cursor: pointer;
  transition: opacity 0.15s;
}

.btn-primary:hover {
  opacity: 0.9;
}

/* ───────── KPI Grid ───────── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.kpi-card {
  background: #ffffff;
  border: 1px solid #c8c5cd;
  border-radius: 4px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kpi-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #47464c;
}

.kpi-label {
  font-size: 11px;
  font-weight: 600;
  line-height: 16px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.kpi-icon {
  font-size: 16px;
}

.kpi-value {
  font-size: 24px;
  font-weight: 600;
  line-height: 32px;
  letter-spacing: -0.02em;
  color: #1c1b1d;
  font-variant-numeric: tabular-nums;
}

.kpi-note {
  font-size: 13px;
  line-height: 18px;
  color: #78767d;
}

/* ───────── Charts Row ───────── */
.charts-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
  min-height: 320px;
}

.chart-card {
  background: #ffffff;
  border: 1px solid #c8c5cd;
  border-radius: 4px;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.chart-card-wide {
  /* takes 2 columns via grid */
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  line-height: 20px;
  color: #1c1b1d;
  margin: 0 0 24px;
}

/* ── Donut Chart ── */
.chart-content {
  display: flex;
  align-items: center;
  justify-content: space-around;
  flex-grow: 1;
  gap: 32px;
}

.donut-container {
  position: relative;
  width: 192px;
  height: 192px;
  flex-shrink: 0;
}

.donut-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring-transition {
  transition: stroke-dasharray 0.8s ease;
}

.donut-center {
  position: absolute;
  inset: 0;
  margin: auto;
  width: 96px;
  height: 96px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.donut-total {
  font-size: 18px;
  font-weight: 600;
  line-height: 24px;
  color: #1c1b1d;
}

.donut-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.05em;
  color: #78767d;
}

/* ── Legend ── */
.chart-legend {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-swatch {
  width: 16px;
  height: 16px;
  border-radius: 2px;
  flex-shrink: 0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.legend-text {
  display: flex;
  flex-direction: column;
}

.legend-name {
  font-size: 13px;
  font-weight: 600;
  color: #1c1b1d;
}

.legend-val {
  font-size: 12px;
  color: #78767d;
  font-variant-numeric: tabular-nums;
}

.legend-divider {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #c8c5cd;
}

.legend-note {
  font-size: 13px;
  color: #47464c;
  line-height: 18px;
  margin: 0;
}

/* ── Project Status Bars ── */
.status-bars {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 8px;
}

.status-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  line-height: 18px;
  color: #47464c;
}

.status-pct {
  font-variant-numeric: tabular-nums;
}

.progress-track {
  width: 100%;
  height: 8px;
  background: #f1edef;
  border-radius: 9999px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 9999px;
  transition: width 0.6s ease;
}

/* ───────── Data Table ───────── */
.table-card {
  background: #ffffff;
  border: 1px solid #c8c5cd;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
}

.table-header {
  padding: 16px;
  border-bottom: 1px solid #c8c5cd;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-header .card-title {
  margin: 0;
}

.view-all-btn {
  background: none;
  border: none;
  font-size: 13px;
  line-height: 18px;
  color: #47464c;
  cursor: pointer;
  text-decoration: none;
}

.view-all-btn:hover {
  text-decoration: underline;
}

.table-scroll {
  width: 100%;
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.data-table thead tr {
  background: #f6f2f4;
  border-bottom: 1px solid #c8c5cd;
}

.data-table th {
  padding: 8px;
  font-size: 11px;
  font-weight: 600;
  line-height: 16px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #47464c;
}

.data-table th:first-child {
  padding-left: 16px;
}

.data-table th:last-child {
  padding-right: 16px;
}

.data-table tbody tr {
  border-bottom: 1px solid #c8c5cd;
  transition: background 0.1s;
}

.data-table tbody tr:last-child {
  border-bottom: none;
}

.data-table tbody tr:hover {
  background: #fcf8fa;
}

.data-table td {
  padding: 8px;
  font-size: 13px;
  line-height: 18px;
  color: #1c1b1d;
}

.data-table td:first-child {
  padding-left: 16px;
}

.data-table td:last-child {
  padding-right: 16px;
}

.mono {
  font-variant-numeric: tabular-nums;
}

.muted {
  color: #78767d;
}

.text-right {
  text-align: right;
}

.text-center {
  text-align: center;
}

.stage-badge {
  display: inline-block;
  background: #ebe7e9;
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: 12px;
}

.more-btn {
  background: none;
  border: none;
  color: #78767d;
  cursor: pointer;
  padding: 2px;
}

.more-btn:hover {
  color: #1c1b1d;
}

.more-btn .material-symbols-outlined {
  font-size: 18px;
}

.empty-row td {
  padding: 24px;
  color: #78767d;
}

/* ───────── Material Symbols ───────── */
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}
</style>
