<template>
  <div class="step-card">
    <div class="step-header">
      <h2 class="step-title">Team Cost Calculator</h2>
      <p class="step-sub">Add team members, set their type and base pay to calculate total project cost.</p>
    </div>

    <!-- Add Employee Button -->
    <div class="add-section">
      <button class="btn-add" @click="store.addEmployee()">
        <span class="material-symbols-outlined">person_add</span>
        Add Employee
      </button>
    </div>

    <!-- Cost Table -->
    <div v-if="store.employees.length > 0" class="table-section">
      <label class="section-label">Cost Breakdown</label>
      <div class="table-wrap">
        <table class="cost-table">
          <thead>
            <tr>
              <th>Type</th>
              <th class="num-col">Base Pay / Month (₹)</th>
              <th class="num-col">Pay / Hr (₹)</th>
              <th class="num-col">Hrs / Day</th>
              <th class="num-col">Total Days</th>
              <th class="num-col">Total Cost (₹)</th>
              <th class="action-col"></th>
            </tr>
          </thead>
          <tbody>
            <TransitionGroup name="emp-row">
              <tr
                v-for="emp in store.employeesWithCost"
                :key="emp.id"
                class="emp-row"
                :class="{ 'row-hovered': hoveredEmpId === emp.id }"
                @mouseenter="hoveredEmpId = emp.id"
                @mouseleave="hoveredEmpId = null"
              >
                <!-- Type dropdown -->
                <td>
                  <select
                    :value="emp.type"
                    class="type-select"
                    :class="{ placeholder: !emp.type }"
                    @change="store.updateEmployee(emp.id, 'type', $event.target.value)"
                  >
                    <option value="" disabled>— Select —</option>
                    <option v-for="t in empTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
                  </select>
                </td>
                <!-- Base Pay -->
                <td>
                  <CurrencyInput
                    :id="`base-pay-${emp.id}`"
                    :modelValue="emp.basePay"
                    class="table-input"
                    :class="{ error: payError(emp) }"
                    placeholder="e.g. 25000"
                    @update:modelValue="store.updateEmployee(emp.id, 'basePay', $event)"
                  />
                </td>
                <!-- Pay/Hr (auto) -->
                <td class="num-cell derived">{{ emp.payPerHour ? '₹' + emp.payPerHour.toFixed(2) : '—' }}</td>
                <!-- Hrs/Day -->
                <td>
                  <input
                    :id="`hrs-day-${emp.id}`"
                    :value="emp.hrsPerDay"
                    type="number"
                    min="0.5"
                    max="8"
                    step="0.5"
                    class="table-input"
                    :class="{ error: hrsError(emp) }"
                    @input="store.updateEmployee(emp.id, 'hrsPerDay', parseFloat($event.target.value) || null)"
                  />
                </td>
                <!-- Total Days (locked from step 1) -->
                <td class="num-cell locked">{{ store.workingDays }}</td>
                <!-- Total Cost -->
                <td class="num-cell cost-cell">{{ formatINR(emp.totalCost) }}</td>
                <!-- Remove -->
                <td>
                  <button class="remove-btn" title="Remove" @click="store.removeEmployee(emp.id)">
                    <span class="material-symbols-outlined">close</span>
                  </button>
                </td>
              </tr>
            </TransitionGroup>
          </tbody>
          <tfoot>
            <tr class="total-row">
              <td colspan="3" class="total-label">TOTAL</td>
              <td class="num-cell total-val">{{ store.teamHrsPerDay }} hrs/day</td>
              <td class="num-cell total-val">{{ store.workingDays }} days</td>
              <td class="num-cell total-val cost-cell">{{ formatINR(animatedTeamCost) }}</td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>

      <!-- Bar chart -->
      <div class="chart-section">
        <label class="section-label">Cost Distribution</label>
        <div class="bar-chart">
          <div
            v-for="emp in store.employeesWithCost"
            :key="emp.id"
            class="bar-row"
            :class="{ 'bar-hovered': hoveredEmpId === emp.id }"
            @mouseenter="hoveredEmpId = emp.id"
            @mouseleave="hoveredEmpId = null"
          >
            <div class="bar-label">{{ emp.type || emp.label }}</div>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: barWidth(emp.totalCost) + '%' }"></div>
            </div>
            <div class="bar-value">{{ formatINR(emp.totalCost) }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="empty-state">
      <span class="material-symbols-outlined empty-icon">group_add</span>
      <p class="empty-text">No team members added yet.<br/>Click <strong>"Add Employee"</strong> to start building your cost breakdown.</p>
    </div>

    <!-- CTA -->
    <div class="step-footer">
      <button class="btn-ghost" @click="store.setStep(1)">
        <span class="material-symbols-outlined">arrow_back</span>
        Back
      </button>
      <button
        id="est-step2-next"
        class="btn-primary"
        :disabled="!store.step2Valid"
        :title="!store.step2Valid ? 'Add at least one employee and fill all fields to continue' : ''"
        @click="store.setStep(3)"
      >
        Next: Partner Remuneration
        <span class="material-symbols-outlined">arrow_forward</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useEstimateStore } from '../../stores/estimate'
