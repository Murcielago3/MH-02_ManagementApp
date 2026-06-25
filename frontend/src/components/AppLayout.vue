<template>
  <div class="app-shell">

    <!-- ── Sidebar ── -->
    <aside class="sidebar" :class="{ open: sidebarOpen }">
      <div class="sidebar-brand">
        <div class="brand-logo">
          <img :src="logoUrl" alt="Studio MH02" class="brand-logo-img" />
        </div>
        <div class="brand-text">
          <span class="brand-name">{{ brandName }}</span>
          <span class="brand-tag">Enterprise ERP</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <!-- Top items -->
        <div class="nav-section">
          <router-link
            v-for="item in navItemsTop"
            :key="item.path"
            :to="item.path"
            :class="['nav-item', { active: isActive(item.path) }]"
          >
            <span class="nav-icon material-symbols-outlined"
              :style="isActive(item.path) ? 'font-variation-settings:\'FILL\' 1' : ''">
              {{ item.icon }}
            </span>
            <span class="nav-label">{{ item.label }}</span>
          </router-link>
        </div>

        <div class="nav-divider" />

        <!-- Projects group -->
        <div class="nav-section">
          <button
            class="nav-item"
            :class="{ active: isProjectsSectionActive }"
            @click="toggleProjects"
          >
            <span class="nav-icon material-symbols-outlined"
              :style="isProjectsSectionActive ? 'font-variation-settings:\'FILL\' 1' : ''">
              architecture
            </span>
            <span class="nav-label">Projects</span>
            <span class="nav-chevron material-symbols-outlined">
              {{ subNavVisible ? 'expand_less' : 'expand_more' }}
            </span>
          </button>
          <transition name="subnav">
            <div v-show="subNavVisible" class="nav-subitems">
              <router-link
                v-for="sub in projectSubNav"
                :key="sub.path"
                :to="sub.path"
                :class="['nav-sub', { active: isSubActive(sub.path) }]"
              >
                <span class="sub-dot" />
                {{ sub.label }}
              </router-link>
            </div>
          </transition>
        </div>

        <div class="nav-divider" />

        <!-- Bottom items -->
        <div class="nav-section">
          <router-link
            v-for="item in navItemsBottom"
            :key="item.path"
            :to="item.path"
            :class="['nav-item', { active: isActive(item.path) }]"
          >
            <span class="nav-icon material-symbols-outlined"
              :style="isActive(item.path) ? 'font-variation-settings:\'FILL\' 1' : ''">
              {{ item.icon }}
            </span>
            <span class="nav-label">{{ item.label }}</span>
          </router-link>
        </div>
      </nav>

      <!-- Sidebar footer -->
      <div class="sidebar-footer">
        <div class="sidebar-user" @click="goToSettings">
          <div class="sidebar-avatar">{{ userInitials }}</div>
          <div class="sidebar-user-info">
            <span class="sidebar-user-name">{{ currentUser?.name || 'Admin' }}</span>
            <span class="sidebar-user-role">{{ authStore.role }}</span>
          </div>
          <span class="material-symbols-outlined sidebar-user-icon">settings</span>
        </div>
      </div>
    </aside>

    <!-- Mobile backdrop -->
    <div v-if="sidebarOpen" class="sidebar-backdrop" @click="sidebarOpen = false"></div>

    <!-- ── Main area ── -->
    <div class="main-area">

      <!-- Top bar -->
      <header class="top-bar">
        <button class="hamburger" @click="sidebarOpen = true" aria-label="Open menu">
          <span class="material-symbols-outlined">menu</span>
        </button>
        <div class="top-bar-search">
          <span class="material-symbols-outlined search-icon">search</span>
          <input type="text" placeholder="Search anything…" class="search-field" />
        </div>
        <div class="top-bar-right">
          <button class="top-icon-btn" title="Notifications">
            <span class="material-symbols-outlined">notifications</span>
          </button>
          <button class="top-icon-btn" title="Help">
            <span class="material-symbols-outlined">help_outline</span>
          </button>
          <div class="top-avatar-wrap" @click.stop="showProfileMenu = !showProfileMenu">
            <div class="top-avatar">{{ userInitials }}</div>
            <transition name="dropdown">
              <div v-if="showProfileMenu" class="profile-dropdown">
                <div class="dropdown-user">
                  <div class="dropdown-avatar">{{ userInitials }}</div>
                  <div>
                    <p class="dropdown-name">{{ currentUser?.name || authStore.user?.name || 'Admin' }}</p>
                    <p class="dropdown-role">{{ authStore.role }}</p>
                  </div>
                </div>
                <div class="dropdown-sep" />
                <router-link to="/employee/profile" class="dropdown-item" @click="showProfileMenu = false">
                  <span class="material-symbols-outlined">person</span>My Profile
                </router-link>
                <button class="dropdown-item" @click="goToSettings; showProfileMenu = false">
                  <span class="material-symbols-outlined">settings</span>Settings
                </button>
                <div class="dropdown-sep" />
                <button class="dropdown-item danger" @click.stop="handleLogout">
                  <span class="material-symbols-outlined">logout</span>Log out
                </button>
              </div>
            </transition>
          </div>
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
import { usersAPI } from '../api/users'
import { getBrandLogoUrl } from '../utils/logo'

