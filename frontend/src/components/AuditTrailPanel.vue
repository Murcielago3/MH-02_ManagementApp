<template>
  <div class="audit-panel">
    <div class="ap-head">
      <div>
        <h2 class="ap-title">Audit Trail</h2>
        <p class="ap-note">Every major action — submissions, approvals, rejections, exports — with who did it and when.</p>
      </div>
      <button class="btn-ghost" @click="load" title="Refresh">
        <span class="material-symbols-outlined">refresh</span>
      </button>
    </div>

    <!-- Filters -->
    <div class="ap-filters">
      <select v-model="filterEntity" class="ap-select">
        <option value="">All types</option>
        <option v-for="t in entityTypes" :key="t" :value="t">{{ pretty(t) }}</option>
      </select>
      <input v-model="dateFrom" type="date" class="ap-select" title="From date" />
      <input v-model="dateTo" type="date" class="ap-select" title="To date" />
      <button v-if="filterEntity || dateFrom || dateTo" class="btn-clear" @click="clearFilters">
        <span class="material-symbols-outlined">filter_alt_off</span> Clear
      </button>
    </div>

    <!-- Table -->
    <div class="ap-table-wrap">
      <table class="ap-table">
        <thead>
          <tr>
            <th style="width:170px">When</th>
            <th style="width:140px">Who</th>
            <th style="width:170px">Action</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading"><td colspan="4" class="ap-empty">Loading…</td></tr>
          <tr v-else-if="!items.length"><td colspan="4" class="ap-empty">No audit entries found.</td></tr>
          <tr v-for="r in items" :key="r.id">
            <td class="mono muted">{{ fmtWhen(r.created_at) }}</td>
            <td class="strong">{{ r.actor_name || 'System' }}</td>
            <td><span class="action-chip" :class="chipClass(r.action)">{{ pretty(r.action) }}</span></td>
            <td class="muted">{{ r.summary }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="ap-footer">
      <span class="muted small">{{ total }} entries</span>
      <div class="ap-pager">
        <button class="btn-ghost sm" :disabled="offset === 0" @click="prevPage">
          <span class="material-symbols-outlined">chevron_left</span>
        </button>
        <span class="muted small">{{ pageLabel }}</span>
        <button class="btn-ghost sm" :disabled="offset + limit >= total" @click="nextPage">
          <span class="material-symbols-outlined">chevron_right</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { auditAPI } from '../api/audit'

const items = ref([])
const total = ref(0)
const loading = ref(true)
const entityTypes = ref([])

const filterEntity = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const limit = 50
const offset = ref(0)

const pageLabel = computed(() => {
  if (!total.value) return '0 / 0'
  const page = Math.floor(offset.value / limit) + 1
  const pages = Math.max(1, Math.ceil(total.value / limit))
  return `${page} / ${pages}`
})

async function load() {
  loading.value = true
  try {
    const params = { limit, offset: offset.value }
    if (filterEntity.value) params.entity_type = filterEntity.value
    if (dateFrom.value) params.date_from = dateFrom.value
    if (dateTo.value) params.date_to = dateTo.value
    const res = await auditAPI.list(params)
    items.value = res.data.items
    total.value = res.data.total
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadTypes() {
  try { entityTypes.value = (await auditAPI.entityTypes()).data } catch {}
}

watch([filterEntity, dateFrom, dateTo], () => { offset.value = 0; load() })

function prevPage() { offset.value = Math.max(0, offset.value - limit); load() }
function nextPage() { offset.value += limit; load() }
function clearFilters() { filterEntity.value = ''; dateFrom.value = ''; dateTo.value = '' }

function pretty(s) {
  return String(s || '').replace(/[._]/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}
function fmtWhen(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}
function chipClass(action) {
  if (/approved/.test(action)) return 'chip-green'
  if (/rejected|deleted|deactivated/.test(action)) return 'chip-red'
  if (/submitted|created|increment/.test(action)) return 'chip-blue'
  return 'chip-grey'
}

onMounted(() => { load(); loadTypes() })
</script>

<style scoped>
.audit-panel { padding: 28px 32px; }
.ap-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
.ap-title { font-family: var(--font-display); font-size: 15px; font-weight: 800; margin: 0 0 4px; color: var(--color-on-surface); }
.ap-note { margin: 0; font-size: 13px; color: var(--color-on-surface-variant); max-width: 560px; }

.ap-filters { display: flex; gap: 8px; align-items: center; margin-bottom: 14px; flex-wrap: wrap; }
.ap-select {
  padding: 8px 10px; border: 1px solid var(--color-outline); border-radius: var(--radius-md);
  font-family: var(--font-body); font-size: 12.5px; color: var(--color-on-surface); background: var(--color-surface);
}
.btn-clear {
  display: inline-flex; align-items: center; gap: 4px; padding: 7px 12px;
  background: none; border: 1px solid var(--color-outline); border-radius: var(--radius-md);
  font-size: 12px; font-weight: 600; color: var(--color-on-surface-variant); cursor: pointer;
}
.btn-clear .material-symbols-outlined { font-size: 15px; }
.btn-clear:hover { background: #fee2e2; color: #dc2626; }

.ap-table-wrap { border: 1px solid var(--color-outline); border-radius: var(--radius-lg); overflow: hidden; }
.ap-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.ap-table th {
  text-align: left; padding: 10px 14px; background: var(--color-surface-dim);
  font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .06em;
  color: var(--color-on-surface-variant); border-bottom: 1px solid var(--color-outline);
}
.ap-table td { padding: 10px 14px; border-bottom: 1px solid var(--color-outline-variant); vertical-align: top; }
.ap-table tbody tr:last-child td { border-bottom: none; }
.ap-empty { text-align: center; padding: 32px; color: var(--color-on-surface-variant); }
.mono { font-variant-numeric: tabular-nums; white-space: nowrap; }
.muted { color: var(--color-on-surface-variant); }
.strong { font-weight: 600; }
.small { font-size: 12px; }

.action-chip { display: inline-flex; padding: 2px 9px; border-radius: var(--radius-full); font-size: 11px; font-weight: 700; white-space: nowrap; }
.chip-green { background: #dcfce7; color: #166534; }
.chip-red { background: #fee2e2; color: #991b1b; }
.chip-blue { background: #dbeafe; color: #1e40af; }
.chip-grey { background: #f1f5f9; color: #475569; }

.ap-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 12px; }
.ap-pager { display: flex; align-items: center; gap: 8px; }
.btn-ghost {
  display: inline-flex; align-items: center; justify-content: center; padding: 8px 12px;
  border: 1px solid var(--color-outline); border-radius: var(--radius-lg);
  background: var(--color-surface); cursor: pointer; color: var(--color-on-surface-variant);
}
.btn-ghost.sm { padding: 4px 8px; }
.btn-ghost:hover:not(:disabled) { background: var(--color-surface-dim); }
.btn-ghost:disabled { opacity: .4; cursor: not-allowed; }
.btn-ghost .material-symbols-outlined { font-size: 18px; }

@media (max-width: 768px) {
  .audit-panel { padding: 18px 16px; }
  .ap-table-wrap { overflow-x: auto; }
  .ap-table { min-width: 640px; }
}
</style>
