<template>
  <AppLayout>
    <!-- Page Actions -->
    <div class="page-actions">
      <div class="actions-left">
        <div class="search-box">
          <span class="material-symbols-outlined search-icon">search</span>
          <input v-model="searchQuery" type="text" placeholder="Search clients..." class="search-input" />
        </div>
      </div>
      <button class="add-btn" @click="openAddModal">
        <span class="material-symbols-outlined">add</span>
        Add Client
      </button>
    </div>

    <!-- Table -->
    <div class="table-card">
      <table class="proj-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Phone</th>
            <th>Address</th>
            <th class="text-center col-actions">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="5" class="empty-cell"><div class="loading-text">Loading clients…</div></td>
          </tr>
          <tr v-else-if="filtered.length === 0">
            <td colspan="5" class="empty-cell">No clients found.</td>
          </tr>
          <tr v-for="c in filtered" :key="c.id" class="proj-row">
            <td><span class="proj-name">{{ c.name }}</span></td>
            <td class="muted">{{ c.email || '—' }}</td>
            <td class="mono muted">{{ c.phone || '—' }}</td>
            <td class="muted">{{ c.address || '—' }}</td>
            <td>
              <div class="row-actions">
                <button class="action-btn edit-btn" title="Edit" @click="openEditModal(c)">
                  <span class="material-symbols-outlined">edit</span>
                </button>
                <button class="action-btn delete-btn" title="Delete" @click="confirmDelete(c)">
                  <span class="material-symbols-outlined">delete</span>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="table-footer">
        <span class="page-info">
          {{ filtered.length }} {{ filtered.length === 1 ? 'client' : 'clients' }}
        </span>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <Teleport to="body">
      <div v-if="modalOpen" class="modal-backdrop" @click.self="closeModal">
        <div class="modal modal-wide">
          <div class="modal-header">
            <h3 class="modal-title">{{ isEditing ? 'Edit Client' : 'Add New Client' }}</h3>
            <button class="modal-close" @click="closeModal">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>

          <form @submit.prevent="handleSubmit" class="modal-body">
            <!-- Draft restore banner -->
            <div v-if="showDraftBanner" class="draft-banner">
              <span class="material-symbols-outlined">history</span>
              <span>You have an unsaved draft from a previous session.</span>
              <button type="button" class="draft-restore-btn" @click="restoreClientDraft">Restore</button>
              <button type="button" class="draft-discard-btn" @click="discardClientDraft">Discard</button>
            </div>

            <div class="form-grid">
              <!-- Name -->
              <div class="form-field">
                <label>Name *</label>
                <input v-model="form.name" type="text" required placeholder="e.g. ABC Corp" />
              </div>
              <!-- Email -->
              <div class="form-field">
                <label>Email</label>
                <input v-model="form.email" type="email" placeholder="client@example.com" />
              </div>
              <!-- Phone -->
              <div class="form-field">
                <label>Phone</label>
                <input v-model="form.phone" type="tel" placeholder="+91 9876543210" />
              </div>
              <!-- Address -->
              <div class="form-field span-2">
                <label>Address</label>
                <textarea v-model="form.address" placeholder="Full address..." rows="3"></textarea>
              </div>
              <!-- GSTIN -->
              <div class="form-field span-2">
                <label>GSTIN</label>
                <input v-model="form.gstin" type="text" placeholder="e.g. 27AAAAA0000A1Z5" />
              </div>
            </div>

            <div v-if="formError" class="form-error">
              <span class="material-symbols-outlined">error</span>
              {{ formError }}
            </div>

            <div class="modal-footer">
              <button type="button" class="btn-cancel" @click="closeModal">Cancel</button>
              <button type="submit" class="btn-submit" :disabled="submitting">
                {{ submitting ? 'Saving…' : (isEditing ? 'Save Changes' : 'Add Client') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Delete Confirmation -->
    <Teleport to="body">
      <div v-if="deleteTarget" class="modal-backdrop" @click.self="deleteTarget = null">
        <div class="modal modal-sm">
          <div class="modal-header">
            <h3 class="modal-title">Delete Client</h3>
            <button class="modal-close" @click="deleteTarget = null">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <div class="modal-body">
            <p>Are you sure you want to delete <strong>{{ deleteTarget.name }}</strong>?<br/>This action cannot be undone.</p>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="deleteTarget = null">Cancel</button>
            <button class="btn-danger" :disabled="submitting" @click="handleDelete">
              {{ submitting ? 'Deleting…' : 'Delete' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </AppLayout>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import { clientsAPI } from '../api/clients'
import { useDraftStorage } from '../composables/useDraftStorage'

const clients = ref([])
const loading = ref(true)
const searchQuery = ref('')

const modalOpen = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const submitting = ref(false)
const formError = ref('')
const deleteTarget = ref(null)

const { draft: clientDraft, saveDraft: saveClientDraft, clearDraft: clearClientDraft, hasDraft: hasClientDraft, load: loadClientDraft } = useDraftStorage('client_create')
const showDraftBanner = ref(false)

const form = reactive({
  name: '',
  email: '',
  phone: '',
  address: '',
  gstin: '',
})

// Auto-save draft during add mode
watch(() => ({ ...form }), (val) => {
  if (modalOpen.value && !isEditing.value) {
    saveClientDraft({ ...val })
  }
}, { deep: true })

async function fetchClients() {
  loading.value = true
  try {
    const res = await clientsAPI.getClients()
    clients.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchClients)

const filtered = computed(() => {
  let list = [...clients.value]
  list.sort((a, b) => (b.id || 0) - (a.id || 0))
  const q = searchQuery.value.toLowerCase()
  if (!q) return list
  return list.filter(c =>
    c.name.toLowerCase().includes(q) ||
    (c.email || '').toLowerCase().includes(q) ||
    (c.phone || '').toLowerCase().includes(q) ||
    (c.address || '').toLowerCase().includes(q)
  )
})

function resetForm() {
  form.name = ''
  form.email = ''
  form.phone = ''
  form.address = ''
  form.gstin = ''
  formError.value = ''
}

function restoreClientDraft() {
  if (!clientDraft.value) return
  const d = clientDraft.value
  Object.keys(form).forEach(k => { if (d[k] !== undefined) form[k] = d[k] })
  showDraftBanner.value = false
}

function discardClientDraft() {
  clearClientDraft()
  showDraftBanner.value = false
}

async function openAddModal() {
  resetForm()
  isEditing.value = false
  editingId.value = null
  modalOpen.value = true
  // Pull the latest draft for this account (may have been saved on another device).
  await loadClientDraft()
  if (hasClientDraft.value) showDraftBanner.value = true
}

function openEditModal(c) {
  isEditing.value = true
  editingId.value = c.id
  form.name = c.name
  form.email = c.email || ''
  form.phone = c.phone || ''
  form.address = c.address || ''
  form.gstin = c.gstin || ''
  formError.value = ''
  modalOpen.value = true
}

function closeModal() { modalOpen.value = false }

async function handleSubmit() {
  formError.value = ''
  submitting.value = true
  try {
    const payload = {
      name: form.name,
      email: form.email || null,
      phone: form.phone || null,
      address: form.address || null,
      gstin: form.gstin || null,
    }
    if (isEditing.value) {
      await clientsAPI.updateClient(editingId.value, payload)
    } else {
      await clientsAPI.createClient(payload)
      clearClientDraft()
    }
    closeModal()
    await fetchClients()
  } catch (err) {
    formError.value = err.response?.data?.detail || 'Operation failed. Please try again.'
  } finally {
    submitting.value = false
  }
}

function confirmDelete(c) { deleteTarget.value = c }

async function handleDelete() {
  submitting.value = true
  try {
    await clientsAPI.deleteClient(deleteTarget.value.id)
    deleteTarget.value = null
    await fetchClients()
  } catch (err) {
    console.error(err)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
/* ─── Material Symbols ─── */
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

/* ─── Page Actions ─── */
.page-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.actions-left { display: flex; gap: 8px; align-items: center; }

/* Search */
.search-box { position: relative; }
.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-on-surface-variant);
  font-size: 16px;
  pointer-events: none;
}
.search-input {
  padding: 9px 12px 9px 34px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  width: 240px;
  outline: none;
  transition: border-color var(--transition), box-shadow var(--transition);
}
.search-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}
.search-input::placeholder { color: var(--color-on-surface-variant); }

/* Add button */
.add-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity var(--transition), box-shadow var(--transition);
  box-shadow: var(--shadow-sm);
}
.add-btn:hover { opacity: 0.88; box-shadow: var(--shadow-md); }
.add-btn .material-symbols-outlined { font-size: 16px; }

/* ─── Table Card ─── */
.table-card {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}
.proj-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}
.proj-table thead { background: #f8fafc; }
.proj-table th {
  padding: 12px 16px;
  font-family: var(--font-body);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .06em;
  text-transform: uppercase;
  color: var(--color-on-surface-variant);
  border-bottom: 1px solid var(--color-outline);
  white-space: nowrap;
}
.proj-table tbody tr {
  border-bottom: 1px solid var(--color-outline-variant);
  transition: background var(--transition);
}
.proj-table tbody tr:last-child { border-bottom: none; }
.proj-row:hover { background: #fafbfc; }
.proj-table td {
  padding: 12px 16px;
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  vertical-align: middle;
}

.proj-name { font-weight: 600; }
.muted { color: var(--color-on-surface-variant); }
.mono { font-variant-numeric: tabular-nums; }
.text-center { text-align: center; }
.col-actions { width: 90px; }

/* Empty / loading */
.empty-cell {
  padding: 48px 16px;
  text-align: center;
  color: var(--color-on-surface-variant);
  font-family: var(--font-body);
  font-size: 13px;
}
.loading-text { animation: pulse 1.4s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }

/* ─── Table Footer / Pagination ─── */
.table-footer {
  padding: 10px 16px;
  border-top: 1px solid var(--color-outline);
  background: #f8fafc;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.page-info {
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--color-on-surface-variant);
}
.page-btns { display: flex; gap: 6px; }
.page-btn {
  padding: 5px 12px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-on-surface);
  cursor: pointer;
  transition: background var(--transition);
}
.page-btn:hover:not(:disabled) { background: var(--color-outline-variant); }
.page-btn:disabled { opacity: 0.45; cursor: not-allowed; }

/* Row actions — visible on hover */
.row-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  opacity: 0;
  transition: opacity var(--transition);
}
.proj-row:hover .row-actions { opacity: 1; }
.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: none;
  background: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-on-surface-variant);
  transition: background var(--transition), color var(--transition);
}
.action-btn .material-symbols-outlined { font-size: 17px; }
.edit-btn:hover   { color: var(--color-primary); background: var(--color-primary-light); }
.delete-btn:hover { color: var(--color-error);   background: #fee2e2; }

/* ─── Modal ─── */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  animation: fadeIn 0.15s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.modal {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  width: 600px;
  max-width: 95vw;
  max-height: 92vh;
  overflow-y: auto;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.18);
  animation: slideUp 0.2s ease;
}
.modal-wide { width: 760px; }
.modal-sm   { width: 420px; }
@keyframes slideUp { from { transform: translateY(16px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-outline);
}
.modal-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  color: var(--color-on-surface);
  margin: 0;
  letter-spacing: -0.01em;
}
.modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: none;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-on-surface-variant);
  cursor: pointer;
  transition: background var(--transition);
}
.modal-close:hover { background: var(--color-outline-variant); }

