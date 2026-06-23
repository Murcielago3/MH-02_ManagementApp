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
        <button class="btn-save-draft" @click="handleSaveDraft">
          <span class="material-symbols-outlined">save</span>
          Save Draft
        </button>
        <button class="btn-reset-sm" @click="confirmReset = true">
          <span class="material-symbols-outlined">restart_alt</span>
          New Estimate
        </button>
      </div>
    </div>

    <!-- Unsaved Drafts Panel -->
    <div v-if="hasDrafts && store.step === 1 && !store.projectName" class="drafts-card">
      <div class="drafts-header">
        <div class="drafts-header-left">
          <span class="material-symbols-outlined drafts-icon">edit_note</span>
          <span class="drafts-title">Unsaved Drafts</span>
          <span class="drafts-count">{{ drafts.length }}</span>
        </div>
      </div>
      <div class="drafts-list">
        <div v-for="d in drafts" :key="d.id" class="draft-item">
          <div class="draft-info">
            <span class="draft-label">{{ d.label }}</span>
            <span class="draft-meta">Last edited {{ formatDraftDate(d.updatedAt) }}</span>
          </div>
          <div class="draft-actions">
            <button class="draft-resume-btn" @click="resumeDraft(d.id)">
              <span class="material-symbols-outlined">edit</span>
              Resume
            </button>
            <button class="draft-delete-btn" @click="handleDeleteDraft(d.id)" title="Delete draft">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Saved Estimates List (shown when no active estimate) -->
    <div v-if="store.step === 1 && !store.projectName && store.savedEstimates.length > 0" class="saved-estimates">
      <div class="saved-header">
        <h3 class="saved-title">Saved Estimates</h3>
        <p class="saved-desc">Click an estimate to load and edit it</p>
      </div>
      <div class="saved-grid">
        <div
          v-for="est in store.savedEstimates"
          :key="est.id"
          class="saved-card"
          @click="store.loadEstimate(est)"
        >
          <div class="saved-card-top">
            <div class="saved-card-color" :style="{ background: est.project_color || '#287475' }"></div>
            <div class="saved-card-info">
              <span class="saved-card-name">{{ est.project_name }}</span>
              <span class="saved-card-date">
                {{ formatDate(est.start_date) }} – {{ formatDate(est.end_date) }}
              </span>
            </div>
            <span class="saved-card-status" :class="est.status">{{ est.status }}</span>
          </div>
          <div class="saved-card-bottom">
            <span class="saved-card-total">{{ inrFormat.format(est.grand_total || 0) }}</span>
            <span class="saved-card-team">{{ est.employees?.length || 0 }} team member{{ (est.employees?.length || 0) !== 1 ? 's' : '' }}</span>
          </div>
          <button class="saved-card-delete" title="Delete estimate" @click.stop="handleDeleteEstimate(est.id)">
            <span class="material-symbols-outlined">delete</span>
          </button>
        </div>
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
    </div>

    <!-- Active step panel -->
    <div class="step-panel-wrap">
      <Transition name="step-slide" mode="out-in">
        <StepOneDetails v-if="store.step === 1" key="step1" />
        <StepTwoEmployees v-else-if="store.step === 2" key="step2" />
        <StepThreePartner v-else-if="store.step === 3" key="step3" @reset="confirmReset = true" />
      </Transition>
    </div>

    <ToastNotification v-if="toastMsg" :message="toastMsg" :type="toastType" @done="toastMsg = ''" />

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
import { ref, computed, onMounted } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import { useEstimateStore, inrFormat } from '../stores/estimate'
import { useEstimateDrafts } from '../composables/useEstimateDrafts'
import StepIndicator from '../components/estimates/StepIndicator.vue'
import CollapsedStepCard from '../components/estimates/CollapsedStepCard.vue'
import StepOneDetails from '../components/estimates/StepOneDetails.vue'
import StepTwoEmployees from '../components/estimates/StepTwoEmployees.vue'
import StepThreePartner from '../components/estimates/StepThreePartner.vue'
import ToastNotification from '../components/ToastNotification.vue'

const store = useEstimateStore()
const { drafts, hasDrafts, deleteDraft: deleteDraftFromStorage, refresh: refreshDrafts } = useEstimateDrafts()
const confirmReset = ref(false)
const toastMsg = ref('')
const toastType = ref('success')
function showToast(msg, type = 'success') { toastMsg.value = msg; toastType.value = type }

onMounted(() => {
  refreshDrafts()
  store.fetchSavedEstimates()
})

async function resumeDraft(draftId) {
  await store.loadDraftById(draftId)
}

