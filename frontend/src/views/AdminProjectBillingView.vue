<template>
  <AppLayout>
    <div class="page-header">
      <div>
        <h1 class="page-title">Project Billing</h1>
        <p class="page-sub">Billed vs unbilled amounts and cost breakdown</p>
      </div>
    </div>

    <div class="split-layout">
      <aside class="col-left">
        <ProjectSelector v-model:selectedProjectId="selectedProjectId" />
      </aside>
      <section class="col-right">
        <transition name="fade-panel" mode="out-in">
          <div v-if="!selectedProjectId" key="empty" class="empty-center">
            <span class="material-symbols-outlined empty-ic">payments</span>
            <p>Select a project to view billing</p>
          </div>

          <div v-else-if="loading" key="load" class="detail-skeleton">
            <div class="sk-h1" />
            <div class="sk-sub" />
            <div class="sk-cards" />
          </div>

          <div v-else-if="loadError" key="err" class="empty-center text-error">{{ loadError }}</div>

          <div v-else key="content" class="detail-content">
            <div class="header-block">
              <h2 class="detail-title">{{ billing.project_name }}</h2>
              <p class="detail-sub">{{ projectMeta?.project_number }} · {{ projectMeta?.year || '—' }}</p>
              <div class="header-meta">
                <span class="dot" :style="{ background: projectMeta?.color || '#287475' }" />
                <span class="stage-badge" :class="stageClass(projectMeta?.current_stage)">
                  {{ projectMeta?.current_stage || 'N/A' }}
                </span>
              </div>
            </div>

            <div class="card billed-card">
              <label class="field-label">Billed Amount</label>
              <div class="billed-row">
                <span class="rupee-prefix">₹</span>
                <input v-model.number="billedInput" type="number" min="0" step="100" class="billed-input" />
                <button type="button" class="btn-primary" :disabled="savingBilled" @click="saveBilled">
                  {{ savingBilled ? 'Saving…' : 'Save' }}
                </button>
              </div>
              <p v-if="billingUpdatedLabel" class="muted-sm">Last updated: {{ billingUpdatedLabel }}</p>
              <div v-if="!Number(billing.billed_amount)" class="warn-amber">
                <span class="material-symbols-outlined">warning</span>
                No billed amount recorded yet
              </div>
            </div>

            <div class="stat-row">
              <div class="stat-card">
                <span class="stat-label">Total Cost</span>
                <span class="stat-val">{{ formatInr(billing.total_cost, 0) }}</span>
                <span class="stat-sub">Employee spend + partner cost</span>
              </div>
              <div class="stat-card">
                <span class="stat-label">Billed</span>
                <span class="stat-val" :class="Number(billing.billed_amount) > 0 ? 'text-green' : 'text-grey'">
                  {{ formatInr(billing.billed_amount, 0) }}
                </span>
              </div>
              <div class="stat-card">
                <span class="stat-label">Unbilled</span>
                <span
                  class="stat-val"
                  :class="Number(billing.unbilled_amount) > 0 ? 'text-red' : 'text-green'"
                >
                  {{ formatInr(billing.unbilled_amount, 0) }}
                </span>
              </div>
            </div>

            <div class="chart-wrap" v-show="selectedProjectId && !loading">
              <div class="chart-empty" v-show="pieBothZero">
                No billing data yet — add a billed amount above
              </div>
              <div class="chart-box" v-show="!pieBothZero">
                <canvas
                  id="billingPieChart"
                  ref="chartCanvas"
                  :key="selectedProjectId + '-' + billing.billed_amount"
                  width="280"
                  height="280"
                />
              </div>
              <ul v-show="!pieBothZero" class="legend">
                <li v-for="row in legendRows" :key="row.label" class="legend-row">
                  <span class="swatch" :style="{ background: row.color }" />
                  <span class="leg-label">{{ row.label }}</span>
                  <span class="leg-val">{{ formatInr(row.value, 0) }}</span>
                  <span class="leg-pct">{{ row.pct }}%</span>
                </li>
              </ul>
            </div>

            <div class="badge-row">
              <span :class="['status-badge', billingStatusClass]">{{ billingStatusLabel }}</span>
            </div>
          </div>
        </transition>
      </section>
    </div>

    <ToastNotification
      v-if="toastMsg"
      :message="toastMsg"
      :type="toastType"
      @done="toastMsg = ''"
    />
  </AppLayout>
