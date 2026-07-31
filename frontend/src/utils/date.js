/**
 * Local calendar date as YYYY-MM-DD.
 *
 * Never use `d.toISOString().split('T')[0]` for this. toISOString() converts to
 * UTC first, so in any timezone ahead of UTC (IST is +5:30) it returns the
 * PREVIOUS day - always for a Date built at local midnight, and between 00:00
 * and 05:30 local for `new Date()`. That silently shifted calendar cells,
 * "today" highlights and deadline lookups by a day.
 */
export function toLocalDateStr(d = new Date()) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

/** Today as YYYY-MM-DD in the viewer's timezone. */
export function todayStr() {
  return toLocalDateStr(new Date())
}