const route     = useRoute()
const router    = useRouter()
const authStore = useAuthStore()
const currentUser     = ref(null)
const showProfileMenu = ref(false)
const projectsExpanded = ref(false)
const sidebarOpen     = ref(false)

const logoUrl = getBrandLogoUrl()

const brandName = computed(() => {
  if (currentUser.value?.name) return currentUser.value.name
  if (authStore.user?.name)    return authStore.user.name
  return 'Studio MH02'
})

const userInitials = computed(() => {
  const name = currentUser.value?.name || authStore.user?.name || 'Admin'
  return name.split(' ').map((p) => p[0]).join('').toUpperCase().slice(0, 2)
})

const closeMenu = (e) => {
  if (!e.target.closest('.top-avatar-wrap')) showProfileMenu.value = false
}

onMounted(async () => {
  document.addEventListener('click', closeMenu)
  if (!authStore.isAuthenticated) return
  try { currentUser.value = (await usersAPI.getMe()).data } catch {}
})
onUnmounted(() => document.removeEventListener('click', closeMenu))

const handleLogout = () => {
  showProfileMenu.value = false
  authStore.clearAuth()
  router.push('/login')
}
const goToSettings = () => router.push('/admin/settings')

const navItemsTop = [
  { path: '/admin/dashboard', icon: 'dashboard',  label: 'Dashboard' },
  { path: '/admin/employees', icon: 'group',       label: 'Employees' },
]

const projectSubNav = [
  { path: '/admin/projects',         label: 'All Projects' },
  { path: '/admin/projects/reports', label: 'Reports' },
]

const navItemsBottom = [
  { path: '/admin/clients',    icon: 'handshake',       label: 'Clients' },
  { path: '/admin/tasks',      icon: 'task_alt',        label: 'Tasks' },
  { path: '/admin/leaves',     icon: 'event_busy',      label: 'Leaves' },
  { path: '/admin/timesheets', icon: 'pending_actions', label: 'Timesheets' },
  { path: '/employee/timesheet', icon: 'schedule',        label: 'My Timesheet' },
  { path: '/admin/expenses',        icon: 'payments',        label: 'Expenses' },
  { path: '/admin/reimbursements', icon: 'request_quote',   label: 'Reimbursements' },
  { path: '/admin/salary-slips',   icon: 'paid',            label: 'Salary Slips' },
  { path: '/admin/invoices',       icon: 'receipt_long',    label: 'Invoices' },
  { path: '/admin/estimates',  icon: 'calculate',       label: 'Estimates' },
]

watch(() => route.path, (p) => {
  projectsExpanded.value = p.startsWith('/admin/projects')
  sidebarOpen.value = false   // close the mobile drawer on navigation
}, { immediate: true })

const isProjectsSectionActive = computed(() => route.path.startsWith('/admin/projects'))
const subNavVisible = computed(() => projectsExpanded.value || isProjectsSectionActive.value)

function isActive(path)    { return route.path === path }
function isSubActive(path) { return route.path === path }
function toggleProjects()  { projectsExpanded.value = !projectsExpanded.value }
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
  background: var(--color-sidebar-bg);
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
  border-bottom: 1px solid var(--color-sidebar-border);
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

