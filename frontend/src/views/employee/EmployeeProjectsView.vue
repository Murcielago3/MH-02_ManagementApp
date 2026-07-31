<template>
  <EmployeeLayout>
    <div class="page-header">
      <h1 class="page-title">Projects</h1>
      <p class="page-sub">All projects in the studio. Click one to view your team members.</p>
    </div>

    <div v-if="loading" class="empty">Loading projects…</div>
    <div v-else-if="!projects.length" class="empty">No projects yet.</div>

    <div v-else class="proj-grid">
      <button
        v-for="p in projects"
        :key="p.id"
        type="button"
        class="proj-card"
        @click="openTeam(p)"
      >
        <span class="color-strip" :style="{ background: p.color || '#B5EAD7' }"></span>
        <div class="proj-info">
          <div class="proj-num">{{ p.project_number }}</div>
          <div class="proj-name">{{ p.name }}</div>
          <div class="proj-meta">
            <span v-if="p.current_stage" class="stage">{{ p.current_stage }}</span>
            <span v-if="p.year" class="year">{{ p.year }}</span>
          </div>
        </div>
        <span class="material-symbols-outlined chev">chevron_right</span>
      </button>
    </div>

    <!-- Team Members modal -->
    <Teleport to="body">
      <div v-if="teamModalOpen" class="modal-backdrop">
        <div class="modal">
          <div class="modal-head">
            <div>
              <h3 class="modal-title">{{ selectedProject?.name }}</h3>
              <p class="modal-sub">{{ selectedProject?.project_number }}</p>
            </div>
            <button type="button" class="modal-close" @click="closeTeam">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>

          <div class="m-tabs">
            <button type="button" class="m-tab" :class="{ active: modalTab === 'stages' }" @click="modalTab = 'stages'">
              <span class="material-symbols-outlined">flag</span> Stages
            </button>
            <button type="button" class="m-tab" :class="{ active: modalTab === 'team' }" @click="modalTab = 'team'">
              <span class="material-symbols-outlined">group</span> Team
            </button>
          </div>

          <!-- ── Stages ── -->
          <div v-if="modalTab === 'stages'" class="modal-body">
            <div v-if="stagesLoading" class="muted">Loading stages…</div>
            <div v-else-if="!stageInfo || !stageInfo.stages.length" class="muted">
              No stages defined for this project yet.
            </div>
            <template v-else>
              <!-- Active stage headline -->
              <div v-if="activeStage" class="active-stage">
                <span class="as-label">Currently active</span>
                <div class="as-name">{{ activeStage.name }}</div>
                <div class="as-bar"><div class="as-fill" :style="{ width: activeStage.completion_percent + '%' }"></div></div>
                <div class="as-meta">
                  {{ activeStage.completion_percent }}% complete
                  · {{ activeStage.subtask_completed }}/{{ activeStage.subtask_total }} subtasks
                </div>
              </div>

              <div v-for="s in stageInfo.stages" :key="s.id" class="es-stage" :class="{ done: s.status === 'completed' }">
                <div class="es-head" @click="toggleStage(s.id)">
                  <span class="material-symbols-outlined es-chev" :class="{ open: openStages[s.id] }">chevron_right</span>
                  <span class="es-name">{{ s.name }}</span>
                  <span v-if="s.status === 'completed'" class="es-done">Complete</span>
                  <span class="es-spacer"></span>
                  <span class="es-pct">{{ s.completion_percent }}%</span>
                </div>
                <div class="es-bar"><div class="es-fill" :style="{ width: s.completion_percent + '%' }"></div></div>

                <ul v-if="openStages[s.id]" class="es-subs">
                  <li v-for="t in s.subtasks" :key="t.id" class="es-sub" :class="{ done: t.status === 'completed' }">
                    <span class="material-symbols-outlined es-ic">
                      {{ t.status === 'completed' ? 'check_circle' : 'radio_button_unchecked' }}
                    </span>
                    <div class="es-sub-body">
                      <div class="es-sub-title">{{ t.title }}</div>
                      <div v-if="t.due_date" class="es-sub-due" :class="{ late: t.is_overdue }">
                        Due {{ fmtDate(t.due_date) }}
                        <template v-if="t.is_overdue">· {{ t.days_overdue }}d late</template>
                      </div>
                    </div>
                  </li>
                  <li v-if="!s.subtasks.length" class="muted sm">No subtasks in this stage.</li>
                </ul>
              </div>
            </template>
          </div>

          <div v-show="modalTab === 'team'" class="modal-body">
            <div v-if="teamLoading" class="muted">Loading…</div>
            <div v-else-if="!myTeam" class="muted">
              You're not on a team for this project yet.
            </div>
            <div v-else>
              <div class="team-name-row">
                <span class="team-name">{{ myTeam.name }}</span>
              </div>
              <ul class="member-list">
                <li v-for="m in myTeam.members" :key="m.id" class="member-item">
                  <div class="m-info">
                    <div class="m-name">
                      {{ m.name }}
                      <span v-if="myTeam.team_lead_id === m.user_id" class="lead-tag">LEAD</span>
                      <span v-if="m.user_id === currentUserId" class="me-tag">YOU</span>
                    </div>
                    <div class="m-desig">{{ m.designation || '-' }}</div>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </EmployeeLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import EmployeeLayout from '../../components/EmployeeLayout.vue'
