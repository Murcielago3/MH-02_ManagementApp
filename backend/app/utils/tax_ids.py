"""PAN / GSTIN structural + checksum validation for Indian tax IDs.

GSTIN structure (15 chars): 2-digit state code + 10-char PAN + 1-char entity
code (1-9 or A-Z) + fixed 'Z' + 1-char checksum.

The checksum (15th char) uses the GSTN "Luhn mod 36" algorithm: each of the
first 14 characters is assigned a base-36 value (0-9, A-Z=10-35), multiplied by
an alternating factor (1,2,1,2,...), reduced via divmod(product, 36) -> quotient
+ remainder, summed, and the check character is (36 - sum % 36) % 36 mapped back
through the same alphabet. Verified against multiple independent published
references (not just structural regex) since a wrong algorithm would reject
valid GSTINs, which is worse than not checking at all.
"""
import re

CODEPOINTS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
# digits 1-2 state code, 3-12 PAN, 13 entity code (1-9 or A-Z), 14 fixed 'Z', 15 checksum
GSTIN_STRUCT_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")


def gstin_checksum_char(first14: str) -> str:
    """Compute the 15th (checksum) character for a 14-char GSTIN prefix."""
    total = 0
    factor = 1
    for ch in first14:
        value = CODEPOINTS.index(ch)
        product = value * factor
        q, r = divmod(product, 36)
        total += q + r
        factor = 2 if factor == 1 else 1
    checksum_index = (36 - (total % 36)) % 36
    return CODEPOINTS[checksum_index]


def validate_pan(pan: str) -> str | None:
    """Returns an error message if invalid, else None."""
    if not PAN_RE.match(pan):
        return "Invalid PAN format (expected 5 letters + 4 digits + 1 letter, e.g. AAAAA9999A)"
    return None


def validate_gstin(gstin: str) -> str | None:
    """Returns an error message if invalid, else None. Checks structure AND checksum."""
    if not GSTIN_STRUCT_RE.match(gstin):
        return "Invalid GSTIN format (expected 15 characters: state code + PAN + entity code + Z + checksum)"
    expected = gstin_checksum_char(gstin[:14])
    if gstin[14] != expected:
        return f"Invalid GSTIN checksum (expected '{expected}' as the last character)"
    return None


def pan_from_gstin(gstin: str) -> str | None:
    """Extract the embedded 10-char PAN (chars 3-12) from a GSTIN, if long enough."""
    if gstin and len(gstin) >= 12:
        return gstin[2:12]
    return None
