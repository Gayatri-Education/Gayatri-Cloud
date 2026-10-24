'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../../lib/api-client';
import { SubscriptionPlan, SubscriptionRecord } from '../../../lib/types/billing';
import BillingNav from '../../../components/billing/BillingNav';
import PlanSelectorCards from '../../../components/billing/PlanSelectorCards';
import LoadingSkeleton from '../../../components/common/LoadingSkeleton';
import ErrorState from '../../../components/common/ErrorState';
import { Sparkles, CheckCircle2 } from 'lucide-react';

export default function BillingPlansPage() {
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [activePlanCode, setActivePlanCode] = useState<string>('free');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [checkoutMsg, setCheckoutMsg] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [plansData, subData] = await Promise.all([
        api.getBillingPlans().catch(() => [
          {
            id: 'plan-1',
            code: 'free',
            name: 'Free Learner',
            description: 'Baseline educational access with standard AI tutoring and practice assessments.',
            price_cents: 0,
            currency: 'USD',
            billing_interval: 'monthly',
            seat_limit: 1,
            features: ['tutoring:basic', 'courses:public', 'assessments:practice'],
          },
          {
            id: 'plan-2',
            code: 'pro_learner',
            name: 'Pro Learner',
            description: 'Unlimited adaptive AI tutoring, custom RAG document uploads, and BYOK integration.',
            price_cents: 1200,
            currency: 'USD',
            billing_interval: 'monthly',
            seat_limit: 1,
            features: [
              'tutoring:advanced',
              'courses:all',
              'assessments:all',
              'rag:custom_uploads',
              'ai:byok_unlimited',
            ],
          },
          {
            id: 'plan-3',
            code: 'institution_standard',
            name: 'Institution Standard',
            description: 'Comprehensive institutional campus tier with cohort analytics and roster management.',
            price_cents: 4900,
            currency: 'USD',
            billing_interval: 'monthly',
            seat_limit: 250,
            features: [
              'tutoring:institution',
              'teacher:copilot',
              'analytics:cohort',
              'roster:unlimited',
              'ai:byok_org',
            ],
          },
          {
            id: 'plan-4',
            code: 'institution_enterprise',
            name: 'Institution Enterprise',
            description: 'Full-scale university/academy license with custom domains and unlimited seat allocations.',
            price_cents: 19900,
            currency: 'USD',
            billing_interval: 'monthly',
            seat_limit: 1000,
            features: [
              'tutoring:institution',
              'teacher:copilot',
              'analytics:advanced',
              'domain:unlimited',
              'sla:priority',
              'ai:byok_org',
            ],
          },
        ]),
        api.getActiveSubscription().catch(() => ({
          plan_code: 'free',
        })),
      ]);
      setPlans(plansData);
      setActivePlanCode(subData.plan_code || 'free');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load subscription plans');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSelectPlan = async (code: string, idempotencyKey: string) => {
    try {
      setCheckoutMsg(null);
      const res = await api.subscribePlan(code, idempotencyKey);
      setActivePlanCode(res.plan_code);
      setCheckoutMsg(`Successfully upgraded to ${res.plan_code}! Invoice ${res.invoice_number} generated.`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to complete subscription transition');
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8" data-testid="billing-plans-page">
      <div className="mb-6 flex items-center gap-2">
        <span className="rounded-lg bg-purple-100 p-1.5 text-purple-700">
          <Sparkles className="h-5 w-5" />
        </span>
        <h1 className="text-2xl font-black tracking-tight text-slate-900">
          Subscription Tiers & Entitlements
        </h1>
      </div>

      <BillingNav />

      {checkoutMsg && (
        <div className="mb-6 flex items-center gap-2 rounded-2xl bg-emerald-50 p-4 text-sm font-semibold text-emerald-800 border border-emerald-200" data-testid="checkout-success-msg">
          <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600" />
          <span>{checkoutMsg}</span>
        </div>
      )}

      {isLoading ? (
        <LoadingSkeleton />
      ) : error ? (
        <ErrorState message={error} onRetry={loadData} />
      ) : (
        <PlanSelectorCards
          plans={plans}
          activePlanCode={activePlanCode}
          onSelectPlan={handleSelectPlan}
        />
      )}
    </div>
  );
}