async function handleDeleteDraft(draftId) {
  await deleteDraftFromStorage(draftId)
  // If this was the active draft, clear it in the store
  if (store.activeDraftId === draftId) {
    store.activeDraftId = null
  }
}

async function handleSaveDraft() {
  await store.saveAndGetDraftId()
  await refreshDrafts()
  showToast('Draft saved')
}

function formatDraftDate(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  const now = new Date()
  const diffMs = now - d
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHrs = Math.floor(diffMins / 60)
  if (diffHrs < 24) return `${diffHrs}h ago`
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
}

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

function doReset() {
  store.reset()
  confirmReset.value = false
}

async function handleDeleteEstimate(id) {
  if (!confirm('Delete this saved estimate? This cannot be undone.')) return
  try {
    await store.deleteEstimate(id)
  } catch (err) {
    // Global axios interceptor surfaces the error toast
    console.error(err)
  }
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

.page-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-save-draft {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  color: var(--color-on-surface);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-save-draft:hover { background: var(--color-surface-dim); }
.btn-save-draft .material-symbols-outlined { font-size: 16px; color: var(--color-on-surface-variant); }

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

/* ── Drafts Card ── */
.drafts-card {
  background: #fffdf7;
  border: 1px solid #fde68a;
  border-radius: var(--radius-lg);
  overflow: hidden;
  margin-bottom: 16px;
}
.drafts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 18px;
  background: #fefce8;
  border-bottom: 1px solid #fde68a;
}
.drafts-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.drafts-icon {
  font-size: 18px;
  color: #b45309;
}
.drafts-title {
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 800;
  color: #92400e;
}
.drafts-count {
  font-size: 11px;
  font-weight: 700;
  background: #fbbf24;
  color: #78350f;
  padding: 1px 7px;
  border-radius: var(--radius-full);
}
.drafts-list {
  padding: 6px 10px;
}
.draft-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 8px;
  border-bottom: 1px solid #fef3c7;
  gap: 12px;
}
.draft-item:last-child { border-bottom: none; }
.draft-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.draft-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.draft-meta {
  font-size: 11px;
  color: var(--color-on-surface-variant);
}
.draft-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.draft-resume-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.15s;
}
.draft-resume-btn:hover { opacity: 0.88; }
.draft-resume-btn .material-symbols-outlined { font-size: 14px; }
.draft-delete-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-on-surface-variant);
  transition: background 0.15s, color 0.15s;
}
.draft-delete-btn:hover { background: #fee2e2; color: var(--color-error); }
.draft-delete-btn .material-symbols-outlined { font-size: 16px; }

/* ── Saved Estimates ── */
.saved-estimates {
  margin-bottom: 16px;
}
.saved-header {
  margin-bottom: 16px;
}
.saved-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  color: var(--color-on-surface);
  margin: 0;
}
.saved-desc {
  font-size: 13px;
  color: var(--color-on-surface-variant);
  margin: 4px 0 0;
}
.saved-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}
.saved-card {
  position: relative;
  background: var(--color-surface);
  border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius-lg);
  padding: 16px;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.saved-card:hover {
  border-color: var(--color-primary);
  box-shadow: 0 2px 12px rgba(40, 116, 117, 0.1);
}
.saved-card-top {
  display: flex;
  align-items: center;
  gap: 12px;
}
.saved-card-color {
  width: 8px;
  height: 36px;
  border-radius: 4px;
  flex-shrink: 0;
}
.saved-card-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.saved-card-name {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 700;
  color: var(--color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.saved-card-date {
  font-size: 11px;
  color: var(--color-on-surface-variant);
}
.saved-card-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  flex-shrink: 0;
}
.saved-card-status.draft { background: #f1f5f9; color: #64748b; }
.saved-card-status.finalized { background: #dcfce7; color: #15803d; }
.saved-card-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.saved-card-total {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  color: var(--color-primary);
  font-variant-numeric: tabular-nums;
}
.saved-card-team {
  font-size: 12px;
  color: var(--color-on-surface-variant);
}
.saved-card-delete {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-on-surface-variant);
  opacity: 0;
  transition: all 0.15s;
}
.saved-card:hover .saved-card-delete { opacity: 1; }
.saved-card-delete:hover { background: #fee2e2; color: #dc2626; }
.saved-card-delete .material-symbols-outlined { font-size: 16px; }
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

@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; gap: 10px; }
  .page-header-right { flex-wrap: wrap; }
  .saved-grid { grid-template-columns: 1fr; }
  .step-indicator { padding: 0 4px 20px; gap: 0; }
  .step-label { font-size: 9px; }
  .drafts-card { margin-bottom: 12px; }
}
</style>
