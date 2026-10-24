import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiClient } from '../src/lib/api-client';
import {
  SubscriptionPlan,
  SubscriptionRecord,
  InstitutionFeeItem,
  StudentFeePayment,
  InvoiceReceiptItem,
} from '../src/lib/types/billing';

describe('P16 Billing, Subscriptions, Entitlements and Institution Fees — Frontend Contracts', () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient('http://localhost:8000');
    vi.restoreAllMocks();
  });

  describe('1. Subscription Plans & Entitlements', () => {
    it('retrieves freemium plan tiers and active entitlements', async () => {
      client.setToken('test-token');

      const mockPlans: SubscriptionPlan[] = [
        {
          id: 'p1',
          code: 'free',
          name: 'Free Learner',
          description: 'Baseline tier',
          price_cents: 0,
          currency: 'USD',
          billing_interval: 'monthly',
          seat_limit: 1,
          features: ['tutoring:basic'],
        },
        {
          id: 'p2',
          code: 'pro_learner',
          name: 'Pro Learner',
          description: 'Unlimited adaptive tier',
          price_cents: 1200,
          currency: 'USD',
          billing_interval: 'monthly',
          seat_limit: 1,
          features: ['tutoring:advanced', 'rag:custom_uploads'],
        },
      ];

      global.fetch = vi.fn().mockImplementation((url) => {
        if (url.endsWith('/plans')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => mockPlans,
          });
        }
        return Promise.reject(new Error('Unknown endpoint'));
      });

      const plans = await client.getBillingPlans();
      expect(plans).toHaveLength(2);
      expect(plans[0].code).toBe('free');
      expect(plans[1].price_cents).toBe(1200);
    });

    it('retrieves active subscription status and BYOK clarity disclaimer', async () => {
      client.setToken('test-token');

      const mockSub: SubscriptionRecord = {
        subscription_id: 'sub-123',
        status: 'active',
        plan_code: 'pro_learner',
        plan_name: 'Pro Learner',
        price_cents: 1200,
        currency: 'USD',
        current_period_end: '2026-11-24T12:00:00Z',
        cancel_at_period_end: false,
        seat_limit: 1,
        entitlements: ['tutoring:advanced', 'rag:custom_uploads'],
        byok_disclaimer:
          'Third-party AI inference (BYOK) is billed directly by your AI provider and is not charged by Gayatri Cloud.',
      };

      global.fetch = vi.fn().mockImplementation((url) => {
        if (url.endsWith('/subscription')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => mockSub,
          });
        }
        return Promise.reject(new Error('Unknown endpoint'));
      });

      const sub = await client.getActiveSubscription();
      expect(sub.status).toBe('active');
      expect(sub.entitlements).toContain('rag:custom_uploads');
      expect(sub.byok_disclaimer).toContain('BYOK');
    });
  });

  describe('2. Idempotent Subscription Transition & Cancellation', () => {
    it('subscribes with required idempotency key', async () => {
      client.setToken('test-token');

      global.fetch = vi.fn().mockImplementation((url, init) => {
        expect(init.method).toBe('POST');
        const body = JSON.parse(init.body as string);
        expect(body.plan_code).toBe('pro_learner');
        expect(body.idempotency_key).toBe('test-idem-key-123');

        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            transaction_id: 'tx-1',
            invoice_number: 'INV-202610-A1B2',
            status: 'succeeded',
            plan_code: 'pro_learner',
            amount_paid_cents: 1200,
          }),
        });
      });

      const res = await client.subscribePlan('pro_learner', 'test-idem-key-123');
      expect(res.status).toBe('succeeded');
      expect(res.invoice_number).toBe('INV-202610-A1B2');
    });

    it('cancels subscription renewal cleanly', async () => {
      client.setToken('test-token');

      global.fetch = vi.fn().mockImplementation((url, init) => {
        expect(init.method).toBe('POST');
        expect(url).toContain('/cancel');
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            subscription_id: 'sub-123',
            cancel_at_period_end: true,
            message: 'Subscription will cancel at end of period.',
          }),
        });
      });

      const res = await client.cancelSubscription();
      expect(res.cancel_at_period_end).toBe(true);
    });
  });

  describe('3. Institutional Fee Schedules & Student Payments', () => {
    it('creates and lists institution fee schedules', async () => {
      client.setToken('admin-token');
      client.setOrganizationId('org-stanford');

      const mockFees: InstitutionFeeItem[] = [
        {
          id: 'fee-101',
          title: 'Physics Lab Fee',
          description: 'Sensors and manuals',
          amount_cents: 3500,
          currency: 'USD',
          due_date: '2026-11-15T00:00:00Z',
        },
      ];

      // List fees
      global.fetch = vi.fn().mockImplementation((url) => {
        expect(url).toContain('organization_id=org-stanford');
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mockFees,
        });
      });

      const fees = await client.getInstitutionFees('org-stanford');
      expect(fees).toHaveLength(1);
      expect(fees[0].amount_cents).toBe(3500);

      // Create fee
      global.fetch = vi.fn().mockImplementation((url, init) => {
        expect(init.method).toBe('POST');
        const body = JSON.parse(init.body as string);
        expect(body.title).toBe('Robotics Kit Fee');
        expect(body.amount_cents).toBe(5000);
        return Promise.resolve({
          ok: true,
          status: 201,
          json: async () => ({
            id: 'fee-102',
            title: 'Robotics Kit Fee',
            description: '',
            amount_cents: 5000,
            currency: 'USD',
            due_date: null,
          }),
        });
      });

      const created = await client.createInstitutionFee('org-stanford', {
        title: 'Robotics Kit Fee',
        amount_cents: 5000,
      });
      expect(created.amount_cents).toBe(5000);
    });

    it('pays student fee with idempotency guard', async () => {
      client.setToken('student-token');

      global.fetch = vi.fn().mockImplementation((url, init) => {
        expect(init.method).toBe('POST');
        expect(url).toContain('/pay');
        const body = JSON.parse(init.body as string);
        expect(body.idempotency_key).toBe('pay-key-456');

        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            payment_id: 'pay-1',
            transaction_id: 'tx-2',
            invoice_number: 'FEE-202610-9988',
            status: 'completed',
            amount_paid_cents: 3500,
          }),
        });
      });

      const res = await client.payStudentFee('fee-101', 'pay-key-456');
      expect(res.status).toBe('completed');
      expect(res.invoice_number).toBe('FEE-202610-9988');
    });
  });

  describe('4. Invoices and Receipts History', () => {
    it('retrieves invoice history with line items', async () => {
      client.setToken('test-token');

      const mockInvoices: InvoiceReceiptItem[] = [
        {
          invoice_number: 'INV-202610-001',
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
            payer_name: 'John Doe',
          },
          issued_at: '2026-10-24T10:00:00Z',
        },
      ];

      global.fetch = vi.fn().mockImplementation(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mockInvoices,
        })
      );

      const invoices = await client.getInvoices();
      expect(invoices).toHaveLength(1);
      expect(invoices[0].invoice_number).toBe('INV-202610-001');
      expect(invoices[0].line_items[0].description).toContain('Pro Learner');
    });
  });
});
