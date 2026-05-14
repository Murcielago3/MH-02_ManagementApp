<template>
  <AppLayout>
    <!-- Page header -->
    <div class="page-header">
      <div>
        <h2 class="page-title">Dashboard</h2>
        <p class="page-subtitle">Studio MH02 Financial Overview</p>
      </div>
      <div class="header-actions">
        <button class="btn-outline">Export Report</button>
        <button class="btn-primary">New Project</button>
      </div>
    </div>

    <!-- Dashboard Grid 2x2 -->
    <div class="dashboard-grid">
      <!-- Top Left: Monthly Sales Chart -->
      <div class="dashboard-card">
        <h3 class="card-title">Monthly Sales</h3>
        <div class="chart-content">
          <svg viewBox="0 0 800 300" class="bar-chart">
            <!-- Y-axis labels and gridlines -->
            <line x1="60" y1="20" x2="60" y2="260" stroke="#ddd" stroke-width="2" />
            <line x1="60" y1="260" x2="780" y2="260" stroke="#ddd" stroke-width="2" />
            
            <!-- Grid lines and labels -->
            <text x="45" y="265" font-size="12" text-anchor="end" fill="#999">0</text>
            <line x1="55" y1="260" x2="780" y2="260" stroke="#f0f0f0" stroke-width="1" stroke-dasharray="4" />
            
            <text x="45" y="195" font-size="12" text-anchor="end" fill="#999">{{ maxSalesValue }}</text>
            <line x1="55" y1="190" x2="780" y2="190" stroke="#f0f0f0" stroke-width="1" stroke-dasharray="4" />

            <!-- Bars -->
            <g v-for="(sale, idx) in monthlyChartData" :key="idx">
              <rect 
                :x="65 + idx * 58" 
                :y="260 - (Number(sale.value) / maxSalesValue * 235)" 
                width="45" 
                :height="Number(sale.value) / maxSalesValue * 235" 
                fill="#4ade80" 
                rx="4"
              />
              <text 
                :x="65 + idx * 58 + 22.5" 
                y="280" 
                font-size="11" 
                text-anchor="middle" 
                fill="#666"
              >
                {{ sale.month }}
              </text>
            </g>
          </svg>
        </div>
      </div>

      <!-- Top Right: Total Turnover -->
      <div class="dashboard-card metric-card">
        <h3 class="card-title">Total Turnover (Current FY)</h3>
        <div class="metric-value">{{ formatCurrency(stats.total_fy_turnover) }}</div>
        <div class="metric-note">Financial Year Total</div>
      </div>

      <!-- Bottom Left: Billed/Unbilled -->
      <div class="dashboard-card">
        <h3 class="card-title">Project Status</h3>
        <div class="status-info">
          <div class="status-item">
            <div class="status-label">Unbilled Total</div>
            <div class="status-value unbilled">{{ formatCurrency(stats.total_unbilled) }}</div>
          </div>
          <div class="status-item">
            <div class="status-label">Billed Total</div>
            <div class="status-value billed">{{ formatCurrency(stats.total_billed) }}</div>
          </div>
        </div>
      </div>

      <!-- Bottom Right: Expenses Pie Chart -->
      <div class="dashboard-card">
        <h3 class="card-title">Expenses (Current FY)</h3>
        <div class="pie-chart-container">
          <div class="pie-chart-wrapper">
            <svg viewBox="0 0 200 200" class="pie-chart">
              <!-- Pie slices -->
              <g v-for="(slice, idx) in pieSlices" :key="idx">
                <path 
                  :d="slice.path" 
                  :fill="slice.color"
                  opacity="0.9"
                />
              </g>
              <!-- Border circle -->
              <circle cx="100" cy="100" r="80" fill="none" stroke="#e5e1e3" stroke-width="1" />
            </svg>
          </div>
          <div class="pie-legend">
            <div class="legend-item">
              <div class="legend-color" style="background-color: #0ea5e9;"></div>
              <div class="legend-text">
                <div class="legend-label">Salary</div>
                <div class="legend-value">{{ formatCurrency(stats.fy_expenses?.salary || 0) }}</div>
              </div>
            </div>
            <div class="legend-item">
              <div class="legend-color" style="background-color: #f97316;"></div>
              <div class="legend-text">
                <div class="legend-label">Office Rent</div>
                <div class="legend-value">{{ formatCurrency(stats.fy_expenses?.office_rent || 0) }}</div>
              </div>
            </div>
            <div class="legend-item">
              <div class="legend-color" style="background-color: #a855f7;"></div>
              <div class="legend-text">
                <div class="legend-label">Electricity</div>
                <div class="legend-value">{{ formatCurrency(stats.fy_expenses?.electricity_bills || 0) }}</div>
              </div>
            </div>
            <div class="legend-item">
              <div class="legend-color" style="background-color: #06b6d4;"></div>
              <div class="legend-text">
                <div class="legend-label">Software</div>
                <div class="legend-value">{{ formatCurrency(stats.fy_expenses?.software_licenses || 0) }}</div>
              </div>
            </div>
          </div>
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
  total_fy_turnover: 0,
  total_billed: 0,
  total_unbilled: 0,
  fy_expenses: {
    salary: 0,
    office_rent: 0,
    electricity_bills: 0,
    software_licenses: 0,
    total: 0
  },
  monthly_sales: {},
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

