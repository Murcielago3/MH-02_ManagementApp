<template>
  <div class="app-shell">

    <!-- ── Sidebar ── -->
    <aside class="sidebar" :class="{ open: sidebarOpen }">
      <div class="sidebar-brand">
        <div class="brand-logo">
          <img :src="logoUrl" alt="Studio MH02" class="brand-logo-img" />
        </div>
        <div class="brand-text">
          <span class="brand-name">Studio MH02</span>
          <span class="brand-tag">Employee Portal</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-section">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            :class="['nav-item', { active: isActive(item.path) }]"
          >
            <span
              class="nav-icon material-symbols-outlined"
              :style="isActive(item.path) ? 'font-variation-settings:\'FILL\' 1' : ''"
            >{{ item.icon }}</span>
            <span class="nav-label">{{ item.label }}</span>
            <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
          </router-link>
        </div>
      </nav>

      <!-- Sidebar footer -->
      <div class="sidebar-footer">
        <div class="sidebar-user" @click="showProfileMenu = !showProfileMenu">
          <div class="sidebar-avatar" :style="avatarStyle">
            <span v-if="!avatarUrl">{{ userInitials }}</span>
          </div>
          <div class="sidebar-user-info">
            <span class="sidebar-user-name">{{ currentUser?.name || authStore.user?.name || 'Employee' }}</span>
            <span class="sidebar-user-role">{{ authStore.role }}</span>
          </div>
          <span class="material-symbols-outlined sidebar-user-icon">unfold_more</span>

          <!-- Profile Dropdown -->
          <transition name="dropdown">
            <div v-if="showProfileMenu" class="profile-dropdown" @click.stop>
              <div class="dropdown-user">
                <div class="dropdown-avatar" :style="avatarStyle">
                  <span v-if="!avatarUrl">{{ userInitials }}</span>
                </div>
                <div>
                  <p class="dropdown-name">{{ currentUser?.name || authStore.user?.name || 'Employee' }}</p>
                  <p class="dropdown-role">{{ authStore.role }}</p>
                </div>
              </div>
              <div class="dropdown-sep" />
              <router-link to="/employee/profile" class="dropdown-item" @click="showProfileMenu = false">
                <span class="material-symbols-outlined">person</span>My Profile
              </router-link>
              <div class="dropdown-sep" />
              <button class="dropdown-item danger" @click.stop="handleLogout">
                <span class="material-symbols-outlined">logout</span>Log out
              </button>
            </div>
          </transition>
        </div>
      </div>
    </aside>

    <!-- Mobile backdrop -->
    <div v-if="sidebarOpen" class="sidebar-backdrop" @click="sidebarOpen = false"></div>

    <!-- ── Main area ── -->
    <div class="main-area">

      <!-- Top bar -->
      <header class="top-bar">
        <div class="top-bar-left">
          <button class="hamburger" @click="sidebarOpen = true" aria-label="Open menu">
            <span class="material-symbols-outlined">menu</span>
          </button>
          <h2 class="page-title">{{ currentPageTitle }}</h2>
        </div>
        <div class="top-bar-right">
          <button class="top-icon-btn" title="Notifications">
            <span class="material-symbols-outlined">notifications</span>
          </button>
        </div>
      </header>

      <main class="page-content">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useTimesheetStore } from '../stores/timesheet'
import { usersAPI } from '../api/users'
import { getBrandLogoUrl } from '../utils/logo'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const timesheetStore = useTimesheetStore()
const currentUser = ref(null)
const showProfileMenu = ref(false)
const sidebarOpen = ref(false)
const logoUrl = getBrandLogoUrl()

// Close the mobile drawer whenever the route changes
watch(() => route.path, () => { sidebarOpen.value = false })

