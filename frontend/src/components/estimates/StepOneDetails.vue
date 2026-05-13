<template>
  <div class="step-card">
    <div class="step-header">
      <h2 class="step-title">Project Details</h2>
      <p class="step-sub">Define the project name and timeline to calculate working hours.</p>
    </div>

    <!-- Fields -->
    <div class="form-grid">
      <div class="form-field full-width">
        <label class="field-label">Project Name <span class="req">*</span></label>
        <input
          id="est-project-name"
          v-model="store.projectName"
          type="text"
          class="field-input"
          :class="{ error: nameError }"
          placeholder="e.g. Villa Renovation — Phase 2"
          @blur="nameBlurred = true"
        />
        <span v-if="nameError" class="field-error">Project name is required.</span>
      </div>

      <div class="form-field">
        <label class="field-label">Start Date <span class="req">*</span></label>
        <input
          id="est-start-date"
          v-model="store.startDate"
          type="date"
          class="field-input"
          :class="{ error: dateError }"
          @change="onDateChange"
        />
      </div>

      <div class="form-field">
        <label class="field-label">End Date <span class="req">*</span></label>
        <input
          id="est-end-date"
          v-model="store.endDate"
          type="date"
          class="field-input"
          :class="{ error: dateError }"
          :min="store.startDate"
          @change="onDateChange"
        />
        <span v-if="dateError" class="field-error">End date must be after start date.</span>
      </div>
    </div>

    <!-- Stats cards -->
    <transition name="stats-fade">
      <div v-if="statsVisible" class="stats-section">
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-label">Calendar Days</div>
            <div class="stat-value" id="stat-calendar">{{ displayCalendar }}</div>
          </div>
          <div class="stat-card accent">
            <div class="stat-label">Working Days</div>
            <div class="stat-value" id="stat-working">{{ displayWorking }}</div>
          </div>
          <div class="stat-card dim">
            <div class="stat-label">Weeks</div>
            <div class="stat-value" id="stat-weeks">{{ displayWeeks }}</div>
          </div>
        </div>

        <!-- Summary line -->
        <div class="summary-line">
          <span class="material-symbols-outlined sum-icon">calendar_today</span>
          <span>
            <strong>{{ displayWeeks }}</strong> weeks ·
            <strong>{{ displayWorking }}</strong> working days
          </span>
        </div>

        <!-- Timeline bar -->
        <div class="timeline-bar-wrap">
          <div class="timeline-bar-label">{{ formatDate(store.startDate) }}</div>
          <div class="timeline-track">
            <div
              class="timeline-fill"
              :style="{ width: timelineFillPct + '%' }"
            ></div>
            <div class="timeline-thumb" :style="{ left: timelineFillPct + '%' }"></div>
          </div>
          <div class="timeline-bar-label">{{ formatDate(store.endDate) }}</div>
        </div>
      </div>
    </transition>

    <!-- CTA -->
    <div class="step-footer">
      <button
        id="est-step1-next"
        class="btn-primary"
        :disabled="!store.step1Valid"
        :title="!store.step1Valid ? 'Fill in all fields with a valid date range to continue' : ''"
        @click="goNext"
      >
        Next: Add Team
        <span class="material-symbols-outlined">arrow_forward</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useEstimateStore } from '../../stores/estimate'

const store = useEstimateStore()

const nameBlurred = ref(false)
const statsVisible = ref(false)

// Animated display values
const animatedCalendar = ref(0)
const animatedWorking = ref(0)

// Formatted display strings
const displayCalendar = computed(() => animatedCalendar.value)
const displayWorking = computed(() => animatedWorking.value)
const displayWeeks = computed(() => {
  if (!store.calendarDays) return 0
  const w = store.calendarDays / 7
  return Number.isInteger(w) ? w : parseFloat(w.toFixed(1))
})

// Error states
const nameError = computed(() => nameBlurred.value && !store.projectName.trim())
const dateError = computed(() => {
  if (!store.startDate || !store.endDate) return false
  return new Date(store.endDate) <= new Date(store.startDate)
})

// Timeline fill percentage (always 100% when valid, animates from 0)
const timelineFillPct = ref(0)

