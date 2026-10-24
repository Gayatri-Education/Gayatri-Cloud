'use client';

import React, { useState } from 'react';
import { InstitutionFeeItem } from '../../lib/types/billing';
import { Building2, Plus, Calendar, DollarSign, CheckCircle2 } from 'lucide-react';

interface InstitutionFeeManagerProps {
  fees: InstitutionFeeItem[];
  onCreateFee: (payload: {
    title: string;
    description: string;
    amount_cents: number;
    currency: string;
    due_date?: string;
  }) => Promise<void>;
}

export default function InstitutionFeeManager({ fees, onCreateFee }: InstitutionFeeManagerProps) {
  const safeFees = Array.isArray(fees) ? fees : [];
  const [showModal, setShowModal] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [amountDollars, setAmountDollars] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const dollars = parseFloat(amountDollars);
    if (isNaN(dollars) || dollars <= 0) {
      setErrorMsg('Please enter a valid fee amount greater than zero.');
      return;
    }

    try {
      setSaving(true);
      setErrorMsg(null);
      await onCreateFee({
        title: title.trim(),
        description: description.trim(),
        amount_cents: Math.round(dollars * 100),
        currency: 'USD',
        due_date: dueDate ? new Date(dueDate).toISOString() : undefined,
      });
      setShowModal(false);
      setTitle('');
      setDescription('');
      setAmountDollars('');
      setDueDate('');
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to create fee schedule');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="institution-fee-manager">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-indigo-600" />
            <h3 className="text-base font-bold text-slate-900">
              Institutional Fee Schedules & Collections
            </h3>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Configure tuition, laboratory, and examination fee schedules payable by enrolled learners or guardians.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700"
          data-testid="btn-create-fee-modal"
        >
          <Plus className="h-4 w-4" />
          Create Fee Schedule
        </button>
      </div>

      {/* Fees List */}
      <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-left text-sm" data-testid="institution-fees-table">
          <thead className="bg-slate-50 text-xs font-semibold text-slate-600 uppercase tracking-wider">
            <tr>
              <th className="px-5 py-3">Fee Title</th>
              <th className="px-5 py-3">Description</th>
              <th className="px-5 py-3">Amount</th>
              <th className="px-5 py-3">Due Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {safeFees.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-5 py-8 text-center text-xs text-slate-400">
                  No institutional fee schedules configured yet.
                </td>
              </tr>
            ) : (
              safeFees.map((fee) => (
                <tr key={fee.id} className="hover:bg-slate-50/75 transition" data-testid={`fee-row-${fee.id}`}>
                  <td className="px-5 py-4 font-semibold text-slate-900">{fee.title}</td>
                  <td className="px-5 py-4 text-xs text-slate-500">{fee.description || '—'}</td>
                  <td className="px-5 py-4 font-mono font-semibold text-slate-900">
                    ${(fee.amount_cents / 100).toFixed(2)} {fee.currency}
                  </td>
                  <td className="px-5 py-4 text-xs text-slate-500">
                    {fee.due_date ? new Date(fee.due_date).toLocaleDateString() : 'No due date'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-xl">
            <h4 className="text-base font-bold text-slate-900 mb-4">Create Fee Schedule</h4>

            {errorMsg && (
              <div className="mb-4 rounded-xl bg-rose-50 p-3 text-xs text-rose-700 border border-rose-200">
                {errorMsg}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">
                  Fee Title
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Physics Lab Materials Fee"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none"
                  data-testid="input-fee-title"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">
                  Description
                </label>
                <textarea
                  rows={2}
                  placeholder="Optional context for students and parents..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">
                    Amount (USD)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    placeholder="35.00"
                    value={amountDollars}
                    onChange={(e) => setAmountDollars(e.target.value)}
                    className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none"
                    data-testid="input-fee-amount"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">
                    Due Date
                  </label>
                  <input
                    type="date"
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50"
                  data-testid="btn-submit-fee"
                >
                  {saving ? 'Creating...' : 'Create Fee'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
