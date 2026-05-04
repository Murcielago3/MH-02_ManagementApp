<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Navigation -->
    <nav class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center text-white">
            <i class="pi pi-building text-lg"></i>
          </div>
          <h1 class="text-xl font-bold text-gray-900">Studio MH02</h1>
        </div>
        <button
          @click="handleLogout"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition"
        >
          Logout
        </button>
      </div>
    </nav>

    <main class="max-w-7xl mx-auto px-6 py-12">
      <!-- Welcome Card -->
      <div
        class="mb-8 rounded-lg border border-gray-200 overflow-hidden shadow-sm"
        style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
      >
        <div class="p-8 text-white">
          <h2 class="text-3xl font-bold mb-2">Welcome to Studio MH02</h2>
          <p class="text-white/80 text-lg">Management Application v4.8 • Ready to elevate your projects</p>
        </div>
      </div>

      <!-- Main Content Card -->
      <div class="bg-white rounded-lg border border-gray-200 shadow-sm p-8 mb-8">
        <p class="text-gray-700 mb-6">
          You have successfully logged in to the Studio MH02 management system. Your workspace is ready for use.
        </p>

        <!-- Feature Cards Grid -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <!-- Projects Card -->
          <div class="rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
            <div class="bg-blue-50 p-6 flex items-center justify-center h-32">
              <i class="pi pi-briefcase text-5xl text-blue-600"></i>
            </div>
            <div class="p-6">
              <h3 class="font-semibold text-gray-900 mb-1 text-lg">Projects</h3>
              <p class="text-gray-600 text-sm">Manage your architectural projects and assignments</p>
            </div>
          </div>

          <!-- Team Card -->
          <div class="rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
            <div class="bg-green-50 p-6 flex items-center justify-center h-32">
              <i class="pi pi-users text-5xl text-green-600"></i>
            </div>
            <div class="p-6">
              <h3 class="font-semibold text-gray-900 mb-1 text-lg">Team Members</h3>
              <p class="text-gray-600 text-sm">View and collaborate with your team members</p>
            </div>
          </div>

          <!-- Analytics Card -->
          <div class="rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
            <div class="bg-purple-50 p-6 flex items-center justify-center h-32">
              <i class="pi pi-chart-bar text-5xl text-purple-600"></i>
            </div>
            <div class="p-6">
              <h3 class="font-semibold text-gray-900 mb-1 text-lg">Analytics</h3>
              <p class="text-gray-600 text-sm">View project analytics and performance reports</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Stats -->
      <div class="bg-white rounded-lg border border-gray-200 shadow-sm p-8">
        <h3 class="text-lg font-semibold text-gray-900 mb-6">Quick Stats</h3>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div class="text-center p-6 bg-blue-50 rounded-lg border border-blue-100">
            <div class="text-4xl font-bold text-blue-600 mb-2">12</div>
            <div class="text-sm font-medium text-gray-600">Active Projects</div>
          </div>
          <div class="text-center p-6 bg-green-50 rounded-lg border border-green-100">
            <div class="text-4xl font-bold text-green-600 mb-2">45</div>
            <div class="text-sm font-medium text-gray-600">Team Members</div>
          </div>
          <div class="text-center p-6 bg-purple-50 rounded-lg border border-purple-100">
            <div class="text-4xl font-bold text-purple-600 mb-2">8</div>
            <div class="text-sm font-medium text-gray-600">Completed Projects</div>
          </div>
          <div class="text-center p-6 bg-amber-50 rounded-lg border border-amber-100">
            <div class="text-4xl font-bold text-amber-600 mb-2">92%</div>
            <div class="text-sm font-medium text-gray-600">On-time Delivery</div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const handleLogout = () => {
  authStore.clearAuth()
  router.push('/login')
}
</script>