.modal-body { padding: 24px; }
.modal-body p {
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-on-surface-variant);
  margin: 0;
}

/* Modal footer */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 18px 24px;
  border-top: 1px solid var(--color-outline);
  background: #f8fafc;
  border-radius: 0 0 var(--radius-xl) var(--radius-xl);
}
form .modal-footer {
  margin-top: 24px;
  padding: 0;
  border-top: none;
  background: none;
  border-radius: 0;
}

/* ─── Form ─── */
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.form-field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.span-2 { grid-column: span 2; }

.form-field label {
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: var(--color-on-surface-variant);
}
.form-field input,
.form-field textarea {
  padding: 8px 12px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-on-surface);
  background: var(--color-surface);
  outline: none;
  transition: border-color var(--transition), box-shadow var(--transition);
  width: 100%;
  box-sizing: border-box;
}
.form-field input { height: 38px; }
.form-field input:focus,
.form-field textarea:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}
.form-field input::placeholder,
.form-field textarea::placeholder { color: var(--color-on-surface-variant); }
.form-field textarea { resize: vertical; }

.form-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 11px 14px;
  background: #fee2e2;
  border: 1px solid #fecaca;
  border-radius: var(--radius-md);
  color: #b91c1c;
  font-family: var(--font-body);
  font-size: 13px;
  margin-top: 4px;
}
.form-error .material-symbols-outlined { font-size: 16px; flex-shrink: 0; }

