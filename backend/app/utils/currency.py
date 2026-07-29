"""Indian-grouped rupee formatting — the single source of truth for how money
renders in backend-generated text (Slack messages, audit-log summaries, PDFs).

Python's ``{:,}`` groups in thousands (1,000,000); India groups the last three
digits, then every two after that (10,00,000). Use ``format_inr`` everywhere
instead of ``f"{x:,.0f}"``.
"""


def format_inr(value, decimals: int = 0) -> str:
    """Indian-grouped number string, no currency symbol.

        531000      -> "5,31,000"
        1234567.5   -> "12,34,568"   (decimals=0, rounded)
        531000, 2   -> "5,31,000.00"

    Callers that want the symbol prepend ``₹`` themselves.
    """
    try:
        n = float(value or 0)
    except (TypeError, ValueError):
        n = 0.0
    neg = n < 0
    s = f"{abs(n):.{decimals}f}"
    int_part, _, dec_part = s.partition(".")

    if len(int_part) > 3:
        last3 = int_part[-3:]
        rest = int_part[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        int_part = ",".join(groups) + "," + last3

    out = f"{int_part}.{dec_part}" if dec_part else int_part
    return ("-" if neg else "") + out


def rupees(value, decimals: int = 0) -> str:
    """``format_inr`` with a ₹ prefix, e.g. 531000 -> '₹5,31,000'."""
    return "₹" + format_inr(value, decimals)
