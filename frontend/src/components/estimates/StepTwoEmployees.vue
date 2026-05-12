<template>
  <div class="step-card">
    <div class="step-header">
      <h2 class="step-title">Team Cost Calculator</h2>
      <p class="step-sub">Search and select employees, then enter their rates to calculate total team cost.</p>
    </div>

    <!-- Employee Picker -->
    <div class="picker-section">
      <label class="section-label">Select Employees</label>
      <div class="picker-search-wrap">
        <span class="material-symbols-outlined search-icon">search</span>
        <input
          id="est-emp-search"
          v-model="searchQuery"
          type="text"
          class="picker-search"
          placeholder="Search employees..."
        />
      </div>

      <div v-if="loadingUsers" class="picker-loading">
        <div class="spinner"></div>
        Loading employees…
      </div>
      <div v-else-if="filteredUsers.length === 0" class="picker-empty">No employees found.</div>
      <div v-else class="picker-grid">
        <div
          v-for="user in filteredUsers"
          :key="user.id"
          class="picker-chip"
          :class="{ selected: isSelected(user.id) }"
          @click="toggleEmployee(user)"
        >
          <div class="chip-avatar" :style="{ background: avatarColor(user.name) }">
            {{ initials(user.name) }}
          </div>
          <div class="chip-info">
            <div class="chip-name">{{ user.name }}</div>
            <div class="chip-role">{{ user.designation || user.role }}</div>
          </div>
          <span v-if="isSelected(user.id)" class="material-symbols-outlined chip-check">check_circle</span>
        </div>
      </div>
    </div>

    <!-- Cost Table -->
    <div v-if="store.employees.length > 0" class="table-section">
      <label class="section-label">Cost Breakdown</label>
      <div class="table-wrap">
        <table class="cost-table">
          <thead>
            <tr>
              <th>Employee</th>
              <th class="num-col">Pay/Hr (₹)</th>
              <th class="num-col">Hrs/Day</th>
              <th class="num-col">Total Days</th>
              <th class="num-col">Total Hours</th>
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
                <td>
                  <div class="name-cell">
                    <div class="row-avatar" :style="{ background: avatarColor(emp.name) }">
                      {{ initials(emp.name) }}
                    </div>
                    <div>
                      <div class="emp-name">{{ emp.name }}</div>
                      <div class="emp-role">{{ emp.designation }}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <CurrencyInput
                    :id="`pay-hr-${emp.id}`"
                    :modelValue="emp.payPerHour"
                    class="table-input"
                    :class="{ error: payError(emp) }"
                    placeholder="e.g. 250"
                    @update:modelValue="store.updateEmployee(emp.id, 'payPerHour', $event)"
                  />
                </td>
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
                <td class="num-cell locked">{{ store.workingDays }}</td>
                <td class="num-cell">{{ emp.totalHours }}</td>
                <td class="num-cell cost-cell">{{ formatINR(emp.totalCost) }}</td>
                <td>
                  <button class="remove-btn" title="Remove employee" @click="store.removeEmployee(emp.id)">
                    <span class="material-symbols-outlined">close</span>
                  </button>
                </td>
              </tr>
            </TransitionGroup>
          </tbody>
          <tfoot>
            <tr class="total-row">
              <td colspan="4" class="total-label">TOTAL</td>
              <td class="num-cell total-val">{{ animatedTeamHours }}</td>
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
            <div class="bar-label">{{ emp.name }}</div>
            <div class="bar-track">
              <div
                class="bar-fill"
                :style="{ width: barWidth(emp.totalCost) + '%' }"
              ></div>
            </div>
            <div class="bar-value">{{ formatINR(emp.totalCost) }}</div>
          </div>
        </div>
      </div>
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
        :title="!store.step2Valid ? 'Add at least one employee and fill all rates to continue' : ''"
        @click="store.setStep(3)"
      >
        Next: Partner Remuneration
        <span class="material-symbols-outlined">arrow_forward</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useEstimateStore } from '../../stores/estimate'
