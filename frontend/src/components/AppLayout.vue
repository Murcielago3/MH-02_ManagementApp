<template>
  <div class="app-shell">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-logo">
          <div class="logo-grid-mini">
            <div class="lg-cell lg-a"></div>
            <div class="lg-cell lg-b"></div>
            <div class="lg-cell lg-c"></div>
            <div class="lg-cell lg-a"></div>
          </div>
        </div>
        <div>
          <h1 class="brand-name">{{ brandName }}</h1>
          <p class="brand-sub">Enterprise ERP</p>
        </div>
      </div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="['nav-item', { active: isActive(item.path) }]"
        >
          <span
            class="material-symbols-outlined"
            :style="isActive(item.path) ? 'font-variation-settings: \'FILL\' 1;' : ''"
          >{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>
    </aside>

    <!-- Main content area -->
    <div class="main-area">
      <!-- Top App Bar -->
      <header class="top-bar">
        <div class="top-bar-left">
          <span class="material-symbols-outlined top-bar-icon">search</span>
          <input
            type="text"
            placeholder="Search..."
            class="search-input"
          />
        </div>
        <div class="top-bar-right">
          <button class="icon-btn">
            <span class="material-symbols-outlined">notifications</span>
          </button>
          <button class="icon-btn">
            <span class="material-symbols-outlined">settings</span>
          </button>
          <button class="icon-btn">
            <span class="material-symbols-outlined">help</span>
          </button>
          
          <div class="avatar-wrapper" style="position: relative;" @click="showProfileMenu = !showProfileMenu">
            <div class="avatar">{{ userInitials }}</div>
            
            <!-- Profile Dropdown -->
            <div v-if="showProfileMenu" class="profile-dropdown">
              <div class="dropdown-header">
                <p class="dropdown-name">{{ currentUser?.name || authStore.user?.name || 'Admin' }}</p>
                <p class="dropdown-role">{{ authStore.role }}</p>
              </div>
              <div class="dropdown-divider"></div>
              <router-link to="/employee/profile" class="dropdown-item" @click="showProfileMenu = false">
                <span class="material-symbols-outlined">person</span>
                My Profile
              </router-link>
              <button class="dropdown-item">
                <span class="material-symbols-outlined">settings</span>
                Settings
              </button>
              <div class="dropdown-divider"></div>
              <button class="dropdown-item text-error" @click.stop="handleLogout">
                <span class="material-symbols-outlined">logout</span>
                Log out
              </button>
            </div>
          </div>
        </div>
      </header>

      <!-- Page content slot -->
      <main class="page-content">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { usersAPI } from '../api/users'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const currentUser = ref(null)
const showProfileMenu = ref(false)

const closeProfileMenu = (e) => {
  if (!e.target.closest('.avatar-wrapper')) {
    showProfileMenu.value = false
  }
}

const brandName = computed(() => {
  if (currentUser.value?.name) return currentUser.value.name
  if (authStore.user?.name) return authStore.user.name
  if (authStore.role === 'admin') return 'Studio MH02'
  if (authStore.role === 'project_manager') return 'Project Manager'
  if (authStore.role === 'employee') return 'Employee'
  return 'Studio MH02'
})

const userInitials = computed(() => {
  const name = currentUser.value?.name || authStore.user?.name || 'Admin'
  return name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
})

onMounted(async () => {
  document.addEventListener('click', closeProfileMenu)
  if (!authStore.isAuthenticated) return

  try {
    const response = await usersAPI.getMe()
    currentUser.value = response.data
  } catch (err) {
    console.warn('Unable to load current user profile', err)
  }
})

onUnmounted(() => {
  document.removeEventListener('click', closeProfileMenu)
})

const handleLogout = () => {
  showProfileMenu.value = false
  authStore.clearAuth()
  router.push('/login')
}

const navItems = [
  { path: '/admin/dashboard', icon: 'dashboard', label: 'Dashboard' },
  { path: '/employee/dashboard', icon: 'badge', label: 'Employee Portal' },
  { path: '/admin/employees', icon: 'group', label: 'Employees' },
  { path: '/admin/projects', icon: 'architecture', label: 'Projects' },
  { path: '/admin/clients', icon: 'handshake', label: 'Clients' },
  { path: '/admin/tasks', icon: 'task', label: 'Tasks' },
  { path: '/admin/leaves', icon: 'event_busy', label: 'Leaves' },
  { path: '/admin/timesheets', icon: 'pending_actions', label: 'Timesheets' },
  { path: '/admin/expenses', icon: 'payments', label: 'Expenses' },
  { path: '/admin/invoices', icon: 'receipt_long', label: 'Invoices' },
  { path: '/admin/estimates', icon: 'calculate', label: 'Estimates' },
  { path: '/admin/reports', icon: 'analytics', label: 'Reports' },
]

function isActive(path) {
  return route.path === path
}
</script>

<style scoped>
/* ───────── Shell ───────── */
.app-shell {
  display: flex;
  min-height: 100vh;
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 20px;
  color: var(--color-on-surface);
  background: var(--color-background);
}

/* ───────── Sidebar ───────── */
.sidebar {
  width: 260px;
  min-width: 260px;
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  background: var(--color-on-surface);
  display: flex;
  flex-direction: column;
  padding: 16px 0;
  z-index: 20;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 32px;
  padding: 0 24px;
}

.brand-logo {
  width: 32px;
  height: 32px;
  border-radius: var(--radius);
  overflow: hidden;
  flex-shrink: 0;
}

.logo-grid-mini {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2px;
  width: 100%;
  height: 100%;
  padding: 3px;
  background: var(--color-primary);
}

.lg-cell {
  border-radius: 1px;
}

.lg-a {
  background: #ffffff;
}

.lg-b {
  background: rgba(255, 255, 255, 0.4);
}

.lg-c {
  background: rgba(255, 255, 255, 0.7);
}

.brand-name {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: #ffffff;
  margin: 0;
}

.brand-sub {
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.5);
  margin: 4px 0 0;
}

