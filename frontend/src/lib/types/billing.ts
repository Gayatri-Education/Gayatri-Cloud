export interface SubscriptionPlan {
  id: string;
  code: string;
  name: string;
  description: string;
  price_cents: number;
  currency: string;
  billing_interval: string;
  seat_limit: number;
  features: string[];
}

export interface SubscriptionRecord {
  subscription_id: string | null;
  status: string;
  plan_code: string;
  plan_name: string;
  price_cents: number;
  currency: string;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  seat_limit: number;
  entitlements: string[];
  byok_disclaimer: string;
}

export interface InstitutionFeeItem {
  id: string;
  title: string;
  description: string;
  amount_cents: number;
  currency: string;
  due_date: string | null;
}

export interface StudentFeePayment {
  fee_id: string;
  title: string;
  description: string;
  amount_cents: number;
  currency: string;
  due_date: string | null;
  is_paid: boolean;
  paid_at: string | null;
  payment_reference: string | null;
}

export interface InvoiceReceiptItem {
  invoice_number: string;
  amount_cents: number;
  tax_amount_cents: number;
  line_items: Array<{
    description: string;
    amount_cents: number;
    quantity: number;
  }>;
  billing_details: {
    payer_name?: string;
    payer_email?: string;
    organization_id?: string;
  };
  issued_at: string;
}