import { usersAPI } from '../../api/users'
import CurrencyInput from '../CurrencyInput.vue'

const store = useEstimateStore()

const allUsers = ref([])
const loadingUsers = ref(true)
const searchQuery = ref('')
const hoveredEmpId = ref(null)

// Animated totals
const animatedTeamHours = ref(store.teamTotalHours)
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

watch(() => store.teamTotalHours, (v) => animateTo(animatedTeamHours, v))
watch(() => store.teamTotalCost, (v) => animateTo(animatedTeamCost, v))

onMounted(async () => {
  try {
    const res = await usersAPI.getUsers()
    allUsers.value = res.data.filter((u) => u.is_active !== false)
  } catch (e) {
    console.error('Failed to load users', e)
  } finally {
    loadingUsers.value = false
  }
  // Sync animated values
  animatedTeamHours.value = store.teamTotalHours
  animatedTeamCost.value = store.teamTotalCost
})

const filteredUsers = computed(() => {
  const q = searchQuery.value.toLowerCase()
  if (!q) return allUsers.value
  return allUsers.value.filter(
    (u) =>
      u.name.toLowerCase().includes(q) ||
      (u.designation || '').toLowerCase().includes(q) ||
      u.role.toLowerCase().includes(q)
  )
})

function isSelected(id) {
  return store.employees.some((e) => e.id === id)
}

function toggleEmployee(user) {
  if (isSelected(user.id)) {
    store.removeEmployee(user.id)
  } else {
    store.addEmployee(user)
  }
}

function payError(emp) {
  return emp.payPerHour !== null && (Number(emp.payPerHour) <= 0)
}

function hrsError(emp) {
  return emp.hrsPerDay !== null && (Number(emp.hrsPerDay) <= 0 || Number(emp.hrsPerDay) > 8)
}

const maxCost = computed(() => Math.max(...store.employeesWithCost.map((e) => e.totalCost), 1))
function barWidth(cost) {
  return (cost / maxCost.value) * 100
}

const inrFmt = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
function formatINR(val) {
  return inrFmt.format(val || 0)
}

function initials(name) {
  if (!name) return '?'
  return name.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2)
}

const avatarColors = ['#d4edee', '#d5e3fd', '#f2e1b7', '#e2e0fc', '#ffdad6', '#d5f5e3']
function avatarColor(name) {
  if (!name) return avatarColors[0]
  let h = 0
  for (let i = 0; i < name.length; i++) h = name.charCodeAt(i) + ((h << 5) - h)
  return avatarColors[Math.abs(h) % avatarColors.length]
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
  gap: 28px;
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

.section-label {
  display: block;
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
  margin-bottom: 10px;
}

/* ── Picker ── */
.picker-section { display: flex; flex-direction: column; }

.picker-search-wrap {
  position: relative;
  margin-bottom: 12px;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-outline);
  font-size: 18px;
}

.picker-search {
  width: 100%;
  padding: 9px 12px 9px 36px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-on-surface);
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.15s;
}

.picker-search:focus { border-color: var(--color-primary); box-shadow: 0 0 0 2px rgba(40,116,117,0.12); }

.picker-loading {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-on-surface-variant);
  padding: 16px 0;
}

.spinner {
  width: 18px; height: 18px;
  border: 2px solid var(--color-surface-container-high);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.picker-empty {
  padding: 16px 0;
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-outline);
}

.picker-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
  max-height: 240px;
  overflow-y: auto;
  padding-right: 4px;
}

.picker-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.15s;
  background: var(--color-background);
  position: relative;
}

.picker-chip:hover { border-color: var(--color-primary); background: #f0fafa; }

.picker-chip.selected {
  border-color: var(--color-primary);
  background: #f0fafa;
}

.chip-avatar {
  width: 32px; height: 32px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-body);
  font-size: 12px; font-weight: 700;
  color: var(--color-on-surface);
  flex-shrink: 0;
}

.chip-info { flex: 1; min-width: 0; }

