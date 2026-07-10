-- ============================================================
-- SpareParts AI — Supabase Schema
-- Wklej całość w: Supabase → SQL Editor → New Query → Run
-- ============================================================

-- ── ORGANIZATIONS (multi-tenant) ──────────────────────────
CREATE TABLE organizations (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  slug        TEXT UNIQUE NOT NULL,
  plan        TEXT DEFAULT 'free' CHECK (plan IN ('free','starter','professional')),
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── USERS ─────────────────────────────────────────────────
CREATE TABLE profiles (
  id              UUID PRIMARY KEY REFERENCES auth.users ON DELETE CASCADE,
  organization_id UUID REFERENCES organizations(id),
  full_name       TEXT,
  role            TEXT DEFAULT 'member' CHECK (role IN ('owner','admin','member')),
  lang            TEXT DEFAULT 'EN' CHECK (lang IN ('EN','NO','PL')),
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── MATERIALS (parts catalog) ─────────────────────────────
CREATE TABLE materials (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  material_number TEXT NOT NULL,
  description     TEXT,
  unit            TEXT DEFAULT 'PC',
  standard_price  NUMERIC(12,2) DEFAULT 0,
  safety_stock    NUMERIC(10,2) DEFAULT 0,
  lead_time_days  INT DEFAULT 14,
  storage_location TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(organization_id, material_number)
);

-- ── STOCK MOVEMENTS (MB51 data) ───────────────────────────
CREATE TABLE stock_movements (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  material_id     UUID REFERENCES materials(id) ON DELETE CASCADE,
  material_number TEXT NOT NULL,
  posting_date    DATE NOT NULL,
  quantity        NUMERIC(12,3) NOT NULL,
  movement_type   TEXT NOT NULL,  -- '261','101','201' etc
  is_issue        BOOLEAN NOT NULL DEFAULT FALSE,
  storage_location TEXT,
  document_number TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── CURRENT STOCK (MB52 snapshot) ─────────────────────────
CREATE TABLE current_stock (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  material_id     UUID REFERENCES materials(id),
  material_number TEXT NOT NULL,
  quantity        NUMERIC(12,3) NOT NULL DEFAULT 0,
  open_orders     NUMERIC(12,3) DEFAULT 0,
  snapshot_date   DATE NOT NULL DEFAULT CURRENT_DATE,
  updated_at      TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(organization_id, material_number)
);

-- ── ROP RESULTS (computed, cached) ────────────────────────
CREATE TABLE rop_results (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id     UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  material_number     TEXT NOT NULL,
  avg_daily_usage     NUMERIC(10,4),
  std_daily           NUMERIC(10,4),
  safety_stock_calc   NUMERIC(10,2),
  reorder_point       NUMERIC(10,2),
  forecast_30d        NUMERIC(10,2),
  days_to_stockout    NUMERIC(8,1),
  frozen_capital      NUMERIC(12,2),
  status              TEXT,  -- 'OK','ORDER','OUT','OVERSTOCK','WATCH'
  action_text         TEXT,
  lead_time_used      INT,
  service_level_used  NUMERIC(4,2),
  computed_at         TIMESTAMPTZ DEFAULT NOW()
);

-- ── PROMOTIONS (campaign module) ──────────────────────────
CREATE TABLE promotions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name            TEXT NOT NULL,
  discount_pct    NUMERIC(5,2) NOT NULL DEFAULT 0,
  start_date      DATE,
  end_date        DATE,
  status          TEXT DEFAULT 'draft' CHECK (status IN ('draft','active','ended')),
  ai_copy_no      TEXT,  -- AI generated copy Norwegian
  ai_copy_en      TEXT,  -- AI generated copy English
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── PROMOTION ITEMS ───────────────────────────────────────
CREATE TABLE promotion_items (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  promotion_id    UUID NOT NULL REFERENCES promotions(id) ON DELETE CASCADE,
  material_number TEXT NOT NULL,
  original_price  NUMERIC(12,2),
  promo_price     NUMERIC(12,2),
  qty_available   NUMERIC(10,2)
);

-- ── AUDIT CHECKLISTS (ISO module) ─────────────────────────
CREATE TABLE audit_templates (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organizations(id),
  name            TEXT NOT NULL,
  standard        TEXT DEFAULT 'ISO 9001:2015',
  is_public       BOOLEAN DEFAULT FALSE,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE audit_criteria (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_id     UUID NOT NULL REFERENCES audit_templates(id) ON DELETE CASCADE,
  criterion_id    TEXT NOT NULL,  -- '1.1', '1.1.1' etc
  question        TEXT NOT NULL,
  notes           TEXT,
  iso_reference   TEXT,
  audit_type      TEXT DEFAULT 'full',
  sort_order      INT DEFAULT 0
);

CREATE TABLE audit_sessions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  template_id     UUID REFERENCES audit_templates(id),
  auditor_id      UUID REFERENCES profiles(id),
  status          TEXT DEFAULT 'in_progress' CHECK (status IN ('in_progress','completed')),
  score_total     NUMERIC(5,2),
  score_max       NUMERIC(5,2),
  started_at      TIMESTAMPTZ DEFAULT NOW(),
  completed_at    TIMESTAMPTZ
);

CREATE TABLE audit_answers (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id      UUID NOT NULL REFERENCES audit_sessions(id) ON DELETE CASCADE,
  criterion_id    UUID NOT NULL REFERENCES audit_criteria(id),
  score           NUMERIC(3,1) CHECK (score IN (0, 0.5, 1)),
  notes           TEXT,
  photo_url       TEXT,
  answered_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ── FILE UPLOAD LOG ───────────────────────────────────────
CREATE TABLE file_imports (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  filename        TEXT,
  import_type     TEXT CHECK (import_type IN ('MB51','MB52','custom')),
  rows_imported   INT DEFAULT 0,
  mapping_profile JSONB,
  status          TEXT DEFAULT 'done',
  imported_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ── ROW LEVEL SECURITY ────────────────────────────────────
ALTER TABLE organizations    ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles         ENABLE ROW LEVEL SECURITY;
ALTER TABLE materials        ENABLE ROW LEVEL SECURITY;
ALTER TABLE stock_movements  ENABLE ROW LEVEL SECURITY;
ALTER TABLE current_stock    ENABLE ROW LEVEL SECURITY;
ALTER TABLE rop_results      ENABLE ROW LEVEL SECURITY;
ALTER TABLE promotions       ENABLE ROW LEVEL SECURITY;
ALTER TABLE promotion_items  ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_sessions   ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_answers    ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_imports     ENABLE ROW LEVEL SECURITY;

-- Policy: user sees only their organization's data
CREATE POLICY "org_isolation" ON materials
  FOR ALL USING (
    organization_id = (
      SELECT organization_id FROM profiles WHERE id = auth.uid()
    )
  );

CREATE POLICY "org_isolation" ON stock_movements
  FOR ALL USING (
    organization_id = (
      SELECT organization_id FROM profiles WHERE id = auth.uid()
    )
  );

CREATE POLICY "org_isolation" ON current_stock
  FOR ALL USING (
    organization_id = (
      SELECT organization_id FROM profiles WHERE id = auth.uid()
    )
  );

CREATE POLICY "org_isolation" ON rop_results
  FOR ALL USING (
    organization_id = (
      SELECT organization_id FROM profiles WHERE id = auth.uid()
    )
  );

CREATE POLICY "org_isolation" ON promotions
  FOR ALL USING (
    organization_id = (
      SELECT organization_id FROM profiles WHERE id = auth.uid()
    )
  );

CREATE POLICY "org_isolation" ON audit_sessions
  FOR ALL USING (
    organization_id = (
      SELECT organization_id FROM profiles WHERE id = auth.uid()
    )
  );

CREATE POLICY "org_isolation" ON file_imports
  FOR ALL USING (
    organization_id = (
      SELECT organization_id FROM profiles WHERE id = auth.uid()
    )
  );

-- ── INDEXES ───────────────────────────────────────────────
CREATE INDEX idx_movements_org_mat ON stock_movements(organization_id, material_number);
CREATE INDEX idx_movements_date    ON stock_movements(posting_date);
CREATE INDEX idx_rop_org           ON rop_results(organization_id);
CREATE INDEX idx_stock_org_mat     ON current_stock(organization_id, material_number);
