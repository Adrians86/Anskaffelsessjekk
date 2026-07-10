-- ============================================================
-- SpareParts AI — SCHEMA PATCH v2
-- URUCHOM PO wcześniejszym supabase_schema.sql
-- Naprawia signup flow (pozwala tworzyć organization + profile)
-- ============================================================

-- ── Pozwól zalogowanym userom tworzyć organizacje przy signup
DROP POLICY IF EXISTS "org_insert_authenticated" ON organizations;
CREATE POLICY "org_insert_authenticated" ON organizations
  FOR INSERT TO authenticated
  WITH CHECK (true);

DROP POLICY IF EXISTS "org_select_own" ON organizations;
CREATE POLICY "org_select_own" ON organizations
  FOR SELECT TO authenticated
  USING (
    id IN (SELECT organization_id FROM profiles WHERE id = auth.uid())
  );

-- ── Pozwól userom tworzyć własny profil przy signup
DROP POLICY IF EXISTS "profile_insert_self" ON profiles;
CREATE POLICY "profile_insert_self" ON profiles
  FOR INSERT TO authenticated
  WITH CHECK (id = auth.uid());

DROP POLICY IF EXISTS "profile_select_own" ON profiles;
CREATE POLICY "profile_select_own" ON profiles
  FOR SELECT TO authenticated
  USING (id = auth.uid());

DROP POLICY IF EXISTS "profile_update_own" ON profiles;
CREATE POLICY "profile_update_own" ON profiles
  FOR UPDATE TO authenticated
  USING (id = auth.uid());

-- ── Pozwól userom robić insert w swoich tabelach org
DROP POLICY IF EXISTS "materials_insert" ON materials;
CREATE POLICY "materials_insert" ON materials
  FOR INSERT TO authenticated
  WITH CHECK (
    organization_id = (SELECT organization_id FROM profiles WHERE id = auth.uid())
  );

DROP POLICY IF EXISTS "movements_insert" ON stock_movements;
CREATE POLICY "movements_insert" ON stock_movements
  FOR INSERT TO authenticated
  WITH CHECK (
    organization_id = (SELECT organization_id FROM profiles WHERE id = auth.uid())
  );

DROP POLICY IF EXISTS "stock_insert" ON current_stock;
CREATE POLICY "stock_insert" ON current_stock
  FOR INSERT TO authenticated
  WITH CHECK (
    organization_id = (SELECT organization_id FROM profiles WHERE id = auth.uid())
  );

DROP POLICY IF EXISTS "rop_insert" ON rop_results;
CREATE POLICY "rop_insert" ON rop_results
  FOR INSERT TO authenticated
  WITH CHECK (
    organization_id = (SELECT organization_id FROM profiles WHERE id = auth.uid())
  );

DROP POLICY IF EXISTS "rop_delete" ON rop_results;
CREATE POLICY "rop_delete" ON rop_results
  FOR DELETE TO authenticated
  USING (
    organization_id = (SELECT organization_id FROM profiles WHERE id = auth.uid())
  );

DROP POLICY IF EXISTS "imports_insert" ON file_imports;
CREATE POLICY "imports_insert" ON file_imports
  FOR INSERT TO authenticated
  WITH CHECK (
    organization_id = (SELECT organization_id FROM profiles WHERE id = auth.uid())
  );

-- ── Zezwól na email signup w Supabase Auth
-- (to jest w UI - Authentication → Providers → Email → Enable)
