<template>
  <div class="invoice-preview" v-if="invoice">
    <div class="header">
      <div class="logo-block">
        <img src="http://localhost:8000/static/logo.jpg" class="logo-img" alt="Studio MH02 Logo" />
        <div class="firm-details">
          <div class="firm-name">Studio MH02 LLP</div>
          201, Prathamesh Apt, Mahant Road, Vile Parle East<br>
          Mumbai, Maharashtra 400507<br>
          GSTIN 27AEQFS5715Q1Z1<br>
          9769911588 | INFO@STUDIOMH02.COM
        </div>
      </div>
      <div class="invoice-type-block">
        <div class="invoice-type">{{ invoice.invoice_type === 'tax' ? 'TAX INVOICE' : 'PROFORMA INVOICE' }}</div>
        <div class="invoice-num" v-if="invoice.invoice_type === 'tax'">Invoice {{ invoice.invoice_number }}</div>
      </div>
    </div>

    <table class="meta-table">
      <tr>
        <td>
          <div class="section-label">Invoice Date:</div>
          <div>{{ formatDate(invoice.invoice_date) }}</div>
        </td>
        <td>
          <div class="section-label">Place of Supply:</div>
          <div>{{ invoice.place_of_supply || '' }}</div>
        </td>
      </tr>
      <tr>
        <td>
          <div class="section-label">Bill To</div>
          <div class="section-value">{{ invoice.bill_to_name || '' }}</div>
          <div>{{ invoice.bill_to_address || '' }}</div>
          <div>GSTIN {{ invoice.bill_to_gstin || '' }}</div>
        </td>
        <td>
          <div class="section-label">Ship To</div>
          <div class="section-value">{{ invoice.ship_to_name || '' }}</div>
          <div>{{ invoice.ship_to_address || '' }}</div>
          <div>GSTIN {{ invoice.ship_to_gstin || '' }}</div>
        </td>
      </tr>
      <tr>
        <td colspan="2">
          <div class="section-label">Project:</div>
          <div>{{ invoice.subject || '' }}</div>
        </td>
      </tr>
    </table>

    <table class="items-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Item and Description</th>
          <th>HSN/SAC</th>
          <th class="amount-col">Amount</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, idx) in invoice.items" :key="idx">
          <td>{{ idx + 1 }}</td>
          <td>{{ item.description }}</td>
          <td>{{ item.hsn_sac || '' }}</td>
          <td class="amount-col">₹{{ formatAmount(item.amount) }}</td>
        </tr>
        <tr class="items-spacer">
          <td colspan="4"></td>
        </tr>
      </tbody>
    </table>

    <div class="footer-section">
      <div class="footer-left">
        <div class="total-words">
          <strong>Total in Words</strong><br>
          {{ numberToWords(invoice.total || 0) }}
        </div>
        <br>
        <table class="bank-table" v-if="invoice.bank_account">
          <tr><td>Bank Name</td><td>{{ invoice.bank_account.bank_name }}</td></tr>
          <tr><td>Account</td><td>Type {{ invoice.bank_account.account_type }}</td></tr>
          <tr><td>Account Holder Name</td><td>{{ invoice.bank_account.account_holder_name }}</td></tr>
          <tr><td>IFSC Code</td><td>{{ invoice.bank_account.ifsc_code }}</td></tr>
        </table>
      </div>
      <div class="footer-right">
        <table class="totals-table">
          <tr>
            <td>Sub Total</td>
            <td class="amount-col">₹{{ formatAmount(invoice.subtotal) }}</td>
          </tr>
          <template v-if="invoice.tax_type === 'CGST_SGST'">
            <tr>
              <td>CGST (9%)</td>
              <td class="amount-col">₹{{ formatAmount(invoice.cgst) }}</td>
            </tr>
            <tr>
              <td>SGST (9%)</td>
              <td class="amount-col">₹{{ formatAmount(invoice.sgst) }}</td>
            </tr>
          </template>
          <template v-else>
            <tr>
              <td>IGST (18%)</td>
              <td class="amount-col">₹{{ formatAmount(invoice.igst) }}</td>
            </tr>
          </template>
          <tr class="total-row">
            <td>Total</td>
            <td class="amount-col">₹{{ formatAmount(invoice.total) }}</td>
          </tr>
        </table>
      </div>
    </div>

    <div class="tc-section">
      <div class="tc-label">Terms &amp; Conditions</div>
      <div class="tc-text">
        Kindly Process the payment to the bank details given below or in cheque. You are requested to revert in 7days, in order to seek clarity on this invoice. Please process the payment within 30 days from the date of receiving this order to avoid further charges.
      </div>
    </div>

    <div class="signatory-section">
      <div>
        <div class="signatory-name">Srujan Gadgil</div>
      </div>
      <div>
        <div class="signatory-label">Authorized Signatory</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  invoice: {
    type: Object,
    required: true
  }
})

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-GB')
}

