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
            <td><span class="proj-name">{{ l.employee?.name }}</span></td>
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
    (l.employee?.name || '').toLowerCase().includes(q) ||
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
  transform: translateY(-50%); color: var(--color-on-surface-variant); font-size: 18px;
}
.search-input, .status-select {
  padding: 8px 8px 8px 32px; background: #fff; border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg); font-family: var(--font-display); font-size: 13px;
  color: var(--color-on-surface); outline: none; transition: border 0.15s;
}
.status-select { padding-left: 8px; }
.search-input:focus, .status-select:focus { border-color: var(--color-primary); }

.table-card {
  background: #fff; border: 1px solid var(--color-surface-container-high); border-radius: var(--radius-lg);
  overflow: hidden;
}
.proj-table {
  width: 100%; border-collapse: collapse;
}
.proj-table th {
  padding: 12px 16px; text-align: left; font-family: var(--font-display);
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--color-on-surface-variant); border-bottom: 1px solid var(--color-surface-container-high);
  background: var(--color-background);
}
.proj-table td {
  padding: 12px 16px; border-bottom: 1px solid var(--color-surface-container);
  font-family: var(--font-display); font-size: 13px; color: var(--color-on-surface);
}
.proj-row:hover { background: var(--color-background); }
.proj-name { font-weight: 500; }
.muted { color: var(--color-on-surface-variant); }
.mono { font-variant-numeric: tabular-nums; }
.text-center { text-align: center; }
.col-actions { width: 120px; }

.empty-cell {
  text-align: center; padding: 48px 16px; color: var(--color-on-surface-variant);
  font-family: var(--font-display); font-size: 13px;
}
.loading-text { color: var(--color-on-surface-variant); }

.table-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; background: var(--color-background); border-top: 1px solid var(--color-surface-container-high);
}
.page-info {
  font-family: var(--font-display); font-size: 13px; color: var(--color-on-surface-variant);
}
.page-btns { display: flex; gap: 4px; }
.page-btn {
  padding: 6px 12px; background: #fff; border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius); font-family: var(--font-display); font-size: 13px;
  color: var(--color-on-surface-variant); cursor: pointer; transition: all 0.15s;
}
.page-btn:hover:not(:disabled) { background: var(--color-surface-container); }
.page-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.row-actions { display: flex; justify-content: center; gap: 8px; }
.action-btn {
  padding: 6px; background: none; border: none; border-radius: var(--radius);
  cursor: pointer; transition: background 0.15s; display: flex; align-items: center;
}
.approve-btn:hover { background: #dcfce7; }
.reject-btn:hover { background: #fef2f2; }
.action-btn .material-symbols-outlined { font-size: 18px; color: var(--color-on-surface-variant); }
.approve-btn .material-symbols-outlined { color: #16a34a; }
.reject-btn .material-symbols-outlined { color: #dc2626; }

.status-badge {
  padding: 4px 8px; border-radius: var(--radius-lg); font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.05em;
}
.status-badge.status-pending { background: #fef3c7; color: #92400e; }
.status-badge.status-approved { background: #dcfce7; color: #166534; }
.status-badge.status-rejected { background: #fee2e2; color: #991b1b; }
</style>