import { projectsAPI } from '../../api/projects'
import { stagesAPI } from '../../api/stages'
import { teamsAPI } from '../../api/teams'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const currentUserId = authStore.user?.id

const projects = ref([])
const loading = ref(true)

const teamModalOpen = ref(false)
const modalTab = ref('stages')
const stageInfo = ref(null)
const stagesLoading = ref(false)
const openStages = ref({})

// The active stage is the first not-yet-complete one - the work in flight.
const activeStage = computed(() => {
  const list = stageInfo.value?.stages || []
  return list.find(s => s.status !== 'completed') || null
})

function toggleStage(id) { openStages.value = { ...openStages.value, [id]: !openStages.value[id] } }
function fmtDate(d) {
  return d ? new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) : ''
}
const teamLoading = ref(false)
const selectedProject = ref(null)
const myTeam = ref(null)

async function loadProjects() {
  loading.value = true
  try {
    const res = await projectsAPI.getProjects()
    projects.value = res.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function openTeam(p) {
  selectedProject.value = p
  teamModalOpen.value = true
  modalTab.value = 'stages'
  teamLoading.value = true
  myTeam.value = null
  loadStages(p.id)
  try {
    const res = await teamsAPI.getMyTeamForProject(p.id)
    myTeam.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    teamLoading.value = false
  }
}

async function loadStages(projectId) {
  stagesLoading.value = true
  stageInfo.value = null
  openStages.value = {}
  try {
    const { data } = await stagesAPI.list(projectId)
    stageInfo.value = data
    // Open the active stage by default - it's what the employee needs now.
    if (activeStage.value) openStages.value = { [activeStage.value.id]: true }
  } catch (e) {
    stageInfo.value = null
  } finally {
    stagesLoading.value = false
  }
}

function closeTeam() {
  teamModalOpen.value = false
  selectedProject.value = null
  myTeam.value = null
  stageInfo.value = null
}

onMounted(loadProjects)
</script>

<style scoped>
/* ── Modal tabs ── */
.m-tabs { display: flex; gap: 2px; padding: 0 20px; border-bottom: 1px solid var(--color-outline); }
.m-tab {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 10px 14px; margin-bottom: -1px; background: none; border: none;
  border-bottom: 2px solid transparent; cursor: pointer;
  font-size: 13px; font-weight: 700; color: var(--color-on-surface-variant);
}
.m-tab.active { color: var(--color-primary); border-bottom-color: var(--color-primary); }
.m-tab .material-symbols-outlined { font-size: 16px; }

/* ── Active stage headline ── */
.active-stage {
  background: var(--color-primary-light, #e6f0f0); border-radius: var(--radius-lg);
  padding: 14px 16px; margin-bottom: 14px;
}
.as-label { font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: .06em; color: var(--color-primary); }
.as-name { font-size: 17px; font-weight: 800; color: var(--color-on-surface); margin: 2px 0 8px; }
.as-bar { height: 6px; border-radius: 999px; background: rgba(255,255,255,.6); overflow: hidden; }
.as-fill { height: 100%; background: var(--color-primary); transition: width .2s; }
.as-meta { font-size: 12px; font-weight: 600; color: var(--color-primary); margin-top: 6px; }

/* ── Stage list ── */
.es-stage { border: 1px solid var(--color-outline); border-radius: var(--radius-lg); padding: 10px 12px; margin-bottom: 8px; }
.es-stage.done { background: #f0fdf4; border-color: #bbf7d0; }
.es-head { display: flex; align-items: center; gap: 6px; cursor: pointer; }
.es-chev { font-size: 18px; color: var(--color-on-surface-variant); transition: transform .15s; }
.es-chev.open { transform: rotate(90deg); }
.es-name { font-weight: 700; font-size: 13px; color: var(--color-on-surface); }
.es-done { font-size: 10px; font-weight: 800; color: #166534; text-transform: uppercase; }
.es-spacer { flex: 1; }
.es-pct { font-size: 12px; font-weight: 700; color: var(--color-primary); }
.es-bar { height: 4px; border-radius: 999px; background: var(--color-outline-variant); margin-top: 6px; overflow: hidden; }
.es-fill { height: 100%; background: #059669; }
.es-subs { list-style: none; margin: 10px 0 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.es-sub { display: flex; align-items: flex-start; gap: 8px; }
.es-sub.done .es-sub-title { text-decoration: line-through; color: var(--color-on-surface-variant); }
.es-ic { font-size: 16px; color: var(--color-outline); flex-shrink: 0; }
.es-sub.done .es-ic { color: #059669; }
.es-sub-title { font-size: 13px; color: var(--color-on-surface); }
.es-sub-due { font-size: 11px; color: var(--color-on-surface-variant); margin-top: 1px; }
.es-sub-due.late { color: #dc2626; font-weight: 700; }
.muted.sm { font-size: 12px; }

.page-header { margin-bottom: 20px; }
.page-title {
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 700;
  margin: 0 0 4px;
  color: var(--color-on-surface);
  letter-spacing: -0.02em;
}
.page-sub {
  margin: 0;
  font-size: 13px;
  color: var(--color-on-surface-variant);
}
.empty {
  padding: 40px;
  text-align: center;
  color: var(--color-on-surface-variant);
  border: 1px dashed var(--color-outline-variant);
  border-radius: var(--radius-lg);
  background: #fff;
}
.proj-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}
.proj-card {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fff;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 12px 14px;
  text-align: left;
  cursor: pointer;
  transition: box-shadow .12s, transform .12s;
}
.proj-card:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,.06);
  transform: translateY(-1px);
}
.color-strip {
  flex: none;
  width: 4px;
  height: 38px;
  border-radius: 2px;
}
.proj-info { flex: 1; min-width: 0; }
.proj-num {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-on-surface-variant);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.proj-name {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-on-surface);
  margin: 2px 0 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.proj-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: var(--color-on-surface-variant);
}
.stage, .year {
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
}
.chev {
  color: var(--color-on-surface-variant);
  font-size: 20px;
}

/* modal */
.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.4);
  display: flex; align-items: center; justify-content: center;
  z-index: 200;
}
.modal {
  width: 440px; max-width: 94vw;
  background: #fff;
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 24px rgba(0,0,0,.1);
  border: 1px solid var(--color-outline-variant);
}
.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-outline-variant);
}
.modal-title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 17px;
}
.modal-sub {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--color-on-surface-variant);
}
.modal-close {
  background: none; border: none; cursor: pointer;
  color: var(--color-on-surface-variant);
}
.modal-body { padding: 16px 20px 20px; }
.muted { color: var(--color-on-surface-variant); font-size: 13px; }
.team-name-row {
  margin-bottom: 12px;
}
.team-name {
  font-weight: 700;
  font-size: 13px;
  background: rgba(40,116,117,.1);
  color: var(--color-primary);
  padding: 4px 10px;
  border-radius: 999px;
}
.member-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.member-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  background: #fafafa;
}
.m-info { flex: 1; min-width: 0; }
.m-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-on-surface);
  display: flex;
  align-items: center;
  gap: 6px;
}
.m-desig {
  font-size: 12px;
  color: var(--color-on-surface-variant);
  margin-top: 2px;
}
.lead-tag {
  font-size: 9px;
  font-weight: 700;
  background: var(--color-primary);
  color: #fff;
  padding: 1px 6px;
  border-radius: 2px;
}
.me-tag {
  font-size: 9px;
  font-weight: 700;
  background: #fef3c7;
  color: #92400e;
  padding: 1px 6px;
  border-radius: 2px;
}

.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}
</style>
