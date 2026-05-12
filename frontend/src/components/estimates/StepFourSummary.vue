<template>
  <div class="step-card">
    <div class="step-header">
      <h2 class="step-title">Final Estimate</h2>
      <p class="step-sub">Complete cost summary for <strong>{{ store.projectName }}</strong></p>
    </div>

    <!-- Summary document -->
    <div class="summary-doc" id="est-print-area">
      <!-- Project header -->
      <div class="doc-project-header">
        <div class="doc-badge">ESTIMATE</div>
        <div class="doc-project-name">{{ store.projectName }}</div>
        <div class="doc-timeline">
          <span class="material-symbols-outlined timeline-icon">date_range</span>
          {{ formatDate(store.startDate) }} → {{ formatDate(store.endDate) }}
          · {{ store.workingDays }} working days · {{ store.totalHours }} hrs
        </div>
      </div>

      <!-- Team costs -->
      <div class="doc-section">
        <div class="doc-section-title">
          <span class="material-symbols-outlined">group</span>
          Team Costs
        </div>
        <div class="doc-rows">
          <div
            v-for="emp in store.employeesWithCost"
            :key="emp.id"
            class="doc-row"
          >
            <div class="doc-row-name">{{ emp.name }}</div>
            <div class="doc-row-formula">
              {{ emp.totalHours }} hrs × {{ formatINR(emp.payPerHour) }}/hr
            </div>
            <div class="doc-row-amount">{{ formatINR(emp.totalCost) }}</div>
          </div>
        </div>
        <div class="doc-subtotal">
          <span>Team Subtotal</span>
          <span class="sub-val">{{ formatINR(store.teamTotalCost) }}</span>
        </div>
      </div>

      <!-- Partner -->
      <div class="doc-section">
        <div class="doc-section-title">
          <span class="material-symbols-outlined">person</span>
          Partner Remuneration
        </div>
        <div class="doc-rows">
          <div class="doc-row">
            <div class="doc-row-name">Partner</div>
            <div class="doc-row-formula">
              {{ store.totalHours }} hrs × {{ formatINR(store.partnerPayPerHour) }}/hr
            </div>
            <div class="doc-row-amount">{{ formatINR(store.partnerCost) }}</div>
          </div>
        </div>
      </div>

      <!-- Grand total -->
      <div class="doc-grand-total">
        <div class="grand-label">TOTAL ESTIMATE</div>
        <div class="grand-value">{{ formatINR(animatedGrand) }}</div>
      </div>
    </div>

    <!-- Action buttons -->
    <div class="action-bar">
      <button class="btn-ghost" @click="store.setStep(3)">
        <span class="material-symbols-outlined">arrow_back</span>
        Back
      </button>
      <div class="action-right">
        <button id="est-reset" class="btn-outline-danger" @click="handleReset">
          <span class="material-symbols-outlined">restart_alt</span>
          Start New Estimate
        </button>
        <button id="est-add-project" class="btn-add" :disabled="isAddingProject" @click="handleAddProject">
          <span class="material-symbols-outlined">{{ isAddingProject ? 'hourglass_empty' : 'library_add' }}</span>
          {{ isAddingProject ? 'Adding...' : 'Add to Projects' }}
        </button>
        <button id="est-print" class="btn-print" @click="handlePrint">
          <span class="material-symbols-outlined">print</span>
          Download as PDF
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useEstimateStore } from '../../stores/estimate'
import { projectsAPI } from '../../api/projects'

const store = useEstimateStore()
const router = useRouter()

const animatedGrand = ref(store.grandTotal)
const isAddingProject = ref(false)

