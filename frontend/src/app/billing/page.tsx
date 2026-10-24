'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../lib/api-client';
import { SubscriptionRecord } from '../../lib/types/billing';
import BillingNav from '../../components/billing/BillingNav';
import EntitlementsBadge from '../../components/billing/EntitlementsBadge';
import LoadingSkeleton from '../../components/common/LoadingSkeleton';
import ErrorState from '../../components/common/ErrorState';
import { CreditCard } from 'lucide-react';

export default function BillingOverviewPage() {
  const [subscription, setSubscription] = useState<SubscriptionRecord | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSubscription = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getActiveSubscription().catch(() => ({
        subscription_id: null,
        status: 'free_tier',
        plan_code: 'free',
        plan_name: 'Free Learner',
        price_cents: 0,
        currency: 'USD',
        current_period_end: null,
        cancel_at_period_end: false,
        seat_limit: 1,
        entitlements: ['tutoring:basic', 'courses:public', 'assessments:practice'],
        byok_disclaimer:
          'Third-party AI inference (BYOK) is billed directly by your AI provider and is not charged by Gayatri Cloud.',
      }));
      setSubscription(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load subscription status');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSubscription();
  }, [loadSubscription]);

  const handleCancel = async () => {
    if (!confirm('Are you sure you want to cancel your subscription renewal?')) return;
    await api.cancelSubscription();
    await loadSubscription();
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8" data-testid="billing-overview-page">
      <div className="mb-6 flex items-center gap-2">
        <span className="rounded-lg bg-indigo-100 p-1.5 text-indigo-700">
          <CreditCard className="h-5 w-5" />
        </span>
        <h1 className="text-2xl font-black tracking-tight text-slate-900">
          Billing & Subscription Management
        </h1>
      </div>

      <BillingNav />

      {isLoading ? (
        <LoadingSkeleton />
      ) : error ? (
        <ErrorState message={error} onRetry={loadSubscription} />
      ) : subscription ? (
        <EntitlementsBadge
          subscription={subscription}
          onCancelSubscription={handleCancel}
        />
      ) : null}
    </div>
  );
}
