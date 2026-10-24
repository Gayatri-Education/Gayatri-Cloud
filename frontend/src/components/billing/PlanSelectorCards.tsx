'use client';

import React, { useState } from 'react';
import { SubscriptionPlan } from '../../lib/types/billing';
import { Check, Sparkles, Building2, User, ArrowRight } from 'lucide-react';

interface PlanSelectorCardsProps {
  plans: SubscriptionPlan[];
  activePlanCode: string;
  onSelectPlan: (planCode: string, idempotencyKey: string) => Promise<void>;
}

export default function PlanSelectorCards({
  plans,
  activePlanCode,
  onSelectPlan,
}: PlanSelectorCardsProps) {
  const [loadingPlan, setLoadingPlan] = useState<string | null>(null);

  const handleSelect = async (code: string) => {
    try {
      setLoadingPlan(code);
      const idempotencyKey = `sub-${code}-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
      await onSelectPlan(code, idempotencyKey);
    } finally {
      setLoadingPlan(null);
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6" data-testid="plan-selector-grid">
      {plans.map((p) => {
        const isCurrent = p.code === activePlanCode;
        const isOrg = p.seat_limit > 1;

        return (
          <div
            key={p.code}
            className={`flex flex-col justify-between rounded-2xl border p-6 transition shadow-sm ${
              isCurrent
                ? 'border-indigo-600 bg-indigo-50/20 ring-2 ring-indigo-600/20'
                : 'border-slate-200 bg-white hover:border-slate-300'
            }`}
            data-testid={`plan-card-${p.code}`}
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  {isOrg ? 'Institutional' : 'Individual'}
                </span>
                {isOrg ? (
                  <Building2 className="h-4 w-4 text-indigo-600" />
                ) : (
                  <User className="h-4 w-4 text-sky-600" />
                )}
              </div>

              <h4 className="mt-2 text-xl font-black text-slate-900">{p.name}</h4>
              <p className="mt-1 text-xs text-slate-500">{p.description}</p>

              <div className="mt-4">
                <span className="text-3xl font-extrabold text-slate-900">
                  ${(p.price_cents / 100).toFixed(0)}
                </span>
                <span className="text-xs text-slate-500"> / {p.billing_interval}</span>
                {isOrg && (
                  <p className="mt-1 text-xs font-semibold text-indigo-700">
                    Includes up to {p.seat_limit} enrolled seats
                  </p>
                )}
              </div>

              {/* Features list */}
              <ul className="mt-6 space-y-2.5 border-t border-slate-100 pt-4">
                {p.features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-xs text-slate-700">
                    <Check className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                    <span>{f.replace(':', ' — ')}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-8">
              {isCurrent ? (
                <div
                  className="w-full text-center rounded-xl bg-slate-100 py-2.5 text-xs font-bold text-slate-600"
                  data-testid={`current-plan-badge-${p.code}`}
                >
                  Current Plan
                </div>
              ) : (
                <button
                  type="button"
                  disabled={loadingPlan !== null}
                  onClick={() => handleSelect(p.code)}
                  className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-slate-800 disabled:opacity-50 transition"
                  data-testid={`btn-select-plan-${p.code}`}
                >
                  <span>{loadingPlan === p.code ? 'Processing...' : 'Select Plan'}</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
