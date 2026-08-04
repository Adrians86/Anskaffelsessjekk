const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchApi<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API ${path}: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export interface KpiStats {
  total_invoices: number;
  avvik: number;
  til_vurdering: number;
  samsvar: number;
  verdi_funnet: number;
  n_foreign: number;
}

export interface HealthBar {
  pct_avvik: number;
  pct_til_vurdering: number;
  pct_samsvar: number;
}

export interface StatsResponse {
  kpi: KpiStats;
  health: HealthBar;
  periode_fra: string;
  periode_til: string;
}

export interface InvoiceRow {
  id: number;
  invoice_number: string;
  supplier_name: string;
  supplier_id: number;
  amount: number;
  currency: string;
  date: string;
  verdict: string;
  status: string;
  finding: string;
}

export interface Finding {
  severity: string;
  code: string;
  message: string;
  citation: string;
  expected: string | null;
  actual: string | null;
  deviation_amount: number | null;
}

export interface InvoiceDetail {
  id: number;
  invoice_number: string;
  supplier_name: string;
  supplier_id: number;
  amount: number;
  currency: string;
  date: string;
  verdict: string;
  status: string;
  findings: Finding[];
  lines: { item_ref: string; description: string; quantity: number; unit_price: number; line_total: number }[];
}

export interface SupplierRow {
  id: number;
  name: string;
  org_number: string;
  city: string | null;
  status: string | null;
  n_invoices: number;
  n_contracts: number;
}

export interface SupplierDetail {
  id: number;
  name: string;
  org_number: string;
  address: string | null;
  postal_code: string | null;
  city: string | null;
  website: string | null;
  email: string | null;
  phone: string | null;
  status: string | null;
  invoices: InvoiceRow[];
  contracts: { id: number; reference: string; title: string; valid_from: string; status: string | null }[];
}
