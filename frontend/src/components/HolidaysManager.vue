<template>
  <div class="holidays-manager">
    <div class="hm-head">
      <div>
        <h2 class="hm-title">Public Holidays</h2>
        <p class="hm-note">Mark company-wide holidays. They're greyed out as non-working days on the task calendar and every employee dashboard.</p>
      </div>
    </div>

    <div class="hm-layout">
      <!-- Calendar -->
      <div class="hm-calendar">
        <div class="hm-cal-head">
          <button class="hm-nav" @click="prevMonth"><span class="material-symbols-outlined">chevron_left</span></button>
          <span class="hm-month">{{ monthLabel }}</span>
          <button class="hm-nav" @click="nextMonth"><span class="material-symbols-outlined">chevron_right</span></button>
        </div>
        <div class="hm-grid">
          <div v-for="d in ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']" :key="d" class="hm-dow">{{ d }}</div>
          <div
            v-for="(cell, i) in cells"
            :key="i"
            class="hm-cell"
            :class="{
              'is-blank': !cell,
              'is-weekend': cell && cell.isWeekend,
              'is-holiday': cell && holidayFor(cell.dateStr),
              'is-today': cell && cell.dateStr === todayStr,
            }"
            @click="cell && onCellClick(cell.dateStr)"
          >
            <template v-if="cell">
              <span class="hm-num">{{ cell.day }}</span>
              <span v-if="holidayFor(cell.dateStr)" class="hm-holiday-name">{{ holidayFor(cell.dateStr).name }}</span>
            </template>
          </div>
        </div>
        <p class="hm-hint"><span class="material-symbols-outlined">info</span> Click a day to add a holiday. Click an existing holiday to remove it.</p>
      </div>

      <!-- List -->
      <div class="hm-list-panel">
        <h3 class="hm-list-title">All Holidays</h3>
        <div v-if="loading" class="hm-empty">Loading…</div>
        <div v-else-if="sortedHolidays.length === 0" class="hm-empty">No holidays added yet.</div>
        <ul v-else class="hm-list">
          <li v-for="h in sortedHolidays" :key="h.id" class="hm-list-row">
            <div class="hm-list-info">
              <span class="hm-list-date">{{ formatDate(h.date) }}</span>
              <span class="hm-list-name">{{ h.name }}</span>
            </div>
            <button class="hm-del" @click="removeHoliday(h)" title="Remove holiday">
              <span class="material-symbols-outlined">delete</span>
            </button>
          </li>
        </ul>
      </div>
    </div>

    <!-- Add holiday inline dialog -->
    <Teleport to="body">
      <div v-if="addDate" class="modal-backdrop">
        <div class="add-modal">
          <h3 class="add-title">Add Holiday</h3>
          <p class="add-date">{{ formatDate(addDate) }}</p>
          <input
            ref="nameInput"
            v-model="addName"
            type="text"
            class="add-input"
            placeholder="Holiday name (e.g. Diwali)"
            @keyup.enter="saveHoliday"
          />
          <div class="add-actions">
            <button class="btn-cancel" @click="addDate = null">Cancel</button>
            <button class="btn-submit" :disabled="!addName.trim() || saving" @click="saveHoliday">
              {{ saving ? 'Saving…' : 'Add Holiday' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <ToastNotification v-if="toastMsg" :message="toastMsg" :type="toastType" @done="toastMsg = ''" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { holidaysAPI } from '../api/holidays'
import ToastNotification from './ToastNotification.vue'

const holidays = ref([])
const loading = ref(true)
const saving = ref(false)
const cursor = ref(new Date())   // month being viewed
const addDate = ref(null)
const addName = ref('')
const nameInput = ref(null)

const toastMsg = ref('')
const toastType = ref('success')
function toast(msg, type = 'success') { toastType.value = type; toastMsg.value = msg }

const todayStr = toIso(new Date())

function toIso(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const holidayMap = computed(() => {
  const map = {}
  for (const h of holidays.value) map[h.date] = h
  return map
})
function holidayFor(dateStr) { return holidayMap.value[dateStr] || null }

const sortedHolidays = computed(() =>
  [...holidays.value].sort((a, b) => new Date(a.date) - new Date(b.date))
)

const monthLabel = computed(() =>
  cursor.value.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })
)

// Build the month grid (Mon-first), with leading blanks
const cells = computed(() => {
  const y = cursor.value.getFullYear()
  const m = cursor.value.getMonth()
  const first = new Date(y, m, 1)
  const daysInMonth = new Date(y, m + 1, 0).getDate()
  // Monday-first offset: JS getDay() Sun=0..Sat=6 → Mon=0..Sun=6
  const lead = (first.getDay() + 6) % 7
  const out = []
  for (let i = 0; i < lead; i++) out.push(null)
  for (let day = 1; day <= daysInMonth; day++) {
    const d = new Date(y, m, day)
    const dow = d.getDay()
    out.push({ day, dateStr: toIso(d), isWeekend: dow === 0 || dow === 6 })
  }
  return out
})

function prevMonth() {
  cursor.value = new Date(cursor.value.getFullYear(), cursor.value.getMonth() - 1, 1)
}
function nextMonth() {
  cursor.value = new Date(cursor.value.getFullYear(), cursor.value.getMonth() + 1, 1)
}

function formatDate(dateStr) {
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', weekday: 'short' })
}

async function fetchHolidays() {
  loading.value = true
  try {
    const res = await holidaysAPI.getHolidays()
    holidays.value = res.data
  } catch (e) {
    toast('Failed to load holidays', 'error')
  } finally {
    loading.value = false
  }
}
onMounted(fetchHolidays)

function onCellClick(dateStr) {
  const existing = holidayFor(dateStr)
  if (existing) {
    removeHoliday(existing)
    return
  }
  addDate.value = dateStr
  addName.value = ''
  nextTick(() => nameInput.value?.focus())
}

async function saveHoliday() {
  if (!addName.trim()) return
  saving.value = true
  try {
    await holidaysAPI.createHoliday({ date: addDate.value, name: addName.trim() })
    toast('Holiday added.')
    addDate.value = null
    await fetchHolidays()
  } catch (e) {
    toast(e.response?.data?.detail || 'Failed to add holiday', 'error')
  } finally {
    saving.value = false
  }
}

async function removeHoliday(h) {
  try {
    await holidaysAPI.deleteHoliday(h.id)
    toast('Holiday removed.')
    await fetchHolidays()
  } catch (e) {
    toast('Failed to remove holiday', 'error')
  }
}
</script>

<style scoped>
.holidays-manager { padding: 28px 32px; }
.hm-head { margin-bottom: 20px; }
.hm-title { font-family: var(--font-display); font-size: 15px; font-weight: 800; margin: 0 0 4px; color: var(--color-on-surface); }
.hm-note { margin: 0; font-size: 13px; color: var(--color-on-surface-variant); max-width: 560px; }

.hm-layout { display: grid; grid-template-columns: 1.4fr 1fr; gap: 24px; align-items: start; }

/* Calendar */
.hm-cal-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.hm-month { font-family: var(--font-display); font-size: 15px; font-weight: 700; color: var(--color-on-surface); }
.hm-nav {
  width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;
  border: 1px solid var(--color-outline); background: var(--color-surface);
  border-radius: var(--radius-md); cursor: pointer; color: var(--color-on-surface-variant);
}
.hm-nav:hover { background: var(--color-surface-dim); }

.hm-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; }
.hm-dow {
  text-align: center; font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--color-on-surface-variant); padding-bottom: 4px;
}
.hm-cell {
  min-height: 58px;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-md);
  padding: 5px 6px;
  cursor: pointer;
  display: flex; flex-direction: column; gap: 3px;
  transition: background 0.12s, border-color 0.12s;
  background: var(--color-surface);
}
.hm-cell:hover:not(.is-blank) { border-color: var(--color-primary); background: var(--color-primary-light); }
.hm-cell.is-blank { border: none; background: none; cursor: default; }
.hm-cell.is-weekend { background: #f3f4f6; }
.hm-cell.is-today .hm-num { color: var(--color-primary); font-weight: 800; }
.hm-cell.is-holiday {
  background: repeating-linear-gradient(-45deg, #fef3c7, #fef3c7 6px, #fde68a 6px, #fde68a 12px);
  border-color: #f59e0b;
}
.hm-num { font-size: 12px; font-weight: 600; color: var(--color-on-surface); }
.hm-holiday-name {
  font-size: 9px; font-weight: 700; color: #92400e;
  text-transform: uppercase; letter-spacing: 0.02em;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.hm-hint {
  display: flex; align-items: center; gap: 6px;
  margin: 12px 0 0; font-size: 11px; color: var(--color-on-surface-variant);
}
.hm-hint .material-symbols-outlined { font-size: 14px; }

/* List */
.hm-list-panel {
  border: 1px solid var(--color-outline); border-radius: var(--radius-lg);
  padding: 16px; background: var(--color-surface-dim);
}
.hm-list-title { font-family: var(--font-display); font-size: 13px; font-weight: 700; margin: 0 0 12px; color: var(--color-on-surface); }
.hm-empty { font-size: 13px; color: var(--color-on-surface-variant); padding: 12px 0; }
.hm-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; max-height: 360px; overflow-y: auto; }
.hm-list-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 10px; background: var(--color-surface);
  border: 1px solid var(--color-outline-variant); border-radius: var(--radius-md);
}
.hm-list-info { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.hm-list-date { font-size: 11px; color: var(--color-on-surface-variant); font-variant-numeric: tabular-nums; }
.hm-list-name { font-size: 13px; font-weight: 600; color: var(--color-on-surface); }
.hm-del {
  background: none; border: none; cursor: pointer; padding: 4px; border-radius: var(--radius-md);
  color: var(--color-on-surface-variant); flex-shrink: 0;
}
.hm-del:hover { background: #fee2e2; color: var(--color-error); }
.hm-del .material-symbols-outlined { font-size: 17px; }

/* Add modal */
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 16px;
}
.add-modal {
  background: #fff; border-radius: var(--radius-xl); padding: 24px;
  width: 380px; max-width: 100%; box-shadow: 0 20px 60px rgba(0,0,0,0.18);
}
.add-title { font-family: var(--font-display); font-size: 16px; font-weight: 700; margin: 0 0 4px; }
.add-date { margin: 0 0 16px; font-size: 13px; color: var(--color-on-surface-variant); }
.add-input {
  width: 100%; padding: 10px 12px; border: 1px solid var(--color-outline);
  border-radius: var(--radius-md); font-size: 14px; outline: none; box-sizing: border-box;
}
.add-input:focus { border-color: var(--color-primary); box-shadow: 0 0 0 2px rgba(40,116,117,0.1); }
.add-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 18px; }
.btn-cancel {
  padding: 9px 16px; background: #fff; border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg); font-size: 13px; font-weight: 600;
  color: var(--color-on-surface-variant); cursor: pointer;
}
.btn-cancel:hover { background: var(--color-surface-dim); }
.btn-submit {
  padding: 9px 18px; background: var(--color-primary); color: #fff; border: none;
  border-radius: var(--radius-lg); font-size: 13px; font-weight: 600; cursor: pointer;
}
.btn-submit:hover:not(:disabled) { background: #1a4e4f; }
.btn-submit:disabled { opacity: 0.55; cursor: not-allowed; }

@media (max-width: 768px) {
  .holidays-manager { padding: 18px 16px; }
  .hm-layout { grid-template-columns: 1fr; }
  .hm-cell { min-height: 48px; }
}
</style>