// ── Computed: Monthly Sales Chart ──
const monthlyChartData = computed(() => {
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const sales = stats.value.monthly_sales || {}
  return monthNames.map(month => ({
    month,
    value: Number(sales[month.replace('Jan', 'January').replace('Feb', 'February').replace('Mar', 'March').replace('Apr', 'April').replace('May', 'May').replace('Jun', 'June').replace('Jul', 'July').replace('Aug', 'August').replace('Sep', 'September').replace('Oct', 'October').replace('Nov', 'November').replace('Dec', 'December')] || 0)
  }))
})

const maxSalesValue = computed(() => {
  const values = monthlyChartData.value.map(d => d.value)
  const max = Math.max(...values)
  if (max === 0) return 1
  return Math.ceil(max / 100000) * 100000
})

// ── Computed: Pie Chart Slices ──
const totalExpenses = computed(() => {
  const fy = stats.value.fy_expenses || {}
  return fy.total || 0
})

const expenseData = computed(() => [
  { name: 'Salary', value: stats.value.fy_expenses?.salary || 0, color: '#0ea5e9' },
  { name: 'Office Rent', value: stats.value.fy_expenses?.office_rent || 0, color: '#f97316' },
  { name: 'Electricity', value: stats.value.fy_expenses?.electricity_bills || 0, color: '#a855f7' },
  { name: 'Software', value: stats.value.fy_expenses?.software_licenses || 0, color: '#06b6d4' }
])

const pieSlices = computed(() => {
  if (totalExpenses.value === 0) return []
  
  const slices = []
  const centerX = 100
  const centerY = 100
  const radius = 80
  let currentAngle = -Math.PI / 2 // Start at top

  for (const item of expenseData.value) {
    const sliceAngle = (item.value / totalExpenses.value) * 2 * Math.PI
    const startAngle = currentAngle
    const endAngle = currentAngle + sliceAngle
    
    // Calculate start and end points on the circle
    const x1 = centerX + radius * Math.cos(startAngle)
    const y1 = centerY + radius * Math.sin(startAngle)
    const x2 = centerX + radius * Math.cos(endAngle)
    const y2 = centerY + radius * Math.sin(endAngle)
    
    // Determine if we need the large arc flag (if angle > PI)
    const largeArc = sliceAngle > Math.PI ? 1 : 0
    
    // Create the SVG path
    const path = `M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`
    
    slices.push({
      name: item.name,
      path,
      color: item.color,
      value: item.value,
      percent: ((item.value / totalExpenses.value) * 100).toFixed(1)
    })
    
    currentAngle = endAngle
  }
  
  return slices
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
  color: var(--color-on-surface);
  margin: 0;
}

.page-subtitle {
  font-size: 13px;
  line-height: 18px;
  color: var(--color-on-surface-variant);
  margin: 4px 0 0;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.btn-outline {
  background: #ffffff;
  border: 1px solid var(--color-outline);
  color: var(--color-on-surface);
  padding: 8px 16px;
  border-radius: var(--radius);
  font-size: 13px;
  line-height: 18px;
  cursor: pointer;
  transition: background 0.15s;
}

.btn-outline:hover {
  background: var(--color-surface-container);
}

.btn-primary {
  background: var(--color-primary);
  color: #ffffff;
  border: none;
  padding: 8px 16px;
  border-radius: var(--radius);
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
  border: 1px solid var(--color-outline);
  border-radius: var(--radius);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kpi-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--color-on-surface-variant);
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
  color: var(--color-on-surface);
  font-variant-numeric: tabular-nums;
}

.kpi-note {
  font-size: 13px;
  line-height: 18px;
  color: var(--color-on-surface-variant);
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
  border: 1px solid var(--color-outline);
  border-radius: var(--radius);
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
  color: var(--color-on-surface);
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
  color: var(--color-on-surface);
}

.donut-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.05em;
  color: var(--color-on-surface-variant);
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
  color: var(--color-on-surface);
}

