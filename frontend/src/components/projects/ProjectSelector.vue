<template>
  <div class="selector-panel">
    <div class="selector-head">
      <label class="field-label">Projects</label>
      <div class="search-wrap">
        <span class="material-symbols-outlined search-ic">search</span>
        <input
          v-model="search"
          type="text"
          class="search-field"
          placeholder="Search by name or number…"
          autocomplete="off"
        />
      </div>
    </div>

    <div v-if="loading" class="skeleton-list">
      <div v-for="n in 6" :key="n" class="sk-row" />
    </div>
    <div v-else-if="filtered.length === 0" class="empty-msg">
      {{ projects.length === 0 ? 'No projects yet.' : 'No projects found' }}
    </div>
    <ul v-else class="proj-list" role="listbox">
      <li
        v-for="p in filtered"
        :key="p.id"
        role="option"
        :aria-selected="p.id === selectedProjectId"
        :class="['proj-item', { selected: p.id === selectedProjectId }]"
        @click="select(p.id)"
      >
        <span class="dot" :style="{ background: p.color || '#287475' }" />
        <div class="proj-text">
          <span class="proj-line">
            <span class="proj-num">{{ p.project_number }}</span>
            <span class="proj-name">{{ p.name }}</span>
          </span>
          <span class="stage-badge" :class="stageClass(p.current_stage)">{{ p.current_stage || 'N/A' }}</span>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { projectsAPI } from '../../api/projects'

const props = defineProps({
  selectedProjectId: { type: Number, default: null },
})

const emit = defineEmits(['update:selectedProjectId'])

const projects = ref([])
const loading = ref(true)
const search = ref('')

onMounted(async () => {
  loading.value = true
  try {
    const res = await projectsAPI.getProjects()
    projects.value = res.data || []
  } catch (e) {
    console.error(e)
    projects.value = []
  } finally {
    loading.value = false
  }
})

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return projects.value
  return projects.value.filter(
    (p) =>
      (p.name || '').toLowerCase().includes(q) ||
      (p.project_number || '').toLowerCase().includes(q)
  )
})

function select(id) {
  emit('update:selectedProjectId', id)
}

function stageClass(stage) {
  if (!stage) return 'stage-na'
  if (stage === 'Completed') return 'stage-done'
  if (stage === 'Incomplete Beyond Deadline' || stage === 'Halted') return 'stage-warn'
  return 'stage-active'
}
</script>

<style scoped>
.selector-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 360px;
  background: #fff;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.selector-head {
  padding: 16px;
  border-bottom: 1px solid var(--color-outline-variant);
  flex-shrink: 0;
}

.field-label {
  display: block;
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
  margin-bottom: 8px;
}

.search-wrap {
  position: relative;
}

.search-ic {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 18px;
  color: var(--color-on-surface-variant);
  pointer-events: none;
  width: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.search-field {
  width: 100%;
  height: 40px;
  padding: 0 12px 0 36px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  outline: none;
  transition: border 0.15s, box-shadow 0.15s;
}

.search-field:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 1px var(--color-primary);
}

.skeleton-list {
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sk-row {
  height: 52px;
  border-radius: var(--radius-lg);
  background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
  background-size: 200% 100%;
  animation: shimmer 1.2s ease-in-out infinite;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.empty-msg {
  padding: 32px 16px;
  text-align: center;
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface-variant);
}

.proj-list {
  list-style: none;
  margin: 0;
  padding: 8px;
  overflow-y: auto;
  flex: 1;
}

.proj-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease;
  border: 1px solid transparent;
}

.proj-item:hover {
  background: #f1f5f9;
}

.proj-item.selected {
  background: rgba(40, 116, 117, 0.12);
  border-color: var(--color-primary);
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 4px;
}

.proj-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.proj-line {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.proj-num {
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 600;
  color: var(--color-on-surface-variant);
  font-variant-numeric: tabular-nums;
}

.proj-name {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-on-surface);
  line-height: 1.3;
  word-break: break-word;
}

.stage-badge {
  display: inline-block;
  align-self: flex-start;
  padding: 2px 8px;
  border-radius: 2px;
  font-size: 10px;
  font-weight: 600;
  text-transform: capitalize;
}

.stage-active {
  background: #d4edee;
  color: #113b3c;
}
.stage-done {
  background: #dcfce7;
  color: #166534;
}
.stage-warn {
  background: #fef3c7;
  color: #92400e;
}
.stage-na {
  background: #f1f5f9;
  color: #64748b;
}

.material-symbols-outlined {
  font-family: 'Material Symbols Outlined';
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
  overflow: hidden;
  user-select: none;
}
</style>
