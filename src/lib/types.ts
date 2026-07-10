export type Lang = 'EN' | 'NO' | 'PL'

export interface Organization {
  id: string
  name: string
  slug: string
  plan: 'free' | 'starter' | 'professional'
  created_at: string
}

export interface Profile {
  id: string
  organization_id: string
  full_name: string
  role: 'owner' | 'admin' | 'member'
  lang: Lang
}

export interface Material {
  id: string
  organization_id: string
  material_number: string
  description: string
  unit: string
  standard_price: number
  safety_stock: number
  lead_time_days: number
  storage_location: string
}

export interface StockMovement {
  id: string
  organization_id: string
  material_number: string
  posting_date: string
  quantity: number
  movement_type: string
  is_issue: boolean
  storage_location?: string
  document_number?: string
}

export interface CurrentStock {
  organization_id: string
  material_number: string
  quantity: number
  open_orders: number
  snapshot_date: string
}

export interface RopResult {
  id: string
  organization_id: string
  material_number: string
  avg_daily_usage: number
  std_daily: number
  safety_stock_calc: number
  reorder_point: number
  forecast_30d: number
  days_to_stockout: number
  frozen_capital: number
  status: 'OK' | 'ORDER' | 'OUT' | 'OVERSTOCK' | 'WATCH'
  action_text: string
  lead_time_used: number
  service_level_used: number
  computed_at: string
}

export interface DashboardStats {
  total_materials: number
  critical_count: number
  watch_count: number
  ok_count: number
  frozen_capital_nok: number
  active_promotions: number
  last_import?: string
}
