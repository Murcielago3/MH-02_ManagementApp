<template>
  <AppLayout>
    <div class="page-header">
      <div>
        <h1 class="page-title">Projects</h1>
        <p class="page-sub">Manage stage subtasks - add them, set deadlines, and mark them complete.</p>
      </div>
      <button class="refresh-btn" @click="reload" :disabled="loading">
        <span class="material-symbols-outlined">refresh</span> Refresh
      </button>
    </div>

    <div class="pm-layout">
      <!-- Project picker -->
      <aside class="pm-list">
        <div class="search-wrap">
          <span class="material-symbols-outlined search-icon">search</span>
          <input v-model="search" type="text" class="search-input" placeholder="Search projects…" />
        </div>

        <div v-if="loading" class="msg">Loading projects…</div>
        <div v-else-if="!filtered.length" class="msg">No projects found.</div>

        <button
          v-for="p in filtered"
          :key="p.id"
          type="button"
          class="pm-item"
          :class="{ active: selectedId === p.id }"
          @click="select(p.id)"
        >
          <span class="dot" :style="{ background: p.color || '#287475' }"></span>
          <span class="pm-item-body">
            <span class="pm-name">{{ p.name }}</span>
            <span class="pm-num">{{ p.project_number }}</span>
          </span>
          <span v-if="counts[p.id]" class="pm-badge" :class="{ all: counts[p.id].open === 0 }">
            {{ counts[p.id].open }} open
          </span>
        </button>
      </aside>

      <!-- Stages + subtasks -->
      <section class="pm-detail">
        <div v-if="!selectedId" class="empty-panel">
          <span class="material-symbols-outlined">flag</span>
          <p>Select a project to see its stages and subtasks.</p>
        </div>

        <template v-else>
          <div class="detail-head">
            <div>
              <h2 class="detail-name">{{ selectedProject?.name }}</h2>
              <p class="detail-num">{{ selectedProject?.project_number }}</p>
            </div>
            <div v-if="stageData" class="overall">
              <span class="overall-val">{{ overallPercent }}%</span>
              <span class="overall-lbl">subtasks done</span>
            </div>
          </div>

          <div v-if="stageData" class="pm-note">
            <span class="material-symbols-outlined">info</span>
            Stages and their percentages are set by an admin. You can add, edit and
            complete the subtasks inside each stage.
          </div>

          <div v-if="stagesLoading" class="msg">Loading stages…</div>
          <ProjectStagesEditor
            v-else-if="stageData"
            :data="stageData"
            :can-edit-stages="false"
            :can-edit-subtasks="true"
            @changed="loadStages"
          />
          <div v-else class="msg">Could not load stages for this project.</div>
        </template>
      </section>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import AppLayout from '../../components/AppLayout.vue'
import ProjectStagesEditor from '../../components/ProjectStagesEditor.vue'
import { projectsAPI } from '../../api/projects'
import { stagesAPI } from '../../api/stages'

const projects = ref([])
const loading = ref(true)
const search = ref('')
const selectedId = ref(null)
const stageData = ref(null)
const stagesLoading = ref(false)
// { projectId: { open, total } } so the list shows where work is outstanding.
const counts = ref({})

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  const list = q
    ? projects.value.filter(p =>
        (p.name || '').toLowerCase().includes(q) ||
        (p.project_number || '').toLowerCase().includes(q))
    : projects.value
  // Projects with open subtasks first - that's what a PM is here to clear.
  return [...list].sort((a, b) => (counts.value[b.id]?.open || 0) - (counts.value[a.id]?.open || 0))
})

const selectedProject = computed(() => projects.value.find(p => p.id === selectedId.value) || null)

const overallPercent = computed(() => {
  const stages = stageData.value?.stages || []
  const total = stages.reduce((s, x) => s + x.subtask_total, 0)
  const done = stages.reduce((s, x) => s + x.subtask_completed, 0)
  return total ? Math.round(done / total * 100) : 0
})

async function loadProjects() {
  loading.value = true
  try {
    const { data } = await projectsAPI.getProjects()
    projects.value = data || []
    // Fetch open-subtask counts in parallel so the list is informative.
    const results = await Promise.all(
      projects.value.map(p =>
        stagesAPI.listSubtasks(p.id).then(r => [p.id, r.data || []]).catch(() => [p.id, []])
      )
    )
    const map = {}
    for (const [pid, subs] of results) {
      if (!subs.length) continue
      map[pid] = { open: subs.filter(s => s.status !== 'completed').length, total: subs.length }
    }
    counts.value = map
  } catch (e) {
    projects.value = []
  } finally {
    loading.value = false
  }
}

