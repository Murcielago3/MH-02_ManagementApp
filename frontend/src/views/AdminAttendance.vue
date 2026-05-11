<template>
  <AppLayout>
    <!-- Page Actions -->
    <div class="page-actions">
      <div class="actions-left">
        <div class="search-box">
          <span class="material-symbols-outlined search-icon">search</span>
          <input v-model="searchQuery" type="text" placeholder="Search attendance..." class="search-input" />
        </div>
        <input v-model="filterDate" type="date" class="date-input" />
        <select v-model="filterEmployee" class="emp-select">
          <option value="">All Employees</option>
          <option v-for="emp in employees" :key="emp.id" :value="emp.id">{{ emp.name }}</option>
        </select>
      </div>
      <div class="actions-right">
        <button class="today-btn" @click="showToday = !showToday">
          {{ showToday ? 'Show All' : 'Show Today' }}
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="table-card">
      <table class="proj-table">
        <thead>
          <tr>
            <th>Employee</th>
            <th>Date</th>
            <th>Check In</th>
            <th>Check Out</th>
            <th>Site Visit</th>
            <th>Site Name</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="6" class="empty-cell"><div class="loading-text">Loading attendance…</div></td>
          </tr>
          <tr v-else-if="filtered.length === 0">
            <td colspan="6" class="empty-cell">No attendance records found.</td>
          </tr>
          <tr v-for="a in paginated" :key="a.id" class="proj-row">
            <td><span class="proj-name">{{ a.user?.name }}</span></td>
            <td class="mono">{{ formatDate(a.date) }}</td>
            <td class="mono">{{ a.check_in || '—' }}</td>
            <td class="mono">{{ a.check_out || '—' }}</td>
            <td>
              <span v-if="a.is_site_visit" class="site-badge">Yes</span>
              <span v-else class="muted">No</span>
            </td>
            <td class="muted">{{ a.site_name || '—' }}</td>
          </tr>
        </tbody>
      </table>

      <div class="table-footer">
        <span class="page-info">
          Showing {{ filtered.length === 0 ? 0 : startIdx + 1 }} to {{ endIdx }} of {{ filtered.length }} entries
        </span>
        <div class="page-btns">
          <button class="page-btn" :disabled="currentPage === 1" @click="currentPage--">Prev</button>
          <button class="page-btn" :disabled="currentPage >= totalPages" @click="currentPage++">Next</button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import { attendanceAPI } from '../api/attendance'
import { usersAPI } from '../api/users'

const attendance = ref([])
const employees = ref([])
const loading = ref(true)
const searchQuery = ref('')
const filterDate = ref('')
const filterEmployee = ref('')
const currentPage = ref(1)
const perPage = 10
const showToday = ref(false)

async function fetchAttendance() {
  loading.value = true
  try {
    const params = {}
    if (filterEmployee.value) params.employee_id = filterEmployee.value
    if (filterDate.value) params.date_filter = filterDate.value

    const res = showToday.value
      ? await attendanceAPI.getTodayAttendance()
      : await attendanceAPI.getAttendance(params)
    attendance.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function fetchEmployees() {
  try {
    const res = await usersAPI.getUsers()
    employees.value = res.data
  } catch (e) {
    console.error(e)
  }
}

onMounted(async () => {
  await Promise.all([fetchAttendance(), fetchEmployees()])
})

watch([filterDate, filterEmployee, showToday], fetchAttendance)

const filtered = computed(() => {
  let list = attendance.value
  const q = searchQuery.value.toLowerCase()
  if (q) list = list.filter(a =>
    (a.user?.name || '').toLowerCase().includes(q) ||
    (a.site_name || '').toLowerCase().includes(q)
  )
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage)))
const startIdx = computed(() => (currentPage.value - 1) * perPage)
const endIdx = computed(() => Math.min(startIdx.value + perPage, filtered.value.length))
const paginated = computed(() => filtered.value.slice(startIdx.value, endIdx.value))

// Helpers
function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('en-IN')
}
</script>

<style scoped>
.page-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.actions-left { display: flex; gap: 8px; align-items: center; }
.actions-right { display: flex; gap: 8px; align-items: center; }
.search-box { position: relative; }
.search-icon {
  position: absolute; left: 8px; top: 50%;
  transform: translateY(-50%); color: #78767d; font-size: 18px;
}
.search-input, .date-input, .emp-select {
  padding: 8px 8px 8px 32px; background: #fff; border: 1px solid #c8c5cd;
  border-radius: 6px; font-family: 'Integral CF', sans-serif; font-size: 13px;
  color: #1c1b1d; outline: none; transition: border 0.15s;
}
.date-input, .emp-select { padding-left: 8px; }
.search-input:focus, .date-input:focus, .emp-select:focus { border-color: #0d9488; }

.today-btn {
  padding: 8px 16px; background: #0d9488; color: #fff; border: none;
  border-radius: 6px; font-family: 'Integral CF', sans-serif; font-size: 13px;
  font-weight: 500; cursor: pointer; transition: background 0.15s;
}
.today-btn:hover { background: #0f766e; }

.table-card {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
  overflow: hidden;
}
.proj-table {
  width: 100%; border-collapse: collapse;
}
.proj-table th {
  padding: 12px 16px; text-align: left; font-family: 'Integral CF', sans-serif;
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.05em; color: #334155; border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}
.proj-table td {
  padding: 12px 16px; border-bottom: 1px solid #f1f5f9;
  font-family: 'Integral CF', sans-serif; font-size: 13px; color: #1c1b1d;
}
.proj-row:hover { background: #f8fafc; }
.proj-name { font-weight: 500; }
.muted { color: #64748b; }
.mono { font-variant-numeric: tabular-nums; }

.empty-cell {
  text-align: center; padding: 48px 16px; color: #64748b;
  font-family: 'Integral CF', sans-serif; font-size: 13px;
}
.loading-text { color: #64748b; }

.table-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; background: #f8fafc; border-top: 1px solid #e2e8f0;
}
.page-info {
  font-family: 'Integral CF', sans-serif; font-size: 13px; color: #64748b;
}
.page-btns { display: flex; gap: 4px; }
.page-btn {
  padding: 6px 12px; background: #fff; border: 1px solid #e2e8f0;
  border-radius: 4px; font-family: 'Integral CF', sans-serif; font-size: 13px;
  color: #334155; cursor: pointer; transition: all 0.15s;
}
.page-btn:hover:not(:disabled) { background: #f1f5f9; }
.page-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.site-badge {
  padding: 4px 8px; background: #dbeafe; color: #1e40af;
  border-radius: 12px; font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.05em;
}
</style>