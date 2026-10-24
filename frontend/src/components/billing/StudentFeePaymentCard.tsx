'use client';

import React, { useState } from 'react';
import { StudentFeePayment } from '../../lib/types/billing';
import { CreditCard, CheckCircle2, Clock, AlertTriangle, ShieldCheck } from 'lucide-react';

interface StudentFeePaymentCardProps {
  fees: StudentFeePayment[];
  onPayFee: (feeId: string, idempotencyKey: string) => Promise<void>;
}

export default function StudentFeePaymentCard({ fees, onPayFee }: StudentFeePaymentCardProps) {
  const safeFees = Array.isArray(fees) ? fees : [];
  const [payingFeeId, setPayingFeeId] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handlePay = async (feeId: string) => {
    try {
      setPayingFeeId(feeId);
      setSuccessMessage(null);
      const idempotencyKey = `pay-${feeId}-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
      await onPayFee(feeId, idempotencyKey);
      setSuccessMessage('Payment completed successfully. Invoice receipt generated.');
    } finally {
      setPayingFeeId(null);
    }
  };

  return (
    <div className="space-y-4" data-testid="student-fee-payment-panel">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CreditCard className="h-5 w-5 text-sky-600" />
          <h3 className="text-base font-bold text-slate-900">
            Assigned Course & Tuition Fees
          </h3>
        </div>
        <span className="text-xs text-slate-400">{fees.length} fee items</span>
      </div>

      {successMessage && (
        <div className="flex items-center gap-2 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800 border border-emerald-200" data-testid="payment-success-msg">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
          <span>{successMessage}</span>
        </div>
      )}

      {safeFees.length === 0 ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-xs text-slate-400">
          No tuition or institutional fee obligations on record.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {safeFees.map((f) => (
            <div
              key={f.fee_id}
              className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
              data-testid={`student-fee-card-${f.fee_id}`}
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-900 text-sm">{f.title}</span>
                  {f.is_paid ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800" data-testid="fee-status-paid">
                      <CheckCircle2 className="h-3 w-3" />
                      Paid
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-800" data-testid="fee-status-due">
                      <Clock className="h-3 w-3" />
                      Payment Due
                    </span>
                  )}
                </div>

                <p className="mt-1 text-xs text-slate-500">{f.description || 'Institutional fee schedule item.'}</p>

                <div className="mt-4 flex items-baseline gap-2">
                  <span className="text-2xl font-black text-slate-900">
                    ${(f.amount_cents / 100).toFixed(2)}
                  </span>
                  <span className="text-xs text-slate-400">{f.currency}</span>
                </div>

                {f.due_date && (
                  <p className="mt-1 text-xs text-slate-500">
                    Due: {new Date(f.due_date).toLocaleDateString()}
                  </p>
                )}
              </div>

              <div className="mt-6 border-t border-slate-100 pt-3">
                {f.is_paid ? (
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>Reference: {f.payment_reference || 'N/A'}</span>
                    <span>Paid on {f.paid_at ? new Date(f.paid_at).toLocaleDateString() : 'N/A'}</span>
                  </div>
                ) : (
                  <button
                    type="button"
                    disabled={payingFeeId === f.fee_id}
                    onClick={() => handlePay(f.fee_id)}
                    className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-sky-600 py-2 text-xs font-semibold text-white shadow-sm hover:bg-sky-700 disabled:opacity-50 transition"
                    data-testid={`btn-pay-fee-${f.fee_id}`}
                  >
                    <CreditCard className="h-3.5 w-3.5" />
                    <span>{payingFeeId === f.fee_id ? 'Processing...' : 'Pay Fee Online'}</span>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
