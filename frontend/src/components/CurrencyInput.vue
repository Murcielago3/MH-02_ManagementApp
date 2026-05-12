<template>
  <input
    type="text"
    v-model="displayValue"
    @blur="onBlur"
    @focus="onFocus"
    v-bind="$attrs"
  />
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: [Number, String], default: null }
})
const emit = defineEmits(['update:modelValue'])

const displayValue = ref('')
const isFocused = ref(false)

const inrFmt = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 })

function format(val) {
  if (val === null || val === undefined || val === '') return ''
  const num = Number(val)
  if (isNaN(num)) return val
  return inrFmt.format(num)
}

watch(() => props.modelValue, (newVal) => {
  if (!isFocused.value) {
    displayValue.value = format(newVal)
  }
}, { immediate: true })

watch(displayValue, (newVal) => {
  if (isFocused.value) {
    const raw = String(newVal).replace(/,/g, '')
    if (raw === '') {
      emit('update:modelValue', null)
      return
    }
    if (raw.endsWith('.')) {
      // emit string so it doesn't lose dot
      emit('update:modelValue', raw)
      return
    }
    const num = parseFloat(raw)
    emit('update:modelValue', isNaN(num) ? null : num)
  }
})

function onFocus() {
  isFocused.value = true
  if (props.modelValue !== null && props.modelValue !== undefined) {
    displayValue.value = String(props.modelValue)
  } else {
    displayValue.value = ''
  }
}

function onBlur() {
  isFocused.value = false
  const raw = String(displayValue.value).replace(/,/g, '')
  if (raw === '') {
    emit('update:modelValue', null)
    displayValue.value = ''
  } else {
    const num = parseFloat(raw)
    if (!isNaN(num)) {
      emit('update:modelValue', num)
      displayValue.value = format(num)
    } else {
      displayValue.value = format(props.modelValue)
    }
  }
}
</script>
