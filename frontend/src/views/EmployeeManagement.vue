<template>
  <div class="flex h-screen">
    <!-- Sidebar -->
    <aside class="w-64 fixed left-0 top-0 h-screen border-r border-[#E6E2D3]/10 bg-[#1A1C18] flex flex-col py-8 z-50">
      <div class="px-6 mb-10">
        <h1 class="text-lg font-bold text-white tracking-widest uppercase">Studio MH02</h1>
        <p class="text-[10px] text-[#A2937E] uppercase tracking-widest mt-1">Architecture Firm</p>
      </div>
      <nav class="flex-1 space-y-1 overflow-y-auto">
        <router-link
          to="/"
          class="text-[#A2937E] flex items-center gap-3 px-6 py-3 hover:bg-white/5 hover:text-white transition-all duration-300"
        >
          <span class="material-symbols-outlined">dashboard</span>
          <span class="text-sm">Dashboard</span>
        </router-link>
        <router-link
          to="/employee-management"
          class="text-white font-semibold bg-[#386641]/10 flex items-center gap-3 px-6 py-3 border-r-2 border-[#386641]"
        >
          <span class="material-symbols-outlined">badge</span>
          <span class="text-sm">Employee Management</span>
        </router-link>
        <a
          href="#"
          class="text-[#A2937E] flex items-center gap-3 px-6 py-3 hover:bg-white/5 hover:text-white transition-all duration-300"
        >
          <span class="material-symbols-outlined">architecture</span>
          <span class="text-sm">Project Management</span>
        </a>
        <a
          href="#"
          class="text-[#A2937E] flex items-center gap-3 px-6 py-3 hover:bg-white/5 hover:text-white transition-all duration-300"
        >
          <span class="material-symbols-outlined">assignment_ind</span>
          <span class="text-sm">Project Allocation</span>
        </a>
        <a
          href="#"
          class="text-[#A2937E] flex items-center gap-3 px-6 py-3 hover:bg-white/5 hover:text-white transition-all duration-300"
        >
          <span class="material-symbols-outlined">handshake</span>
          <span class="text-sm">Client Management</span>
        </a>
        <a
          href="#"
          class="text-[#A2937E] flex items-center gap-3 px-6 py-3 hover:bg-white/5 hover:text-white transition-all duration-300"
        >
          <span class="material-symbols-outlined">receipt_long</span>
          <span class="text-sm">Expense Tracker</span>
        </a>
        <a
          href="#"
          class="text-[#A2937E] flex items-center gap-3 px-6 py-3 hover:bg-white/5 hover:text-white transition-all duration-300"
        >
          <span class="material-symbols-outlined">description</span>
          <span class="text-sm">Invoice Tracker</span>
        </a>
        <a
          href="#"
          class="text-[#A2937E] flex items-center gap-3 px-6 py-3 hover:bg-white/5 hover:text-white transition-all duration-300"
        >
          <span class="material-symbols-outlined">calculate</span>
          <span class="text-sm">Estimate Calculator</span>
        </a>
        <a
          href="#"
          class="text-[#A2937E] flex items-center gap-3 px-6 py-3 hover:bg-white/5 hover:text-white transition-all duration-300"
        >
          <span class="material-symbols-outlined">analytics</span>
          <span class="text-sm">Reports</span>
        </a>
      </nav>
    </aside>

    <!-- Main Content -->
    <div class="flex flex-col flex-1 ml-64">
      <!-- Top App Bar -->
      <header class="fixed top-0 right-0 ml-64 w-[calc(100%-16rem)] h-16 bg-surface border-b border-[#1A1C18]/10 flex justify-between items-center px-8 z-40">
        <div class="flex items-center gap-4">
          <h2 class="text-primary text-sm uppercase tracking-wider font-bold">
            Welcome Admin | Employee Management | Add Employee
          </h2>
        </div>
        <div class="flex items-center gap-6">
          <button
            @click="handleLogout"
            class="text-on-surface-variant hover:text-primary transition-colors flex items-center gap-2"
          >
            <span class="material-symbols-outlined text-[20px]">logout</span>
            <span class="text-sm">Logout</span>
          </button>
          <div class="h-8 w-8 bg-surface-container-high rounded-full overflow-hidden border border-outline-variant flex items-center justify-center text-primary">
            <span class="material-symbols-outlined text-[20px]">account_circle</span>
          </div>
        </div>
      </header>

      <!-- Content Area -->
      <main class="mt-16 min-h-screen">
        <div class="p-10 max-w-7xl mx-auto">
          <div class="mb-8">
            <h3 class="text-4xl font-bold text-on-surface mb-2">New Associate</h3>
            <p class="text-lg text-on-surface-variant">Onboard a new member to the Studio MH02 architectural team.</p>
          </div>

          <div class="grid grid-cols-12 gap-6">
            <!-- Left Column: Media & Docs -->
            <div class="col-span-12 lg:col-span-4 space-y-6">
              <!-- Profile Photo Upload -->
              <div
                class="bg-surface-container-lowest border border-on-surface/10 p-6 flex flex-col items-center justify-center aspect-square group cursor-pointer relative overflow-hidden rounded-lg hover:bg-surface-container-low transition-colors"
                @click="triggerPhotoInput"
              >
                <img v-if="photoPreview" :src="photoPreview" class="w-full h-full object-cover absolute inset-0" alt="Profile photo" />
                <template v-else>
                  <span class="material-symbols-outlined text-[48px] text-outline mb-4">account_circle</span>
                  <p class="text-xs text-on-surface-variant font-bold tracking-widest uppercase">Upload Photo</p>
                  <p class="text-[10px] text-outline-variant mt-2 uppercase">JPG, PNG • Max 5MB</p>
                </template>
                <input ref="photoInputRef" type="file" accept="image/*" class="hidden" @change="onPhotoSelected" />
              </div>

              <!-- Documentation -->
              <div class="bg-surface-container-low border border-on-surface/10 p-6 rounded-lg">
                <h4 class="text-xs font-bold text-on-surface-variant uppercase tracking-widest mb-4">
                  Documentation
                </h4>
                <div class="space-y-3">
                  <div class="flex items-center justify-between p-3 border-b border-outline-variant/30 hover:bg-surface-container transition-colors cursor-pointer" @click="triggerDocInput('aadhar')">
                    <div class="flex items-center gap-3">
                      <span class="material-symbols-outlined text-[20px]" :class="docFiles.aadhar ? 'text-green-600' : 'text-primary'">{{ docFiles.aadhar ? 'check_circle' : 'cloud_upload' }}</span>
                      <div>
                        <span class="text-xs font-semibold block">Aadhar Card</span>
                        <span class="text-[10px] text-outline-variant">{{ docFiles.aadhar ? docFiles.aadhar.name : 'PDF / Image' }}</span>
                      </div>
                    </div>
                    <span class="material-symbols-outlined text-outline text-[18px]">{{ docFiles.aadhar ? 'done' : 'add' }}</span>
                  </div>
                  <div class="flex items-center justify-between p-3 border-b border-outline-variant/30 hover:bg-surface-container transition-colors cursor-pointer" @click="triggerDocInput('pan')">
                    <div class="flex items-center gap-3">
                      <span class="material-symbols-outlined text-[20px]" :class="docFiles.pan ? 'text-green-600' : 'text-primary'">{{ docFiles.pan ? 'check_circle' : 'cloud_upload' }}</span>
                      <div>
                        <span class="text-xs font-semibold block">PAN Card</span>
                        <span class="text-[10px] text-outline-variant">{{ docFiles.pan ? docFiles.pan.name : 'PDF / Image' }}</span>
                      </div>
                    </div>
                    <span class="material-symbols-outlined text-outline text-[18px]">{{ docFiles.pan ? 'done' : 'add' }}</span>
                  </div>
                  <div class="flex items-center justify-between p-3 border-b border-outline-variant/30 hover:bg-surface-container transition-colors cursor-pointer" @click="triggerDocInput('other')">
                    <div class="flex items-center gap-3">
                      <span class="material-symbols-outlined text-[20px]" :class="docFiles.other ? 'text-green-600' : 'text-primary'">{{ docFiles.other ? 'check_circle' : 'cloud_upload' }}</span>
                      <div>
                        <span class="text-xs font-semibold block">Other Document</span>
                        <span class="text-[10px] text-outline-variant">{{ docFiles.other ? docFiles.other.name : 'PDF / Image' }}</span>
                      </div>
                    </div>
                    <span class="material-symbols-outlined text-outline text-[18px]">{{ docFiles.other ? 'done' : 'add' }}</span>
                  </div>
                </div>
                <input ref="docInputRef" type="file" accept=".pdf,image/*" class="hidden" @change="onDocSelected" />
              </div>
            </div>

            <!-- Right Column: Form -->
            <div class="col-span-12 lg:col-span-8">
              <form @submit.prevent="handleAddEmployee" class="space-y-8">
                <div class="grid grid-cols-2 gap-x-6 gap-y-6">
                  <!-- Full Name -->
                  <div class="col-span-2 md:col-span-1">
                    <label class="text-xs font-bold text-on-surface-variant block mb-2 uppercase tracking-wide">
                      Full Name
                    </label>
                    <input
                      v-model="form.name"
                      type="text"
                      placeholder="Johnathan Doe"
                      class="w-full bg-transparent border-b border-[#A2937E] focus:border-primary focus:ring-0 px-0 py-2 outline-none transition-colors"
                    />
                  </div>

                  <!-- Designation -->
                  <div class="col-span-2 md:col-span-1">
                    <label class="text-xs font-bold text-on-surface-variant block mb-2 uppercase tracking-wide">
                      Designation
                    </label>
                    <select
                      v-model="form.designation"
                      class="w-full bg-transparent border-b border-[#A2937E] focus:border-primary focus:ring-0 px-0 py-2 outline-none transition-colors"
                    >
                      <option value="">Select designation</option>
                      <option value="Senior Architect">Senior Architect</option>
                      <option value="Junior Architect">Junior Architect</option>
                      <option value="Project Manager">Project Manager</option>
                      <option value="Interior Designer">Interior Designer</option>
                      <option value="Draftsperson">Draftsperson</option>
                    </select>
                  </div>

                  <!-- Joining Date -->
                  <div class="col-span-2 md:col-span-1">
                    <label class="text-xs font-bold text-on-surface-variant block mb-2 uppercase tracking-wide">
                      Joining Date
                    </label>
                    <input
                      v-model="form.joining_date"
                      type="date"
                      class="w-full bg-transparent border-b border-[#A2937E] focus:border-primary focus:ring-0 px-0 py-2 outline-none transition-colors"
                    />
                  </div>

                  <!-- End Date -->
                  <div class="col-span-2 md:col-span-1">
                    <label class="text-xs font-bold text-on-surface-variant block mb-2 uppercase tracking-wide">
                      Contract End Date
                    </label>
                    <input
                      v-model="form.end_date"
                      type="date"
                      class="w-full bg-transparent border-b border-[#A2937E] focus:border-primary focus:ring-0 px-0 py-2 outline-none transition-colors"
                    />
                  </div>

                  <!-- Salary / Month -->
                  <div class="col-span-2 md:col-span-1">
                    <label class="text-xs font-bold text-on-surface-variant block mb-2 uppercase tracking-wide">
                      Salary / Month (₹)
                    </label>
                    <div class="relative">
                      <span class="absolute left-0 top-2 text-on-surface">₹</span>
                      <CurrencyInput
                        v-model="form.salary_month"
                        placeholder="0.00"
                        class="w-full bg-transparent border-b border-[#A2937E] focus:border-primary focus:ring-0 pl-6 py-2 outline-none transition-colors"
                      />
                    </div>
                  </div>

                  <!-- Salary / Hour (Read-Only) -->
                  <div class="col-span-2 md:col-span-1">
                    <label class="text-xs font-bold text-on-surface-variant block mb-2 uppercase tracking-wide">
                      Salary / Hour (₹)
                    </label>
                    <div class="relative bg-surface-container-low/50">
                      <span class="absolute left-0 top-2 text-outline">₹</span>
                      <input
                        type="text"
                        :value="calculateSalaryPerHour()"
                        disabled
                        class="w-full bg-transparent border-b border-[#A2937E]/30 focus:ring-0 pl-6 py-2 outline-none text-outline cursor-not-allowed"
                      />
                    </div>
                  </div>

                  <!-- Reporting Manager -->
                  <div class="col-span-2 md:col-span-1">
                    <label class="text-xs font-bold text-on-surface-variant block mb-2 uppercase tracking-wide">
                      Reporting Manager
                    </label>
                    <select
                      v-model="form.manager_id"
                      class="w-full bg-transparent border-b border-[#A2937E] focus:border-primary focus:ring-0 px-0 py-2 outline-none transition-colors"
                    >
                      <option value="">— None —</option>
                      <option v-for="m in managers" :key="m.id" :value="m.id">{{ m.name }}</option>
                    </select>
                  </div>

                  <!-- Annual Leave Quota -->
                  <div class="col-span-2 md:col-span-1">
                    <label class="text-xs font-bold text-on-surface-variant block mb-2 uppercase tracking-wide">
                      Annual Leave Quota
                    </label>
                    <input
                      v-model="form.leaves_allowed"
                      type="number"
                      placeholder="24"
                      class="w-full bg-transparent border-b border-[#A2937E] focus:border-primary focus:ring-0 px-0 py-2 outline-none transition-colors"
                    />
                  </div>

                  <!-- PAN Number -->
                  <div class="col-span-2 md:col-span-1">
                    <label class="text-xs font-bold text-on-surface-variant block mb-2 uppercase tracking-wide">
                      PAN Number
                    </label>
                    <input
                      v-model="form.pan_number"
                      type="text"
                      placeholder="ABCDE1234F"
                      class="w-full bg-transparent border-b border-[#A2937E] focus:border-primary focus:ring-0 px-0 py-2 outline-none transition-colors uppercase"
                    />
                  </div>

                  <!-- Aadhar Number -->
                  <div class="col-span-2 md:col-span-1">
                    <label class="text-xs font-bold text-on-surface-variant block mb-2 uppercase tracking-wide">
                      Aadhar Number
                    </label>
                    <input
                      v-model="form.aadhar_number"
                      type="text"
                      placeholder="0000 0000 0000"
                      class="w-full bg-transparent border-b border-[#A2937E] focus:border-primary focus:ring-0 px-0 py-2 outline-none transition-colors"
                    />
                  </div>

                  <!-- Official Email -->
                  <div class="col-span-2 md:col-span-1">
                    <label class="text-xs font-bold text-on-surface-variant block mb-2 uppercase tracking-wide">
                      Official Email
                    </label>
                    <input
                      v-model="form.studio_email"
                      type="email"
                      placeholder="name@studiomh02.com"
                      class="w-full bg-transparent border-b border-[#A2937E] focus:border-primary focus:ring-0 px-0 py-2 outline-none transition-colors"
                    />
                  </div>

                  <!-- Personal Email -->
                  <div class="col-span-2 md:col-span-1">
                    <label class="text-xs font-bold text-on-surface-variant block mb-2 uppercase tracking-wide">
                      Personal Email
                    </label>
                    <input
                      v-model="form.personal_mail"
                      type="email"
                      placeholder="personal@email.com"
                      class="w-full bg-transparent border-b border-[#A2937E] focus:border-primary focus:ring-0 px-0 py-2 outline-none transition-colors"
                    />
                  </div>

                  <!-- Password -->
                  <div class="col-span-2 md:col-span-1">
                    <label class="text-xs font-bold text-on-surface-variant block mb-2 uppercase tracking-wide">
                      Password
                    </label>
                    <input
                      v-model="form.password"
                      type="password"
                      placeholder="Enter password"
                      class="w-full bg-transparent border-b border-[#A2937E] focus:border-primary focus:ring-0 px-0 py-2 outline-none transition-colors"
                    />
                  </div>

                  <!-- Role -->
                  <div class="col-span-2 md:col-span-1">
                    <label class="text-xs font-bold text-on-surface-variant block mb-2 uppercase tracking-wide">
                      Role
                    </label>
                    <select
                      v-model="form.role"
                      class="w-full bg-transparent border-b border-[#A2937E] focus:border-primary focus:ring-0 px-0 py-2 outline-none transition-colors"
                    >
                      <option value="employee">Employee</option>
                      <option value="project_manager">Project Manager</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>

                  <!-- Time Tracker Login -->
                  <div class="col-span-2 md:col-span-1">
                    <label class="text-xs font-bold text-on-surface-variant block mb-2 uppercase tracking-wide">
                      User ID for Time Tracker Login
                    </label>
                    <input
                      v-model="form.time_tracker_login"
                      type="text"
                      placeholder="user@studiomh02.com"
                      class="w-full bg-transparent border-b border-[#A2937E] focus:border-primary focus:ring-0 px-0 py-2 outline-none transition-colors"
                    />
                  </div>

                  <!-- Time Tracker Password -->
                  <div class="col-span-2 md:col-span-1">
                    <label class="text-xs font-bold text-on-surface-variant block mb-2 uppercase tracking-wide">
                      Password for Time Tracker Login
                    </label>
                    <input
                      v-model="form.time_tracker_password"
                      type="password"
                      placeholder="Enter time tracker password"
                      class="w-full bg-transparent border-b border-[#A2937E] focus:border-primary focus:ring-0 px-0 py-2 outline-none transition-colors"
                    />
                  </div>
                </div>

                <!-- Action Buttons -->
                <div class="flex items-center justify-end gap-6 pt-8">
                  <button
                    type="button"
                    @click="resetForm"
                    class="px-8 py-3 border border-error/20 text-error text-xs uppercase tracking-widest font-bold hover:bg-error/5 transition-colors rounded"
                  >
                    Discard Changes
                  </button>
                  <button
                    type="submit"
                    :disabled="loading"
                    class="px-8 py-3 bg-primary-container text-white text-xs uppercase tracking-widest font-bold hover:bg-primary transition-all active:scale-95 disabled:opacity-50 rounded"
                  >
                    {{ loading ? 'Adding...' : 'Add Employee' }}
                  </button>
                </div>

                <!-- Error Message -->
                <p v-if="error" class="text-error text-sm bg-error/10 p-3 rounded">{{ error }}</p>
                <!-- Success Message -->
                <p v-if="success" class="text-green-600 text-sm bg-green-50 p-3 rounded">{{ success }}</p>
              </form>
            </div>
          </div>

          <!-- Info Cards -->
          <div class="grid grid-cols-3 gap-6 mt-12 mb-8">
            <div class="bg-surface-container-low border border-outline-variant/20 p-6 rounded-lg">
              <div class="flex items-center gap-3 mb-3">
                <span class="material-symbols-outlined text-primary text-[24px]">lock</span>
                <h4 class="text-sm font-bold text-on-surface uppercase tracking-wide">Privacy First</h4>
              </div>
              <p class="text-xs text-on-surface-variant">
                All PII data including Aadhar and PAN are encrypted at rest following ISO 27001 standards.
              </p>
            </div>
            <div class="bg-surface-container-low border border-outline-variant/20 p-6 rounded-lg">
              <div class="flex items-center gap-3 mb-3">
                <span class="material-symbols-outlined text-primary text-[24px]">cloud_sync</span>
                <h4 class="text-sm font-bold text-on-surface uppercase tracking-wide">ERP Sync</h4>
              </div>
              <p class="text-xs text-on-surface-variant">
                Account credentials will be automatically generated and sent to the official email.
              </p>
            </div>
            <div class="bg-surface-container-low border border-outline-variant/20 p-6 rounded-lg">
              <div class="flex items-center gap-3 mb-3">
                <span class="material-symbols-outlined text-primary text-[24px]">event_note</span>
                <h4 class="text-sm font-bold text-on-surface uppercase tracking-wide">Leave Policy</h4>
              </div>
              <p class="text-xs text-on-surface-variant">
                Default studio leave policy applied. Prorated calculations based on joining date.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { usersAPI } from '../api/users'
