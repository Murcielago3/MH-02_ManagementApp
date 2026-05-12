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
          <tr v-for="c in paginated" :key="c.id" class="proj-row">
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
          Showing {{ filtered.length === 0 ? 0 : startIdx + 1 }} to {{ endIdx }} of {{ filtered.length }} entries
        </span>
        <div class="page-btns">
          <button class="page-btn" :disabled="currentPage === 1" @click="currentPage--">Prev</button>
          <button class="page-btn" :disabled="currentPage >= totalPages" @click="currentPage++">Next</button>
        </div>
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
import { ref, reactive, computed, onMounted } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import { clientsAPI } from '../api/clients'

const clients = ref([])
const loading = ref(true)
const searchQuery = ref('')
const currentPage = ref(1)
const perPage = 10

const modalOpen = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const submitting = ref(false)
const formError = ref('')
const deleteTarget = ref(null)

const form = reactive({
  name: '',
  email: '',
  phone: '',
  address: '',
})

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
  const q = searchQuery.value.toLowerCase()
  if (!q) return clients.value
  return clients.value.filter(c =>
    c.name.toLowerCase().includes(q) ||
    (c.email || '').toLowerCase().includes(q) ||
    (c.phone || '').toLowerCase().includes(q) ||
    (c.address || '').toLowerCase().includes(q)
  )
})

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage)))
const startIdx = computed(() => (currentPage.value - 1) * perPage)
const endIdx = computed(() => Math.min(startIdx.value + perPage, filtered.value.length))
const paginated = computed(() => filtered.value.slice(startIdx.value, endIdx.value))

function resetForm() {
  form.name = ''
  form.email = ''
  form.phone = ''
  form.address = ''
  formError.value = ''
}

function openAddModal() {
  resetForm()
  isEditing.value = false
  editingId.value = null
  modalOpen.value = true
}

function openEditModal(c) {
  isEditing.value = true
  editingId.value = c.id
  form.name = c.name
  form.email = c.email || ''
  form.phone = c.phone || ''
  form.address = c.address || ''
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
    }
    if (isEditing.value) {
      await clientsAPI.updateClient(editingId.value, payload)
    } else {
      await clientsAPI.createClient(payload)
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
/* ─── Page Actions ─── */
.page-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.actions-left { display: flex; gap: 8px; align-items: center; }
.search-box { position: relative; }
.search-icon {
  position: absolute; left: 8px; top: 50%;
  transform: translateY(-50%); color: var(--color-on-surface-variant); font-size: 18px;
}
.search-input {
  padding: 8px 8px 8px 32px; background: #fff; border: 1px solid var(--color-outline);
  border-radius: var(--radius-lg); font-family: var(--font-display); font-size: 13px;
  color: var(--color-on-surface); width: 256px; outline: none; transition: border 0.15s;
}
.search-input:focus { border-color: var(--color-primary); }
.add-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 16px; background: var(--color-primary); color: #fff; border: none;
  border-radius: var(--radius-lg); font-family: var(--font-display); font-size: 13px;
  font-weight: 500; cursor: pointer; transition: background 0.15s;
}
.add-btn:hover { background: #2a2a3e; }

/* ─── Table ─── */
.table-card {
  background: #fff; border: 1px solid var(--color-surface-container-high); border-radius: var(--radius-lg);
  overflow: hidden;
}
.proj-table {
  width: 100%; border-collapse: collapse;
}
.proj-table th {
  padding: 12px 16px; text-align: left; font-family: var(--font-display);
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--color-on-surface-variant); border-bottom: 1px solid var(--color-surface-container-high);
  background: var(--color-background);
}
.proj-table td {
  padding: 12px 16px; border-bottom: 1px solid var(--color-surface-container);
  font-family: var(--font-display); font-size: 13px; color: var(--color-on-surface);
}
.proj-row:hover { background: var(--color-background); }
.proj-name { font-weight: 500; }
.muted { color: var(--color-on-surface-variant); }
.mono { font-variant-numeric: tabular-nums; }
.text-center { text-align: center; }
.col-actions { width: 100px; }

.empty-cell {
  text-align: center; padding: 48px 16px; color: var(--color-on-surface-variant);
  font-family: var(--font-display); font-size: 13px;
}
.loading-text { color: var(--color-on-surface-variant); }

