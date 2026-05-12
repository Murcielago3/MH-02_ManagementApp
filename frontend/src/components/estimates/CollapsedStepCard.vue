<template>
  <div class="collapsed-card" @click="$emit('edit')">
    <div class="card-left">
      <div class="card-step-badge">
        <span class="material-symbols-outlined check-sm">check_circle</span>
        Step {{ stepNumber }}
      </div>
      <div class="card-title">{{ title }}</div>
    </div>
    <div class="card-right">
      <div class="card-summary">{{ summary }}</div>
      <button class="edit-pill" @click.stop="$emit('edit')">
        <span class="material-symbols-outlined">edit</span>
        Edit
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  stepNumber: { type: Number, required: true },
  title: { type: String, required: true },
  summary: { type: String, required: true },
})

defineEmits(['edit'])
</script>

<style scoped>
.collapsed-card {
  background: #ffffff;
  border: 1px solid var(--color-surface-container-high);
  border-left: 3px solid var(--color-primary);
  border-radius: var(--radius-lg);
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  cursor: pointer;
  transition: background 0.15s, box-shadow 0.15s;
  margin-bottom: 8px;
}

.collapsed-card:hover {
  background: var(--color-background);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.card-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.card-step-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-primary);
}

.check-sm {
  font-size: 14px;
}

.card-title {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-on-surface);
}

.card-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.card-summary {
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface-variant);
  font-variant-numeric: tabular-nums;
}

.edit-pill {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius);
  background: #ffffff;
  color: var(--color-on-surface-variant);
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.edit-pill:hover {
  background: var(--color-surface-container);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.edit-pill .material-symbols-outlined {
  font-size: 14px;
}
</style>
