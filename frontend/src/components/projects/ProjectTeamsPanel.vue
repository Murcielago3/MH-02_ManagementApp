<template>
  <div class="teams-panel">
    <div class="panel-head">
      <h4 class="section-title">Teams</h4>
      <button type="button" class="btn-add-team" :disabled="creating" @click="addTeam">
        {{ creating ? 'Creating…' : '+ Add Team' }}
      </button>
    </div>

    <div v-if="loading" class="muted">Loading teams…</div>
    <div v-else-if="!teams.length" class="empty-state">No teams yet. Add a team and assign employees to it.</div>

    <div v-else class="teams-list">
      <div v-for="team in teams" :key="team.id" class="team-card">
        <div class="team-head">
          <div class="team-name">{{ team.name }}</div>
          <button type="button" class="btn-del-team" @click="confirmDelete(team)">Delete team</button>
        </div>

        <div class="members-row">
          <div v-if="!team.members.length" class="muted small">No members yet.</div>
          <span v-for="m in team.members" :key="m.id" class="member-chip"
                :class="{ lead: team.team_lead_id === m.user_id }">
            <span v-if="team.team_lead_id === m.user_id" class="lead-tag">LEAD</span>
            {{ m.name }}
            <button type="button" class="chip-x" @click="removeMember(team, m)" title="Remove">×</button>
          </span>
        </div>

        <div class="team-controls">
          <div class="ctl">
            <label>Add member</label>
            <select v-model="addMemberSelection[team.id]">
              <option :value="null">— Select employee —</option>
              <option v-for="u in availableUsersForTeam(team)" :key="u.id" :value="u.id">
                {{ u.name }}{{ u.designation ? ' (' + u.designation + ')' : '' }}
              </option>
            </select>
            <button
              type="button"
              class="btn-sm"
              :disabled="!addMemberSelection[team.id]"
              @click="addMember(team)"
            >Add</button>
          </div>

          <div class="ctl">
            <label>Team Lead</label>
            <select :value="team.team_lead_id ?? ''" @change="updateLead(team, $event.target.value)">
              <option value="">— None —</option>
              <option v-for="m in team.members" :key="m.user_id" :value="m.user_id">
                {{ m.name }}
              </option>
            </select>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { teamsAPI } from '../../api/teams'

const props = defineProps({
  projectId: { type: [Number, String], required: true },
  allUsers: { type: Array, default: () => [] },
})

const emit = defineEmits(['error', 'changed'])

const teams = ref([])
const loading = ref(false)
const creating = ref(false)
const addMemberSelection = reactive({})

const usedUserIds = computed(() => {
  const s = new Set()
  for (const t of teams.value) for (const m of t.members) s.add(m.user_id)
  return s
})

function availableUsersForTeam(_team) {
  // employee is on at most one team per project, so any user already on any team is unavailable
  return props.allUsers.filter(u => !usedUserIds.value.has(u.id))
}

async function load() {
  if (!props.projectId) return
  loading.value = true
  try {
    const res = await teamsAPI.listProjectTeams(props.projectId)
    teams.value = res.data || []
  } catch (e) {
    emit('error', apiErr(e))
  } finally {
    loading.value = false
  }
}

async function addTeam() {
  creating.value = true
  try {
    const res = await teamsAPI.createTeam(props.projectId)
    teams.value.push(res.data)
    emit('changed')
  } catch (e) {
    emit('error', apiErr(e))
  } finally {
    creating.value = false
  }
}

async function confirmDelete(team) {
  if (!confirm(`Delete ${team.name}? Members will be unassigned from this team.`)) return
  try {
    await teamsAPI.deleteTeam(props.projectId, team.id)
    await load()
    emit('changed')
  } catch (e) {
    emit('error', apiErr(e))
  }
}

async function addMember(team) {
  const uid = addMemberSelection[team.id]
  if (!uid) return
  try {
    const res = await teamsAPI.addMember(props.projectId, team.id, uid)
    const i = teams.value.findIndex(t => t.id === team.id)
    if (i !== -1) teams.value[i] = res.data
    addMemberSelection[team.id] = null
    emit('changed')
  } catch (e) {
    emit('error', apiErr(e))
  }
}

async function removeMember(team, member) {
  try {
    await teamsAPI.removeMember(props.projectId, team.id, member.id)
    await load()
    emit('changed')
  } catch (e) {
    emit('error', apiErr(e))
  }
}

async function updateLead(team, val) {
  const lead = val === '' || val == null ? null : Number(val)
  try {
    const res = await teamsAPI.updateTeam(props.projectId, team.id, { team_lead_id: lead })
    const i = teams.value.findIndex(t => t.id === team.id)
    if (i !== -1) teams.value[i] = res.data
    emit('changed')
  } catch (e) {
    emit('error', apiErr(e))
  }
}

function apiErr(e) {
  const d = e.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map(x => x.msg || JSON.stringify(x)).join(' ')
  return e.message || 'Request failed'
}

onMounted(load)
watch(() => props.projectId, load)

defineExpose({ reload: load })
</script>

<style scoped>
.teams-panel { width: 100%; }
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.section-title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  color: var(--color-on-surface);
}
.btn-add-team {
  padding: 6px 14px;
  border: none;
  background: var(--color-primary);
  color: #fff;
  font-weight: 600;
  font-size: 13px;
  border-radius: var(--radius-lg);
  cursor: pointer;
}
.btn-add-team:disabled { opacity: .55; cursor: not-allowed; }
.empty-state {
  padding: 12px;
  text-align: center;
  color: var(--color-on-surface-variant);
  font-size: 13px;
  background: #f8fafc;
  border-radius: var(--radius-lg);
}
.muted { color: var(--color-on-surface-variant); font-size: 13px; }
.muted.small { font-size: 12px; }
.teams-list { display: flex; flex-direction: column; gap: 12px; }
.team-card {
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-lg);
  padding: 14px;
  background: #fff;
}
.team-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.team-name {
  font-weight: 700;
  font-size: 14px;
  color: var(--color-on-surface);
}
.btn-del-team {
  background: none;
  border: 1px solid #fecaca;
  color: #b91c1c;
  padding: 4px 10px;
  border-radius: var(--radius-lg);
  font-size: 12px;
  cursor: pointer;
}
.btn-del-team:hover { background: #fef2f2; }
.members-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
  min-height: 32px;
  align-items: center;
}
.member-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px 4px 10px;
  background: #f1f5f9;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
}
.member-chip.lead {
  background: rgba(40, 116, 117, 0.12);
  color: var(--color-primary);
}
.lead-tag {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.05em;
  background: var(--color-primary);
  color: #fff;
  padding: 1px 5px;
  border-radius: 2px;
}
.chip-x {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  color: #64748b;
  padding: 0 2px;
}
.chip-x:hover { color: #b91c1c; }
.team-controls {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 12px;
}
.ctl {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.ctl label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-on-surface-variant);
  font-weight: 600;
}
.ctl select {
  height: 36px;
  padding: 0 8px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  font-size: 13px;
  background: #fff;
}
.ctl > .btn-sm {
  align-self: flex-start;
  margin-top: 4px;
  padding: 6px 14px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-lg);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
.ctl > .btn-sm:disabled { opacity: .55; cursor: not-allowed; }

@media (max-width: 720px) {
  .team-controls { grid-template-columns: 1fr; }
}
</style>
