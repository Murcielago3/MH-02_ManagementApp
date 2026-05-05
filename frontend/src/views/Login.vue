<template>
  <div class="flex min-h-screen bg-background">
    <!-- Left Section: Visual Branding (Desktop only) -->
    <div
      class="hidden lg:flex lg:w-1/2 relative overflow-hidden items-center justify-center border-r border-outline-variant/30"
      style="background: linear-gradient(165deg, #e2dfff 0%, #f7f9fb 100%)"
    >
      <div class="absolute inset-0 opacity-[0.08]"></div>
      <div class="absolute inset-0 bg-gradient-to-tr from-primary/5 via-transparent to-transparent"></div>

      <div class="relative z-10 w-full max-w-2xl px-8">
        <div class="mb-8">
          <div
            class="inline-flex p-4 bg-white/60 backdrop-blur-md rounded-xl border border-white/40 shadow-lg mb-6 transform hover:translate-y-[-2px] transition-all duration-500"
          >
            <div class="grid grid-cols-2 gap-2">
              <div class="w-10 h-10 bg-primary rounded-sm"></div>
              <div class="w-10 h-10 bg-primary opacity-30 rounded-sm"></div>
              <div class="w-10 h-10 bg-primary opacity-60 rounded-sm"></div>
              <div class="w-10 h-10 bg-primary rounded-sm"></div>
            </div>
          </div>
          <h2 class="text-7xl font-bold text-primary mb-4 tracking-tighter leading-[1.1] uppercase">
            Studio<br />MH 02
          </h2>
          <div class="w-24 h-1.5 bg-primary/20 mb-6"></div>
          <p class="text-xl text-on-surface-variant max-w-md leading-relaxed">
            Precision-engineered studio suite for high-performance architectural design and enterprise resource
            planning.
          </p>
        </div>

        <!-- Stats Indicators -->
        <div class="grid grid-cols-2 gap-8 mt-12 pt-12 border-t border-outline-variant/40">
          <div>
            <div class="text-primary text-2xl font-bold tracking-tight">1.2ms</div>
            <div class="text-on-surface-variant/60 text-xs uppercase tracking-widest font-semibold mt-1">
              Rendering Latency
            </div>
          </div>
          <div>
            <div class="text-primary text-2xl font-bold tracking-tight">v4.8.0</div>
            <div class="text-on-surface-variant/60 text-xs uppercase tracking-widest font-semibold mt-1">
              Build Release
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Right Section: Login Content -->
    <main class="w-full lg:w-1/2 flex items-center justify-center p-4 sm:p-8 bg-surface relative">
      <div class="lg:hidden absolute top-0 left-0 w-full h-40 opacity-60" style="background: linear-gradient(165deg, #e2dfff 0%, #f7f9fb 100%)"></div>

      <div class="w-full max-w-sm space-y-8 relative">
        <!-- Mobile Logo -->
        <div class="lg:hidden flex flex-col items-center mb-8">
          <div
            class="p-3 bg-white/80 backdrop-blur border border-outline-variant rounded-lg flex items-center justify-center mb-4 shadow-lg"
          >
            <div class="grid grid-cols-2 gap-1.5">
              <div class="w-4 h-4 bg-primary"></div>
              <div class="w-4 h-4 bg-primary opacity-30"></div>
              <div class="w-4 h-4 bg-primary opacity-60"></div>
              <div class="w-4 h-4 bg-primary"></div>
            </div>
          </div>
          <h1 class="text-2xl font-bold text-on-surface">Studio MH02</h1>
        </div>

        <!-- Header -->
        <header class="space-y-2">
          <h2 class="text-3xl font-bold text-on-surface tracking-tight">Welcome back</h2>
          <p class="text-base text-on-surface-variant">Enter your workspace credentials to continue.</p>
        </header>

        <!-- Authentication Form -->
        <form @submit.prevent="handleLogin" class="space-y-6">
          <!-- Studio Email Field -->
          <div class="space-y-2">
            <label for="studio_email" class="text-sm font-semibold text-on-surface-variant block">Studio Email</label>
            <div class="relative group">
              <input
                id="studio_email"
                v-model="form.studio_email"
                type="email"
                placeholder="e.g. user@studiomh02.com"
                required
                class="w-full h-14 pl-4 pr-12 text-on-surface bg-white border border-outline-variant rounded-lg focus:outline-none focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all placeholder:text-outline/60 shadow-sm group-hover:border-outline"
              />
              <div class="absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-none text-outline group-focus-within:text-primary transition-colors">
                <span class="material-symbols-outlined">mail</span>
              </div>
            </div>
            <p v-if="errors.email" class="text-error text-sm">{{ errors.email }}</p>
          </div>

          <!-- Password Field -->
          <div class="space-y-2">
            <div class="flex justify-between items-center">
              <label for="password" class="text-sm font-semibold text-on-surface-variant block">Password</label>
              <a href="#" class="text-sm text-primary hover:text-tertiary transition-colors">Forgot password?</a>
            </div>
            <div class="relative group">
              <input
                id="password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="••••••••••••"
                required
                class="w-full h-14 pl-4 pr-12 text-on-surface bg-white border border-outline-variant rounded-lg focus:outline-none focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all placeholder:text-outline/60 shadow-sm group-hover:border-outline"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-auto text-outline group-focus-within:text-primary transition-colors hover:text-primary"
              >
                <span class="material-symbols-outlined">{{ showPassword ? 'visibility' : 'visibility_off' }}</span>
              </button>
            </div>
            <p v-if="errors.password" class="text-error text-sm">{{ errors.password }}</p>
          </div>

          <!-- Keep signed in -->
          <div class="flex items-center">
            <input
              id="keep-signed"
              v-model="form.keepSigned"
              type="checkbox"
              class="w-4 h-4 border-outline-variant rounded"
            />
            <label for="keep-signed" class="ml-2 text-sm text-on-surface-variant">Keep me signed in</label>
          </div>

          <!-- Error Message -->
          <p v-if="errors.general" class="text-error text-sm bg-error/10 p-3 rounded">{{ errors.general }}</p>

          <!-- Sign In Button -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full h-14 bg-primary text-on-primary font-bold uppercase tracking-wider rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95"
          >
            <span v-if="!loading">Sign In →</span>
            <span v-else>Signing in...</span>
          </button>
        </form>

        <!-- Footer -->
        <p class="text-center text-on-surface-variant text-sm">
          Don't have an account yet?
          <a href="#" class="text-primary hover:text-tertiary font-semibold transition-colors">Contact administration</a>
        </p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { authAPI } from '../api/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  studio_email: '',
  password: '',
  keepSigned: false,
})

