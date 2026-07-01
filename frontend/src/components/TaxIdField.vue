<template>
  <div class="taxid-wrap">
    <div v-if="showError" class="taxid-popover">
      <span class="material-symbols-outlined">error</span>
      {{ error }}
    </div>
    <input
      ref="inputRef"
      type="text"
      :value="modelValue"
      :maxlength="kind === 'pan' ? 10 : 15"
      :class="{ 'taxid-invalid': showError }"
      @input="onInput"
      @blur="touched = true"
      v-bind="$attrs"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { validatePan, validateGstin } from '../utils/taxIds'

// $attrs (placeholder, required, etc.) are placed on the inner <input> only —
// don't also let Vue auto-fallthrough them onto the wrapper <div>.
defineOptions({ inheritAttrs: false })

const props = defineProps({
  modelValue: { type: String, default: '' },
  kind: { type: String, default: 'gstin' }, // 'gstin' | 'pan'
})
const emit = defineEmits(['update:modelValue'])

const inputRef = ref(null)
const touched = ref(false)

function onInput(e) {
  // Auto-caps: GST/PAN are always uppercase.
  const v = e.target.value.toUpperCase()
  emit('update:modelValue', v)
}

const expectedLen = computed(() => (props.kind === 'pan' ? 10 : 15))

const error = computed(() => {
  const v = (props.modelValue || '').trim()
  if (!v) return null
  return props.kind === 'pan' ? validatePan(v) : validateGstin(v)
})

// Only surface the popover once the field looks "done" (full length reached,
// or the user has moved on) — avoids flagging every valid-so-far keystroke.
const showError = computed(
  () => !!error.value && (touched.value || (props.modelValue || '').length >= expectedLen.value)
)

defineExpose({ error })
</script>

<style scoped>
.taxid-wrap { position: relative; }
.taxid-invalid { border-color: var(--color-error) !important; }
.taxid-invalid:focus { box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.12) !important; }

.taxid-popover {
  position: absolute;
  bottom: calc(100% + 6px);
  left: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 6px;
  max-width: 320px;
  padding: 7px 11px;
  background: #b91c1c;
  color: #fff;
  border-radius: var(--radius-md);
  font-size: 11.5px;
  font-weight: 600;
  line-height: 1.35;
  box-shadow: 0 4px 12px rgba(0,0,0,0.18);
  animation: taxid-pop-in 0.12s ease;
}
.taxid-popover::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 14px;
  border: 5px solid transparent;
  border-top-color: #b91c1c;
}
.taxid-popover .material-symbols-outlined { font-size: 14px; flex-shrink: 0; }

@keyframes taxid-pop-in {
  from { opacity: 0; transform: translateY(3px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
