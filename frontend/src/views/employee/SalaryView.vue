<template>
  <EmployeeLayout>
    <div class="salary-view">
      <div class="view-header">
        <h2 class="view-title">Salary Slips</h2>
      </div>

      <!-- Month selector -->
      <div class="controls-row">
        <div class="year-select-group">
          <label>Financial Year</label>
          <select v-model="selectedYear" class="field-select">
            <option v-for="y in yearOptions" :key="y" :value="y">{{ y }} – {{ y + 1 }}</option>
          </select>
        </div>
      </div>

      <!-- Slips Grid -->
      <div class="slips-grid">
        <div
          v-for="month in months"
          :key="month.key"
          class="slip-card"
          :class="{ 'is-future': month.isFuture }"
        >
          <div class="slip-month">{{ month.label }}</div>
          <div class="slip-year">{{ month.year }}</div>

          <div class="slip-actions" v-if="!month.isFuture">
            <button class="btn-slip" disabled title="Salary slip will be available once uploaded by admin">
              <span class="material-symbols-outlined">download</span>
              Download
            </button>
          </div>
          <div class="slip-actions" v-else>
            <span class="slip-status">Upcoming</span>
          </div>
        </div>
      </div>

      <!-- Info Notice -->
      <div class="info-notice">
        <span class="material-symbols-outlined">info</span>
        <p>Salary slips are uploaded by the admin at the end of each month. If a slip is missing, please contact HR.</p>
      </div>
    </div>
  </EmployeeLayout>
</template>

<script setup>
import { computed, ref } from 'vue'
import EmployeeLayout from '../../components/EmployeeLayout.vue'

const now = new Date()
const currentMonth = now.getMonth() // 0-indexed
const currentCalendarYear = now.getFullYear()

// Indian FY: April (of selectedYear) to March (of selectedYear+1)
// Default to the FY that contains the current month
const defaultFY = currentMonth >= 3 ? currentCalendarYear : currentCalendarYear - 1
const selectedYear = ref(defaultFY)

const yearOptions = computed(() => {
  const years = []
  for (let y = defaultFY; y >= defaultFY - 4; y--) {
    years.push(y)
  }
  return years
})

const monthNames = [
  'April', 'May', 'June', 'July', 'August', 'September',
  'October', 'November', 'December', 'January', 'February', 'March'
]

const months = computed(() => {
  const fy = selectedYear.value
  return monthNames.map((label, i) => {
    // April=3 ... Dec=11, Jan=0, Feb=1, Mar=2
    const monthIndex = (i + 3) % 12
    const year = i < 9 ? fy : fy + 1
    const isFuture = new Date(year, monthIndex + 1, 0) > now
    return {
      key: `${year}-${monthIndex}`,
      label,
      year,
      monthIndex,
      isFuture,
    }
  })
})
</script>

<style scoped>
.salary-view {
  max-width: 1000px;
  margin: 0 auto;
}

.view-header {
  margin-bottom: 24px;
}

.view-title {
  font-family: 'Integral CF', sans-serif;
  font-size: 28px;
  font-weight: 700;
  color: var(--color-on-surface);
  margin: 0;
  letter-spacing: -0.02em;
}

/* Controls */
.controls-row {
  margin-bottom: 32px;
}

.year-select-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.year-select-group label {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-on-surface-variant);
}

.field-select {
  height: 40px;
  padding: 0 12px;
  border-radius: 4px;
  border: 1px solid #cbd5e1;
  font-family: var(--font-body);
  font-size: 14px;
  background: var(--color-surface);
  outline: none;
  cursor: pointer;
  min-width: 160px;
}

.field-select:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(40, 116, 117, 0.1);
}

/* Slips Grid */
.slips-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

@media (max-width: 900px) {
  .slips-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 640px) {
  .slips-grid { grid-template-columns: repeat(2, 1fr); }
}

.slip-card {
  background: var(--color-surface);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: border-color 0.2s;
}

.slip-card:hover:not(.is-future) {
  border-color: var(--color-primary);
}

.slip-card.is-future {
  opacity: 0.45;
}

.slip-month {
  font-family: 'Integral CF', sans-serif;
  font-size: 16px;
  font-weight: 700;
  color: var(--color-on-surface);
}

.slip-year {
  font-size: 13px;
  color: var(--color-on-surface-variant);
  margin-bottom: 12px;
  font-variant-numeric: tabular-nums;
}

.slip-actions {
  margin-top: auto;
}

.btn-slip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--color-surface-container);
  color: var(--color-on-surface-variant);
  border: 1px solid var(--color-outline-variant);
  border-radius: 4px;
  font-size: 13px;
  font-weight: 600;
  cursor: not-allowed;
  opacity: 0.7;
  transition: all 0.2s;
}

.btn-slip .material-symbols-outlined {
  font-size: 18px;
}

.slip-status {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-outline);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Info Notice */
.info-notice {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 20px;
  background: var(--color-surface-container);
  border: 1px solid var(--color-outline-variant);
  border-radius: 4px;
}

.info-notice .material-symbols-outlined {
  font-size: 20px;
  color: var(--color-primary);
  margin-top: 1px;
}

.info-notice p {
  margin: 0;
  font-size: 13px;
  color: var(--color-on-surface-variant);
  line-height: 1.5;
}
</style>