/* ─── Buttons ─── */
.btn-cancel {
  padding: 9px 18px;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-surface);
  cursor: pointer;
  transition: background var(--transition);
}
.btn-cancel:hover { background: var(--color-outline-variant); }

.btn-submit {
  padding: 9px 18px;
  border: none;
  border-radius: var(--radius-lg);
  background: var(--color-primary);
  color: #fff;
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity var(--transition);
}
.btn-submit:hover:not(:disabled) { opacity: 0.88; }
.btn-submit:disabled { opacity: 0.45; cursor: not-allowed; }

.btn-danger {
  padding: 9px 18px;
  border: none;
  border-radius: var(--radius-lg);
  background: var(--color-error);
  color: #fff;
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity var(--transition);
}
.btn-danger:hover:not(:disabled) { opacity: 0.88; }
.btn-danger:disabled { opacity: 0.45; cursor: not-allowed; }

/* Draft banner */
.draft-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  margin-bottom: 18px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-size: 13px;
  color: #92400e;
}
.draft-banner .material-symbols-outlined { font-size: 18px; flex-shrink: 0; }
.draft-restore-btn {
  margin-left: auto;
  padding: 5px 12px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}
.draft-restore-btn:hover { opacity: 0.88; }
.draft-discard-btn {
  padding: 5px 12px;
  background: none;
  border: 1px solid #d97706;
  color: #d97706;
  border-radius: var(--radius-md);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}
.draft-discard-btn:hover { background: #fef3c7; }

@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; gap: 10px; }
  .filter-bar { flex-direction: column; align-items: stretch; gap: 8px; }
  .filter-bar-left { flex-wrap: wrap; }
  .table-card { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .data-table { min-width: 500px; }
  .modal { max-width: 100%; width: 100%; }
  .modal-backdrop { padding: 8px; }
  .form-grid { grid-template-columns: 1fr; }
  .span-2 { grid-column: span 1; }
}
</style>