import CurrencyInput from '../CurrencyInput.vue'

const store = useEstimateStore()
const hoveredEmpId = ref(null)

const empTypes = [
  { value: 'Intern', label: 'Intern' },
  { value: 'Junior', label: 'Junior' },
  { value: 'Mid-Level', label: 'Mid-Level' },
  { value: 'Senior', label: 'Senior' },
  { value: 'Employee', label: 'Employee' },
]

// Animated total
const animatedTeamCost = ref(store.teamTotalCost)
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
watch(() => store.teamTotalCost, (v) => animateTo(animatedTeamCost, v))

function payError(emp) {
  return emp.basePay !== null && (Number(emp.basePay) <= 0)
}
function hrsError(emp) {
  return emp.hrsPerDay !== null && (Number(emp.hrsPerDay) <= 0 || Number(emp.hrsPerDay) > 8)
}

const maxCost = computed(() => Math.max(...store.employeesWithCost.map((e) => e.totalCost), 1))
function barWidth(cost) { return (cost / maxCost.value) * 100 }

const inrFmt = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
function formatINR(val) { return inrFmt.format(val || 0) }
</script>

<style scoped>
.step-card {
  background: #ffffff;
  border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius-lg);
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.step-header { display: flex; flex-direction: column; gap: 4px; }
.step-title { font-family: var(--font-display); font-size: 20px; font-weight: 700; color: var(--color-on-surface); margin: 0; }
.step-sub { font-family: var(--font-body); font-size: 14px; color: var(--color-on-surface-variant); margin: 0; }

.section-label {
  display: block; font-family: var(--font-body); font-size: 11px; font-weight: 600;
  letter-spacing: 0.05em; text-transform: uppercase; color: var(--color-on-surface-variant); margin-bottom: 10px;
}

/* Add button */
.add-section { display: flex; }
.btn-add {
  display: flex; align-items: center; gap: 8px; padding: 10px 20px;
  background: var(--color-primary); color: #fff; border: none; border-radius: var(--radius-lg);
  font-family: var(--font-body); font-size: 14px; font-weight: 600; cursor: pointer; transition: opacity .15s;
}
.btn-add:hover { opacity: 0.9; }
.btn-add .material-symbols-outlined { font-size: 18px; }

/* Empty state */
.empty-state {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  padding: 48px 24px; border: 2px dashed var(--color-surface-container-high);
  border-radius: var(--radius-lg); text-align: center;
}
.empty-icon { font-size: 40px; color: var(--color-outline); }
.empty-text { font-family: var(--font-body); font-size: 14px; color: var(--color-on-surface-variant); margin: 0; line-height: 1.6; }

/* Table */
.table-section { display: flex; flex-direction: column; }
.table-wrap { border: 1px solid var(--color-surface-container-high); border-radius: var(--radius-lg); overflow: hidden; margin-bottom: 20px; }
.cost-table { width: 100%; border-collapse: collapse; font-family: var(--font-body); font-size: 13px; }
.cost-table thead { background: var(--color-background); border-bottom: 1px solid var(--color-surface-container-high); }
.cost-table th { padding: 10px 12px; font-size: 11px; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; color: var(--color-on-surface-variant); text-align: left; white-space: nowrap; }
.num-col, .cost-table .num-cell { text-align: right; }
.action-col { width: 40px; }

.emp-row { border-bottom: 1px solid var(--color-surface-container); transition: background 0.1s; }
.emp-row:hover, .row-hovered { background: var(--color-background); }
.emp-row:last-child { border-bottom: none; }
.cost-table td { padding: 10px 12px; color: var(--color-on-surface); vertical-align: middle; }