/* ───────── Nav ───────── */
.sidebar-nav {
  display: flex;
  flex-direction: column;
  flex-grow: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  font-family: var(--font-body);
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s ease;
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #ffffff;
}

.nav-item.active {
  background: rgba(40, 116, 117, 0.15);
  color: #ffffff;
  border-left-color: var(--color-primary);
}

.nav-item .material-symbols-outlined {
  font-size: 20px;
}

/* ───────── Main Area ───────── */
.main-area {
  flex-grow: 1;
  margin-left: 260px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* ───────── Top Bar ───────── */
.top-bar {
  height: 64px;
  position: fixed;
  top: 0;
  right: 0;
  left: 260px;
  z-index: 10;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-outline-variant);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 40%;
}

.top-bar-icon {
  color: var(--color-outline);
  font-size: 20px;
}

.search-input {
  background: transparent;
  border: none;
  outline: none;
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-on-surface);
  width: 100%;
  padding: 0;
}

.search-input::placeholder {
  color: var(--color-on-surface-variant);
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  border: none;
  background: none;
  border-radius: var(--radius);
  color: var(--color-on-surface-variant);
  cursor: pointer;
  transition: background 0.15s;
}

.icon-btn:hover {
  background: var(--color-surface-container);
}

.icon-btn:active {
  opacity: 0.8;
}

.icon-btn .material-symbols-outlined {
  font-size: 22px;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--color-primary-container);
  color: var(--color-on-primary-container);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.05em;
  cursor: pointer;
  border: 1px solid var(--color-outline-variant);
}

/* ───────── Profile Dropdown ───────── */
.avatar-wrapper {
  position: relative;
}

.profile-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  width: 220px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 100;
}

.dropdown-header {
  padding: 16px;
  background: var(--color-surface-container-low);
}

.dropdown-name {
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 700;
  color: var(--color-on-surface);
  margin: 0;
}

.dropdown-role {
  font-family: var(--font-body);
  font-size: 11px;
  color: var(--color-on-surface-variant);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 4px 0 0;
}

.dropdown-divider {
  height: 1px;
  background: var(--color-outline-variant);
  margin: 0;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: none;
  border: none;
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  cursor: pointer;
  text-align: left;
  transition: background 0.15s;
}

.dropdown-item:hover {
  background: var(--color-surface-container);
}

.dropdown-item .material-symbols-outlined {
  font-size: 18px;
  color: var(--color-on-surface-variant);
}

.dropdown-item.text-error {
  color: var(--color-error);
}

.dropdown-item.text-error .material-symbols-outlined {
  color: var(--color-error);
}

/* ───────── Page Content ───────── */
.page-content {
  margin-top: 64px;
  padding: 32px;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* ───────── Material Symbols ───────── */
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}
</style>