</template>

<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import { Chart, registerables } from 'chart.js'
import AppLayout from '../components/AppLayout.vue'
import ProjectSelector from '../components/projects/ProjectSelector.vue'
import ToastNotification from '../components/ToastNotification.vue'
import { projectsAPI } from '../api/projects'
import { formatInr } from '../utils/currency'

Chart.register(...registerables)

const TEAL = '#287475'
const RED = '#ef4444'

const selectedProjectId = ref(null)
const loading = ref(false)
const loadError = ref('')
const billing = ref({
  project_id: null,
  project_name: '',
  billed_amount: 0,
  unbilled_amount: 0,
  total_cost: 0,
  pie_data: [],
})
const projectMeta = ref(null)
const billedInput = ref(0)
const savingBilled = ref(false)
const billingUpdatedAt = ref(null)

const chartCanvas = ref(null)
let chartInstance = null

const toastMsg = ref('')
const toastType = ref('success')

function toast(msg, type = 'success') {
  toastType.value = type
  toastMsg.value = msg
}

const pieBothZero = computed(() => {
  const pie = billing.value.pie_data || []
  if (pie.length < 2) {
    const sum = pie.reduce((s, p) => s + (Number(p.value) || 0), 0)
    return sum === 0
  }
  return pie.every((p) => !Number(p.value))
})

const legendRows = computed(() => {
  const pie = billing.value.pie_data || []
  const colors = [TEAL, RED]
  const sum = pie.reduce((s, p) => s + (Number(p.value) || 0), 0)
  return pie.map((p, i) => ({
    label: p.label,
    value: Number(p.value) || 0,
    color: colors[i] || TEAL,
    pct: sum > 0 ? (((Number(p.value) || 0) / sum) * 100).toFixed(1) : '0.0',
  }))
})

const billingStatusLabel = computed(() => {
  const billed = Number(billing.value.billed_amount) || 0
  const total = Number(billing.value.total_cost) || 0
  if (billed === 0) return 'Unbilled'
  if (billed >= total && total > 0) return 'Fully Billed'
  if (billed > 0 && billed < total) return 'Partially Billed'
  if (total <= 0 && billed > 0) return 'Fully Billed'
  return 'Unbilled'
})

const billingStatusClass = computed(() => {
  const t = billingStatusLabel.value
  if (t === 'Fully Billed') return 'badge-green'
  if (t === 'Partially Billed') return 'badge-amber'
  return 'badge-red'
})

const billingUpdatedLabel = computed(() => {
  if (!billingUpdatedAt.value) return ''
  try {
    return new Intl.DateTimeFormat('en-IN', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(billingUpdatedAt.value))
  } catch {
    return String(billingUpdatedAt.value)
  }
})

function stageClass(stage) {
  if (!stage) return 'stage-na'
  if (stage === 'Completed') return 'stage-done'
  if (stage === 'Incomplete Beyond Deadline' || stage === 'Halted') return 'stage-warn'
  return 'stage-active'
}

async function loadBilling() {
  if (!selectedProjectId.value) return
  loading.value = true
  loadError.value = ''
  try {
    const [bRes, pRes] = await Promise.all([
      projectsAPI.getProjectBilling(selectedProjectId.value),
      projectsAPI.getProject(selectedProjectId.value),
    ])
    billing.value = bRes.data
    projectMeta.value = pRes.data
    billedInput.value = Number(bRes.data.billed_amount) || 0
    billingUpdatedAt.value = bRes.data.updated_at || bRes.data.billing_updated_at || null
  } catch (e) {
    loadError.value = e.response?.data?.detail || 'Could not load billing.'
    console.error(e)
  } finally {
    loading.value = false
    await nextTick()
    // Small delay to ensure the canvas is painted and has dimensions
    setTimeout(() => {
      renderOrDestroyChart()
    }, 250)
  }
}

