<template>
  <div class="gs" ref="rootEl">
    <span class="material-symbols-outlined gs-icon">search</span>
    <input
      ref="inputEl"
      v-model="raw"
      type="text"
      class="gs-field"
      placeholder="Search anything…  try  invoices:adani"
      @focus="openList"
      @keydown.down.prevent="move(1)"
      @keydown.up.prevent="move(-1)"
      @keydown.enter.prevent="run()"
      @keydown.esc="close"
      @keydown.tab="completeScope"
    />
    <kbd v-if="!open" class="gs-kbd">/</kbd>
    <button v-if="raw" type="button" class="gs-clear" @click="clear" title="Clear">
      <span class="material-symbols-outlined">close</span>
    </button>

    <div v-if="open" class="gs-panel">
      <p class="gs-hint">
        <strong>scope:term</strong> jumps straight there - e.g.
        <button type="button" class="gs-example" @click="useExample">invoices:adani motilal</button>
      </p>

      <ul class="gs-list">
        <li
          v-for="(o, i) in options"
          :key="o.key"
          class="gs-opt"
          :class="{ active: i === cursor }"
          @mouseenter="cursor = i"
          @mousedown.prevent="run(o)"
        >
          <span class="material-symbols-outlined gs-opt-icon">{{ o.icon }}</span>
          <span class="gs-opt-body">
            <span class="gs-opt-label">{{ o.label }}</span>
            <span class="gs-opt-sub">{{ o.sub }}</span>
          </span>
          <span class="material-symbols-outlined gs-go">arrow_forward</span>
        </li>
        <li v-if="!options.length" class="gs-empty">No matching section.</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// Every searchable section. `q` names the query param the target page reads.
const SECTIONS = [
  { key: 'invoices',       label: 'Invoices',       icon: 'receipt_long',    path: '/admin/invoices',       roles: ['admin'], alias: ['invoice', 'bill', 'inv'] },
  { key: 'projects',       label: 'Projects',       icon: 'architecture',    path: '/admin/projects',       roles: ['admin'], alias: ['project', 'proj'] },
  { key: 'clients',        label: 'Clients',        icon: 'handshake',       path: '/admin/clients',        roles: ['admin'], alias: ['client', 'customer'] },
  { key: 'employees',      label: 'Employees',      icon: 'group',           path: '/admin/employees',      roles: ['admin'], alias: ['employee', 'emp', 'staff', 'people'] },
  { key: 'timesheets',     label: 'Timesheets',     icon: 'pending_actions', path: '/admin/timesheets',     roles: ['admin', 'project_manager'], alias: ['timesheet', 'ts', 'hours'] },
  { key: 'reimbursements', label: 'Reimbursements', icon: 'request_quote',   path: '/admin/reimbursements', roles: ['admin'], alias: ['reimbursement', 'reimb', 'claim'] },
  { key: 'expenses',       label: 'Expenses',       icon: 'payments',        path: '/admin/expenses',       roles: ['admin'], alias: ['expense', 'spend'] },
  { key: 'estimates',      label: 'Estimates',      icon: 'calculate',       path: '/admin/estimates',      roles: ['admin'], alias: ['estimate', 'quote'] },
  { key: 'salary',         label: 'Salary Slips',   icon: 'paid',            path: '/admin/salary-slips',   roles: ['admin'], alias: ['salary', 'payslip', 'slip', 'payroll'] },
  { key: 'leaves',         label: 'Leaves',         icon: 'event_busy',      path: '/admin/leaves',         roles: ['admin'], alias: ['leave', 'holiday', 'off'] },
  { key: 'tasks',          label: 'Tasks',          icon: 'task_alt',        path: '/admin/tasks',          roles: ['admin'], alias: ['task', 'calendar'] },
]

const raw = ref('')
const open = ref(false)
const cursor = ref(0)
const rootEl = ref(null)
const inputEl = ref(null)

const allowed = computed(() =>
  SECTIONS.filter(s => s.roles.includes(authStore.role)))

// "invoices:adani motilal" -> { scope: 'invoices', term: 'adani motilal' }
const parsed = computed(() => {
  const v = raw.value
  const i = v.indexOf(':')
  if (i === -1) return { scope: '', term: v.trim() }
  return { scope: v.slice(0, i).trim().toLowerCase(), term: v.slice(i + 1).trim() }
})

function matchesScope(s, scope) {
  return s.key.startsWith(scope) || s.alias.some(a => a.startsWith(scope))
}

const options = computed(() => {
  const { scope, term } = parsed.value
  if (scope) {
    // Scoped: offer the sections whose name matches, carrying the search term.
    return allowed.value
      .filter(s => matchesScope(s, scope))
      .map(s => ({
        ...s,
        sub: term ? `Search “${term}”` : 'Open section',
        term,
      }))
  }
  if (!term) {
    return allowed.value.map(s => ({ ...s, sub: 'Open section', term: '' }))
  }
  // Unscoped: search the term inside every section, best-named match first.
  const t = term.toLowerCase()
  const scored = allowed.value.map(s => ({
    ...s,
    sub: `Search “${term}”`,
    term,
    _hit: s.label.toLowerCase().includes(t) || s.alias.some(a => a.includes(t)) ? 0 : 1,
  }))
  return scored.sort((a, b) => a._hit - b._hit)
})

