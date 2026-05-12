import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// ─── Indian currency formatter ───────────────────────────────────────────────
export const inrFormat = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})

export const numFormat = new Intl.NumberFormat('en-IN', {
  maximumFractionDigits: 0,
})

// ─── Working days calculation (loop, Mon–Fri only) ───────────────────────────
export function countWorkingDays(startStr, endStr) {
  if (!startStr || !endStr) return 0
  const [sy, sm, sd] = startStr.split('-').map(Number)
  const [ey, em, ed] = endStr.split('-').map(Number)
  const current = new Date(sy, sm - 1, sd)
  const endDate = new Date(ey, em - 1, ed)
  if (isNaN(current) || isNaN(endDate) || current > endDate) return 0
  let count = 0
  while (current <= endDate) {
    const day = current.getDay()
    if (day !== 0 && day !== 6) count++
    current.setDate(current.getDate() + 1)
  }
  return count
}

export function countCalendarDays(startStr, endStr) {
  if (!startStr || !endStr) return 0
  const [sy, sm, sd] = startStr.split('-').map(Number)
  const [ey, em, ed] = endStr.split('-').map(Number)
  const s = new Date(sy, sm - 1, sd)
  const e = new Date(ey, em - 1, ed)
  if (isNaN(s) || isNaN(e) || s > e) return 0
  const msInDay = 1000 * 60 * 60 * 24
  return Math.round((Date.UTC(e.getFullYear(), e.getMonth(), e.getDate()) - Date.UTC(s.getFullYear(), s.getMonth(), s.getDate())) / msInDay) + 1
}

// ─── Store ───────────────────────────────────────────────────────────────────
export const useEstimateStore = defineStore('estimate', () => {
  // ── Raw state ──────────────────────────────────────────────────────────────
  const step = ref(1)
  const projectName = ref('')
  const startDate = ref('')
  const endDate = ref('')

  /** @type {import('vue').Ref<Array<{
   *   id: number, name: string, designation: string,
   *   payPerHour: number|null, hrsPerDay: number|null
   * }>>} */
  const employees = ref([])

  const partnerPayPerHour = ref(null)

  // ── Computed getters (derived — never stored) ──────────────────────────────
  const workingDays = computed(() => countWorkingDays(startDate.value, endDate.value))
  const calendarDays = computed(() => countCalendarDays(startDate.value, endDate.value))
  const totalHours = computed(() => workingDays.value * 8)

  const employeesWithCost = computed(() =>
    employees.value.map((emp) => {
      const ph = Number(emp.payPerHour) || 0
      const hd = Number(emp.hrsPerDay) || 0
      const hours = hd * workingDays.value
      const cost = ph * hours
      return { ...emp, totalHours: hours, totalCost: cost }
    })
  )

  const teamTotalHours = computed(() =>
    employeesWithCost.value.reduce((s, e) => s + e.totalHours, 0)
  )
  const teamTotalCost = computed(() =>
    employeesWithCost.value.reduce((s, e) => s + e.totalCost, 0)
  )

  const partnerCost = computed(() => {
    const ph = Number(partnerPayPerHour.value) || 0
    return ph * totalHours.value
  })

  const grandTotal = computed(() => teamTotalCost.value + partnerCost.value)

  // ── Validation helpers ─────────────────────────────────────────────────────
  const step1Valid = computed(() => {
    if (!projectName.value.trim()) return false
    if (!startDate.value || !endDate.value) return false
    return new Date(endDate.value) > new Date(startDate.value)
  })

  const step2Valid = computed(() => {
    if (employees.value.length === 0) return false
    return employees.value.every(
      (e) =>
        e.payPerHour !== null &&
        e.payPerHour !== '' &&
        Number(e.payPerHour) > 0 &&
        e.hrsPerDay !== null &&
        e.hrsPerDay !== '' &&
        Number(e.hrsPerDay) > 0 &&
        Number(e.hrsPerDay) <= 8
    )
  })

  const step3Valid = computed(
    () => partnerPayPerHour.value !== null && Number(partnerPayPerHour.value) > 0
  )

  // ── Actions ────────────────────────────────────────────────────────────────
  function setStep(n) {
    step.value = n
  }

  function addEmployee(emp) {
    if (employees.value.find((e) => e.id === emp.id)) return
    employees.value.push({
      id: emp.id,
      name: emp.name,
      designation: emp.designation || '',
      payPerHour: null,
      hrsPerDay: 8,
    })
  }

  function removeEmployee(id) {
    employees.value = employees.value.filter((e) => e.id !== id)
  }

  function updateEmployee(id, field, value) {
    const emp = employees.value.find((e) => e.id === id)
    if (emp) emp[field] = value
  }

  function reset() {
    step.value = 1
    projectName.value = ''
    startDate.value = ''
    endDate.value = ''
    employees.value = []
    partnerPayPerHour.value = null
  }

  return {
    // state
    step,
    projectName,
    startDate,
    endDate,
    employees,
    partnerPayPerHour,
    // computed
    workingDays,
    calendarDays,
    totalHours,
    employeesWithCost,
    teamTotalHours,
    teamTotalCost,
    partnerCost,
    grandTotal,
    step1Valid,
    step2Valid,
    step3Valid,
    // actions
    setStep,
    addEmployee,
    removeEmployee,
    updateEmployee,
    reset,
  }
})