const formatAmount = (val) => {
  return Number(val || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function numberToWords(amount) {
  const ones = ['', 'One', 'Two', 'Three', 'Four', 'Five',
    'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Eleven',
    'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
    'Seventeen', 'Eighteen', 'Nineteen']
  const tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty',
    'Sixty', 'Seventy', 'Eighty', 'Ninety']

  function wordsUnderThousand(n) {
    if (n === 0) return ''
    if (n < 20) return ones[n]
    if (n < 100) return tens[Math.floor(n/10)] + 
      (n%10 ? ' ' + ones[n%10] : '')
    return ones[Math.floor(n/100)] + ' Hundred' + 
      (n%100 ? ' ' + wordsUnderThousand(n%100) : '')
  }

  let n = Math.floor(amount)
  if (n === 0) return 'Zero Rupees Only'

  const crore = Math.floor(n / 10000000); n %= 10000000
  const lakh = Math.floor(n / 100000); n %= 100000
  const thousand = Math.floor(n / 1000); n %= 1000
  const rest = n

  const parts = []
  if (crore) parts.push(wordsUnderThousand(crore) + ' Crore')
  if (lakh) parts.push(wordsUnderThousand(lakh) + ' Lakh')
  if (thousand) parts.push(wordsUnderThousand(thousand) + ' Thousand')
  if (rest) parts.push(wordsUnderThousand(rest))

  return 'Indian Rupee ' + parts.join(' ') + ' Only'
}
</script>

<style scoped>
.invoice-preview {
  background: white;
  padding: 40px;
  max-width: 800px;
  margin: 0 auto;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  font-family: Arial, sans-serif;
  font-size: 11px;
  color: #000;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border: 1px solid #000;
  padding: 12px;
}

.logo-block {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-img {
  width: 60px;
  height: 60px;
  object-fit: contain;
}

.firm-details {
  font-size: 10px;
  line-height: 1.5;
}

.firm-name {
  font-size: 13px;
  font-weight: bold;
}

.invoice-type-block {
  text-align: right;
}

.invoice-type {
  font-size: 18px;
  font-weight: bold;
  letter-spacing: 1px;
}

.invoice-num {
  font-size: 11px;
  margin-top: 4px;
}

.meta-table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #000;
  border-top: none;
}

.meta-table td {
  border: 1px solid #000;
  padding: 8px 10px;
  vertical-align: top;
  width: 50%;
}

.section-label {
  font-size: 10px;
  color: #555;
  margin-bottom: 2px;
}

.section-value {
  font-weight: bold;
  margin-bottom: 2px;
}

.items-table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #000;
  border-top: none;
}

.items-table th {
  background: #f0f0f0;
  border: 1px solid #000;
  padding: 8px;
  text-align: left;
  font-size: 10px;
}

.items-table td {
  border: 1px solid #000;
  padding: 8px;
  vertical-align: top;
}

.items-table th:first-child, .items-table td:first-child { width: 40px; }
.items-table th:nth-child(3), .items-table td:nth-child(3) { width: 80px; }
.items-table th:last-child, .items-table td:last-child { width: 120px; }

.amount-col {
  text-align: right;
}

.items-spacer td {
  height: 80px;
  border: 1px solid #000;
}

.footer-section {
  display: flex;
  border: 1px solid #000;
  border-top: none;
}

.footer-left {
  width: 55%;
  padding: 12px;
  border-right: 1px solid #000;
}

.footer-right {
  width: 45%;
}

.totals-table {
  width: 100%;
  border-collapse: collapse;
}

.totals-table td {
  padding: 6px 12px;
  font-size: 11px;
  border-bottom: 1px solid #eee;
}

.total-row td {
  font-weight: bold;
  font-size: 13px;
  border-top: 2px solid #000;
  border-bottom: none;
}

.total-words {
  font-style: italic;
  font-size: 11px;
  margin-top: 4px;
}

.bank-table td {
  padding: 2px 0;
  font-size: 10px;
}
.bank-table td:first-child {
  width: 140px;
  color: #555;
}

.tc-section {
  border: 1px solid #000;
  border-top: none;
  padding: 10px 12px;
}

.tc-label {
  font-weight: bold;
  font-size: 11px;
  margin-bottom: 4px;
}

.tc-text {
  font-size: 10px;
  color: #333;
  line-height: 1.4;
}

.signatory-section {
  border: 1px solid #000;
  border-top: none;
  padding: 16px 12px;
  display: flex;
  justify-content: space-between;
}

.signatory-name {
  font-weight: bold;
  font-size: 12px;
}

.signatory-label {
  font-size: 10px;
  color: #555;
  margin-top: 2px;
}
</style>
