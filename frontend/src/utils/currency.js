/** Indian Rupee formatting (design: Intl.NumberFormat en-IN) */
export function formatInr(amount, fractionDigits = 0) {
  const n = Number(amount)
  if (Number.isNaN(n)) return '₹0'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(n)
}

export function formatInrPerHour(amount) {
  const n = Number(amount)
  if (Number.isNaN(n)) return '₹0.00/hr'
  const num = new Intl.NumberFormat('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(n)
  return `₹${num}/hr`
}

/** Live preview: ((base_pay × 13) / 12) / 160 — mirrors backend */
export function previewHourlyFromBasePay(basePay) {
  const bp = Number(basePay)
  if (!bp || bp <= 0) return null
  const raw = ((bp * 13) / 12) / 160
  return Math.round(raw * 100) / 100
}