watch(selectedProjectId, (id) => {
  destroyChart()
  if (!id) return
  loadBilling()
})

watch(
  () => billing.value.pie_data,
  () => {
    if (!loading.value) {
      renderOrDestroyChart()
    }
  },
  { deep: true }
)

function destroyChart() {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
}

function renderOrDestroyChart() {
  destroyChart()
  if (pieBothZero.value) {
    console.log('[ChartDebug] Skipping: pieBothZero is true')
    return
  }

  const el = chartCanvas.value || document.getElementById('billingPieChart')
  if (!el) {
    console.warn('[ChartDebug] Skipping: Canvas element not found')
    return
  }

  const pie = billing.value.pie_data || []
  if (pie.length === 0) {
    console.log('[ChartDebug] Skipping: No pie data')
    return
  }

  const values = pie.map((p) => Number(p.value) || 0)
  const labels = pie.map((p) => p.label)
  const bg = [TEAL, RED]

  console.log('[ChartDebug] Rendering chart with values:', values)

  try {
    chartInstance = new Chart(el, {
      type: 'pie',
      data: {
        labels,
        datasets: [
          {
            data: values,
            backgroundColor: bg.slice(0, labels.length),
            borderWidth: 0,
          },
        ],
      },
      options: {
        responsive: false,
        animation: { duration: 400 },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label(ctx) {
                const v = ctx.parsed
                const total = values.reduce((a, b) => a + b, 0)
                const pct = total > 0 ? ((v / total) * 100).toFixed(1) : '0.0'
                return `${ctx.label}: ${formatInr(v, 0)} (${pct}%)`
              },
            },
          },
        },
      },
    })
    console.log('[ChartDebug] Chart instance created successfully')
  } catch (err) {
    console.error('[ChartDebug] Failed to create Chart instance:', err)
  }
}

onBeforeUnmount(() => destroyChart())

async function saveBilled() {
  if (!selectedProjectId.value) return
  savingBilled.value = true
  try {
    await projectsAPI.patchProjectBilling(selectedProjectId.value, {
      billed_amount: Number(billedInput.value) || 0,
      partner_hourly_rate:
        projectMeta.value?.partner_hourly_rate != null && projectMeta.value?.partner_hourly_rate !== ''
          ? Number(projectMeta.value.partner_hourly_rate)
          : undefined,
    })
    billingUpdatedAt.value = new Date().toISOString()
    toast('Billed amount saved.')
    await loadBilling()
  } catch (e) {
    toast(e.response?.data?.detail || 'Save failed.', 'error')
  } finally {
    savingBilled.value = false
  }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 24px;
}
.page-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--color-on-surface);
  margin: 0 0 4px;
  letter-spacing: -0.02em;
}
.page-sub {
  margin: 0;
  font-size: 14px;
  color: var(--color-on-surface-variant);
}

.split-layout {
  display: flex;
  gap: 24px;
  align-items: stretch;
  min-height: calc(100vh - 220px);
}

.col-left {
  flex: 0 0 30%;
  max-width: 360px;
  min-width: 240px;
}

.col-right {
  flex: 1;
  min-width: 0;
}

.empty-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  background: #fff;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  color: var(--color-on-surface-variant);
  font-size: 14px;
}
.empty-ic {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.35;
}

