<template>
  <div class="flex min-h-screen bg-gray-50">
    <!-- Left Section: Visual Branding (Desktop only) -->
    <div
      class="hidden lg:flex lg:w-1/2 relative overflow-hidden items-center justify-center border-r border-gray-200"
      style="background: linear-gradient(165deg, #e2dfff 0%, #f7f9fb 100%)"
    >
      <!-- Subtle architectural pattern -->
      <div class="absolute inset-0 pattern-overlay opacity-[0.08]"></div>
      <div class="absolute inset-0 bg-gradient-to-tr from-indigo-600/5 via-transparent to-transparent"></div>

      <!-- Large Architectural Graphic Reference -->
      <div class="relative z-10 w-full max-w-2xl px-8">
        <div class="mb-8">
          <div
            class="inline-flex p-4 bg-white/60 backdrop-blur-md rounded-lg border border-white/40 shadow-lg mb-6 transform hover:translate-y-[-2px] transition-all duration-500"
          >
            <div class="grid grid-cols-2 gap-2">
              <div class="w-10 h-10 bg-indigo-600 rounded-sm"></div>
              <div class="w-10 h-10 bg-indigo-600 opacity-30 rounded-sm"></div>
              <div class="w-10 h-10 bg-indigo-600 opacity-60 rounded-sm"></div>
              <div class="w-10 h-10 bg-indigo-600 rounded-sm"></div>
            </div>
          </div>
          <h2 class="text-7xl font-bold text-indigo-600 mb-4 tracking-tighter leading-[1.1] uppercase">
            Studio<br />MH 02
          </h2>
          <div class="w-24 h-1.5 bg-indigo-600/20 mb-6"></div>
          <p class="text-xl text-gray-700 max-w-md leading-relaxed">
            Precision-engineered studio suite for high-performance architectural design and enterprise resource
            planning.
          </p>
        </div>

        <!-- Stats Indicators -->
        <div class="grid grid-cols-2 gap-8 mt-12 pt-12 border-t border-gray-300/40">
          <div>
            <div class="text-indigo-600 text-2xl font-bold tracking-tight">1.2ms</div>
            <div class="text-gray-600/60 text-xs uppercase tracking-widest font-semibold mt-1">
              Rendering Latency
            </div>
          </div>
          <div>
            <div class="text-indigo-600 text-2xl font-bold tracking-tight">v4.8.0</div>
            <div class="text-gray-600/60 text-xs uppercase tracking-widest font-semibold mt-1">
              Build Release
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Right Section: Login Content -->
    <main class="w-full lg:w-1/2 flex items-center justify-center p-4 sm:p-8 relative">
      <!-- Decorative elements for mobile -->
      <div class="lg:hidden absolute top-0 left-0 w-full h-40 opacity-60" style="background: linear-gradient(165deg, #e2dfff 0%, #f7f9fb 100%)"></div>

      <div class="w-full max-w-md space-y-8 relative">
        <!-- Mobile Logo -->
        <div class="lg:hidden flex flex-col items-center mb-8">
          <div
            class="p-3 bg-white/80 backdrop-blur border border-gray-300 rounded-lg flex items-center justify-center mb-4 shadow-lg"
          >
            <div class="grid grid-cols-2 gap-1.5">
              <div class="w-4 h-4 bg-indigo-600"></div>
              <div class="w-4 h-4 bg-indigo-600 opacity-30"></div>
              <div class="w-4 h-4 bg-indigo-600 opacity-60"></div>
              <div class="w-4 h-4 bg-indigo-600"></div>
            </div>
          </div>
          <h1 class="text-2xl font-bold text-gray-900">Studio MH02</h1>
        </div>

        <!-- Header -->
        <header class="space-y-2">
          <h2 class="text-3xl font-bold text-gray-900 tracking-tight">Welcome back</h2>
          <p class="text-base text-gray-600">Enter your workspace credentials to continue.</p>
        </header>

        <!-- Authentication Form -->
        <form @submit.prevent="handleLogin" class="space-y-6">
          <!-- Email Field -->
          <div class="space-y-2">
            <label for="email" class="text-sm font-semibold text-gray-700 block ml-0">Studio Email</label>
            <div class="relative group">
              <input
                id="email"
                v-model="form.email"
                type="email"
                placeholder="e.g. creative_user_01"
                required
                class="w-full h-14 pl-4 pr-12 font-sm text-gray-900 bg-white border border-gray-300 rounded-lg focus:outline-none focus:border-indigo-600 focus:ring-4 focus:ring-indigo-600/10 transition-all placeholder:text-gray-400 shadow-sm group-hover:border-gray-400"
              />
              <div class="absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-none text-gray-400 group-focus-within:text-indigo-600 transition-colors">
                <i class="pi pi-envelope text-xl"></i>
              </div>
            </div>
            <p v-if="emailError" class="text-red-500 text-sm mt-1">{{ emailError }}</p>
          </div>

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
