// PAN / GSTIN structural + checksum validation, mirroring backend/app/utils/tax_ids.py
// exactly (same Luhn mod-36 algorithm) so the live form popover and the server's
// authoritative check never disagree.

const CODEPOINTS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

const PAN_RE = /^[A-Z]{5}[0-9]{4}[A-Z]$/
// digits 1-2 state code, 3-12 PAN, 13 entity code (1-9 or A-Z), 14 fixed 'Z', 15 checksum
const GSTIN_STRUCT_RE = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$/

export function gstinChecksumChar(first14) {
  let total = 0
  let factor = 1
  for (const ch of first14) {
    const value = CODEPOINTS.indexOf(ch)
    const product = value * factor
    const q = Math.floor(product / 36)
    const r = product % 36
    total += q + r
    factor = factor === 1 ? 2 : 1
  }
  const checksumIndex = (36 - (total % 36)) % 36
  return CODEPOINTS[checksumIndex]
}

/** Returns an error message string if invalid, else null. */
export function validatePan(pan) {
  if (!PAN_RE.test(pan)) {
    return 'Invalid PAN format (expected 5 letters + 4 digits + 1 letter, e.g. AAAAA9999A)'
  }
  return null
}

/** Returns an error message string if invalid, else null. Checks structure AND checksum. */
export function validateGstin(gstin) {
  if (!GSTIN_STRUCT_RE.test(gstin)) {
    return 'Invalid GSTIN format (expected 15 characters: state code + PAN + entity code + Z + checksum)'
  }
  const expected = gstinChecksumChar(gstin.slice(0, 14))
  if (gstin[14] !== expected) {
    return `Invalid GSTIN checksum (expected '${expected}' as the last character)`
  }
  return null
}

/** Extract the embedded 10-char PAN (chars 3-12) from a GSTIN, if long enough. */
export function panFromGstin(gstin) {
  if (gstin && gstin.length >= 12) return gstin.slice(2, 12)
  return null
}