const showPassword = ref(false)
const loading = ref(false)
const errors = reactive({
  email: '',
  password: '',
  general: '',
})

const handleLogin = async () => {
  // Reset errors
  errors.email = ''
  errors.password = ''
  errors.general = ''

  // Validation
  if (!form.studio_email) {
    errors.email = 'Studio email is required'
    return
  }
  if (!form.password) {
    errors.password = 'Password is required'
    return
  }

  loading.value = true

  try {
    const response = await authAPI.login(form.studio_email, form.password)
    
    if (response.data.access_token) {
      authStore.setToken(response.data.access_token, response.data.role || 'employee')
      
      // Redirect based on role
      if (response.data.role === 'admin') {
        router.push('/employee-management')
      } else {
        router.push('/')
      }
    }
  } catch (error) {
    if (error.response?.status === 401) {
      errors.general = 'Invalid email or password'
    } else {
      errors.general = error.message || 'Login failed. Please try again.'
    }
    console.error('Login error:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}
</style>

          <!-- Password Field -->
          <div class="space-y-2">
            <div class="flex justify-between items-center px-0">
              <label for="password" class="text-sm font-semibold text-gray-700 block">Password</label>
              <a href="#" class="text-sm text-indigo-600 hover:text-indigo-700 transition-colors font-semibold">
                Forgot password?
              </a>
            </div>
            <div class="relative group">
              <input
                id="password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="••••••••••••"
                required
                class="w-full h-14 pl-4 pr-12 font-sm text-gray-900 bg-white border border-gray-300 rounded-lg focus:outline-none focus:border-indigo-600 focus:ring-4 focus:ring-indigo-600/10 transition-all placeholder:text-gray-400 shadow-sm group-hover:border-gray-400"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-auto text-gray-400 group-focus-within:text-indigo-600 transition-colors hover:text-gray-600"
              >
                <i :class="showPassword ? 'pi pi-eye-slash text-xl' : 'pi pi-eye text-xl'"></i>
              </button>
            </div>
            <p v-if="passwordError" class="text-red-500 text-sm mt-1">{{ passwordError }}</p>
          </div>

          <!-- Secondary Actions -->
          <div class="flex items-center px-0">
            <label class="flex items-center gap-3 cursor-pointer group">
              <input
                v-model="form.rememberMe"
                type="checkbox"
                class="w-5 h-5 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600/20 cursor-pointer transition-all"
              />
              <span class="font-sm text-gray-700 group-hover:text-gray-900 transition-colors">
                Keep me signed in
              </span>
            </label>
          </div>

          <!-- Primary Action -->
          <div class="space-y-4">
            <button
              type="submit"
              :disabled="isLoading || !form.email || !form.password"
              class="w-full h-14 bg-indigo-600 text-white font-semibold text-base rounded-lg flex items-center justify-center gap-2 hover:bg-indigo-700 hover:shadow-lg hover:shadow-indigo-600/20 active:scale-[0.98] transition-all uppercase tracking-wider disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span>{{ isLoading ? 'Signing in...' : 'Sign In' }}</span>
              <i class="pi pi-arrow-right text-lg"></i>
            </button>

            <!-- Error Message -->
            <div v-if="apiError" class="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p class="text-red-700 text-sm font-medium">{{ apiError }}</p>
            </div>
          </div>
        </form>

        <!-- Footer / Registration -->
        <footer class="pt-6 text-center border-t border-gray-200">
          <p class="font-sm text-gray-600">
            Don't have an account yet?
            <a href="#" class="font-semibold text-indigo-600 ml-1 hover:underline underline-offset-4">
              Contact administration
            </a>
          </p>
        </footer>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { authAPI } from '../api/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({
  email: '',
  password: '',
  rememberMe: false,
})

const showPassword = ref(false)
const isLoading = ref(false)
const apiError = ref('')
const emailError = ref('')
const passwordError = ref('')

const validateEmail = () => {
  const email = form.value.email
  if (!email) {
    emailError.value = 'Email is required'
  } else if (!email.includes('@')) {
    emailError.value = 'Please enter a valid email'
  } else {
    emailError.value = ''
  }
}

const handleLogin = async () => {
  emailError.value = ''
  passwordError.value = ''
  apiError.value = ''

  // Basic validation
  if (!form.value.email) {
    emailError.value = 'Email is required'
    return
  }
  if (!form.value.password) {
    passwordError.value = 'Password is required'
    return
  }

  isLoading.value = true
  try {
    const response = await authAPI.login(form.value.email, form.value.password)
    const { access_token, token_type, role } = response.data

    authStore.setToken(access_token, role)
    router.push('/')
  } catch (error) {
    apiError.value = error.response?.data?.detail || 'Login failed. Please try again.'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.pattern-overlay {
  background-image: radial-gradient(circle at 1px 1px, #3525cd 1px, transparent 0);
  background-size: 32px 32px;
}
</style>
