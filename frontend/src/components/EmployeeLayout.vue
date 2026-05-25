<template>
  <div class="app-layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo-box">
          <img :src="logoUrl" alt="Studio MH02 Logo" class="sidebar-logo-img" />
        </div>
        <h1 class="brand-title">{{ brandName }}</h1>
      </div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
        >
          <span class="material-symbols-outlined nav-icon">{{ item.icon }}</span>
          <div class="nav-label-wrapper">
            <span class="nav-label">{{ item.label }}</span>
            <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
          </div>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="version-tag">v1.0.0</div>
      </div>
    </aside>

    <!-- Main content area -->
    <div class="main-area">
      <!-- Top App Bar -->
      <header class="top-bar">
        <div class="top-bar-left">
          <!-- Employee view generally won't have global search, keeping it simple -->
          <h2 class="page-title">{{ currentPageTitle }}</h2>
        </div>
        <div class="top-bar-right">
          <button class="icon-btn">
            <span class="material-symbols-outlined">notifications</span>
          </button>
          
          <div class="avatar-wrapper" style="position: relative;" @click="showProfileMenu = !showProfileMenu">
            <div class="avatar" :style="avatarStyle">
              <span v-if="!avatarUrl">{{ userInitials }}</span>
            </div>
            
            <!-- Profile Dropdown -->
            <div v-if="showProfileMenu" class="profile-dropdown">
              <div class="dropdown-header">
                <p class="dropdown-name">{{ currentUser?.name || authStore.user?.name || 'Employee' }}</p>
                <p class="dropdown-role">{{ authStore.role }}</p>
              </div>
              <div class="dropdown-divider"></div>
              <router-link to="/employee/profile" class="dropdown-item" @click="showProfileMenu = false">
                <span class="material-symbols-outlined">person</span>
                My Profile
              </router-link>
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
import { useTimesheetStore } from '../stores/timesheet'
import { usersAPI } from '../api/users'
import { getAppLogoUrl } from '../utils/logo'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const timesheetStore = useTimesheetStore()
const currentUser = ref(null)
const showProfileMenu = ref(false)
const logoUrl = getAppLogoUrl()

const closeProfileMenu = (e) => {
  if (!e.target.closest('.avatar-wrapper')) {
    showProfileMenu.value = false
  }
}

onMounted(async () => {
  document.addEventListener('click', closeProfileMenu)
  if (!authStore.isAuthenticated) return

  try {
    const response = await usersAPI.getMe()
    currentUser.value = response.data
    
    // Fetch timesheet data for badges if employee
    if (authStore.role === 'employee' || authStore.role === 'project_manager' || authStore.role === 'admin') {
      timesheetStore.fetchPendingWeeks()
    }
  } catch (err) {
    console.warn('Unable to load data', err)
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

const brandName = computed(() => {
  return 'Studio MH02'
})

const avatarUrl = computed(() => {
  return currentUser.value?.photo_url ? usersAPI.resolveFileUrl(currentUser.value.photo_url) : null
})

const avatarStyle = computed(() => {
  if (avatarUrl.value) {
    return {
      backgroundImage: `url(${avatarUrl.value})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      color: 'transparent'
    }
  }
  return {}
})

const userInitials = computed(() => {
  const name = currentUser.value?.name || authStore.user?.name || 'Employee'
  return name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
})

const navItems = computed(() => {
  const items = [
    { path: '/employee/dashboard', icon: 'dashboard', label: 'Dashboard' },
    { path: '/employee/timesheet', icon: 'pending_actions', label: 'Timesheet', badge: timesheetStore.pendingCount > 0 ? timesheetStore.pendingCount : null },
    { path: '/employee/leaves', icon: 'event_busy', label: 'Leaves' },
    { path: '/employee/salary', icon: 'payments', label: 'Salary' },
    { path: '/employee/reimbursements', icon: 'receipt_long', label: 'Reimbursements' },
    { path: '/employee/projects', icon: 'architecture', label: 'Projects' },
  ]
  
  // Team members are project-scoped now — open via the Projects page → click a project.
  
  if (authStore.role === 'admin') {
    items.push({ path: '/admin/dashboard', icon: 'admin_panel_settings', label: 'Admin Portal' })
  }
  
  return items
})

function isActive(path) {
  return route.path.startsWith(path)
}

const currentPageTitle = computed(() => {
  const item = navItems.value.find(nav => route.path.startsWith(nav.path))
  return item ? item.label : 'Employee Portal'
})
</script>

<style scoped>
/* ───────── Shell ───────── */
.app-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: var(--color-background);
  font-family: var(--font-body);
}

/* ───────── Sidebar ───────── */
.sidebar {
  width: 280px;
  background: var(--color-surface);
  border-right: 1px solid var(--color-outline-variant);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  z-index: 20;
}

.sidebar-header {
  height: 80px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  border-bottom: 1px solid var(--color-outline-variant);
}

.logo-box {
  width: 32px;
  height: 32px;
  margin-right: 12px;
  overflow: hidden;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface);
}

.sidebar-logo-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.brand-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 800;
  color: var(--color-on-surface);
  letter-spacing: -0.02em;
  margin: 0;
  text-transform: uppercase;
}

.sidebar-nav {
  flex: 1;
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  color: var(--color-on-surface-variant);
  text-decoration: none;
  transition: all 0.2s ease;
  font-size: 14px;
  font-weight: 600;
}

.nav-item:hover {
  background: var(--color-surface-container);
  color: var(--color-on-surface);
}

.nav-item.active {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.nav-item.active .nav-icon {
  color: var(--color-on-primary);
}

.nav-icon {
  font-size: 20px;
  color: var(--color-outline);
}

.nav-label-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex: 1;
}

.nav-badge {
  background: var(--color-error, #dc2626);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 99px;
  line-height: 1;
}

.sidebar-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--color-outline-variant);
}

.version-tag {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-outline);
  letter-spacing: 0.05em;
}

/* ───────── Main Area ───────── */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  position: relative;
}

/* ───────── Top Bar ───────── */
.top-bar {
  height: 64px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--color-outline-variant);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10;
}

.top-bar-left {
  display: flex;
  align-items: center;
}

.page-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  color: var(--color-on-surface);
  margin: 0;
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icon-btn {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  border: none;
  background: transparent;
  color: var(--color-on-surface-variant);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.icon-btn:hover {
  background: var(--color-surface-container);
  color: var(--color-on-surface);
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  background: var(--color-primary-container);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
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
  text-decoration: none;
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
  flex: 1;
  overflow-y: auto;
  background: var(--color-background);
}
</style>