const closeProfileMenu = (e) => {
  if (!e.target.closest('.sidebar-user')) {
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
/* ── Shell ── */
.app-shell {
  display: flex;
  min-height: 100vh;
  font-family: var(--font-body);
  background: var(--color-background);
}

/* ── Sidebar ── */
.sidebar {
  width: 248px;
  min-width: 248px;
  height: 100vh;
  position: fixed;
  left: 0; top: 0;
  background: #111827;
  display: flex;
  flex-direction: column;
  z-index: 30;
  border-right: 1px solid rgba(255,255,255,0.04);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 18px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.brand-logo {
  width: 34px; height: 34px;
  border-radius: var(--radius-md);
  overflow: hidden;
  flex-shrink: 0;
  background: var(--color-primary);
}
.brand-logo-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.brand-text { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.brand-name {
  font-family: var(--font-display);
  font-size: 15px; font-weight: 700;
  color: #fff;
  letter-spacing: -0.01em;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.brand-tag {
  font-size: 9px; font-weight: 600;
  text-transform: uppercase; letter-spacing: .1em;
  color: rgba(255,255,255,.35);
}

/* ── Nav ── */
.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: 10px 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.sidebar-nav::-webkit-scrollbar { width: 0; }

.nav-section { padding: 0 10px; display: flex; flex-direction: column; gap: 1px; }

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border-radius: var(--radius-md);
  font-size: 13.5px;
  font-weight: 500;
  color: rgba(255,255,255,.55);
  text-decoration: none;
  background: transparent;
  border: none;
  cursor: pointer;
  width: 100%;
  text-align: left;
  transition: background var(--transition), color var(--transition);
}
.nav-item:hover {
  background: rgba(255,255,255,0.06);
  color: rgba(255,255,255,.85);
}
.nav-item.active {
  background: rgba(40,116,117,0.18);
  color: #fff;
}
.nav-item.active .nav-icon {
  color: var(--color-primary);
}

.nav-icon { font-size: 18px; width: 20px; flex-shrink: 0; color: rgba(255,255,255,.4); }
.nav-item.active .nav-icon { color: var(--color-primary); }
.nav-label { flex: 1; }

.nav-badge {
  background: var(--color-error);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: var(--radius-full);
  line-height: 1;
  min-width: 18px;
  text-align: center;
}

/* ── Sidebar footer ── */
.sidebar-footer {
  border-top: 1px solid rgba(255,255,255,0.06);
  padding: 12px 10px;
  position: relative;
}
.sidebar-user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition);
  position: relative;
}
.sidebar-user:hover { background: rgba(255,255,255,.06); }
.sidebar-avatar {
  width: 30px; height: 30px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700;
  flex-shrink: 0;
}
.sidebar-user-info { flex: 1; min-width: 0; }
.sidebar-user-name {
  font-size: 12.5px; font-weight: 600;
  color: rgba(255,255,255,.85);
  display: block;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.sidebar-user-role {
  font-size: 10px; color: rgba(255,255,255,.35);
  text-transform: capitalize;
}
.sidebar-user-icon { font-size: 16px; color: rgba(255,255,255,.3); }

/* ── Profile dropdown (from footer) ── */
.profile-dropdown {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 0;
  right: 0;
  width: 220px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-xl);
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  z-index: 200;
  overflow: hidden;
}
.dropdown-user {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 16px;
  background: var(--color-surface-dim);
}
.dropdown-avatar {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700;
  flex-shrink: 0;
}
.dropdown-name { font-size: 13px; font-weight: 700; color: var(--color-on-surface); margin: 0; }
.dropdown-role { font-size: 10px; color: var(--color-on-surface-variant); text-transform: capitalize; margin: 2px 0 0; }
.dropdown-sep { height: 1px; background: var(--color-outline); }
.dropdown-item {
  display: flex; align-items: center; gap: 10px;
  padding: 11px 16px;
  font-size: 13px; font-weight: 500;
  color: var(--color-on-surface);
  background: none; border: none;
  cursor: pointer; width: 100%; text-align: left;
  text-decoration: none;
  transition: background var(--transition);
}
.dropdown-item:hover { background: var(--color-surface-dim); }
.dropdown-item .material-symbols-outlined { font-size: 17px; color: var(--color-on-surface-variant); }
.dropdown-item.danger { color: var(--color-error); }
.dropdown-item.danger .material-symbols-outlined { color: var(--color-error); }

.dropdown-enter-active, .dropdown-leave-active { transition: opacity .14s, transform .14s; }
.dropdown-enter-from, .dropdown-leave-to { opacity: 0; transform: translateY(6px); }

/* ── Main area ── */
.main-area {
  flex: 1;
  margin-left: 248px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-width: 0;
  width: calc(100% - 248px);
  max-width: calc(100% - 248px);
}

/* ── Top bar ── */
.top-bar {
  height: 56px;
  position: fixed;
  top: 0; right: 0; left: 248px;
  z-index: 20;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-outline);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  gap: 16px;
}
.top-bar-left { display: flex; align-items: center; }
.page-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  color: var(--color-on-surface);
  margin: 0;
  letter-spacing: -0.01em;
}
.top-bar-right { display: flex; align-items: center; gap: 4px; }

.top-icon-btn {
  width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-on-surface-variant);
  cursor: pointer;
  transition: background var(--transition), color var(--transition);
}
.top-icon-btn:hover { background: var(--color-surface-dim); color: var(--color-on-surface); }
.top-icon-btn .material-symbols-outlined { font-size: 20px; }

/* ── Page content ── */
.page-content {
  margin-top: 56px;
  padding: 28px 32px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-width: 0;
  max-width: 100%;
}

/* ── Hamburger + mobile drawer ── */
.hamburger {
  display: none;
  width: 38px; height: 38px;
  align-items: center; justify-content: center;
  background: transparent; border: none;
  border-radius: var(--radius-md);
  color: var(--color-on-surface); cursor: pointer;
  flex-shrink: 0;
}
.hamburger:hover { background: var(--color-surface-container); }
.hamburger .material-symbols-outlined { font-size: 24px; }

.sidebar-backdrop {
  position: fixed; inset: 0;
  background: rgba(15, 23, 42, 0.5);
  z-index: 35;
}

@media (max-width: 900px) {
  .sidebar {
    transform: translateX(-100%);
    transition: transform 0.25s ease;
    z-index: 40;
    box-shadow: 0 0 40px rgba(0, 0, 0, 0.35);
  }
  .sidebar.open { transform: translateX(0); }

  .main-area {
    margin-left: 0;
    width: 100%;
    max-width: 100%;
  }
  .top-bar { left: 0; padding: 0 12px; }
  .hamburger { display: flex; }
  .page-content { padding: 16px 14px; gap: 16px; }
}
</style>
