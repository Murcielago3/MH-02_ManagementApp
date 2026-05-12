<template>
  <EmployeeLayout>
    <div class="checkin-view">
      <div class="card-container" :class="currentState">
        
        <!-- Loading State -->
        <div v-if="loading" class="state-loading">
          <span class="material-symbols-outlined spinner">refresh</span>
          <p>Loading attendance data...</p>
        </div>

        <!-- State A: Not checked in -->
        <div v-else-if="currentState === 'not_checked_in'" class="state-panel state-a">
          <div class="time-display">{{ currentTime }}</div>
          <div class="date-display">{{ currentDate }}</div>

          <form @submit.prevent="handleCheckIn" class="checkin-form">
            <div class="toggle-row">
              <span class="toggle-label">Site Visit?</span>
              <label class="switch">
                <input type="checkbox" v-model="form.is_site_visit">
                <span class="slider round"></span>
              </label>
            </div>

            <div v-if="form.is_site_visit" class="site-fields">
              <input type="text" v-model="form.site_name" placeholder="Site Name" required class="field-input">
              <input type="text" v-model="form.site_timing" placeholder="Site Timing (e.g. 09:00 - 13:00)" required class="field-input">
            </div>

            <button type="submit" class="btn-checkin" :disabled="actionLoading">
              {{ actionLoading ? 'Checking In...' : 'CHECK IN' }}
            </button>
          </form>
        </div>

        <!-- State B: Checked in, not checked out -->
        <div v-else-if="currentState === 'checked_in'" class="state-panel state-b">
          <div class="status-badge checkin-badge">
            <span class="material-symbols-outlined">how_to_reg</span>
            Checked in at {{ checkInTime }}
          </div>
          
          <div class="elapsed-time">
            <span class="elapsed-value">{{ elapsedTime }}</span>
            <span class="elapsed-label">Elapsed Time</span>
          </div>

          <div v-if="todayRecord?.is_site_visit" class="site-info-pills">
            <div class="pill">
              <span class="material-symbols-outlined">location_on</span>
              {{ todayRecord.site_name }}
            </div>
            <div class="pill">
              <span class="material-symbols-outlined">schedule</span>
              {{ todayRecord.site_timing }}
            </div>
          </div>

          <button @click="handleCheckOut" class="btn-checkout" :disabled="actionLoading">
            {{ actionLoading ? 'Checking Out...' : 'CHECK OUT' }}
          </button>
        </div>

        <!-- State C: Checked out -->
        <div v-else-if="currentState === 'checked_out'" class="state-panel state-c">
          <div class="completion-icon">
            <span class="material-symbols-outlined">task_alt</span>
          </div>
          <h2 class="see-you-tomorrow">See you tomorrow!</h2>
          
          <div class="summary-grid">
            <div class="summary-item">
              <span class="label">Check In</span>
              <span class="value">{{ todayRecord?.check_in }}</span>
            </div>
            <div class="summary-item">
              <span class="label">Check Out</span>
              <span class="value">{{ todayRecord?.check_out }}</span>
            </div>
            <div class="summary-item total-hours">
              <span class="label">Total Hours</span>
              <span class="value">{{ totalHours }}</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  </EmployeeLayout>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, reactive } from 'vue'
import EmployeeLayout from '../../components/EmployeeLayout.vue'
import { attendanceAPI } from '../../api/attendance'

const loading = ref(true)
const actionLoading = ref(false)
const todayRecord = ref(null)

const currentTime = ref('')
const currentDate = ref('')
const elapsedTime = ref('0h 0m')

let clockInterval = null

const form = reactive({
  is_site_visit: false,
  site_name: '',
  site_timing: ''
})

const currentState = computed(() => {
  if (loading.value) return 'loading'
  if (!todayRecord.value) return 'not_checked_in'
  if (todayRecord.value && !todayRecord.value.check_out) return 'checked_in'
  return 'checked_out'
})

const checkInTime = computed(() => {
  return todayRecord.value?.check_in || '--:--'
})

const totalHours = computed(() => {
  if (!todayRecord.value?.check_in || !todayRecord.value?.check_out) return '--'
  return calculateDiff(todayRecord.value.check_in, todayRecord.value.check_out)
})

onMounted(async () => {
  updateClock()
  clockInterval = setInterval(() => {
    updateClock()
    updateElapsedTime()
  }, 1000)

  await fetchTodayRecord()
})

onUnmounted(() => {
  if (clockInterval) clearInterval(clockInterval)
})

const fetchTodayRecord = async () => {
  try {
    loading.value = true
    const res = await attendanceAPI.getMyAttendance()
    // Find today's record
    const today = new Date().toISOString().split('T')[0]
    const record = res.data.find(r => r.date === today)
    if (record) {
      todayRecord.value = record
      updateElapsedTime()
    }
  } catch (err) {
    console.error('Failed to load attendance', err)
  } finally {
    loading.value = false
  }
}