async function loadStages() {
  if (!selectedId.value) { stageData.value = null; return }
  stagesLoading.value = true
  try {
    const { data } = await stagesAPI.list(selectedId.value)
    stageData.value = data
  } catch (e) {
    stageData.value = null
  } finally {
    stagesLoading.value = false
  }
  // Keep the sidebar's open-count in step with what was just changed.
  try {
    const { data: subs } = await stagesAPI.listSubtasks(selectedId.value)
    counts.value = {
      ...counts.value,
      [selectedId.value]: { open: subs.filter(s => s.status !== 'completed').length, total: subs.length },
    }
  } catch (e) { /* count is cosmetic */ }
}

function select(id) {
  selectedId.value = id
  loadStages()
}

async function reload() {
  await loadProjects()
  if (selectedId.value) await loadStages()
}

onMounted(loadProjects)
</script>

<style scoped>
.page-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  gap: 12px; margin-bottom: 20px; flex-wrap: wrap;
}
.page-title { font-family: var(--font-display); font-size: 24px; font-weight: 800; margin: 0; color: var(--color-on-surface); }
.page-sub { font-size: 13px; color: var(--color-on-surface-variant); margin: 2px 0 0; }
.refresh-btn {
  display: inline-flex; align-items: center; gap: 6px; padding: 9px 16px;
  border: 1px solid var(--color-outline); border-radius: var(--radius-lg);
  background: var(--color-surface); font-size: 13px; font-weight: 600; cursor: pointer;
  color: var(--color-on-surface-variant);
}
.refresh-btn .material-symbols-outlined { font-size: 17px; }

.pm-layout { display: grid; grid-template-columns: 300px 1fr; gap: 16px; align-items: start; }

/* Project list */
.pm-list {
  display: flex; flex-direction: column; gap: 6px;
  background: var(--color-surface); border: 1px solid var(--color-outline);
  border-radius: var(--radius-xl); padding: 12px; max-height: 74vh; overflow-y: auto;
}
.search-wrap { position: relative; display: flex; align-items: center; margin-bottom: 4px; }
.search-icon { position: absolute; left: 10px; font-size: 17px; color: var(--color-on-surface-variant); pointer-events: none; }
.search-input {
  width: 100%; padding: 8px 12px 8px 34px; border: 1px solid var(--color-outline);
  border-radius: var(--radius-md); font-size: 13px; outline: none;
  background: var(--color-surface-dim, #f8fafc); color: var(--color-on-surface);
}
.search-input:focus { border-color: var(--color-primary); background: var(--color-surface); }

.pm-item {
  display: flex; align-items: center; gap: 9px; width: 100%; text-align: left;
  padding: 10px; border: 1px solid transparent; border-radius: var(--radius-lg);
  background: none; cursor: pointer;
}
.pm-item:hover { background: var(--color-surface-dim, #f8fafc); }
.pm-item.active { background: var(--color-primary-light, #e6f0f0); border-color: var(--color-primary); }
.dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.pm-item-body { display: flex; flex-direction: column; min-width: 0; flex: 1; }
.pm-name { font-size: 13px; font-weight: 700; color: var(--color-on-surface); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pm-num { font-size: 11px; color: var(--color-on-surface-variant); }
.pm-badge {
  font-size: 10px; font-weight: 800; padding: 2px 7px; border-radius: 999px;
  background: #fef3c7; color: #92400e; white-space: nowrap;
}
.pm-badge.all { background: #dcfce7; color: #166534; }

/* Detail */
.pm-detail {
  background: var(--color-surface); border: 1px solid var(--color-outline);
  border-radius: var(--radius-xl); padding: 18px; min-height: 320px;
}
.detail-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 12px; }
.detail-name { font-size: 18px; font-weight: 800; margin: 0; color: var(--color-on-surface); }
.detail-num { font-size: 12px; color: var(--color-on-surface-variant); margin: 2px 0 0; }
.overall { text-align: right; }
.overall-val { display: block; font-size: 24px; font-weight: 800; color: var(--color-primary); line-height: 1; }
.overall-lbl { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; color: var(--color-on-surface-variant); }

.pm-note {
  display: flex; align-items: center; gap: 8px; margin-bottom: 14px;
  padding: 9px 13px; background: var(--color-surface-dim, #f8fafc);
  border: 1px solid var(--color-outline); border-radius: var(--radius-md);
  font-size: 12px; color: var(--color-on-surface-variant);
}
.pm-note .material-symbols-outlined { font-size: 16px; color: var(--color-primary); }

.empty-panel {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 8px; padding: 60px 20px; color: var(--color-on-surface-variant);
}
.empty-panel .material-symbols-outlined { font-size: 38px; opacity: .4; }
.empty-panel p { margin: 0; font-size: 13px; }
.msg { font-size: 13px; color: var(--color-on-surface-variant); font-style: italic; padding: 16px 4px; }

@media (max-width: 900px) {
  .pm-layout { grid-template-columns: 1fr; }
  .pm-list { max-height: 300px; }
}
</style>
