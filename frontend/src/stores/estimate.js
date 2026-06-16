import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { estimatesAPI } from '../api/estimates'
import { useEstimateDrafts } from '../composables/useEstimateDrafts'

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
   *   id: number, label: string, type: string,
   *   basePay: number|null, hrsPerDay: number|null
   * }>>} */
  const employees = ref([])
  let nextEmpId = 1

  const partnerPayPerHour = ref(null)

  // ── Computed getters (derived — never stored) ──────────────────────────────
  const workingDays = computed(() => countWorkingDays(startDate.value, endDate.value))
  const calendarDays = computed(() => countCalendarDays(startDate.value, endDate.value))
  const teamHrsPerDay = computed(() =>
    employees.value.reduce((sum, emp) => sum + (Number(emp.hrsPerDay) || 0), 0)
  )
  const totalHours = computed(() => teamHrsPerDay.value * workingDays.value)

  const employeesWithCost = computed(() =>
    employees.value.map((emp) => {
      const bp = Number(emp.basePay) || 0
      const payPerHour = bp > 0 ? Math.round(((bp * 13 / 12) / 160) * 100) / 100 : 0
      const hd = Number(emp.hrsPerDay) || 0
      const hours = hd * workingDays.value
      const cost = payPerHour * hours
      return { ...emp, payPerHour, totalHours: hours, totalCost: cost }
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
        e.type &&
        e.basePay !== null &&
        e.basePay !== '' &&
        Number(e.basePay) > 0 &&
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

  function addEmployee() {
    employees.value.push({
      id: nextEmpId++,
      label: `Employee ${employees.value.length + 1}`,
      type: '',
      basePay: null,
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

  // ── Saved estimate tracking (for updates vs create) ────────────────────────
  const savedEstimateId = ref(null)
  const saving = ref(false)
  const savedEstimates = ref([])
  const loadingEstimates = ref(false)

  function reset() {
    // Detach from active draft without deleting it
    activeDraftId.value = null
    step.value = 1
    projectName.value = ''
    startDate.value = ''
    endDate.value = ''
    employees.value = []
    partnerPayPerHour.value = null
    savedEstimateId.value = null
  }

  // ── Multi-draft persistence via useEstimateDrafts ─────────────────────────
  const { saveDraft: saveDraftToStorage, deleteDraft: deleteDraftFromStorage, getDraft: getDraftFromStorage } = useEstimateDrafts()
  const activeDraftId = ref(null)

  function getSnapshot() {
    return {
      step: step.value,
      projectName: projectName.value,
      startDate: startDate.value,
      endDate: endDate.value,
      employees: JSON.parse(JSON.stringify(employees.value)),
      partnerPayPerHour: partnerPayPerHour.value,
      savedEstimateId: savedEstimateId.value,
    }
  }

  function saveDraft() {
    if (projectName.value || startDate.value || employees.value.length > 0) {
      activeDraftId.value = saveDraftToStorage(activeDraftId.value, getSnapshot())
    }
  }

  function loadDraftById(draftId) {
    const draft = getDraftFromStorage(draftId)
    if (!draft) return false
    const data = draft.data
    if (!data.projectName && !data.startDate) return false
    activeDraftId.value = draftId
    step.value = data.step || 1
    projectName.value = data.projectName || ''
    startDate.value = data.startDate || ''
    endDate.value = data.endDate || ''
    partnerPayPerHour.value = data.partnerPayPerHour ?? null
    savedEstimateId.value = data.savedEstimateId ?? null
    if (data.employees && data.employees.length > 0) {
      employees.value = data.employees
      nextEmpId = Math.max(...data.employees.map(e => e.id), 0) + 1
    }
    return true
  }

  // Legacy compat — kept for the draft banner restore flow
  function loadDraft() {
    // No-op now; use loadDraftById instead
    return false
  }
  function hasDraft() { return false }

  function clearDraft() {
    if (activeDraftId.value) {
      deleteDraftFromStorage(activeDraftId.value)
      activeDraftId.value = null
    }
  }

  function saveAndGetDraftId() {
    activeDraftId.value = saveDraftToStorage(activeDraftId.value, getSnapshot())
    return activeDraftId.value
  }

  // Auto-save on changes
  watch(
    [step, projectName, startDate, endDate, employees, partnerPayPerHour],
    () => {
      if (projectName.value || startDate.value || employees.value.length > 0) {
        saveDraft()
      }
    },
    { deep: true }
  )

  // ── Server persistence ────────────────────────────────────────────────────
  function buildPayload(overrides = {}) {
    return {
      project_name: projectName.value,
      start_date: startDate.value,
      end_date: endDate.value,
      working_days: workingDays.value,
      partner_pay_per_hour: Number(partnerPayPerHour.value) || 0,
      partner_cost: overrides.partnerCost ?? partnerCost.value,
      team_cost: overrides.teamCost ?? teamTotalCost.value,
      grand_total: overrides.grandTotal ?? grandTotal.value,
      project_color: overrides.projectColor || '#287475',
      status: overrides.status || 'draft',
      employees: employeesWithCost.value.map(e => ({
        emp_type: e.type,
        base_pay: Number(e.basePay) || 0,
        hrs_per_day: Number(e.hrsPerDay) || 0,
        pay_per_hour: e.payPerHour,
        total_hours: e.totalHours,
        total_cost: e.totalCost,
      })),
    }
  }

  async function saveEstimate(overrides = {}) {
    saving.value = true
    try {
      const payload = buildPayload(overrides)
      let res
      if (savedEstimateId.value) {
        res = await estimatesAPI.updateEstimate(savedEstimateId.value, payload)
      } else {
        res = await estimatesAPI.createEstimate(payload)
        savedEstimateId.value = res.data.id
      }
      saveDraft() // update draft with the saved ID
      return res.data
    } catch (err) {
      console.error('Failed to save estimate', err)
      throw err
    } finally {
      saving.value = false
    }
  }

  async function fetchSavedEstimates() {
    loadingEstimates.value = true
    try {
      const res = await estimatesAPI.getEstimates()
      savedEstimates.value = res.data
    } catch (err) {
      console.error('Failed to fetch estimates', err)
    } finally {
      loadingEstimates.value = false
    }
  }

  function loadEstimate(est) {
    projectName.value = est.project_name
    startDate.value = est.start_date
    endDate.value = est.end_date
    partnerPayPerHour.value = est.partner_pay_per_hour || null
    savedEstimateId.value = est.id

    if (est.employees && est.employees.length > 0) {
      employees.value = est.employees.map((e, i) => ({
        id: i + 1,
        label: `Employee ${i + 1}`,
        type: e.emp_type,
        basePay: e.base_pay,
        hrsPerDay: e.hrs_per_day,
      }))
      nextEmpId = est.employees.length + 1
    } else {
      employees.value = []
    }

    step.value = 3 // Jump to summary (partner & summary step)
  }

  async function deleteEstimate(id) {
    try {
      await estimatesAPI.deleteEstimate(id)
      savedEstimates.value = savedEstimates.value.filter(e => e.id !== id)
      if (savedEstimateId.value === id) {
        savedEstimateId.value = null
      }
    } catch (err) {
      console.error('Failed to delete estimate', err)
      throw err
    }
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
    teamHrsPerDay,
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
    // draft persistence
    activeDraftId,
    saveDraft,
    loadDraft,
    loadDraftById,
    hasDraft,
    clearDraft,
    saveAndGetDraftId,
    // server persistence
    savedEstimateId,
    saving,
    savedEstimates,
    loadingEstimates,
    saveEstimate,
    fetchSavedEstimates,
    loadEstimate,
    deleteEstimate,
  }
})