function animateTo(refVal, target, duration = 600) {
  const start = refVal.value
  const diff = target - start
  if (Math.abs(diff) < 1) { refVal.value = target; return }
  const startTime = performance.now()
  function step(now) {
    const p = Math.min((now - startTime) / duration, 1)
    const ease = 1 - Math.pow(1 - p, 3)
    refVal.value = Math.round(start + diff * ease)
    if (p < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

watch(() => store.grandTotal, (v) => animateTo(animatedGrand, v))

onMounted(() => {
  // Trigger counter from 0 when step 4 mounts
  const target = store.grandTotal
  animatedGrand.value = 0
  setTimeout(() => animateTo(animatedGrand, target), 80)
})

const inrFmt = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
function formatINR(val) {
  return inrFmt.format(val || 0)
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

function handlePrint() {
  window.print()
}

function handleReset() {
  store.reset()
}

async function handleAddProject() {
  if (isAddingProject.value) return
  isAddingProject.value = true
  try {
    const startYear = store.startDate ? new Date(store.startDate).getFullYear() : new Date().getFullYear()
    
    // Fetch existing projects to determine the next MH - XXX number
    const allProjRes = await projectsAPI.getProjects()
    const projects = allProjRes.data || []
    
    let maxNum = 0
    for (const p of projects) {
      if (!p.project_number) continue
      // Match the last sequence of digits in strings like "MH - 001", "MH002", "MH-2024-005"
      const match = p.project_number.match(/(\d+)$/)
      if (match) {
        const num = parseInt(match[1], 10)
        if (num > maxNum) maxNum = num
      }
    }
    
    const nextNum = maxNum + 1
    const projectNumber = `MH - ${String(nextNum).padStart(3, '0')}`
    
    const payload = {
      project_number: projectNumber,
      name: store.projectName,
      year: startYear,
      is_billed: 'unbilled',
      partner_remuneration: store.partnerCost,
      employee_remuneration: store.teamTotalCost,
      project_remuneration: store.grandTotal,
    }
    
    // Create the project
    const res = await projectsAPI.createProject(payload)
    const projectId = res.data.id
    
    // Assign team members
    for (const emp of store.employeesWithCost) {
      await projectsAPI.assignUser(projectId, emp.id)
    }
    
    alert(`Project ${projectNumber} and team added successfully!`)
    router.push('/admin/projects')
  } catch (err) {
    console.error('Failed to add project', err)
    alert('Failed to add project. Please try again.')
  } finally {
    isAddingProject.value = false
  }
}
</script>

<style scoped>
.step-card {
  background: #ffffff;
  border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius-lg);
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.step-header { display: flex; flex-direction: column; gap: 4px; }

.step-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  color: var(--color-on-surface);
  margin: 0;
}

.step-sub {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-on-surface-variant);
  margin: 0;
}

/* ── Summary document ── */
.summary-doc {
  border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.doc-project-header {
  background: var(--color-on-surface);
  padding: 28px 28px 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.doc-badge {
  display: inline-block;
  padding: 3px 10px;
  background: var(--color-primary);
  color: #ffffff;
  border-radius: 3px;
  font-family: var(--font-body);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  width: fit-content;
}

.doc-project-name {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.01em;
}

.doc-timeline {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-body);
  font-size: 13px;
  color: rgba(255,255,255,0.65);
  font-variant-numeric: tabular-nums;
}

.timeline-icon { font-size: 15px; }

/* Sections */
.doc-section {
  border-bottom: 1px solid var(--color-surface-container-high);
  padding: 20px 28px;
}

.doc-section:last-of-type { border-bottom: none; }

.doc-section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
  margin-bottom: 14px;
}

.doc-section-title .material-symbols-outlined { font-size: 16px; color: var(--color-primary); }

.doc-rows { display: flex; flex-direction: column; gap: 2px; }

.doc-row {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  align-items: center;
  gap: 8px;
  padding: 8px 4px;
  border-radius: var(--radius);
  transition: background 0.1s;
}

.doc-row:hover { background: var(--color-background); }

.doc-row-name {
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-on-surface);
}

.doc-row-formula {
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface-variant);
  font-variant-numeric: tabular-nums;
}

.doc-row-amount {
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-primary);
  text-align: right;
  font-variant-numeric: tabular-nums;
  min-width: 110px;
}

.doc-subtotal {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 4px 4px;
  border-top: 1px dashed var(--color-surface-container-high);
  margin-top: 10px;
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface-variant);
}

.sub-val {
  font-weight: 700;
  color: var(--color-on-surface);
  font-variant-numeric: tabular-nums;
}

/* Grand total */
.doc-grand-total {
  background: linear-gradient(135deg, #1e5d5e, var(--color-primary));
  padding: 28px 28px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.grand-label {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.8);
}

.grand-value {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 700;
  color: #ffffff;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}

/* ── Actions ── */
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.btn-ghost {
  display: flex; align-items: center; gap: 6px;
  padding: 10px 16px;
  border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius-lg);
  background: #ffffff;
  color: var(--color-on-surface-variant);
  font-family: var(--font-body);
  font-size: 14px; font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-ghost:hover { background: var(--color-background); border-color: var(--color-primary); color: var(--color-primary); }
.btn-ghost .material-symbols-outlined { font-size: 18px; }

.btn-outline-danger {
  display: flex; align-items: center; gap: 6px;
  padding: 10px 16px;
  border: 1px solid #fca5a5;
  border-radius: var(--radius-lg);
  background: #fff5f5;
  color: #dc2626;
  font-family: var(--font-body);
  font-size: 14px; font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-outline-danger:hover { background: #fee2e2; border-color: #dc2626; }
.btn-outline-danger .material-symbols-outlined { font-size: 18px; }

.btn-add {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 24px;
  background: var(--color-primary);
  color: #ffffff;
  border: none; border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 14px; font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.1s;
}

.btn-add:hover:not(:disabled) { opacity: 0.85; }
.btn-add:active:not(:disabled) { transform: scale(0.97); }
.btn-add:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-add .material-symbols-outlined { font-size: 18px; }

.btn-print {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 24px;
  background: var(--color-primary);
  color: #ffffff;
  border: none; border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 14px; font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.1s;
}

.btn-print:hover { opacity: 0.85; }
.btn-print:active { transform: scale(0.97); }
.btn-print .material-symbols-outlined { font-size: 18px; }
</style>
