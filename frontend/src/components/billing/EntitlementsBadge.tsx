'use client';

import React from 'react';
import { SubscriptionRecord } from '../../lib/types/billing';
import { ShieldCheck, Sparkles, AlertCircle, Info, Calendar } from 'lucide-react';

interface EntitlementsBadgeProps {
  subscription: SubscriptionRecord;
  onCancelSubscription?: () => Promise<void>;
}

export default function EntitlementsBadge({
  subscription,
  onCancelSubscription,
}: EntitlementsBadgeProps) {
  const isFree = subscription?.status === 'free_tier' || subscription?.price_cents === 0;

  const entitlementsList: string[] = Array.isArray(subscription?.entitlements)
    ? subscription.entitlements
    : typeof subscription?.entitlements === 'object' && subscription?.entitlements !== null
    ? Object.entries(subscription.entitlements).map(([k, v]) => `${k.replace(/_/g, ' ')}: ${v}`)
    : [];

  return (
    <div className="space-y-6" data-testid="entitlements-panel">
      {/* Current Plan Overview Banner */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded-xl bg-purple-100 p-2 text-purple-700">
                <Sparkles className="h-5 w-5" />
              </span>
              <div>
                <h3 className="text-lg font-bold text-slate-900" data-testid="active-plan-name">
                  {subscription.plan_name}
                </h3>
                <span
                  className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                    subscription.status === 'active'
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-slate-100 text-slate-700'
                  }`}
                  data-testid="subscription-status-badge"
                >
                  <ShieldCheck className="h-3 w-3" />
                  {subscription.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
            </div>

            <p className="mt-3 text-2xl font-black text-slate-900">
              ${(subscription.price_cents / 100).toFixed(2)}
              <span className="text-sm font-normal text-slate-500"> / month</span>
            </p>
          </div>

          <div className="flex flex-col sm:items-end gap-2">
            {subscription.current_period_end && (
              <div className="flex items-center gap-1.5 text-xs text-slate-500">
                <Calendar className="h-3.5 w-3.5" />
                <span>
                  {subscription.cancel_at_period_end ? 'Cancels on ' : 'Renews on '}
                  {new Date(subscription.current_period_end).toLocaleDateString()}
                </span>
              </div>
            )}

            {!isFree && !subscription.cancel_at_period_end && onCancelSubscription && (
              <button
                type="button"
                onClick={onCancelSubscription}
                className="rounded-xl border border-rose-300 px-3 py-1.5 text-xs font-medium text-rose-600 hover:bg-rose-50 transition"
                data-testid="btn-cancel-subscription"
              >
                Cancel Subscription
              </button>
            )}
          </div>
        </div>

        {/* Feature Entitlements Checklist */}
        <div className="mt-6 border-t border-slate-100 pt-4">
          <h4 className="text-xs font-semibold uppercase text-slate-500 mb-3 tracking-wider">
            Active Entitlements & Features
          </h4>
          <div className="flex flex-wrap gap-2" data-testid="entitlements-list">
            {entitlementsList.map((feat) => (
              <span
                key={feat}
                className="inline-flex items-center gap-1.5 rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-800"
              >
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                {feat}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* BYOK Separation Disclaimer */}
      <div className="flex items-start gap-3 rounded-2xl border border-sky-200 bg-sky-50/70 p-4 text-xs text-sky-800" data-testid="byok-disclaimer-box">
        <Info className="h-4 w-4 shrink-0 text-sky-600 mt-0.5" />
        <div>
          <p className="font-semibold text-sky-900">Third-Party AI Inference & BYOK Clarity</p>
          <p className="mt-0.5">{subscription.byok_disclaimer}</p>
        </div>
      </div>
    </div>
  );
}