function openList() { open.value = true; cursor.value = 0 }
function close() { open.value = false }
function clear() { raw.value = ''; inputEl.value?.focus() }
function useExample() {
  raw.value = 'invoices:adani motilal'
  nextTick(() => inputEl.value?.focus())
}

function move(d) {
  if (!open.value) { open.value = true; return }
  const n = options.value.length
  if (!n) return
  cursor.value = (cursor.value + d + n) % n
}

// Tab completes the scope you've started typing, so "inv⇥" becomes "invoices:".
function completeScope(e) {
  const { scope, term } = parsed.value
  if (term || !scope) return
  const hit = allowed.value.find(s => matchesScope(s, scope))
  if (!hit) return
  e.preventDefault()
  raw.value = `${hit.key}:`
}

function run(opt) {
  const target = opt || options.value[cursor.value]
  if (!target) return
  // The term rides along as ?q= - target pages pre-fill their own search box.
  router.push({ path: target.path, query: target.term ? { q: target.term } : {} })
  open.value = false
  raw.value = ''
  inputEl.value?.blur()
}

function onDocClick(e) {
  if (rootEl.value && !rootEl.value.contains(e.target)) open.value = false
}
// "/" focuses search from anywhere, unless you're already typing in a field.
function onKey(e) {
  if (e.key !== '/' || open.value) return
  const t = e.target
  if (t && /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)) return
  if (t && t.isContentEditable) return
  e.preventDefault()
  inputEl.value?.focus()
}

onMounted(() => {
  document.addEventListener('click', onDocClick)
  document.addEventListener('keydown', onKey)
})
onUnmounted(() => {
  document.removeEventListener('click', onDocClick)
  document.removeEventListener('keydown', onKey)
})
</script>

<style scoped>
.gs { position: relative; display: flex; align-items: center; gap: 8px; flex: 1; max-width: 420px; }
.gs-icon { font-size: 16px; color: var(--color-on-surface-variant); flex-shrink: 0; }
.gs-field {
  flex: 1; min-width: 0; border: none; outline: none; background: transparent;
  font-family: var(--font-body); font-size: 13px; color: var(--color-on-surface);
}
.gs-field::placeholder { color: var(--color-on-surface-variant); }
.gs-kbd {
  font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 4px;
  border: 1px solid var(--color-outline); color: var(--color-on-surface-variant);
  background: var(--color-surface-dim, #f8fafc);
}
.gs-clear {
  background: none; border: none; cursor: pointer; padding: 0; display: flex;
  color: var(--color-on-surface-variant);
}
.gs-clear .material-symbols-outlined { font-size: 15px; }

.gs-panel {
  position: absolute; top: calc(100% + 10px); left: -12px; right: -12px;
  background: var(--color-surface); border: 1px solid var(--color-outline);
  border-radius: var(--radius-xl); box-shadow: 0 12px 32px rgba(0,0,0,.14);
  z-index: 60; overflow: hidden; max-height: 60vh; overflow-y: auto;
}
.gs-hint {
  margin: 0; padding: 9px 14px; font-size: 11px; line-height: 1.5;
  color: var(--color-on-surface-variant);
  background: var(--color-surface-dim, #f8fafc);
  border-bottom: 1px solid var(--color-outline);
}
.gs-hint strong { color: var(--color-primary); font-family: var(--font-mono, monospace); }
.gs-example {
  background: none; border: none; padding: 0; cursor: pointer;
  color: var(--color-primary); font-weight: 700; text-decoration: underline; font-size: 11px;
}

.gs-list { list-style: none; margin: 0; padding: 6px; }
.gs-opt {
  display: flex; align-items: center; gap: 10px; padding: 9px 10px;
  border-radius: var(--radius-md); cursor: pointer;
}
.gs-opt.active { background: var(--color-primary-light, #e6f0f0); }
.gs-opt-icon { font-size: 18px; color: var(--color-primary); flex-shrink: 0; }
.gs-opt-body { display: flex; flex-direction: column; min-width: 0; flex: 1; }
.gs-opt-label { font-size: 13px; font-weight: 700; color: var(--color-on-surface); }
.gs-opt-sub {
  font-size: 11px; color: var(--color-on-surface-variant);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.gs-go { font-size: 15px; color: var(--color-on-surface-variant); opacity: 0; }
.gs-opt.active .gs-go { opacity: 1; }
.gs-empty { padding: 14px; font-size: 12px; color: var(--color-on-surface-variant); font-style: italic; }
</style>
