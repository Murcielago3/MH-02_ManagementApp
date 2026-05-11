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
          <div class="avatar">{{ userInitials }}</div>
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
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { usersAPI } from '../api/users'

const route = useRoute()
const authStore = useAuthStore()
const currentUser = ref(null)

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
  if (!authStore.isAuthenticated) return

  try {
    const response = await usersAPI.getMe()
    currentUser.value = response.data
  } catch (err) {
    console.warn('Unable to load current user profile', err)
  }
})

const navItems = [
  { path: '/admin/dashboard', icon: 'dashboard', label: 'Dashboard' },
  { path: '/admin/employees', icon: 'group', label: 'Employees' },
  { path: '/admin/projects', icon: 'architecture', label: 'Projects' },
  { path: '/admin/clients', icon: 'handshake', label: 'Clients' },
  { path: '/admin/tasks', icon: 'task', label: 'Tasks' },
  { path: '/admin/leaves', icon: 'event_busy', label: 'Leaves' },
  { path: '/admin/attendance', icon: 'schedule', label: 'Attendance' },
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
  font-family: 'Integral CF', sans-serif;
  font-size: 14px;
  line-height: 20px;
  color: #1c1b1d;
  background: #fcf8fa;
}

/* ───────── Sidebar ───────── */
.sidebar {
  width: 240px;
  min-width: 240px;
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  background: #1a1a2e;
  border-right: 1px solid #c8c5cd;
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 8px;
  z-index: 20;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 24px;
}

.brand-logo {
  width: 32px;
  height: 32px;
  border-radius: 4px;
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
  background: #1a1a2e;
}

.lg-cell {
  border-radius: 1px;
}

.lg-a {
  background: #ffffff;
}

.lg-b {
  background: rgba(255, 255, 255, 0.35);
}

.lg-c {
  background: rgba(255, 255, 255, 0.6);
}

.brand-name {
  font-size: 24px;
  font-weight: 600;
  line-height: 32px;
  letter-spacing: -0.02em;
  color: #ffffff;
  margin: 0;
}

.brand-sub {
  font-size: 11px;
  font-weight: 600;
  line-height: 16px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #83829b;
  margin: 4px 0 0;
}

/* ───────── Nav ───────── */
.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex-grow: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 4px;
  font-size: 14px;
  line-height: 20px;
  color: #83829b;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.15s ease;
}

.nav-item:hover {
  background: #45455b;
  color: #ffffff;
}

.nav-item:active {
  transform: scale(0.95);
}

.nav-item.active {
  background: #515f74;
  color: #ffffff;
}

.nav-item .material-symbols-outlined {
  font-size: 20px;
}

/* ───────── Main Area ───────── */
.main-area {
  flex-grow: 1;
  margin-left: 240px;
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
  left: 240px;
  z-index: 10;
  background: #ffffff;
  border-bottom: 1px solid #c8c5cd;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 33%;
}

.top-bar-icon {
  color: #78767d;
  font-size: 20px;
}

.search-input {
  background: transparent;
  border: none;
  outline: none;
  font-family: 'Integral CF', sans-serif;
  font-size: 14px;
  line-height: 20px;
  color: #1c1b1d;
  width: 100%;
  padding: 0;
}

.search-input::placeholder {
  color: #78767d;
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
  border-radius: 4px;
  color: #47464c;
  cursor: pointer;
  transition: background 0.15s;
}

.icon-btn:hover {
  background: #f1edef;
}

.icon-btn:active {
  opacity: 0.8;
}

.icon-btn .material-symbols-outlined {
  font-size: 22px;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #515f74;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  cursor: pointer;
  border: 1px solid #c8c5cd;
}

/* ───────── Page Content ───────── */
.page-content {
  margin-top: 64px;
  padding: 24px;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ───────── Material Symbols ───────── */
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}
</style>
