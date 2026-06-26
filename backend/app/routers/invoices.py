from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from pydantic import BaseModel
from datetime import date
from app.database import get_db
from app.models.invoice import Invoice, InvoiceItem
from app.models.bank_account import BankAccount
from app.models.client import Client
from app.auth import require_admin, get_current_user

router = APIRouter(prefix="/invoices", tags=["invoices"])

class InvoiceItemCreate(BaseModel):
    description: str
    hsn_sac: Optional[str] = None
    amount: float

class InvoiceCreate(BaseModel):
    invoice_type: str  # tax or proforma
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    place_of_supply: Optional[str] = None
    bill_to_name: Optional[str] = None
    bill_to_address: Optional[str] = None
    bill_to_gstin: Optional[str] = None
    ship_to_name: Optional[str] = None
    ship_to_address: Optional[str] = None
    ship_to_gstin: Optional[str] = None
    subject: Optional[str] = None
    project_id: Optional[int] = None
    client_id: Optional[int] = None
    bank_account_id: Optional[int] = None
    items: List[InvoiceItemCreate]

def determine_tax_type(gstin: Optional[str]) -> str:
    if gstin and gstin[:2] == "27":
        return "CGST_SGST"
    return "IGST"

def calculate_totals(items: list, tax_type: str) -> dict:
    subtotal = sum(item.amount for item in items)
    if tax_type == "CGST_SGST":
        cgst = round(subtotal * 0.09, 2)
        sgst = round(subtotal * 0.09, 2)
        igst = 0
        total = round(subtotal + cgst + sgst, 2)
    else:
        cgst = 0
        sgst = 0
        igst = round(subtotal * 0.18, 2)
        total = round(subtotal + igst, 2)
    return {
        "subtotal": subtotal,
        "cgst": cgst,
        "sgst": sgst,
        "igst": igst,
        "total": total
    }

@router.get("/")
async def list_invoices(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Invoice).options(selectinload(Invoice.project))
    )
    return result.scalars().all()

@router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.items),
            selectinload(Invoice.bank_account),
            selectinload(Invoice.client),
            selectinload(Invoice.project)
        )
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    return invoice

@router.post("/", status_code=201)
async def create_invoice(
    data: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    tax_type = determine_tax_type(data.bill_to_gstin)
    totals = calculate_totals(data.items, tax_type)

    invoice = Invoice(
        invoice_type=data.invoice_type,
        invoice_number=data.invoice_number,
        invoice_date=data.invoice_date or date.today(),
        place_of_supply=data.place_of_supply,
        bill_to_name=data.bill_to_name,
        bill_to_address=data.bill_to_address,
        bill_to_gstin=data.bill_to_gstin,
        ship_to_name=data.ship_to_name,
        ship_to_address=data.ship_to_address,
        ship_to_gstin=data.ship_to_gstin,
        subject=data.subject,
        project_id=data.project_id,
        client_id=data.client_id,
        bank_account_id=data.bank_account_id,
        created_by=current_user.id,
        tax_type=tax_type,
        **totals
    )
    db.add(invoice)
    await db.flush()

    for item_data in data.items:
        item = InvoiceItem(
            invoice_id=invoice.id,
            description=item_data.description,
            hsn_sac=item_data.hsn_sac,
            amount=item_data.amount
        )
        db.add(item)

    await db.commit()
    # Re-fetch with all relationships so bank_account / items / client are nested
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.items),
            selectinload(Invoice.bank_account),
            selectinload(Invoice.client),
            selectinload(Invoice.project),
        )
        .where(Invoice.id == invoice.id)
    )
    invoice = result.scalar_one()
    from app.routers.projects import _invalidate_reserve
    _invalidate_reserve()
    return invoice