.detail-skeleton {
  background: #fff;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 24px;
}
.sk-h1 {
  height: 28px;
  width: 50%;
  background: #e2e8f0;
  border-radius: 4px;
  margin-bottom: 12px;
  animation: pulse 1.2s ease-in-out infinite;
}
.sk-sub {
  height: 16px;
  width: 28%;
  background: #f1f5f9;
  border-radius: 4px;
  margin-bottom: 24px;
  animation: pulse 1.2s ease-in-out infinite;
}
.sk-cards {
  height: 120px;
  background: #f8fafc;
  border-radius: 8px;
  animation: pulse 1.2s ease-in-out infinite;
}
@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.55;
  }
}

.detail-content {
  background: #fff;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 24px;
}

.header-block {
  margin-bottom: 24px;
}
.detail-title {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 4px;
  color: var(--color-on-surface);
}
.detail-sub {
  margin: 0 0 8px;
  font-size: 13px;
  color: var(--color-on-surface-variant);
}
.header-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}
.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}
.stage-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 2px;
  font-size: 11px;
  font-weight: 600;
}
.stage-active {
  background: #d4edee;
  color: #113b3c;
}
.stage-done {
  background: #dcfce7;
  color: #166534;
}
.stage-warn {
  background: #fef3c7;
  color: #92400e;
}
.stage-na {
  background: #f1f5f9;
  color: #64748b;
}

.billed-card {
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 20px;
  margin-bottom: 24px;
  background: #fafafa;
}
.field-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
  margin-bottom: 12px;
}
.billed-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.rupee-prefix {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--color-on-surface);
}
.billed-input {
  flex: 1;
  min-width: 160px;
  max-width: 320px;
  height: 48px;
  padding: 0 14px;
  font-size: 20px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  background: #fff;
}
.btn-primary {
  padding: 12px 22px;
  border: none;
  border-radius: var(--radius-lg);
  background: var(--color-primary);
  color: #fff;
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.muted-sm {
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--color-on-surface-variant);
}
.warn-amber {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: var(--radius-lg);
  font-size: 13px;
  color: #92400e;
}

.stat-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 28px;
}
.stat-card {
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 16px;
  background: #fff;
}
.stat-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
  margin-bottom: 8px;
}
.stat-val {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--color-on-surface);
}
.stat-sub {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: var(--color-on-surface-variant);
}
.text-green {
  color: #15803d;
}
.text-grey {
  color: #94a3b8;
}
.text-red {
  color: #dc2626;
}

.chart-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24px;
}
.chart-box {
  width: 280px;
  height: 280px;
}
.chart-empty {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 24px;
  font-size: 14px;
  color: var(--color-on-surface-variant);
  border: 1px dashed var(--color-outline);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 400px;
}

.legend {
  list-style: none;
  margin: 20px 0 0;
  padding: 0;
  width: 100%;
  max-width: 360px;
}
.legend-row {
  display: grid;
  grid-template-columns: 16px 1fr auto auto;
  gap: 10px;
  align-items: center;
  padding: 8px 0;
  font-size: 13px;
  border-bottom: 1px solid #f1f5f9;
}
.swatch {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}
.leg-label {
  font-weight: 600;
}
.leg-val,
.leg-pct {
  font-variant-numeric: tabular-nums;
  color: var(--color-on-surface-variant);
}

.badge-row {
  display: flex;
  justify-content: center;
}
.status-badge {
  display: inline-block;
  padding: 8px 16px;
  border-radius: 2px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.badge-green {
  background: #dcfce7;
  color: #166534;
}
.badge-amber {
  background: #fef3c7;
  color: #92400e;
}
.badge-red {
  background: #fee2e2;
  color: #991b1b;
}

.fade-panel-enter-active,
.fade-panel-leave-active {
  transition: opacity 0.2s ease;
}
.fade-panel-enter-from,
.fade-panel-leave-to {
  opacity: 0;
}

.text-error {
  color: var(--color-error);
}

.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

@media (max-width: 960px) {
  .split-layout {
    flex-direction: column;
  }
  .col-left {
    flex: none;
    max-width: none;
    width: 100%;
  }
  .stat-row {
    grid-template-columns: 1fr;
  }
}
</style>
