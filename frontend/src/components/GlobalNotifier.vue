<template>
  <Teleport to="body">
    <div class="notif-stack" role="status" aria-live="polite">
      <transition-group name="notif">
        <div
          v-for="t in toasts"
          :key="t.id"
          class="notif"
          :class="t.type"
          @click="dismiss(t.id)"
        >
          <span class="notif-icon material-symbols-outlined">{{ iconFor(t.type) }}</span>
          <div class="notif-body">
            <div v-if="t.title" class="notif-title">{{ t.title }}</div>
            <div class="notif-msg">{{ t.message }}</div>
          </div>
          <button class="notif-close" @click.stop="dismiss(t.id)" aria-label="Dismiss">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
      </transition-group>
    </div>
  </Teleport>
</template>

<script setup>
import { useNotifier } from '../stores/notifier'

const { toasts, dismiss } = useNotifier()

const iconFor = (type) => {
  switch (type) {
    case 'success': return 'check_circle'
    case 'error': return 'error'
    case 'warning': return 'warning'
    case 'info':
    default: return 'info'
  }
}
</script>

<style scoped>
.notif-stack {
  position: fixed;
  top: 20px;
  right: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 99999;
  max-width: 380px;
  width: calc(100vw - 40px);
  pointer-events: none;
}

.notif {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 14px 14px 16px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 6px 20px rgba(15,23,42,0.16), 0 1px 3px rgba(15,23,42,0.08);
  border-left: 4px solid;
  cursor: pointer;
  pointer-events: auto;
  font-family: var(--font-body, system-ui);
  transition: transform 0.18s ease;
  position: relative;
}
.notif:hover { transform: translateX(-3px); }

.notif.success { border-color: #059669; }
.notif.error { border-color: #dc2626; }
.notif.warning { border-color: #f59e0b; }
.notif.info { border-color: #287475; }

.notif-icon {
  font-size: 22px;
  flex-shrink: 0;
  margin-top: 1px;
}
.notif.success .notif-icon { color: #059669; }
.notif.error .notif-icon { color: #dc2626; }
.notif.warning .notif-icon { color: #b45309; }
.notif.info .notif-icon { color: #287475; }

.notif-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.notif-title {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.25;
}
.notif-msg {
  font-size: 12.5px;
  font-weight: 500;
  color: #475569;
  line-height: 1.4;
  word-wrap: break-word;
}

.notif-close {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px;
  border-radius: 4px;
  color: #94a3b8;
  flex-shrink: 0;
  margin-top: -1px;
  display: flex;
  align-items: center;
  transition: background 0.15s, color 0.15s;
}
.notif-close:hover { background: #f1f5f9; color: #475569; }
.notif-close .material-symbols-outlined { font-size: 16px; }

/* Stack transitions */
.notif-enter-active, .notif-leave-active { transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1); }
.notif-enter-from { opacity: 0; transform: translateX(20px); }
.notif-leave-to { opacity: 0; transform: translateX(20px); }
.notif-leave-active { position: absolute; right: 0; left: 0; }

@media (max-width: 480px) {
  .notif-stack { top: 12px; right: 12px; left: 12px; max-width: none; }
}
</style>