@router.put("/{invoice_id}")
async def update_invoice(
    invoice_id: int,
    data: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.items))
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(404, "Invoice not found")

    tax_type = determine_tax_type(data.bill_to_gstin)
    totals = calculate_totals(data.items, tax_type)

    invoice.invoice_type = data.invoice_type
    invoice.invoice_number = data.invoice_number
    invoice.invoice_date = data.invoice_date or date.today()
    invoice.place_of_supply = data.place_of_supply
    invoice.bill_to_name = data.bill_to_name
    invoice.bill_to_address = data.bill_to_address
    invoice.bill_to_gstin = data.bill_to_gstin
    invoice.ship_to_name = data.ship_to_name
    invoice.ship_to_address = data.ship_to_address
    invoice.ship_to_gstin = data.ship_to_gstin
    invoice.subject = data.subject
    invoice.project_id = data.project_id
    invoice.client_id = data.client_id
    invoice.bank_account_id = data.bank_account_id
    invoice.tax_type = tax_type
    invoice.subtotal = totals["subtotal"]
    invoice.cgst = totals["cgst"]
    invoice.sgst = totals["sgst"]
    invoice.igst = totals["igst"]
    invoice.total = totals["total"]

    for old_item in invoice.items:
        await db.delete(old_item)
    await db.flush()

    for item_data in data.items:
        item = InvoiceItem(
            invoice_id=invoice.id,
            description=item_data.description,
            hsn_sac=item_data.hsn_sac,
            amount=item_data.amount
        )
        db.add(item)

    await db.commit()
    # Re-fetch with all relationships
    from sqlalchemy.orm import selectinload as _sl
    result2 = await db.execute(
        select(Invoice)
        .options(
            _sl(Invoice.items),
            _sl(Invoice.bank_account),
            _sl(Invoice.client),
            _sl(Invoice.project),
        )
        .where(Invoice.id == invoice_id)
    )
    invoice = result2.scalar_one()
    from app.routers.projects import _invalidate_reserve
    _invalidate_reserve()
    return invoice


@router.delete("/{invoice_id}", status_code=204)
async def delete_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    await db.delete(invoice)
    await db.commit()
    from app.routers.projects import _invalidate_reserve
    _invalidate_reserve()

@router.get("/{invoice_id}/pdf")
async def generate_invoice_pdf(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    from sqlalchemy.orm import selectinload
    from app.routers.settings import get_or_create_settings
    result = await db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.items),
            selectinload(Invoice.bank_account),
            selectinload(Invoice.client),
            selectinload(Invoice.project)
        )
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(404, "Invoice not found")

    # Guard: if bank_account relationship didn't load (lazy session), fetch it directly
    if invoice.bank_account_id and invoice.bank_account is None:
        from app.models.bank_account import BankAccount
        ba_res = await db.execute(
            select(BankAccount).where(BankAccount.id == invoice.bank_account_id)
        )
        invoice.bank_account = ba_res.scalar_one_or_none()

    settings = await get_or_create_settings(db)
    html = render_invoice_html(invoice, settings)

    from weasyprint import HTML
    pdf_bytes = HTML(string=html, base_url="http://127.0.0.1:8000").write_pdf()

    filename = f"invoice_{invoice.invoice_number or invoice.id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


