<template>
  <div class="step-card">
    <div class="step-header">
      <h2 class="step-title">Partner Remuneration</h2>
      <p class="step-sub">Set your own hourly rate. Available hours are pulled from the project timeline.</p>
    </div>

    <!-- Rate input -->
    <div class="rate-section">
      <label class="field-label" for="est-partner-rate">Your Hourly Rate (₹) <span class="req">*</span></label>
      <div class="rate-input-wrap">
        <span class="rate-prefix">₹</span>
        <CurrencyInput
          id="est-partner-rate"
          v-model="store.partnerPayPerHour"
          class="rate-input"
          placeholder="e.g. 500"
        />
        <span class="rate-suffix">/ hr</span>
      </div>
    </div>

    <!-- Summary card -->
    <div class="remuneration-card">
      <div class="rem-row">
        <div class="rem-label">
          <span class="material-symbols-outlined rem-icon">payments</span>
          Partner Pay Rate
        </div>
        <div class="rem-value">{{ store.partnerPayPerHour ? formatINR(store.partnerPayPerHour) + '/hr' : '—' }}</div>
      </div>
      <div class="rem-divider"></div>
      <div class="rem-row">
        <div class="rem-label">
          <span class="material-symbols-outlined rem-icon">schedule</span>
          Available Hours
        </div>
        <div class="rem-value">{{ store.totalHours }} hrs <span class="rem-note">(from project timeline)</span></div>
      </div>
      <div class="rem-divider"></div>
      <div class="rem-row total-rem">
        <div class="rem-label big">
          <span class="material-symbols-outlined rem-icon">account_balance_wallet</span>
          Partner Remuneration
        </div>
        <div class="rem-value big animated-val">{{ formatINR(animatedCost) }}</div>
      </div>
    </div>

    <!-- Formula hint -->
    <div class="formula-hint">
      <span class="material-symbols-outlined hint-icon">info</span>
      {{ store.partnerPayPerHour || 0 }} × {{ store.totalHours }} hrs
      = <strong>{{ formatINR(store.partnerCost) }}</strong>
    </div>

    <!-- CTA -->
    <div class="step-footer">
      <button class="btn-ghost" @click="store.setStep(2)">
        <span class="material-symbols-outlined">arrow_back</span>
        Back
      </button>
      <button
        id="est-step3-next"
        class="btn-primary"
        :disabled="!store.step3Valid"
        :title="!store.step3Valid ? 'Enter a valid hourly rate to continue' : ''"
        @click="store.setStep(4)"
      >
        Next: Final Estimate
        <span class="material-symbols-outlined">arrow_forward</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useEstimateStore } from '../../stores/estimate'
import CurrencyInput from '../CurrencyInput.vue'

const store = useEstimateStore()

const animatedCost = ref(store.partnerCost)

function animateTo(refVal, target, duration = 400) {
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

watch(() => store.partnerCost, (v) => animateTo(animatedCost, v))

const inrFmt = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
function formatINR(val) {
  return inrFmt.format(val || 0)
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

.field-label {
  display: block;
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
  margin-bottom: 8px;
}

.req { color: #dc2626; }

/* Rate input */
.rate-section {}

.rate-input-wrap {
  display: flex;
  align-items: center;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  overflow: hidden;
  max-width: 280px;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.rate-input-wrap:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(40,116,117,0.15);
}

.rate-prefix, .rate-suffix {
  padding: 10px 12px;
  background: var(--color-background);
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-on-surface-variant);
  font-weight: 500;
  border-right: 1px solid var(--color-surface-container-high);
  white-space: nowrap;
}

.rate-suffix {
  border-right: none;
  border-left: 1px solid var(--color-surface-container-high);
}

.rate-input {
  flex: 1;
  padding: 10px 12px;
  border: none;
  outline: none;
  font-family: var(--font-body);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-on-surface);
  font-variant-numeric: tabular-nums;
  text-align: center;
  background: #ffffff;
}

/* Remuneration card */
.remuneration-card {
  background: #f0fafa;
  border: 1px solid #c5e8e8;
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.rem-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
}

.rem-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-on-surface-variant);
}

.rem-icon { font-size: 18px; color: var(--color-primary); }

.rem-value {
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-on-surface);
  font-variant-numeric: tabular-nums;
}

.rem-note {
  font-size: 12px;
  font-weight: 400;
  color: var(--color-outline);
  margin-left: 4px;
}

.rem-divider {
  height: 1px;
  background: #c5e8e8;
  margin: 0 20px;
}

.total-rem {
  background: var(--color-primary);
  padding: 20px;
  border-radius: 0 0 10px 10px;
}

.total-rem .rem-label.big {
  color: rgba(255, 255, 255, 0.85);
  font-size: 15px;
  font-weight: 600;
}

.total-rem .rem-icon { color: rgba(255,255,255,0.7); }

.animated-val {
  font-family: var(--font-display) !important;
  font-size: 24px !important;
  color: #ffffff !important;
  font-weight: 700 !important;
}

/* Formula hint */
.formula-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface-variant);
  background: var(--color-background);
  border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius-lg);
  padding: 10px 14px;
}

.hint-icon { font-size: 16px; color: var(--color-outline); }

/* Footer */
.step-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.btn-primary {
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

.btn-primary:hover:not(:disabled) { opacity: 0.9; }
.btn-primary:active:not(:disabled) { transform: scale(0.97); }
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-primary .material-symbols-outlined { font-size: 18px; }

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
</style>