// Number counter animation
function animateTo(ref, target, duration = 400) {
  const start = ref.value
  const diff = target - start
  if (diff === 0) return
  const startTime = performance.now()
  function step(now) {
    const elapsed = now - startTime
    const progress = Math.min(elapsed / duration, 1)
    const ease = 1 - Math.pow(1 - progress, 3)
    ref.value = Math.round(start + diff * ease)
    if (progress < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

function onDateChange() {
  if (store.step1Valid) {
    statsVisible.value = true
    animateTo(animatedCalendar, store.calendarDays)
    animateTo(animatedWorking, store.workingDays)
    // Animate timeline fill
    timelineFillPct.value = 0
    setTimeout(() => {
      timelineFillPct.value = 100
    }, 50)
  }
}

// Re-trigger animation when store values change externally (e.g. going back to edit)
watch(
  () => store.workingDays,
  (val) => {
    if (val > 0) {
      statsVisible.value = true
      animateTo(animatedCalendar, store.calendarDays)
      animateTo(animatedWorking, val)
      timelineFillPct.value = 100
    }
  },
  { immediate: true }
)

onMounted(() => {
  if (store.step1Valid) {
    statsVisible.value = true
    animatedCalendar.value = store.calendarDays
    animatedWorking.value = store.workingDays
    timelineFillPct.value = 100
  }
})

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

function goNext() {
  if (store.step1Valid) store.setStep(2)
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

/* ── Form ── */
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-field { display: flex; flex-direction: column; gap: 6px; }
.full-width { grid-column: 1 / -1; }

.field-label {
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
}

.req { color: #dc2626; }

.field-input {
  padding: 10px 12px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius);
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-on-surface);
  background: #ffffff;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.field-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(40, 116, 117, 0.15);
}

.field-input.error {
  border-color: #dc2626;
  box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.1);
}

.field-error {
  font-family: var(--font-body);
  font-size: 12px;
  color: #dc2626;
}

/* ── Stats ── */
.stats-section { display: flex; flex-direction: column; gap: 16px; }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.stat-card {
  background: var(--color-background);
  border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius-lg);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: transform 0.15s;
}

.stat-card:hover { transform: translateY(-1px); }

.stat-card.accent {
  background: #f0fafa;
  border-color: var(--color-primary);
}

.stat-card.dim {
  background: var(--color-surface-container);
}

.stat-label {
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
}

.stat-value {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--color-on-surface);
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.stat-card.accent .stat-value { color: var(--color-primary); }

/* Summary line */
.summary-line {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-on-surface-variant);
  background: #f0fafa;
  border: 1px solid #c5e8e8;
  border-radius: var(--radius-lg);
  padding: 10px 14px;
}

.sum-icon { color: var(--color-primary); font-size: 18px; }

/* Timeline bar */
.timeline-bar-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

.timeline-bar-label {
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--color-on-surface-variant);
  white-space: nowrap;
  min-width: 90px;
}

.timeline-bar-label:last-child { text-align: right; }

.timeline-track {
  flex: 1;
  height: 8px;
  background: var(--color-surface-container-high);
  border-radius: 99px;
  position: relative;
  overflow: visible;
}

.timeline-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary), #44a8a9);
  border-radius: 99px;
  transition: width 0.8s cubic-bezier(0.25, 1, 0.5, 1);
}

.timeline-thumb {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 16px;
  height: 16px;
  background: var(--color-primary);
  border: 2px solid #ffffff;
  border-radius: 50%;
  box-shadow: 0 1px 4px rgba(0,0,0,0.15);
  transition: left 0.8s cubic-bezier(0.25, 1, 0.5, 1);
}

/* ── CTA ── */
.step-footer { display: flex; justify-content: flex-end; }

.btn-primary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  background: var(--color-primary);
  color: #ffffff;
  border: none;
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.1s;
}

.btn-primary:hover:not(:disabled) { opacity: 0.9; }
.btn-primary:active:not(:disabled) { transform: scale(0.97); }
.btn-primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn-primary .material-symbols-outlined { font-size: 18px; }

/* Transition */
.stats-fade-enter-active { transition: opacity 0.4s ease, transform 0.4s ease; }
.stats-fade-enter-from   { opacity: 0; transform: translateY(8px); }
</style>