def number_to_words(amount: float) -> str:
    """Convert number to Indian currency words"""
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six",
            "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve",
            "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen",
            "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty",
            "Sixty", "Seventy", "Eighty", "Ninety"]

    def words_under_thousand(n):
        if n == 0:
            return ""
        elif n < 20:
            return ones[n]
        elif n < 100:
            return tens[n // 10] + (" " + ones[n % 10] if n % 10 else "")
        else:
            return ones[n // 100] + " Hundred" + (
                " " + words_under_thousand(n % 100) if n % 100 else ""
            )

    n = int(amount)
    if n == 0:
        return "Zero Rupees Only"

    crore = n // 10000000
    n %= 10000000
    lakh = n // 100000
    n %= 100000
    thousand = n // 1000
    n %= 1000
    rest = n

    parts = []
    if crore:
        parts.append(words_under_thousand(crore) + " Crore")
    if lakh:
        parts.append(words_under_thousand(lakh) + " Lakh")
    if thousand:
        parts.append(words_under_thousand(thousand) + " Thousand")
    if rest:
        parts.append(words_under_thousand(rest))

    return "Indian Rupee " + " ".join(parts) + " Only"


def format_indian_currency(amount: float) -> str:
    # Formats a number to the Indian system, e.g., 531000.00 -> "5,31,000.00"
    s = f"{amount:.2f}"
    parts = s.split('.')
    integer_part = parts[0]
    decimal_part = parts[1]
    
    if len(integer_part) <= 3:
        return f"{integer_part}.{decimal_part}"
    
    last_three = integer_part[-3:]
    remaining = integer_part[:-3]
    
    # Insert comma every two digits in remaining part
    remaining_groups = []
    while len(remaining) > 2:
        remaining_groups.insert(0, remaining[-2:])
        remaining = remaining[:-2]
    if remaining:
        remaining_groups.insert(0, remaining)
        
    return f"{','.join(remaining_groups)},{last_three}.{decimal_part}"


def clean_place_of_supply(val: Optional[str]) -> str:
    if not val:
        return ""
    import re
    return re.sub(r'^\d+\s*-\s*|^\d+\s+|\s*\(\d+\)\s*$', '', val).strip()


def get_formatted_invoice_number(invoice) -> str:
    num_str = invoice.invoice_number
    if not num_str:
        return f"AO - {invoice.id:03d}"

    import re
    digits = re.findall(r'\d+', num_str)
    if digits:
        num_val = int(digits[-1])
        return f"AO - {num_val:03d}"
    else:
        clean = num_str.replace("AO-", "").replace("AO -", "").strip()
        return f"AO - {clean}"


def render_invoice_html(invoice, settings=None) -> str:
    # A4 printable area with 8mm margins = 194mm x 281mm.
    # Every section below has a fixed mm height. The items area gets whatever
    # remains so the whole invoice always fills exactly one A4 page.
    # The body is also hard-capped via overflow:hidden to guarantee one page.
    import base64, os
    logo_path = os.path.join(os.path.dirname(__file__), "..", "..", "static", "logo.jpg")
    logo_src = "static/logo.jpg"
    try:
        with open(logo_path, "rb") as f:
            logo_src = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()
    except Exception:
        pass

    HEADER_H = 32
    DATE_ROW_H = 8
    BILLSHIP_H = 20
    SUBJECT_H = 7
    ITEMS_THEAD_H = 7
    FOOTER_H = 36
    TC_H = 13
    SIG_H = 36
    PRINTABLE_H = 265
    ITEMS_AREA_H = PRINTABLE_H - (HEADER_H + DATE_ROW_H + BILLSHIP_H + SUBJECT_H + FOOTER_H + TC_H + SIG_H)
    ITEMS_ROW_H = 7
    num_items = len(invoice.items)
    spacer_height = max(0, ITEMS_AREA_H - ITEMS_THEAD_H - (num_items * ITEMS_ROW_H))

    items_rows = ""
    # !important needed: the items table is `.inner`, and `.inner td { border:0 !important }`
    # would otherwise strip these separators (that's why multi-item rows showed no
    # dividers in the PDF while the preview had them).
    base = 'padding:5px 6px; font-size:11px; border-top:1px solid #000 !important;'
    for i, item in enumerate(invoice.items, 1):
        items_rows += f"""
        <tr style="height:{ITEMS_ROW_H}mm;">
            <td style="{base} border-right:1px solid #000 !important; text-align:center;">{i}</td>
            <td style="{base} border-right:1px solid #000 !important;">{item.description}</td>
            <td style="{base} border-right:1px solid #000 !important;">{item.hsn_sac or ''}</td>
            <td style="{base} text-align:right;">&#8377;{format_indian_currency(float(item.amount))}</td>
        </tr>"""

    bank = invoice.bank_account
    bank_html = ""
    if bank:
        bank_html = f"""
        <tr>
            <td class="bank-label">Bank Name</td>
            <td>{bank.bank_name}</td>
        </tr>
        <tr>
            <td class="bank-label">Account</td>
            <td>Type {bank.account_type}</td>
        </tr>
        <tr>
            <td class="bank-label">Account Holder Name</td>
            <td>{bank.account_holder_name}</td>
        </tr>
        <tr>
            <td class="bank-label">Account Number</td>
            <td>{bank.account_number}</td>
        </tr>
        <tr>
            <td class="bank-label">IFSC Code</td>
            <td>{bank.ifsc_code}</td>
        </tr>
        """

    invoice_type_label = "TAX INVOICE" if invoice.invoice_type == "tax" \
        else "PROFORMA INVOICE"
    formatted_num = get_formatted_invoice_number(invoice)
    invoice_number_html = f"""
        <div class="invoice-num">{formatted_num}</div>
    """ if formatted_num else ""

    if invoice.tax_type == "CGST_SGST":
        tax_rows = f"""
        <tr>
            <td class="tot-label">CGST(9%)</td>
            <td class="tot-val">₹{format_indian_currency(float(invoice.cgst))}</td>
        </tr>
        <tr>
            <td class="tot-label">SGST(9%)</td>
            <td class="tot-val">₹{format_indian_currency(float(invoice.sgst))}</td>
        </tr>"""
    else:
        tax_rows = f"""
        <tr>
            <td class="tot-label">IGST(18%)</td>
            <td class="tot-val">₹{format_indian_currency(float(invoice.igst))}</td>
        </tr>"""

    total_words = number_to_words(float(invoice.total))
    subtotal = float(invoice.subtotal)
    total = float(invoice.total)
    date_str = invoice.invoice_date.strftime("%d/%m/%Y") if invoice.invoice_date else ""
    subject_val = invoice.subject or ''

    # Company profile — pulled from Settings; fall back to historical hardcoded values
    company_name = (settings.company_name if settings and settings.company_name else "Studio MH02 LLP")
    company_address = (settings.company_address if settings and settings.company_address
                       else "201, Prathamesh Apt, Mahant Road, Vile Parle East\nMumbai, Maharashtra 400507")
    company_gstin = (settings.company_gstin if settings and settings.company_gstin else "27AEQFS5715Q1Z1")
    company_phone = (settings.company_phone if settings and settings.company_phone else "9769911588")
    company_email = (settings.company_email if settings and settings.company_email else "INFO@STUDIOMH02.COM")
    signatory_name = (settings.company_signatory_name if settings and settings.company_signatory_name else "Srujan Gadgil")
    signatory_role = (settings.company_signatory_role if settings and settings.company_signatory_role else "Partner")
    company_address_html = company_address.replace('\n', '<br>')

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset=\"UTF-8\">
<style>
  @page {{ size: A4; margin: 8mm; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{
    font-family: Arial, sans-serif;
    font-size: 7px;
    color: #000;
    line-height: 1.25;
    width: 194mm;
    height: 281mm;
    max-height: 281mm;
    overflow: hidden;
  }}
  .sheet {{
    width: 100%;
    height: 100%;
    max-height: 281mm;
    overflow: hidden;
    border-collapse: collapse;
    table-layout: fixed;
    page-break-inside: avoid;
  }}
  .sheet {{ border: 1px solid #000; }}
  .sheet > tbody > tr > td {{ border: 1px solid #000; vertical-align: top; }}
  .inner, .inner td, .inner th, .bank-tbl, .bank-tbl td, .totals-tbl, .totals-tbl td {{ border: 0 !important; }}
  .inner {{ width: 100%; height: 100%; border-collapse: collapse; table-layout: fixed; }}
  .inner td {{ vertical-align: top; padding: 0; }}

  /* ===== HEADER ===== */
  .hdr-left {{ width: 60%; padding: 5mm !important; vertical-align: middle !important; }}
  .hdr-right {{ width: 40%; padding: 5mm 8mm 5mm 5mm !important; vertical-align: middle !important; text-align: right; }}
  .logo-img {{ width: 80px; height: 80px; object-fit: contain; display: block; }}
  .firm-name {{ font-size: 12px; font-weight: bold; margin-bottom: 2px; }}
  .firm-details {{ font-size: 7.5px; line-height: 1.4; color: #222; }}
  .invoice-type {{ font-size: 18px; font-weight: bold; letter-spacing: 0.6px; }}
  .invoice-num {{ font-size: 9px; margin-top: 4px; color: #333; }}

  /* ===== META ===== */
  .meta-label {{ font-size: 8.5px; color: #555; margin-bottom: 2px; }}
  .meta-val-bold {{ font-weight: bold; font-size: 10.5px; margin-bottom: 2px; }}
  .meta-val {{ font-size: 10.5px; font-weight: 600; }}
  .meta-cell {{ padding: 5px 8px; }}

  /* ===== ITEMS ===== */
  .items-head td {{
    background: #f5f5f5;
    padding: 5px 6px;
    font-size: 7px;
    font-weight: 600;
  }}
  .items-row td {{ padding: 5px 6px; font-size: 7px; }}
  .col-num  {{ width: 32px; text-align: center; }}
  .col-hsn  {{ width: 95px; }}
  .col-amt  {{ width: 110px; text-align: right; }}

  /* ===== FOOTER (bank + totals) — bumped to match the +3 address size ===== */
  .foot-left {{ width: 55%; padding: 8px 10px; }}
  .foot-right {{ width: 45%; padding: 8px 10px; }}
  .bank-tbl td {{ padding: 2px 0; font-size: 10.5px; }}
  .bank-label {{ width: 150px; color: #444; font-weight: 600; }}
  .totals-tbl td {{ padding: 3px 6px; font-size: 10.5px; }}
  .tot-val {{ text-align: right; }}
  .total-final td {{
    font-weight: bold;
    font-size: 11.5px;
    border-top: 1.5px solid #000 !important;
    padding-top: 5px;
  }}
  .words-section {{
    margin-top: 8px;
    padding-top: 6px;
    border-top: 1px solid #ccc;
    font-size: 10px;
    font-style: italic;
    color: #333;
  }}
  .words-label {{ font-weight: bold; font-style: normal; margin-bottom: 2px; }}

  /* ===== T&C + SIGNATORY ===== */
  .tc-cell {{ padding: 6px 10px; font-size: 9.5px; line-height: 1.4; }}
  .tc-label {{ font-weight: bold; font-size: 10.5px; margin-bottom: 3px; }}
  .sig-cell {{ padding: 8px 10px; font-size: 10.5px; }}
  .sig-name {{ font-weight: bold; font-size: 11.5px; margin-top: 22mm; }}
  .sig-role {{ color: #444; margin-top: 2px; }}
  .auth-label {{ font-size: 9.5px; color: #555; }}
</style>
</head>
<body>
<table class=\"sheet\">
  <colgroup><col style=\"width:50%\"><col style=\"width:50%\"></colgroup>
  <tbody>
    <tr style=\"height:{HEADER_H}mm;\">
      <td colspan=\"2\" style=\"padding:0;\">
        <table class=\"inner\"><tr>
          <td class=\"hdr-left\">
            <table style=\"border-collapse:collapse;\"><tr>
              <td style=\"vertical-align:middle; padding-right:10px;\">
                <img src=\"{logo_src}\" class=\"logo-img\" alt=\"Logo\"/>
              </td>
              <td style=\"vertical-align:middle;\">
                <div class=\"firm-name\">{company_name}</div>
                <div class=\"firm-details\">
                  {company_address_html}<br>
                  {company_phone} | {company_email}<br>
                  GSTIN {company_gstin}
                </div>
              </td>
            </tr></table>
          </td>
          <td class=\"hdr-right\">
            <div class=\"invoice-type\">{invoice_type_label}</div>
            {invoice_number_html}
          </td>
        </tr></table>
      </td>
    </tr>
    <tr style=\"height:{DATE_ROW_H}mm;\">
      <td style=\"padding:5px 8px;\">
        <span class=\"meta-label\">Invoice Date:</span> <span class=\"meta-val\">{date_str}</span>
      </td>
      <td style=\"padding:5px 8px;\">
        <span class=\"meta-label\">Place of Supply:</span> <span class=\"meta-val\">{clean_place_of_supply(invoice.place_of_supply)}</span>
      </td>
    </tr>
    <tr style=\"height:{BILLSHIP_H}mm;\">
      <td style=\"padding:5px 8px;\">
        <div class=\"meta-label\">Bill To</div>
        <div class=\"meta-val-bold\">{invoice.bill_to_name or ''}</div>
        <div style=\"font-size:10.5px; line-height:1.4; margin-top:2px;\">
          {(invoice.bill_to_address or '').replace(chr(10), '<br>')}
          {'<br>GSTIN ' + invoice.bill_to_gstin if invoice.bill_to_gstin else ''}
        </div>
      </td>
      <td style=\"padding:5px 8px;\">
        <div class=\"meta-label\">Ship To</div>
        <div class=\"meta-val-bold\">{invoice.ship_to_name or ''}</div>
        <div style=\"font-size:10.5px; line-height:1.4; margin-top:2px;\">
          {(invoice.ship_to_address or '').replace(chr(10), '<br>')}
          {'<br>GSTIN ' + invoice.ship_to_gstin if invoice.ship_to_gstin else ''}
        </div>
      </td>
    </tr>
    <tr style=\"height:{SUBJECT_H}mm;\">
      <td colspan=\"2\" style=\"padding:5px 8px;\">
        <span class=\"meta-label\">Subject:</span> {subject_val}
      </td>
    </tr>
    <tr>
      <td colspan=\"2\" style=\"padding:0;\">
        <table class=\"inner\" style=\"border-collapse:collapse;\">
          <colgroup><col style=\"width:32px\"><col><col style=\"width:95px\"><col style=\"width:110px\"></colgroup>
          <tr class=\"items-head\" style=\"height:{ITEMS_THEAD_H}mm;\">
            <td class=\"col-num\" style=\"border-right:1px solid #000 !important;\">#</td>
            <td style=\"padding:5px 6px; border-right:1px solid #000 !important;\">Service / Description</td>
            <td style=\"padding-left:6px; border-right:1px solid #000 !important;\">HSN/SAC</td>
            <td style=\"padding-right:6px; text-align:right;\">Amount</td>
          </tr>
          {items_rows}
          <tr style=\"height:{spacer_height}mm;\">
            <td style=\"border-right:1px solid #000 !important;\"></td>
            <td style=\"border-right:1px solid #000 !important;\"></td>
            <td style=\"border-right:1px solid #000 !important;\"></td>
            <td></td>
          </tr>
        </table>
      </td>
    </tr>
    <tr style=\"height:{FOOTER_H}mm;\">
      <td class=\"foot-left\">
        <table class=\"bank-tbl\" style=\"border-collapse:collapse;\">{bank_html}</table>
      </td>
      <td class=\"foot-right\">
        <table class=\"totals-tbl\" style=\"width:100%; border-collapse:collapse;\">
          <tr>
            <td>Sub Total</td>
            <td class=\"tot-val\">₹{format_indian_currency(subtotal)}</td>
          </tr>
          {tax_rows}
          <tr class=\"total-final\">
            <td>Total</td>
            <td class=\"tot-val\">₹{format_indian_currency(total)}</td>
          </tr>
        </table>
        <div class=\"words-section\">
          <div class=\"words-label\">Total in Words</div>
          {total_words}
        </div>
      </td>
    </tr>
    <tr style=\"height:{TC_H}mm;\">
      <td colspan=\"2\" class=\"tc-cell\">
        <div class=\"tc-label\">Terms &amp; Conditions</div>
        Kindly Process the payment to the bank details given below or in cheque.
        You are requested to revert in 7 days, in order to seek clarity on this
        invoice. Please process the payment within 30 days from the date of
        receiving this order to avoid further charges.
      </td>
    </tr>
    <tr style=\"height:{SIG_H}mm;\">
      <td colspan=\"2\" class=\"sig-cell\">
        <div class=\"auth-label\">Authorized Signatory</div>
        <div class=\"sig-name\">{signatory_name}</div>
        <div class=\"sig-role\">{signatory_role}</div>
        <div class=\"sig-role\">{company_name}</div>
      </td>
    </tr>
  </tbody>
</table>
</body></html>"""
