<template>
  <Teleport to="body">
    <transition name="toast-fade">
      <div v-if="visible" class="toast-container" :class="type">
        <span class="material-symbols-outlined toast-icon">{{ icon }}</span>
        <span class="toast-message">{{ message }}</span>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  message: { type: String, default: '' },
  type: { type: String, default: 'success' }, // success | error
  duration: { type: Number, default: 3000 },
})

const emit = defineEmits(['done'])
const visible = ref(false)

const icon = computed(() => props.type === 'success' ? 'check_circle' : 'error')

watch(() => props.message, (val) => {
  if (val) {
    visible.value = true
    setTimeout(() => {
      visible.value = false
      emit('done')
    }, props.duration)
  }
}, { immediate: true })
</script>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  z-index: 9999;
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
  pointer-events: none;
}
.toast-container.success { background: #059669; }
.toast-container.error { background: #dc2626; }
.toast-icon { font-size: 20px; }
.toast-fade-enter-active, .toast-fade-leave-active { transition: opacity 0.3s, transform 0.3s; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(16px); }
</style>
