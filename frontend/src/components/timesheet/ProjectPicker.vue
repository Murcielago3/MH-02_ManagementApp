<template>
  <div class="project-picker">
    <div class="search-box">
      <span class="material-symbols-outlined search-icon">search</span>
      <input 
        v-model="searchQuery" 
        type="text" 
        placeholder="Filter projects..."
        class="search-input"
      />
    </div>
    
    <div class="pills-container">
      <button
        v-for="project in filteredProjects"
        :key="project.id"
        type="button"
        class="project-pill"
        :class="{ selected: selectedIds.includes(project.id), disabled: readOnly }"
        @click="toggleSelection(project.id)"
        :disabled="readOnly"
      >
        <span class="project-dot" :style="{ background: project.color || '#287475' }"></span>
        <span class="project-name">{{ project.name }}</span>
        <span v-if="selectedIds.includes(project.id) && !readOnly" class="material-symbols-outlined check-icon">check</span>
      </button>
      
      <div v-if="filteredProjects.length === 0" class="no-projects">
        No projects match your search.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  projects: { type: Array, required: true },
  modelValue: { type: Array, default: () => [] },
  readOnly: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue'])

const searchQuery = ref('')

const filteredProjects = computed(() => {
  if (!searchQuery.value) return props.projects
  const q = searchQuery.value.toLowerCase()
  return props.projects.filter(p => p.name.toLowerCase().includes(q))
})

const selectedIds = computed(() => props.modelValue)

function toggleSelection(id) {
  if (props.readOnly) return
  const newSelected = [...selectedIds.value]
  const index = newSelected.indexOf(id)
  if (index > -1) {
    newSelected.splice(index, 1)
  } else {
    newSelected.push(id)
  }
  emit('update:modelValue', newSelected)
}
</script>

<style scoped>
.project-picker {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.search-box {
  position: relative;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-on-surface-variant);
  font-size: 18px;
}

.search-input {
  width: 100%;
  padding: 10px 12px 10px 36px;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-on-surface);
  background: var(--color-surface);
  box-sizing: border-box;
}

.search-input:focus {
  border-color: var(--color-primary);
  outline: none;
}

.pills-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
  padding: 4px;
}

.project-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border: 1px solid var(--color-outline-variant);
  border-radius: 99px;
  background: var(--color-surface);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-surface);
  cursor: pointer;
  transition: all 0.2s;
}

.project-pill:not(.disabled):hover {
  background: var(--color-surface-container);
}

.project-pill.selected {
  background: rgba(40, 116, 117, 0.1);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.project-pill.disabled {
  cursor: default;
  opacity: 0.8;
}

.project-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.check-icon {
  font-size: 14px;
  color: var(--color-primary);
}

.no-projects {
  font-size: 13px;
  color: var(--color-on-surface-variant);
  font-style: italic;
  padding: 8px;
}
</style>
