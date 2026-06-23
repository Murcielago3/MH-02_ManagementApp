<template>
  <input
    ref="inputRef"
    type="text"
    inputmode="decimal"
    :value="displayValue"
    @input="onInput"
    @blur="onBlur"
    @focus="onFocus"
    v-bind="$attrs"
  />
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  modelValue: { type: [Number, String], default: null },
})
const emit = defineEmits(['update:modelValue'])

const displayValue = ref('')
const inputRef = ref(null)

const inrFmt = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 })

// Format a raw numeric string to Indian grouping while preserving the
// fractional part and a trailing decimal-in-progress (e.g. "1234." → "1,234.").
function formatRaw(raw) {
  if (raw == null) return ''
  const str = String(raw).replace(/[^0-9.]/g, '')
  if (str === '') return ''
  // Keep only the first dot, drop the rest
  const firstDot = str.indexOf('.')
  let intPart = firstDot === -1 ? str : str.slice(0, firstDot)
  let fracPart = firstDot === -1 ? '' : str.slice(firstDot + 1).replace(/\./g, '')
  // Strip leading zeros (but keep a single zero before a decimal)
  intPart = intPart.replace(/^0+(?=\d)/, '')
  if (intPart === '') intPart = '0'
  const intNum = Number(intPart)
  const grouped = isNaN(intNum) ? intPart : inrFmt.format(intNum)
  if (firstDot === -1) return grouped
  // Cap fractional digits at 2
  return `${grouped}.${fracPart.slice(0, 2)}`
}

function toNumber(raw) {
  if (raw == null || raw === '') return null
  const cleaned = String(raw).replace(/,/g, '')
  if (cleaned === '' || cleaned === '.') return null
  const n = parseFloat(cleaned)
  return isNaN(n) ? null : n
}

// Count digits/dots up to a given position in a string (everything that
// isn't a grouping comma). Used to preserve the caret position across the
// reformat that happens on input.
function countSignificant(str, upToIndex) {
  let count = 0
  for (let i = 0; i < upToIndex && i < str.length; i++) {
    if (str[i] !== ',') count++
  }
  return count
}

function findCaretFromSignificant(str, target) {
  let count = 0
  for (let i = 0; i < str.length; i++) {
    if (str[i] !== ',') count++
    if (count === target) return i + 1
  }
  return str.length
}

watch(
  () => props.modelValue,
  (val) => {
    // Only reset external value into display when the input isn't focused —
    // otherwise typing would fight with the model echo.
    if (document.activeElement !== inputRef.value) {
      displayValue.value = formatRaw(val)
    }
  },
  { immediate: true }
)

function onInput(e) {
  const el = e.target
  const caret = el.selectionStart ?? el.value.length
  const significantBefore = countSignificant(el.value, caret)
  const next = formatRaw(el.value)
  displayValue.value = next
  emit('update:modelValue', toNumber(next))
  nextTick(() => {
    if (!inputRef.value) return
    const pos = findCaretFromSignificant(inputRef.value.value, significantBefore)
    try {
      inputRef.value.setSelectionRange(pos, pos)
    } catch (_) { /* some input types don't support setSelectionRange */ }
  })
}

function onFocus() {
  if (props.modelValue == null || props.modelValue === '') {
    displayValue.value = ''
  } else {
    displayValue.value = formatRaw(props.modelValue)
  }
}

function onBlur() {
  const n = toNumber(displayValue.value)
  emit('update:modelValue', n)
  displayValue.value = n == null ? '' : formatRaw(n)
}
</script>
