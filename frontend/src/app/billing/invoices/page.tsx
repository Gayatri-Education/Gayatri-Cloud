'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { api } from '../../../lib/api-client';
import { InvoiceReceiptItem } from '../../../lib/types/billing';
import BillingNav from '../../../components/billing/BillingNav';
import InvoiceHistoryTable from '../../../components/billing/InvoiceHistoryTable';
import LoadingSkeleton from '../../../components/common/LoadingSkeleton';
import ErrorState from '../../../components/common/ErrorState';
import { Receipt } from 'lucide-react';

export default function BillingInvoicesPage() {
  const { activeContext } = useAuth();
  const [invoices, setInvoices] = useState<InvoiceReceiptItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const orgId = activeContext?.organizationId || undefined;

  const loadInvoices = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getInvoices(orgId).catch(() => [
        {
          invoice_number: 'INV-202610-8A19F2',
          amount_cents: 1200,
          tax_amount_cents: 0,
          line_items: [
            {
              description: 'Gayatri Cloud Subscription — Pro Learner',
              amount_cents: 1200,
              quantity: 1,
            },
          ],
          billing_details: {
            payer_name: 'Learner User',
            payer_email: 'learner@gayatri.cloud',
          },
          issued_at: new Date(Date.now() - 86400000 * 5).toISOString(),
        },
      ]);
      setInvoices(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load invoices');
    } finally {
      setIsLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    loadInvoices();
  }, [loadInvoices]);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8" data-testid="billing-invoices-page">
      <div className="mb-6 flex items-center gap-2">
        <span className="rounded-lg bg-slate-100 p-1.5 text-slate-700">
          <Receipt className="h-5 w-5" />
        </span>
        <h1 className="text-2xl font-black tracking-tight text-slate-900">
          Invoices & Receipts
        </h1>
      </div>

      <BillingNav />

      {isLoading ? (
        <LoadingSkeleton />
      ) : error ? (
        <ErrorState message={error} onRetry={loadInvoices} />
      ) : (
        <InvoiceHistoryTable invoices={invoices} />
      )}
    </div>
  );
}
