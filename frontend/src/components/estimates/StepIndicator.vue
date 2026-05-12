<template>
  <div class="step-indicator">
    <div v-for="n in 4" :key="n" class="step-wrapper">
      <!-- Connector line (before each step except first) -->
      <div v-if="n > 1" class="step-line" :class="{ filled: n <= currentStep }"></div>

      <!-- Step dot -->
      <div
        class="step-dot"
        :class="{
          completed: n < currentStep,
          active: n === currentStep,
          upcoming: n > currentStep,
        }"
      >
        <span v-if="n < currentStep" class="material-symbols-outlined check-icon">check</span>
        <span v-else class="step-num">{{ n }}</span>
      </div>

      <!-- Step label -->
      <div class="step-label" :class="{ active: n === currentStep, done: n < currentStep }">
        {{ labels[n - 1] }}
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  currentStep: {
    type: Number,
    required: true,
  },
})

const labels = ['Project Details', 'Team Costs', 'Partner Pay', 'Final Estimate']
</script>

<style scoped>
.step-indicator {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: 0;
  padding: 0 16px 32px;
  position: relative;
}

.step-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  position: relative;
  flex: 1;
  max-width: 160px;
}

/* Horizontal connector line */
.step-line {
  position: absolute;
  top: 16px;
  right: calc(50% + 16px);
  left: calc(-50% + 16px);
  height: 2px;
  background: var(--color-surface-container-high);
  transition: background 0.4s ease;
}

.step-line.filled {
  background: var(--color-primary);
}

/* Dot */
.step-dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  z-index: 1;
  transition: all 0.3s ease;
  position: relative;
}

.step-dot.upcoming {
  background: #ffffff;
  border: 2px solid var(--color-surface-container-high);
  color: var(--color-outline);
}

.step-dot.active {
  background: var(--color-primary);
  border: 2px solid var(--color-primary);
  color: #ffffff;
  box-shadow: 0 0 0 4px rgba(40, 116, 117, 0.18);
  animation: pulse-dot 2s ease-in-out infinite;
}

.step-dot.completed {
  background: var(--color-primary);
  border: 2px solid var(--color-primary);
  color: #ffffff;
}

@keyframes pulse-dot {
  0%, 100% { box-shadow: 0 0 0 4px rgba(40, 116, 117, 0.18); }
  50%       { box-shadow: 0 0 0 8px rgba(40, 116, 117, 0.08); }
}

.check-icon {
  font-size: 16px;
}

.step-num {
  font-variant-numeric: tabular-nums;
}

/* Label */
.step-label {
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-outline);
  text-align: center;
  line-height: 1.3;
  transition: color 0.3s;
}

.step-label.active {
  color: var(--color-primary);
}

.step-label.done {
  color: var(--color-on-surface-variant);
}
</style>
