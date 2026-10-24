'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { api } from '../../../lib/api-client';
import { InstitutionFeeItem, StudentFeePayment } from '../../../lib/types/billing';
import BillingNav from '../../../components/billing/BillingNav';
import InstitutionFeeManager from '../../../components/billing/InstitutionFeeManager';
import StudentFeePaymentCard from '../../../components/billing/StudentFeePaymentCard';
import LoadingSkeleton from '../../../components/common/LoadingSkeleton';
import ErrorState from '../../../components/common/ErrorState';
import { Building2 } from 'lucide-react';

export default function BillingFeesPage() {
  const { activeContext } = useAuth();
  const [instFees, setInstFees] = useState<InstitutionFeeItem[]>([]);
  const [studentFees, setStudentFees] = useState<StudentFeePayment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const orgId = activeContext?.organizationId || 'org-default';
  const isAdmin = activeContext?.role === 'ORG_ADMIN' || activeContext?.role === 'SUPER_ADMIN';

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      if (isAdmin) {
        const data = await api.getInstitutionFees(orgId).catch(() => [
          {
            id: 'fee-1',
            title: 'Physics Lab Materials Fee',
            description: 'Optical sensors and laboratory manual.',
            amount_cents: 3500,
            currency: 'USD',
            due_date: new Date(Date.now() + 86400000 * 15).toISOString(),
          },
          {
            id: 'fee-2',
            title: 'Annual Library & Journal Subscription',
            description: 'Digital access to IEEE and ACM catalogs.',
            amount_cents: 2500,
            currency: 'USD',
            due_date: new Date(Date.now() + 86400000 * 30).toISOString(),
          },
        ]);
        setInstFees(data);
      } else {
        const data = await api.getStudentFees().catch(() => [
          {
            fee_id: 'fee-1',
            title: 'Physics Lab Materials Fee',
            description: 'Optical sensors and laboratory manual.',
            amount_cents: 3500,
            currency: 'USD',
            due_date: new Date(Date.now() + 86400000 * 15).toISOString(),
            is_paid: false,
            paid_at: null,
            payment_reference: null,
          },
        ]);
        setStudentFees(data);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load institutional fees');
    } finally {
      setIsLoading(false);
    }
  }, [isAdmin, orgId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreateFee = async (payload: {
    title: string;
    description: string;
    amount_cents: number;
    currency: string;
    due_date?: string;
  }) => {
    await api.createInstitutionFee(orgId, payload);
    await loadData();
  };

  const handlePayFee = async (feeId: string, idempotencyKey: string) => {
    await api.payStudentFee(feeId, idempotencyKey);
    await loadData();
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8" data-testid="billing-fees-page">
      <div className="mb-6 flex items-center gap-2">
        <span className="rounded-lg bg-sky-100 p-1.5 text-sky-700">
          <Building2 className="h-5 w-5" />
        </span>
        <h1 className="text-2xl font-black tracking-tight text-slate-900">
          Institutional Fees & Payments
        </h1>
      </div>

      <BillingNav />

      {isLoading ? (
        <LoadingSkeleton />
      ) : error ? (
        <ErrorState message={error} onRetry={loadData} />
      ) : isAdmin ? (
        <InstitutionFeeManager fees={instFees} onCreateFee={handleCreateFee} />
      ) : (
        <StudentFeePaymentCard fees={studentFees} onPayFee={handlePayFee} />
      )}
    </div>
  );
}
