<template>
  <AppLayout>
    <!-- Page header -->
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-icon">
          <span class="material-symbols-outlined">calculate</span>
        </div>
        <div>
          <h1 class="page-title">Project Estimate</h1>
          <p class="page-desc">Build a detailed cost breakdown in 4 steps</p>
        </div>
      </div>
      <div class="page-header-right" v-if="store.step > 1">
        <button class="btn-reset-sm" @click="confirmReset = true">
          <span class="material-symbols-outlined">restart_alt</span>
          New Estimate
        </button>
      </div>
    </div>

    <!-- Step indicator -->
    <StepIndicator :current-step="store.step" />

    <!-- Collapsed summaries for completed steps -->
    <div class="collapsed-stack">
      <CollapsedStepCard
        v-if="store.step > 1"
        :step-number="1"
        title="Project Details"
        :summary="step1Summary"
        @edit="store.setStep(1)"
      />
      <CollapsedStepCard
        v-if="store.step > 2"
        :step-number="2"
        title="Team Costs"
        :summary="step2Summary"
        @edit="store.setStep(2)"
      />
      <CollapsedStepCard
        v-if="store.step > 3"
        :step-number="3"
        title="Partner Remuneration"
        :summary="step3Summary"
        @edit="store.setStep(3)"
      />
    </div>

    <!-- Active step panel -->
    <div class="step-panel-wrap">
      <Transition name="step-slide" mode="out-in">
        <StepOneDetails v-if="store.step === 1" key="step1" />
        <StepTwoEmployees v-else-if="store.step === 2" key="step2" />
        <StepThreePartner v-else-if="store.step === 3" key="step3" />
        <StepFourSummary v-else-if="store.step === 4" key="step4" />
      </Transition>
    </div>

    <!-- Reset confirmation dialog -->
    <Teleport to="body">
      <div v-if="confirmReset" class="modal-backdrop" @click.self="confirmReset = false">
        <div class="confirm-modal">
          <div class="confirm-icon">
            <span class="material-symbols-outlined">restart_alt</span>
          </div>
          <h3 class="confirm-title">Start Fresh?</h3>
          <p class="confirm-body">This will clear all entered data and return to Step 1.</p>
          <div class="confirm-actions">
            <button class="btn-ghost" @click="confirmReset = false">Cancel</button>
            <button class="btn-danger" @click="doReset">Yes, Reset</button>
          </div>
        </div>
      </div>
    </Teleport>
  </AppLayout>
</template>

<script setup>
import { ref, computed } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import { useEstimateStore, inrFormat } from '../stores/estimate'
import StepIndicator from '../components/estimates/StepIndicator.vue'
import CollapsedStepCard from '../components/estimates/CollapsedStepCard.vue'
import StepOneDetails from '../components/estimates/StepOneDetails.vue'
import StepTwoEmployees from '../components/estimates/StepTwoEmployees.vue'
import StepThreePartner from '../components/estimates/StepThreePartner.vue'
import StepFourSummary from '../components/estimates/StepFourSummary.vue'

const store = useEstimateStore()
const confirmReset = ref(false)

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

const step1Summary = computed(() =>
  `${store.projectName} · ${store.workingDays} working days`
)

const step2Summary = computed(() => {
  const cost = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(store.teamTotalCost)
  return `${store.employees.length} team member${store.employees.length !== 1 ? 's' : ''} · ${cost}`
})

const step3Summary = computed(() => {
  const cost = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(store.partnerCost)
  return `₹${store.partnerPayPerHour}/hr · ${cost}`
})

function doReset() {
  store.reset()
  confirmReset.value = false
}
</script>

<style scoped>
/* ── Page header ── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.page-header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.page-icon {
  width: 44px;
  height: 44px;
  background: var(--color-on-surface);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.page-icon .material-symbols-outlined {
  font-size: 22px;
  color: #ffffff;
}

.page-title {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--color-on-surface);
  margin: 0;
  letter-spacing: -0.02em;
}

.page-desc {
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface-variant);
  margin: 2px 0 0;
}

.btn-reset-sm {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius-lg);
  background: #ffffff;
  color: var(--color-on-surface-variant);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-reset-sm:hover { border-color: #dc2626; color: #dc2626; background: #fff5f5; }
.btn-reset-sm .material-symbols-outlined { font-size: 16px; }

/* ── Collapsed stack ── */
.collapsed-stack {
  display: flex;
  flex-direction: column;
}

/* ── Step panel ── */
.step-panel-wrap {
  flex: 1;
}

/* ── Slide transitions ── */
.step-slide-enter-active {
  transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
}
.step-slide-leave-active {
  transition: all 0.2s ease;
}
.step-slide-enter-from {
  opacity: 0;
  transform: translateX(40px);
}
.step-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

/* ── Confirm modal ── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  backdrop-filter: blur(2px);
}

.confirm-modal {
  background: #ffffff;
  border-radius: var(--radius-lg);
  padding: 32px;
  width: 380px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  text-align: center;
}

.confirm-icon {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: #fff5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 4px;
}

.confirm-icon .material-symbols-outlined {
  font-size: 26px;
  color: #dc2626;
}

.confirm-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--color-on-surface);
  margin: 0;
}

.confirm-body {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-on-surface-variant);
  margin: 0;
}

.confirm-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
  width: 100%;
}

.btn-ghost {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius-lg);
  background: #ffffff;
  color: var(--color-on-surface-variant);
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-ghost:hover { background: var(--color-background); }

.btn-danger {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px 16px;
  border: none;
  border-radius: var(--radius-lg);
  background: #dc2626;
  color: #ffffff;
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}

.btn-danger:hover { opacity: 0.9; }
</style>

<!-- ══ GLOBAL PRINT STYLES ══ -->
<style>
@media print {
  /* Hide everything except the summary document */
  .sidebar,
  .top-bar,
  .page-header,
  .step-indicator,
  .collapsed-stack,
  .step-footer,
  .action-bar,
  .step-title,
  .step-sub,
  .step-header {
    display: none !important;
  }

  .app-shell {
    display: block !important;
  }

  .main-area {
    margin-left: 0 !important;
  }

  .page-content {
    margin-top: 0 !important;
    padding: 0 !important;
  }

  .step-card {
    border: none !important;
    padding: 0 !important;
    box-shadow: none !important;
    gap: 0 !important;
  }

  #est-print-area {
    display: block !important;
  }

  .summary-doc {
    border: none !important;
  }

  .doc-grand-total {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  .doc-project-header {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
}
</style>