.legend-val {
  font-size: 12px;
  color: var(--color-on-surface-variant);
  font-variant-numeric: tabular-nums;
}

.legend-divider {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--color-outline);
}

.legend-note {
  font-size: 13px;
  color: var(--color-on-surface-variant);
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
  color: var(--color-on-surface-variant);
}

.status-pct {
  font-variant-numeric: tabular-nums;
}

.progress-track {
  width: 100%;
  height: 8px;
  background: var(--color-surface-container);
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
  border: 1px solid var(--color-outline);
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
}

.table-header {
  padding: 16px;
  border-bottom: 1px solid var(--color-outline);
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
  color: var(--color-on-surface-variant);
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
  background: var(--color-surface-container);
  border-bottom: 1px solid var(--color-outline);
}

.data-table th {
  padding: 8px;
  font-size: 11px;
  font-weight: 600;
  line-height: 16px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
}

.data-table th:first-child {
  padding-left: 16px;
}

.data-table th:last-child {
  padding-right: 16px;
}

.data-table tbody tr {
  border-bottom: 1px solid var(--color-outline);
  transition: background 0.1s;
}

.data-table tbody tr:last-child {
  border-bottom: none;
}

.data-table tbody tr:hover {
  background: var(--color-background);
}

.data-table td {
  padding: 8px;
  font-size: 13px;
  line-height: 18px;
  color: var(--color-on-surface);
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
  color: var(--color-on-surface-variant);
}

.text-right {
  text-align: right;
}

.text-center {
  text-align: center;
}

.stage-badge {
  display: inline-block;
  background: var(--color-surface-container-high);
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: 12px;
}

.more-btn {
  background: none;
  border: none;
  color: var(--color-on-surface-variant);
  cursor: pointer;
  padding: 2px;
}

.more-btn:hover {
  color: var(--color-on-surface);
}

.more-btn .material-symbols-outlined {
  font-size: 18px;
}

.empty-row td {
  padding: 24px;
  color: var(--color-on-surface-variant);
}

/* ───────── Dashboard Grid (2x2) ───────── */
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.dashboard-card {
  background: #ffffff;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius);
  padding: 20px;
  display: flex;
  flex-direction: column;
  min-height: 300px;
}

.dashboard-card .card-title {
  margin: 0 0 16px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-on-surface);
}

/* ── Metric Card (Top Right) ── */
.metric-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 12px;
  min-height: 300px;
}

.metric-value {
  font-size: 40px;
  font-weight: 700;
  line-height: 48px;
  letter-spacing: -0.02em;
  color: var(--color-on-surface);
  text-align: center;
}

.metric-note {
  font-size: 13px;
  color: var(--color-on-surface-variant);
  text-align: center;
}

/* ── Bar Chart ── */
.chart-content {
  flex-grow: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.bar-chart {
  width: 100%;
  height: 100%;
  max-height: 250px;
}

/* ── Status Info (Billed/Unbilled) ── */
.status-info {
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex-grow: 1;
  justify-content: center;
}

.status-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-label {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-on-surface-variant);
}

.status-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 36px;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}

.status-value.unbilled {
  color: #ea580c;
}

.status-value.billed {
  color: #16a34a;
}

/* ── Pie Chart ── */
.pie-chart-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex-grow: 1;
  justify-content: center;
  align-items: center;
}

.pie-chart-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 0 8px;
}

.pie-chart {
  width: 140px;
  height: 140px;
  max-width: 100%;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.08));
}

.pie-chart circle {
  transform-origin: 100px 100px;
}

.pie-legend {
  display: flex;
  flex-direction: column;
  gap: 14px;
  width: 100%;
  padding: 0 8px;
}

.legend-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 12px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex-shrink: 0;
  margin-top: 2px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.legend-text {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex-grow: 1;
}

.legend-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-on-surface-variant);
  text-transform: capitalize;
  letter-spacing: 0.03em;
}

.legend-value {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-on-surface);
  font-variant-numeric: tabular-nums;
}

/* ── Status Badge ── */
.status-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: var(--radius);
  font-size: 12px;
  font-weight: 600;
  text-transform: capitalize;
}

.status-badge.billed {
  background: #dcfce7;
  color: #166534;
}

.status-badge.unbilled {
  background: #fed7aa;
  color: #92400e;
}

/* ───────── Material Symbols ───────── */
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}
</style>
