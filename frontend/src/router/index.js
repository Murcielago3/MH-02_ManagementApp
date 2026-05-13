import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/',
    name: 'Home',
    redirect: '/login',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false },
  },

  // ── Admin routes ──
  {
    path: '/admin/dashboard',
    name: 'AdminDashboard',
    component: () => import('../views/AdminDashboard.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/admin/employees',
    name: 'AdminEmployees',
    component: () => import('../views/AdminEmployees.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/admin/projects',
    name: 'AdminProjects',
    component: () => import('../views/AdminProjects.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/admin/clients',
    name: 'AdminClients',
    component: () => import('../views/AdminClients.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/admin/expenses',
    name: 'AdminExpenses',
    component: () => import('../views/AdminExpenses.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/admin/tasks',
    name: 'AdminTasks',
    component: () => import('../views/AdminTasks.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/admin/leaves',
    name: 'AdminLeaves',
    component: () => import('../views/AdminLeaves.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/admin/timesheets',
    name: 'AdminTimesheets',
    component: () => import('../views/AdminTimesheets.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/admin/employees/:id',
    name: 'EmployeeProfile',
    component: () => import('../views/EmployeeProfile.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/admin/invoices',
    name: 'AdminInvoices',
    component: () => import('../views/AdminDashboard.vue'), // placeholder
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/admin/estimates',
    name: 'AdminEstimates',
    component: () => import('../views/EstimateView.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/admin/reports',
    name: 'AdminReports',
    component: () => import('../views/AdminDashboard.vue'), // placeholder
    meta: { requiresAuth: true, roles: ['admin'] },
  },

  // ── Project Manager routes ──
  {
    path: '/pm/dashboard',
    name: 'PMDashboard',
    component: () => import('../views/employee/EmployeeDashboard.vue'),
    meta: { requiresAuth: true, roles: ['project_manager'] },
  },
  {
    path: '/pm/employees',
    name: 'PMEmployees',
    component: () => import('../views/employee/EmployeeDashboard.vue'),
    meta: { requiresAuth: true, roles: ['project_manager'] },
  },
  {
    path: '/pm/projects',
    name: 'PMProjects',
    component: () => import('../views/employee/EmployeeDashboard.vue'),
    meta: { requiresAuth: true, roles: ['project_manager'] },
  },

  // ── Employee routes ──
  {
    path: '/employee/dashboard',
    name: 'EmployeeDashboard',
    component: () => import('../views/employee/EmployeeDashboard.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'project_manager', 'employee'] },
  },
  {
    path: '/employee/timesheet',
    name: 'EmployeeTimesheet',
    component: () => import('../views/employee/TimesheetView.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'project_manager', 'employee'] },
  },
  {
    path: '/employee/leaves',
    name: 'EmployeeLeaves',
    component: () => import('../views/employee/LeaveView.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'project_manager', 'employee'] },
  },
  {
    path: '/employee/profile',
    name: 'SelfProfile',
    component: () => import('../views/employee/ProfileView.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'project_manager', 'employee'] },
  },
  {
    path: '/employee/salary',
    name: 'EmployeeSalary',
    component: () => import('../views/employee/SalaryView.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'project_manager', 'employee'] },
  },
  {
    path: '/employee/reimbursements',
    name: 'EmployeeReimbursements',
    component: () => import('../views/employee/ReimbursementView.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'project_manager', 'employee'] },
  },

  // Legacy route
  {
    path: '/employee-management',
    name: 'EmployeeManagement',
    component: () => import('../views/AdminEmployees.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

/**
 * Return the default dashboard path for a given role.
 */
function dashboardForRole(role) {
  switch (role) {
    case 'admin':
      return '/admin/dashboard'
    case 'project_manager':
      return '/pm/dashboard'
    case 'employee':
      return '/employee/dashboard'
    default:
      return '/login'
  }
}

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const isAuthenticated = authStore.isAuthenticated
  const userRole = authStore.role

  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && isAuthenticated) {
    next(dashboardForRole(userRole))
  } else if (to.meta.roles && !to.meta.roles.includes(userRole)) {
    next(dashboardForRole(userRole))
  } else {
    next()
  }
})

export default router
