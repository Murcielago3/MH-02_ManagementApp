import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { weeklyTimesheetsAPI } from '../api/weekly_timesheets'
import { projectsAPI } from '../api/projects'
import { tasksAPI } from '../api/tasks'

export const useTimesheetStore = defineStore('timesheet', () => {
  const pendingWeeks = ref([])
  const submittedTimesheets = ref([])
  const projects = ref([])
  const selectedWeek = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const form = ref({
    description: '',
    entries: [
      { project_id: null, hours: 0, description: '' }
    ]
  })

  // Getters
  const pendingCount = computed(() => {
    return pendingWeeks.value.filter(w => w.status === 'pending').length
  })

  const selectedTimesheet = computed(() => {
    if (!selectedWeek.value) return null
    return submittedTimesheets.value.find(
      ts => ts.week_start === selectedWeek.value.week_start
    )
  })

  // Actions
  async function fetchPendingWeeks() {
    try {
      const res = await weeklyTimesheetsAPI.getPendingWeeks()
      pendingWeeks.value = res.data
    } catch (err) {
      console.error('Failed to fetch pending weeks', err)
      error.value = err.response?.data?.detail || 'Failed to load pending weeks'
    }
  }

  async function fetchMyTimesheets() {
    try {
      const res = await weeklyTimesheetsAPI.getMyTimesheets()
      submittedTimesheets.value = res.data
    } catch (err) {
      console.error('Failed to fetch my timesheets', err)
      error.value = err.response?.data?.detail || 'Failed to load timesheets'
    }
  }

  async function fetchProjects() {
    try {
      const res = await projectsAPI.getProjects()
      projects.value = res.data
    } catch (err) {
      console.error('Failed to fetch projects', err)
      error.value = err.response?.data?.detail || 'Failed to load projects'
    }
  }

  async function initialize() {
    loading.value = true
    error.value = null
    try {
      await Promise.all([
        fetchPendingWeeks(),
        fetchMyTimesheets(),
        fetchProjects()
      ])
    } finally {
      loading.value = false
    }
  }

  async function selectWeek(week) {
    selectedWeek.value = week
    loading.value = true
    try {
      // Reset form
      form.value = {
        description: '',
        entries: []
      }
      
      // 1. Check if we have a submitted/rejected timesheet
      const ts = submittedTimesheets.value.find(t => t.week_start === week.week_start)
      if (ts) {
        form.value.description = ts.description || ''
        if (ts.entries && ts.entries.length > 0) {
          form.value.entries = ts.entries.map(e => ({
            project_id: e.project_id,
            hours: Number(e.hours),
            description: e.description
          }))
        }
      } else {
        // 2. If it's a new timesheet, fetch assigned tasks for this week
        await fetchTasksForWeek(week)
      }
    } finally {
      loading.value = false
    }
  }

  async function fetchTasksForWeek(week) {
    try {
      // We'll use the existing /my tasks endpoint or a range-based one if available.
      // For now, let's fetch my tasks and filter them by date range in JS.
      const res = await tasksAPI.getMyTasks()
      const myTasks = res.data
      
      const wStart = new Date(week.week_start)
      const wEnd = new Date(week.week_end)
      
      const autoEntries = []
      
      for (const t of myTasks) {
        const tStart = new Date(t.date)
        const tEnd = t.end_date ? new Date(t.end_date) : tStart
        
        // Calculate overlap between task range and week range
        const overlapStart = new Date(Math.max(tStart, wStart))
        const overlapEnd = new Date(Math.min(tEnd, wEnd))
        
        if (overlapStart <= overlapEnd) {
          // Task falls in this week. Build daily hours array (Mon=0..Sun=6)
          const daily = [0, 0, 0, 0, 0, 0, 0]
          const hoursPerDay = t.duration_hours || 0
          let current = new Date(overlapStart)
          while (current <= overlapEnd) {
            const jsDay = current.getDay() // 0=Sun, 1=Mon, ...
            // Map JS day to Mon-based index: Mon=0, Tue=1, ..., Sun=6
            const idx = jsDay === 0 ? 6 : jsDay - 1
            daily[idx] = hoursPerDay
            current.setDate(current.getDate() + 1)
          }
          const totalHours = daily.reduce((s, v) => s + v, 0)

          if (totalHours > 0) {
            autoEntries.push({
              project_id: t.project_id,
              hours: totalHours,
              daily: daily,
              description: t.title,
              is_auto: true
            })
          }
        }
      }
      
      if (autoEntries.length > 0) {
        form.value.entries = autoEntries
      } else {
        // Default empty row
        form.value.entries = [{ project_id: null, hours: 0, description: '' }]
      }
    } catch (err) {
      console.error('Failed to fetch tasks for week', err)
      form.value.entries = [{ project_id: null, hours: 0, description: '' }]
    }
  }

  async function submitTimesheet() {
    if (!selectedWeek.value) return
    loading.value = true
    error.value = null
    try {
      await weeklyTimesheetsAPI.submitTimesheet({
        week_start: selectedWeek.value.week_start,
        week_end: selectedWeek.value.week_end,
        description: form.value.description,
        // Only submit rows actually worked on — a project left at 0h means the
        // employee didn't work on it this week, so it's dropped rather than sent.
        entries: form.value.entries
          .filter(e => e.project_id && (Number(e.hours) || 0) > 0)
          .map(e => ({
            project_id: e.project_id,
            hours: Number(e.hours),
            description: e.description,
            daily_hours: e.daily ? e.daily.map(h => Number(h) || 0) : null
          }))
      })
      // Refresh
      await initialize()
      
      // Update selected week to reflect new status
      const updatedWeek = pendingWeeks.value.find(w => w.week_start === selectedWeek.value.week_start)
      if (updatedWeek) {
        selectedWeek.value = updatedWeek
      }
      
    } catch (err) {
      console.error('Failed to submit timesheet', err)
      error.value = err.response?.data?.detail || 'Failed to submit timesheet'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    pendingWeeks,
    submittedTimesheets,
    projects,
    selectedWeek,
    loading,
    error,
    form,
    pendingCount,
    selectedTimesheet,
    fetchPendingWeeks,
    fetchMyTimesheets,
    fetchProjects,
    initialize,
    selectWeek,
    submitTimesheet
  }
})