.type-select {
  width: 130px; padding: 7px 8px; border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius); font-family: var(--font-body); font-size: 13px;
  color: var(--color-on-surface); background: #fff; outline: none; cursor: pointer; transition: border-color .15s;
}
.type-select.placeholder { color: var(--color-outline); }
.type-select:focus { border-color: var(--color-primary); box-shadow: 0 0 0 2px rgba(40,116,117,0.12); }

.num-cell { font-variant-numeric: tabular-nums; }
.locked { color: var(--color-outline); }
.derived { color: var(--color-primary); font-weight: 600; font-size: 13px; }
.cost-cell { font-weight: 600; color: var(--color-primary); }

.table-input {
  width: 100px; padding: 6px 8px; border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius); font-family: var(--font-body); font-size: 13px;
  color: var(--color-on-surface); text-align: right; outline: none; transition: border-color 0.15s;
  font-variant-numeric: tabular-nums;
}
.table-input:focus { border-color: var(--color-primary); box-shadow: 0 0 0 2px rgba(40,116,117,0.12); }
.table-input.error { border-color: #dc2626; }

.remove-btn {
  display: flex; align-items: center; justify-content: center; width: 28px; height: 28px;
  border: none; background: none; border-radius: var(--radius); cursor: pointer;
  color: var(--color-outline); transition: all 0.15s;
}
.remove-btn:hover { background: #fee2e2; color: #dc2626; }
.remove-btn .material-symbols-outlined { font-size: 16px; }

/* Tfoot */
.total-row { background: #f0fafa; border-top: 2px solid var(--color-primary); }
.total-label { padding: 12px; font-family: var(--font-body); font-size: 11px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--color-primary); }
.total-val { font-family: var(--font-body); font-size: 14px; font-weight: 700; color: var(--color-on-surface); font-variant-numeric: tabular-nums; text-align: right; padding: 12px; }

/* Bar chart */
.chart-section { display: flex; flex-direction: column; }
.bar-chart { display: flex; flex-direction: column; gap: 10px; }
.bar-row { display: flex; align-items: center; gap: 12px; padding: 4px 6px; border-radius: var(--radius); transition: background 0.1s; }
.bar-row.bar-hovered { background: #f0fafa; }
.bar-label { font-family: var(--font-body); font-size: 13px; color: var(--color-on-surface-variant); min-width: 120px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-transform: capitalize; }
.bar-track { flex: 1; height: 10px; background: var(--color-surface-container); border-radius: 99px; overflow: hidden; }
.bar-fill { height: 100%; background: linear-gradient(90deg, var(--color-primary), #44b8b9); border-radius: 99px; transition: width 0.5s cubic-bezier(0.25,1,0.5,1); }
.bar-row.bar-hovered .bar-fill { background: linear-gradient(90deg, #1e5d5e, var(--color-primary)); }
.bar-value { font-family: var(--font-body); font-size: 12px; font-weight: 600; color: var(--color-primary); min-width: 90px; text-align: right; font-variant-numeric: tabular-nums; }

/* Row transition */
.emp-row-enter-active { transition: all 0.3s ease; }
.emp-row-leave-active { transition: all 0.2s ease; }
.emp-row-enter-from { opacity: 0; transform: translateY(-8px); }
.emp-row-leave-to { opacity: 0; transform: translateX(20px); }

/* Footer */
.step-footer { display: flex; justify-content: space-between; align-items: center; }
.btn-primary {
  display: flex; align-items: center; gap: 8px; padding: 10px 24px;
  background: var(--color-primary); color: #ffffff; border: none; border-radius: var(--radius-lg);
  font-family: var(--font-body); font-size: 14px; font-weight: 600; cursor: pointer; transition: opacity 0.2s, transform 0.1s;
}
.btn-primary:hover:not(:disabled) { opacity: 0.9; }
.btn-primary:active:not(:disabled) { transform: scale(0.97); }
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-primary .material-symbols-outlined { font-size: 18px; }

.btn-ghost {
  display: flex; align-items: center; gap: 6px; padding: 10px 16px;
  border: 1px solid var(--color-surface-container-high); border-radius: var(--radius-lg);
  background: #ffffff; color: var(--color-on-surface-variant);
  font-family: var(--font-body); font-size: 14px; font-weight: 500; cursor: pointer; transition: all 0.15s;
}
.btn-ghost:hover { background: var(--color-background); border-color: var(--color-primary); color: var(--color-primary); }
.btn-ghost .material-symbols-outlined { font-size: 18px; }
</style>
