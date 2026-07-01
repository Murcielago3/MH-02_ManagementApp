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
            <th>Type</th>
            <th>Email</th>
            <th>Phone</th>
            <th>GSTIN / PAN</th>
            <th class="text-center col-actions">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="6" class="empty-cell"><div class="loading-text">Loading clients…</div></td>
          </tr>
          <tr v-else-if="filtered.length === 0">
            <td colspan="6" class="empty-cell">No clients found.</td>
          </tr>
          <tr v-for="c in filtered" :key="c.id" class="proj-row">
            <td>
              <span class="proj-name">{{ c.salutation || c.name }}</span>
              <span v-if="c.salutation" class="muted" style="display:block; font-size:11px;">{{ c.name }}</span>
            </td>
            <td>
              <span class="type-badge" :class="c.customer_type === 'individual' ? 'type-individual' : 'type-business'">
                {{ c.customer_type === 'individual' ? 'Individual' : 'Business' }}
              </span>
            </td>
            <td class="muted">{{ c.email || '—' }}</td>
            <td class="mono muted">{{ c.phone || '—' }}</td>
            <td class="mono muted">{{ c.customer_type === 'individual' ? (c.pan || '—') : (c.gstin || c.pan || '—') }}</td>
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
      <div v-if="modalOpen" class="modal-backdrop">
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

            <!-- Customer Type -->
            <div class="form-field span-2" style="margin-bottom: 18px;">
              <label>Customer Type</label>
              <div class="type-toggles">
                <button
                  type="button"
                  class="type-toggle-btn"
                  :class="{ active: form.customer_type === 'business' }"
                  @click="form.customer_type = 'business'"
                >
                  <span class="material-symbols-outlined">apartment</span>
                  Business
                </button>
                <button
                  type="button"
                  class="type-toggle-btn"
                  :class="{ active: form.customer_type === 'individual' }"
                  @click="onSelectIndividual"
                >
                  <span class="material-symbols-outlined">person</span>
                  Individual
                </button>
              </div>
            </div>

            <div class="form-grid">
              <!-- Name -->
              <div class="form-field">
                <label>Name *</label>
                <input v-model="form.name" type="text" required placeholder="e.g. ABC Corp" />
              </div>
              <!-- Salutation / display name -->
              <div class="form-field">
                <label>
                  Invoice Display Name
                  <label class="inline-check">
                    <input type="checkbox" v-model="sameAsClientName" />
                    Same as name
                  </label>
                </label>
                <input
                  v-model="form.salutation"
                  type="text"
                  :disabled="sameAsClientName"
                  :placeholder="form.name || 'Name shown on invoices'"
                />
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

              <!-- GSTIN (business only) -->
              <div v-if="form.customer_type === 'business'" class="form-field">
                <label>GSTIN</label>
                <TaxIdField v-model="form.gstin" kind="gstin" placeholder="e.g. 27AAAAA0000A1Z5" />
              </div>
              <!-- PAN (always; required for individuals) -->
              <div class="form-field">
                <label>PAN {{ form.customer_type === 'individual' ? '*' : '' }}</label>
                <TaxIdField
                  v-model="form.pan"
                  kind="pan"
                  placeholder="e.g. AAAAA9999A"
                  :required="form.customer_type === 'individual'"
                />
              </div>

              <!-- Structured address -->
              <div class="form-field span-2">
                <label>Address Line 1</label>
                <input v-model="form.address_line1" type="text" placeholder="Building, street" />
              </div>
              <div class="form-field span-2">
                <label>Address Line 2</label>
                <input v-model="form.address_line2" type="text" placeholder="Area, landmark (optional)" />
              </div>
              <div class="form-field">
                <label>City</label>
                <input v-model="form.city" type="text" placeholder="e.g. Mumbai" />
              </div>
              <div class="form-field">
                <label>State</label>
                <input v-model="form.state" type="text" list="indian-states" placeholder="e.g. Maharashtra" />
                <datalist id="indian-states">
                  <option v-for="s in indianStates" :key="s" :value="s" />
                </datalist>
              </div>
              <div class="form-field">
                <label>Pincode</label>
                <input v-model="form.pincode" type="text" maxlength="6" placeholder="e.g. 400001" />
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
      <div v-if="deleteTarget" class="modal-backdrop">
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
import TaxIdField from '../components/TaxIdField.vue'
import { clientsAPI } from '../api/clients'
import { useDraftStorage } from '../composables/useDraftStorage'
import { panFromGstin } from '../utils/taxIds'

const indianStates = [
  'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 'Goa', 'Gujarat',
  'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Kerala', 'Madhya Pradesh',
  'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab',
  'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand',
  'West Bengal', 'Andaman and Nicobar Islands', 'Chandigarh',
  'Dadra and Nagar Haveli and Daman and Diu', 'Delhi', 'Jammu and Kashmir', 'Ladakh',
  'Lakshadweep', 'Puducherry',
]

const clients = ref([])
const loading = ref(true)
const searchQuery = ref('')

const modalOpen = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const submitting = ref(false)
const formError = ref('')
const deleteTarget = ref(null)
const sameAsClientName = ref(true)
const panManuallyEdited = ref(false)