.chip-name {
  font-family: var(--font-body);
  font-size: 13px; font-weight: 600;
  color: var(--color-on-surface);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

.chip-role {
  font-family: var(--font-body);
  font-size: 11px; color: var(--color-on-surface-variant);
  text-transform: capitalize;
}

.chip-check { color: var(--color-primary); font-size: 18px; }

/* ── Table ── */
.table-section { display: flex; flex-direction: column; }

.table-wrap {
  border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius-lg);
  overflow: hidden;
  margin-bottom: 20px;
}

.cost-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-body);
  font-size: 13px;
}

.cost-table thead {
  background: var(--color-background);
  border-bottom: 1px solid var(--color-surface-container-high);
}

.cost-table th {
  padding: 10px 12px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
  text-align: left;
  white-space: nowrap;
}

.num-col, .cost-table .num-cell { text-align: right; }
.action-col { width: 40px; }

.emp-row {
  border-bottom: 1px solid var(--color-surface-container);
  transition: background 0.1s;
}

.emp-row:hover, .row-hovered { background: var(--color-background); }
.emp-row:last-child { border-bottom: none; }

.cost-table td {
  padding: 10px 12px;
  color: var(--color-on-surface);
  vertical-align: middle;
}

.name-cell { display: flex; align-items: center; gap: 10px; }

.row-avatar {
  width: 30px; height: 30px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700;
  color: var(--color-on-surface); flex-shrink: 0;
}

.emp-name { font-weight: 600; font-size: 13px; }
.emp-role { font-size: 11px; color: var(--color-on-surface-variant); text-transform: capitalize; }

.num-cell { font-variant-numeric: tabular-nums; }

.locked { color: var(--color-outline); }

.cost-cell { font-weight: 600; color: var(--color-primary); }

.table-input {
  width: 90px;
  padding: 6px 8px;
  border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius);
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  text-align: right;
  outline: none;
  transition: border-color 0.15s;
  font-variant-numeric: tabular-nums;
}

.table-input:focus { border-color: var(--color-primary); box-shadow: 0 0 0 2px rgba(40,116,117,0.12); }
.table-input.error { border-color: #dc2626; }

.remove-btn {
  display: flex; align-items: center; justify-content: center;
  width: 28px; height: 28px;
  border: none; background: none;
  border-radius: var(--radius); cursor: pointer;
  color: var(--color-outline);
  transition: all 0.15s;
}

.remove-btn:hover { background: #fee2e2; color: #dc2626; }
.remove-btn .material-symbols-outlined { font-size: 16px; }

/* Tfoot */
.total-row {
  background: #f0fafa;
  border-top: 2px solid var(--color-primary);
}

.total-label {
  padding: 12px;
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-primary);
}

.total-val {
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 700;
  color: var(--color-on-surface);
  font-variant-numeric: tabular-nums;
  text-align: right;
  padding: 12px;
}

/* ── Bar chart ── */
.chart-section { display: flex; flex-direction: column; }

.bar-chart { display: flex; flex-direction: column; gap: 10px; }

.bar-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 6px;
  border-radius: var(--radius);
  transition: background 0.1s;
}

.bar-row.bar-hovered { background: #f0fafa; }

.bar-label {
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface-variant);
  min-width: 120px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bar-track {
  flex: 1;
  height: 10px;
  background: var(--color-surface-container);
  border-radius: 99px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary), #44b8b9);
  border-radius: 99px;
  transition: width 0.5s cubic-bezier(0.25,1,0.5,1);
}

.bar-row.bar-hovered .bar-fill { background: linear-gradient(90deg, #1e5d5e, var(--color-primary)); }

.bar-value {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-primary);
  min-width: 90px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

/* ── Row transition ── */
.emp-row-enter-active { transition: all 0.3s ease; }
.emp-row-leave-active { transition: all 0.2s ease; }
.emp-row-enter-from { opacity: 0; transform: translateY(-8px); }
.emp-row-leave-to   { opacity: 0; transform: translateX(20px); }

/* ── Footer ── */
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
