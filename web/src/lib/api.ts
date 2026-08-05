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

export interface ContactOut {
  id: number;
  name: string;
  role: string | null;
  email: string | null;
  phone: string | null;
  side: string;
}

export interface ServiceOut {
  id: number;
  name: string;
  description: string | null;
  unit: string | null;
  unit_price: number | null;
}

export interface QualificationOut {
  id: number;
  name: string;
  valid_to: string | null;
}

export interface ContractLineOut {
  id: number;
  item_ref: string;
  description: string | null;
  unit: string;
  unit_price: number;
  max_quantity: number | null;
  currency: string;
}

export interface ContractOut {
  id: number;
  supplier_id: number;
  supplier_name: string;
  title: string;
  reference: string;
  contract_type: string;
  regime: string;
  valid_from: string;
  valid_to: string | null;
  total_value: number | null;
  change_clause: string;
  status: string;
  lines: ContractLineOut[];
}

export interface CommitmentOut {
  id: number;
  supplier_id: number;
  condition_type: string;
  source_type: string;
  source_ref: string;
  item_ref: string | null;
  value: number | null;
  unit: string | null;
  valid_from: string;
  valid_to: string | null;
  formalization: string;
  confirmed_by_user: boolean;
  gyldighet: string | null;
}

export interface TerskelResult {
  regime: string;
  consequence: string;
  citation: string;
  citation_url: string | null;
  verdi: number;
  oppdragsgiver: string;
  kontrakttype: string;
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
  categories: string | null;
  notes: string | null;
  invoices: InvoiceRow[];
  contracts: { id: number; reference: string; title: string; valid_from: string; status: string | null }[];
  contacts: ContactOut[];
  services: ServiceOut[];
  qualifications: QualificationOut[];
}
