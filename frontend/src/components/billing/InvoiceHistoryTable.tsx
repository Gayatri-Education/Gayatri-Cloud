'use client';

import React from 'react';
import { InvoiceReceiptItem } from '../../lib/types/billing';
import { Receipt, Calendar, FileText, CheckCircle2 } from 'lucide-react';

interface InvoiceHistoryTableProps {
  invoices: InvoiceReceiptItem[];
}

export default function InvoiceHistoryTable({ invoices }: InvoiceHistoryTableProps) {
  const safeInvoices = Array.isArray(invoices) ? invoices : [];

  return (
    <div className="space-y-4" data-testid="invoice-history-panel">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Receipt className="h-5 w-5 text-slate-700" />
          <h3 className="text-base font-bold text-slate-900">
            Invoices & Payment Receipts
          </h3>
        </div>
        <span className="text-xs text-slate-400">{safeInvoices.length} receipts on record</span>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-left text-sm" data-testid="invoices-table">
          <thead className="bg-slate-50 text-xs font-semibold text-slate-600 uppercase tracking-wider">
            <tr>
              <th className="px-5 py-3">Invoice Number</th>
              <th className="px-5 py-3">Date Issued</th>
              <th className="px-5 py-3">Line Items</th>
              <th className="px-5 py-3">Total Amount</th>
              <th className="px-5 py-3 text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {safeInvoices.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-5 py-8 text-center text-xs text-slate-400">
                  No payment receipts on record.
                </td>
              </tr>
            ) : (
              safeInvoices.map((inv) => (
                <tr key={inv.invoice_number} className="hover:bg-slate-50/75 transition" data-testid={`invoice-row-${inv.invoice_number}`}>
                  <td className="px-5 py-4 font-mono font-semibold text-xs text-slate-900">
                    {inv.invoice_number}
                  </td>
                  <td className="px-5 py-4 text-xs text-slate-500">
                    <div className="flex items-center gap-1.5">
                      <Calendar className="h-3.5 w-3.5 text-slate-400" />
                      {new Date(inv.issued_at).toLocaleDateString()}
                    </div>
                  </td>
                  <td className="px-5 py-4 text-xs text-slate-600">
                    {(Array.isArray(inv.line_items) ? inv.line_items : []).map((li, idx) => (
                      <div key={idx}>
                        {li.description} {li.quantity > 1 ? `(x${li.quantity})` : ''}
                      </div>
                    ))}
                  </td>
                  <td className="px-5 py-4 font-mono font-semibold text-slate-900 text-xs">
                    ${(inv.amount_cents / 100).toFixed(2)} USD
                  </td>
                  <td className="px-5 py-4 text-right">
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">
                      <CheckCircle2 className="h-3 w-3" /> Paid
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