.nav-divider {
  height: 1px;
  background: var(--color-sidebar-border);
  margin: 8px 18px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border-radius: var(--radius-md);
  font-size: 13.5px;
  font-weight: 500;
  color: var(--color-sidebar-text);
  text-decoration: none;
  background: transparent;
  border: none;
  cursor: pointer;
  width: 100%;
  text-align: left;
  transition: background var(--transition-fast), color var(--transition-fast);
}
.nav-item:hover {
  background: rgba(255,255,255,0.06);
  color: var(--color-sidebar-text-hover);
}
.nav-item.active {
  background: var(--color-sidebar-active-bg);
  color: var(--color-sidebar-active-text);
}

.nav-icon { font-size: 18px; width: 20px; flex-shrink: 0; }
.nav-label { flex: 1; }
.nav-chevron { font-size: 16px; opacity: .6; }

/* Subnav */
.nav-subitems {
  padding: 2px 0 4px 30px;
  display: flex; flex-direction: column; gap: 1px;
}
.nav-sub {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  border-radius: var(--radius);
  font-size: 12.5px;
  font-weight: 500;
  color: rgba(255,255,255,.45);
  text-decoration: none;
  transition: color var(--transition-fast), background var(--transition-fast);
}
.nav-sub:hover { color: rgba(255,255,255,.85); background: rgba(255,255,255,.04); }
.nav-sub.active { color: #fff; font-weight: 600; }
.sub-dot {
  width: 5px; height: 5px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
  opacity: .6;
}
.nav-sub.active .sub-dot { opacity: 1; background: var(--color-primary); }

/* Subnav transition */
.subnav-enter-active, .subnav-leave-active { transition: opacity .15s, transform .15s; }
.subnav-enter-from, .subnav-leave-to { opacity: 0; transform: translateY(-4px); }

/* ── Sidebar footer ── */
.sidebar-footer {
  border-top: 1px solid var(--color-sidebar-border);
  padding: 12px 10px;
}
.sidebar-user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-fast);
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
.top-bar-search {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--color-background);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-full);
  padding: 6px 14px;
  width: 260px;
  transition: border-color var(--transition-fast);
}
.top-bar-search:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(40,116,117,.10);
}
.search-icon { font-size: 16px; color: var(--color-on-surface-variant); flex-shrink: 0; }
.search-field {
  background: transparent;
  border: none;
  font-size: 13px;
  color: var(--color-on-surface);
  width: 100%;
  padding: 0;
  box-shadow: none !important;
}
.search-field::placeholder { color: var(--color-on-surface-variant); }

.top-bar-right { display: flex; align-items: center; gap: 4px; }

.top-icon-btn {
  width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-on-surface-variant);
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast);
}
.top-icon-btn:hover { background: var(--color-surface-container); color: var(--color-on-surface); }
.top-icon-btn .material-symbols-outlined { font-size: 20px; }

.top-avatar-wrap { position: relative; margin-left: 6px; }
.top-avatar {
  width: 34px; height: 34px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; letter-spacing: .04em;
  cursor: pointer;
  border: 2px solid var(--color-primary-light);
  transition: box-shadow var(--transition-fast);
}
.top-avatar:hover { box-shadow: 0 0 0 3px rgba(40,116,117,.20); }

/* ── Profile dropdown ── */
.profile-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 230px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
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
  transition: background var(--transition-fast);
}
.dropdown-item:hover { background: var(--color-surface-dim); }
.dropdown-item .material-symbols-outlined { font-size: 17px; color: var(--color-on-surface-variant); }
.dropdown-item.danger { color: var(--color-error); }
.dropdown-item.danger .material-symbols-outlined { color: var(--color-error); }

.dropdown-enter-active, .dropdown-leave-active { transition: opacity .14s, transform .14s; }
.dropdown-enter-from, .dropdown-leave-to { opacity: 0; transform: translateY(-6px); }

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
  .top-bar-search { display: none; }   /* declutter; search is non-functional */
  .hamburger { display: flex; }
  .page-content { padding: 16px 14px; gap: 16px; }
}
</style>
