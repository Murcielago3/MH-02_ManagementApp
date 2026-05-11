<template>
  <AppLayout>
    <!-- Page Actions -->
    <div class="page-actions">
      <div class="actions-left">
        <div class="search-box">
          <span class="material-symbols-outlined search-icon">search</span>
          <input v-model="searchQuery" type="text" placeholder="Search leaves..." class="search-input" />
        </div>
        <select v-model="filterStatus" class="status-select">
          <option value="">All Status</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>
    </div>

    <!-- Table -->
    <div class="table-card">
      <table class="proj-table">
        <thead>
          <tr>
            <th>Employee</th>
            <th>Start Date</th>
            <th>End Date</th>
            <th>Days</th>
            <th>Reason</th>
            <th>Status</th>
            <th class="text-center col-actions">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="7" class="empty-cell"><div class="loading-text">Loading leaves…</div></td>
          </tr>
          <tr v-else-if="filtered.length === 0">
            <td colspan="7" class="empty-cell">No leave requests found.</td>
          </tr>
          <tr v-for="l in paginated" :key="l.id" class="proj-row">
            <td><span class="proj-name">{{ l.user?.name }}</span></td>
            <td class="mono">{{ formatDate(l.start_date) }}</td>
            <td class="mono">{{ formatDate(l.end_date) }}</td>
            <td class="mono">{{ l.days_count }}</td>
            <td class="muted">{{ l.reason }}</td>
            <td>
              <span class="status-badge" :class="`status-${l.status}`">
                {{ l.status }}
              </span>
            </td>
            <td>
              <div class="row-actions" v-if="l.status === 'pending'">
                <button class="action-btn approve-btn" title="Approve" @click="actionLeave(l, 'approved')">
                  <span class="material-symbols-outlined">check</span>
                </button>
                <button class="action-btn reject-btn" title="Reject" @click="actionLeave(l, 'rejected')">
                  <span class="material-symbols-outlined">close</span>
                </button>
              </div>
              <span v-else class="muted">—</span>
            </td>
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
import { ref, reactive, computed, onMounted } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import { leavesAPI } from '../api/leaves'

const leaves = ref([])
const loading = ref(true)
const searchQuery = ref('')
const filterStatus = ref('')
const currentPage = ref(1)
const perPage = 10

async function fetchLeaves() {
  loading.value = true
  try {
    const res = await leavesAPI.getLeaves()
    leaves.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchLeaves)

const filtered = computed(() => {
  let list = leaves.value
  if (filterStatus.value) list = list.filter(l => l.status === filterStatus.value)
  const q = searchQuery.value.toLowerCase()
  if (q) list = list.filter(l =>
    (l.user?.name || '').toLowerCase().includes(q) ||
    l.reason.toLowerCase().includes(q)
  )
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage)))
const startIdx = computed(() => (currentPage.value - 1) * perPage)
const endIdx = computed(() => Math.min(startIdx.value + perPage, filtered.value.length))
const paginated = computed(() => filtered.value.slice(startIdx.value, endIdx.value))

async function actionLeave(leave, status) {
  try {
    await leavesAPI.actionLeave(leave.id, status)
    await fetchLeaves()
  } catch (e) {
    console.error(e)
  }
}

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
.search-box { position: relative; }
.search-icon {
  position: absolute; left: 8px; top: 50%;
  transform: translateY(-50%); color: #78767d; font-size: 18px;
}
.search-input, .status-select {
  padding: 8px 8px 8px 32px; background: #fff; border: 1px solid #c8c5cd;
  border-radius: 6px; font-family: 'Integral CF', sans-serif; font-size: 13px;
  color: #1c1b1d; outline: none; transition: border 0.15s;
}
.status-select { padding-left: 8px; }
.search-input:focus, .status-select:focus { border-color: #0d9488; }

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
.text-center { text-align: center; }
.col-actions { width: 120px; }

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

.row-actions { display: flex; justify-content: center; gap: 8px; }
.action-btn {
  padding: 6px; background: none; border: none; border-radius: 4px;
  cursor: pointer; transition: background 0.15s; display: flex; align-items: center;
}
.approve-btn:hover { background: #dcfce7; }
.reject-btn:hover { background: #fef2f2; }
.action-btn .material-symbols-outlined { font-size: 18px; color: #64748b; }
.approve-btn .material-symbols-outlined { color: #16a34a; }
.reject-btn .material-symbols-outlined { color: #dc2626; }

.status-badge {
  padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.05em;
}
.status-badge.status-pending { background: #fef3c7; color: #92400e; }
.status-badge.status-approved { background: #dcfce7; color: #166534; }
.status-badge.status-rejected { background: #fee2e2; color: #991b1b; }
</style>