const { draft: clientDraft, saveDraft: saveClientDraft, clearDraft: clearClientDraft, hasDraft: hasClientDraft, load: loadClientDraft } = useDraftStorage('client_create')
const showDraftBanner = ref(false)

const form = reactive({
  name: '',
  email: '',
  phone: '',
  gstin: '',
  customer_type: 'business',
  pan: '',
  salutation: '',
  address_line1: '',
  address_line2: '',
  city: '',
  state: '',
  pincode: '',
})

// Auto-save draft during add mode
watch(() => ({ ...form }), (val) => {
  if (modalOpen.value && !isEditing.value) {
    saveClientDraft({ ...val })
  }
}, { deep: true })

// Salutation mirrors the client name until the admin unchecks "Same as name".
watch(sameAsClientName, (same) => { if (same) form.salutation = '' })
watch(() => form.name, () => { if (sameAsClientName.value) form.salutation = '' })

function onSelectIndividual() {
  form.customer_type = 'individual'
  form.gstin = ''   // GSTIN is not applicable to individual clients
}

// Auto-fill PAN from the first 10 chars of a completed 15-char GSTIN, unless
// the admin has already typed a PAN by hand. Implemented via watch() (not a
// DOM @input listener) so it can't race with TaxIdField's own input handling.
let autofillingPan = false
watch(() => form.gstin, (val) => {
  if (panManuallyEdited.value) return
  if ((val || '').length === 15) {
    const extracted = panFromGstin(val)
    if (extracted) {
      autofillingPan = true
      form.pan = extracted
    }
  }
})
watch(() => form.pan, () => {
  if (autofillingPan) { autofillingPan = false; return }
  panManuallyEdited.value = true
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
  let list = [...clients.value]
  list.sort((a, b) => (b.id || 0) - (a.id || 0))
  const q = searchQuery.value.toLowerCase()
  if (!q) return list
  return list.filter(c =>
    c.name.toLowerCase().includes(q) ||
    (c.email || '').toLowerCase().includes(q) ||
    (c.phone || '').toLowerCase().includes(q) ||
    (c.gstin || '').toLowerCase().includes(q) ||
    (c.pan || '').toLowerCase().includes(q)
  )
})

function resetForm() {
  form.name = ''
  form.email = ''
  form.phone = ''
  form.gstin = ''
  form.customer_type = 'business'
  form.pan = ''
  form.salutation = ''
  form.address_line1 = ''
  form.address_line2 = ''
  form.city = ''
  form.state = ''
  form.pincode = ''
  sameAsClientName.value = true
  panManuallyEdited.value = false
  formError.value = ''
}

function restoreClientDraft() {
  if (!clientDraft.value) return
  const d = clientDraft.value
  Object.keys(form).forEach(k => { if (d[k] !== undefined) form[k] = d[k] })
  sameAsClientName.value = !d.salutation
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
  form.gstin = c.gstin || ''
  form.customer_type = c.customer_type || 'business'
  form.pan = c.pan || ''
  form.salutation = c.salutation || ''
  form.address_line1 = c.address_line1 || ''
  form.address_line2 = c.address_line2 || ''
  form.city = c.city || ''
  form.state = c.state || ''
  form.pincode = c.pincode || ''
  // Legacy clients with a freeform address but no structured fields yet: seed
  // line 1 from it so the text isn't invisible in the new form.
  if (!form.address_line1 && !form.city && c.address) {
    form.address_line1 = c.address.split('\n')[0] || ''
  }
  sameAsClientName.value = !c.salutation
  panManuallyEdited.value = true   // don't clobber an existing PAN on edit
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
      customer_type: form.customer_type,
      gstin: form.customer_type === 'business' ? (form.gstin || null) : null,
      pan: form.pan || null,
      salutation: sameAsClientName.value ? null : (form.salutation || null),
      address_line1: form.address_line1 || null,
      address_line2: form.address_line2 || null,
      city: form.city || null,
      state: form.state || null,
      pincode: form.pincode || null,
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

.type-badge {
  display: inline-block;
  padding: 2px 9px;
  border-radius: var(--radius-full);
  font-size: 10.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.type-business { background: var(--color-primary-light); color: var(--color-primary); }
.type-individual { background: #ede9fe; color: #6d28d9; }

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

/* ─── Type toggle ─── */
.type-toggles { display: flex; gap: 10px; margin-top: 4px; }
.type-toggle-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 16px;
  border: 1.5px solid var(--color-outline);
  background: var(--color-surface-dim);
  border-radius: var(--radius-lg);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-on-surface-variant);
  cursor: pointer;
  transition: all 0.15s;
}
.type-toggle-btn.active { background: var(--color-primary-light); border-color: var(--color-primary); color: var(--color-primary); }
.type-toggle-btn .material-symbols-outlined { font-size: 17px; }

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
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.inline-check {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  text-transform: none;
  letter-spacing: 0;
  font-weight: 600;
  font-size: 11px;
  color: var(--color-on-surface-variant);
  cursor: pointer;
}
.inline-check input { width: auto; height: auto; margin: 0; }

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
.form-field input:disabled { background: var(--color-surface-dim); color: var(--color-on-surface-variant); cursor: not-allowed; }
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