import CurrencyInput from '../components/CurrencyInput.vue'

const router = useRouter()
const authStore = useAuthStore()

const managers = ref([])

// File upload state
const photoInputRef = ref(null)
const docInputRef = ref(null)
const photoPreview = ref(null)
const selectedPhoto = ref(null)
const currentDocType = ref('aadhar')
const docFiles = reactive({ aadhar: null, pan: null, other: null })

const form = reactive({
  name: '',
  designation: '',
  joining_date: '',
  end_date: '',
  salary_month: 0,
  salary_hour: 0,
  leaves_allowed: 18,
  pan_number: '',
  aadhar_number: '',
  manager_id: '',
  studio_email: '',
  personal_mail: '',
  password: '',
  role: 'employee',
  time_tracker_login: '',
  time_tracker_password: '',
})

const loading = ref(false)
const error = ref('')
const success = ref('')

onMounted(async () => {
  try {
    const res = await usersAPI.getUsers()
    managers.value = res.data.filter(u => u.role === 'project_manager' || u.role === 'admin')
  } catch (e) {
    console.error('Failed to load managers:', e)
  }
})

const calculateSalaryPerHour = () => {
  if (!form.salary_month || form.salary_month === 0) return '0.00'
  return ((form.salary_month * 13) / 12 / 160).toFixed(2)
}