/* ─── Table Footer ─── */
.table-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; background: var(--color-background); border-top: 1px solid var(--color-surface-container-high);
}
.page-info {
  font-family: var(--font-display); font-size: 13px; color: var(--color-on-surface-variant);
}
.page-btns { display: flex; gap: 4px; }
.page-btn {
  padding: 6px 12px; background: #fff; border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius); font-family: var(--font-display); font-size: 13px;
  color: var(--color-on-surface-variant); cursor: pointer; transition: all 0.15s;
}
.page-btn:hover:not(:disabled) { background: var(--color-surface-container); }
.page-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ─── Row Actions ─── */
.row-actions { display: flex; justify-content: center; gap: 8px; }
.action-btn {
  padding: 6px; background: none; border: none; border-radius: var(--radius);
  cursor: pointer; transition: background 0.15s; display: flex; align-items: center;
}
.edit-btn:hover { background: #e0f2fe; }
.delete-btn:hover { background: #fef2f2; }
.action-btn .material-symbols-outlined { font-size: 18px; color: var(--color-on-surface-variant); }
.edit-btn .material-symbols-outlined { color: var(--color-primary); }
.delete-btn .material-symbols-outlined { color: #dc2626; }

/* ─── Modal ─── */
.modal-backdrop {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.5); display: flex; align-items: center;
  justify-content: center; z-index: 1000;
}
.modal {
  background: #fff; border-radius: var(--radius-lg); max-width: 600px; width: 90%;
  max-height: 90vh; overflow-y: auto; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}
.modal-wide { max-width: 800px; }
.modal-sm { max-width: 400px; }
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 20px 24px; border-bottom: 1px solid var(--color-surface-container-high);
}
.modal-title {
  font-family: var(--font-display); font-size: 18px; font-weight: 600;
  color: var(--color-on-surface); margin: 0;
}
.modal-close {
  background: none; border: none; cursor: pointer; padding: 4px;
  border-radius: var(--radius); transition: background 0.15s;
}
.modal-close:hover { background: var(--color-surface-container); }
.modal-close .material-symbols-outlined { font-size: 20px; color: var(--color-on-surface-variant); }
.modal-body { padding: 24px; }
.modal-footer {
  display: flex; justify-content: flex-end; gap: 12px;
  padding: 20px 24px; border-top: 1px solid var(--color-surface-container-high); background: var(--color-background);
}

/* ─── Form ─── */
.form-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
  margin-bottom: 24px;
}
.form-field span-2 { grid-column: span 2; }
.form-field label {
  display: block; font-family: var(--font-display); font-size: 13px;
  font-weight: 600; color: var(--color-on-surface-variant); margin-bottom: 6px;
}
.form-field input,
.form-field textarea {
  width: 100%; padding: 8px 12px; border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius); font-family: var(--font-display); font-size: 13px;
  color: var(--color-on-surface); outline: none; transition: border 0.15s;
}
.form-field input:focus,
.form-field textarea:focus { border-color: var(--color-primary); }
.form-field textarea { resize: vertical; }

.form-error {
  display: flex; align-items: center; gap: 8px;
  padding: 12px; background: #fef2f2; border: 1px solid #fecaca;
  border-radius: var(--radius); margin-bottom: 16px;
}
.form-error .material-symbols-outlined { color: #dc2626; font-size: 16px; }
.form-error {
  font-family: var(--font-display); font-size: 13px; color: #dc2626;
}

/* ─── Buttons ─── */
.btn-cancel {
  padding: 8px 16px; background: #fff; border: 1px solid var(--color-surface-container-high);
  border-radius: var(--radius); font-family: var(--font-display); font-size: 13px;
  color: var(--color-on-surface-variant); cursor: pointer; transition: all 0.15s;
}
.btn-cancel:hover { background: var(--color-surface-container); }
.btn-submit {
  padding: 8px 16px; background: var(--color-primary); color: #fff; border: none;
  border-radius: var(--radius); font-family: var(--font-display); font-size: 13px;
  font-weight: 500; cursor: pointer; transition: background 0.15s;
}
.btn-submit:hover:not(:disabled) { background: #2a2a3e; }
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger {
  padding: 8px 16px; background: #dc2626; color: #fff; border: none;
  border-radius: var(--radius); font-family: var(--font-display); font-size: 13px;
  font-weight: 500; cursor: pointer; transition: background 0.15s;
}
.btn-danger:hover:not(:disabled) { background: #b91c1c; }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }
</style>