const handleCheckIn = async () => {
  if (form.is_site_visit && (!form.site_name || !form.site_timing)) {
    alert("Please fill in site details")
    return
  }
  
  try {
    actionLoading.value = true
    const res = await attendanceAPI.checkIn({
      is_site_visit: form.is_site_visit,
      site_name: form.site_name || null,
      site_timing: form.site_timing || null
    })
    todayRecord.value = res.data
    alert("Successfully checked in!")
  } catch (err) {
    console.error(err)
    alert(err.response?.data?.detail || "Check in failed")
  } finally {
    actionLoading.value = false
  }
}

const handleCheckOut = async () => {
  try {
    actionLoading.value = true
    const res = await attendanceAPI.checkOut()
    todayRecord.value = res.data
    alert("Successfully checked out!")
  } catch (err) {
    console.error(err)
    alert(err.response?.data?.detail || "Check out failed")
  } finally {
    actionLoading.value = false
  }
}

// Helpers
const updateClock = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  currentDate.value = now.toLocaleDateString('en-GB', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' })
}

const updateElapsedTime = () => {
  if (!todayRecord.value?.check_in || todayRecord.value?.check_out) return
  const now = new Date()
  const currentStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
  elapsedTime.value = calculateDiff(todayRecord.value.check_in, currentStr)
}

const calculateDiff = (time1, time2) => {
  const [h1, m1] = time1.split(':').map(Number)
  const [h2, m2] = time2.split(':').map(Number)
  
  let diffMins = (h2 * 60 + m2) - (h1 * 60 + m1)
  if (diffMins < 0) diffMins += 24 * 60 // crosses midnight
  
  const h = Math.floor(diffMins / 60)
  const m = diffMins % 60
  return `${h}h ${m}m`
}
</script>

<style scoped>
.checkin-view {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 128px);
}

.card-container {
  width: 100%;
  max-width: 480px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 48px 32px;
  box-shadow: 0 12px 32px rgba(0,0,0,0.05);
  text-align: center;
  transition: all 0.5s ease;
}

.state-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: var(--color-outline);
}
.spinner {
  font-size: 32px;
  animation: spin 1s linear infinite;
}
@keyframes spin { 100% { transform: rotate(360deg); } }

/* State A */
.time-display {
  font-family: var(--font-display);
  font-size: 64px;
  font-weight: 800;
  color: var(--color-on-surface);
  line-height: 1;
  margin-bottom: 8px;
}
.date-display {
  font-size: 16px;
  color: var(--color-on-surface-variant);
  margin-bottom: 48px;
}
.checkin-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: var(--color-surface-container-lowest);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-outline-variant);
}
.toggle-label {
  font-weight: 600;
  color: var(--color-on-surface);
}

.switch { position: relative; display: inline-block; width: 44px; height: 24px; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: var(--color-outline-variant); transition: .3s; }
.slider:before { position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px; background-color: white; transition: .3s; }
input:checked + .slider { background-color: var(--color-primary); }
input:checked + .slider:before { transform: translateX(20px); }
.slider.round { border-radius: 24px; }
.slider.round:before { border-radius: 50%; }

.site-fields {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.field-input {
  width: 100%;
  height: 48px;
  padding: 0 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-outline-variant);
  font-family: var(--font-body);
  outline: none;
  box-sizing: border-box;
}
.field-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(40, 116, 117, 0.1);
}

.btn-checkin {
  height: 56px;
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-family: var(--font-display);
  font-size: 18px;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}
.btn-checkin:hover:not(:disabled) {
  opacity: 0.9;
}

/* State B */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 32px;
}
.checkin-badge {
  background: rgba(40, 116, 117, 0.1);
  color: var(--color-primary);
}
.elapsed-time {
  display: flex;
  flex-direction: column;
  margin-bottom: 48px;
}
.elapsed-value {
  font-family: var(--font-display);
  font-size: 48px;
  font-weight: 800;
  color: var(--color-on-surface);
}
.elapsed-label {
  color: var(--color-on-surface-variant);
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 4px;
}
.site-info-pills {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 32px;
}
.pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--color-surface-container);
  border-radius: var(--radius-md);
  font-size: 12px;
  color: var(--color-on-surface-variant);
}

.btn-checkout {
  width: 100%;
  height: 56px;
  background: #0f172a;
  color: #fff;
  font-family: var(--font-display);
  font-size: 18px;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}
.btn-checkout:hover:not(:disabled) {
  opacity: 0.9;
}

/* State C */
.completion-icon {
  font-size: 64px;
  color: var(--color-primary);
  margin-bottom: 24px;
}
.completion-icon span {
  font-size: 64px;
}
.see-you-tomorrow {
  font-family: var(--font-display);
  font-size: 28px;
  margin: 0 0 48px 0;
}
.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.summary-item {
  display: flex;
  flex-direction: column;
  padding: 16px;
  background: var(--color-surface-container-lowest);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-md);
}
.summary-item.total-hours {
  grid-column: span 2;
  background: rgba(40, 116, 117, 0.05);
  border-color: rgba(40, 116, 117, 0.2);
}
.summary-item .label {
  font-size: 12px;
  color: var(--color-on-surface-variant);
  text-transform: uppercase;
  margin-bottom: 4px;
}
.summary-item .value {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  color: var(--color-on-surface);
}
.summary-item.total-hours .value {
  color: var(--color-primary);
  font-size: 28px;
}
</style>