// Photo upload
function triggerPhotoInput() { photoInputRef.value?.click() }
function onPhotoSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return
  selectedPhoto.value = file
  photoPreview.value = URL.createObjectURL(file)
}

// Doc upload
function triggerDocInput(type) {
  currentDocType.value = type
  if (docInputRef.value) docInputRef.value.value = ''
  docInputRef.value?.click()
}
function onDocSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return
  docFiles[currentDocType.value] = file
}

const resetForm = () => {
  form.name = ''
  form.designation = ''
  form.joining_date = ''
  form.end_date = ''
  form.salary_month = 0
  form.leaves_allowed = 18
  form.pan_number = ''
  form.aadhar_number = ''
  form.manager_id = ''
  form.studio_email = ''
  form.personal_mail = ''
  form.password = ''
  form.role = 'employee'
  form.time_tracker_login = ''
  form.time_tracker_password = ''
  error.value = ''
  success.value = ''
  photoPreview.value = null
  selectedPhoto.value = null
  docFiles.aadhar = null
  docFiles.pan = null
  docFiles.other = null
}

const handleAddEmployee = async () => {
  error.value = ''
  success.value = ''

  if (!form.name || !form.designation || !form.joining_date || !form.studio_email || !form.password) {
    error.value = 'Please fill in all required fields'
    return
  }

  loading.value = true

  try {
    const response = await usersAPI.createUser({
      name: form.name,
      designation: form.designation,
      joining_date: form.joining_date,
      end_date: form.end_date || null,
      salary_month: parseFloat(form.salary_month) || 0,
      leaves_allowed: parseInt(form.leaves_allowed) || 18,
      pan_number: form.pan_number,
      aadhar_number: form.aadhar_number,
      manager_id: form.manager_id ? parseInt(form.manager_id) : null,
      studio_email: form.studio_email,
      personal_mail: form.personal_mail,
      password: form.password,
      role: form.role,
      time_tracker_login: form.time_tracker_login,
      time_tracker_password: form.time_tracker_password,
    })

    const userId = response.data.id

    // Upload profile photo if selected
    if (selectedPhoto.value) {
      await usersAPI.uploadPhoto(userId, selectedPhoto.value)
    }

    // Upload documents if selected
    for (const [docType, file] of Object.entries(docFiles)) {
      if (file) await usersAPI.uploadDocument(userId, file, docType)
    }

    success.value = `Employee ${form.name} added successfully!`
    setTimeout(() => { resetForm() }, 2000)
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Failed to add employee'
    console.error('Error adding employee:', err)
  } finally {
    loading.value = false
  }
}

const handleLogout = () => {
  authStore.clearAuth()
  router.push('/login')
}
</script>

<style scoped>
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}
</style>
