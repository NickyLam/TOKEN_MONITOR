export interface Vendor {
  id: number
  slug: string
  display_name: string
  icon_url?: string
  is_active: boolean
  created_at: string
}

export interface VendorDetail extends Vendor {
  plan_count: number
}

export interface Plan {
  id: number
  vendor_id: number
  name: string
  plan_type: 'subscription' | 'token_credits' | 'free_tier'
  monthly_cost?: number
  quota_used?: number
  quota_limit?: number
  quota_unit?: string
  billing_day?: number
  renewal_date?: string
  api_key_ref?: string
  extra_config?: Record<string, unknown>
  is_active: boolean
  notes?: string
  created_at: string
  updated_at: string
}

export interface PlanDetail extends Plan {
  vendor_name?: string
  vendor_slug?: string
  quota_used?: number
  quota_percent?: number
}

export interface UsageRecord {
  id: number
  plan_id: number
  vendor_slug: string
  record_type: 'quota_snapshot' | 'token_usage' | 'cost_snapshot'
  recorded_at: string
  polled_at?: string
  period_start?: string
  period_end?: string
  quota_used?: number
  quota_total?: number
  quota_unit?: string
  input_tokens?: number
  output_tokens?: number
  cache_read_tokens?: number
  cache_write_tokens?: number
  total_cost_usd?: number
  request_count?: number
  model_name?: string
}

export interface TokenBreakdown {
  model: string
  input_tokens: number
  output_tokens: number
  cache_read_tokens: number
  cache_write_tokens: number
  cost_usd: number
}

export interface CostBreakdown {
  model: string
  request_count: number
  total_tokens: number
  cost: number
}

export interface AlertRule {
  id: number
  plan_id?: number
  rule_type: string
  threshold_value: number
  threshold_unit?: string
  is_enabled: boolean
  created_at: string
  updated_at: string
}

export interface AlertEvent {
  id: number
  alert_rule_id: number
  plan_id?: number
  severity: 'info' | 'warning' | 'critical'
  message: string
  evaluated_value?: number
  is_read: boolean
  triggered_at: string
  dismissed_at?: string
}

export interface QuotaStatus {
  plan_id: number
  plan_name: string
  vendor_slug: string
  vendor_name: string
  plan_type: string
  quota_used?: number
  quota_total?: number
  quota_unit?: string
  quota_percent?: number
  monthly_cost?: number
  renewal_date?: string
  days_until_renewal?: number
}

export interface SpendOverview {
  total_spend: number
  budget?: number
  period_start?: string
  period_end?: string
  vendor_breakdown: VendorSpendItem[]
}

export interface VendorSpendItem {
  vendor_slug: string
  vendor_name: string
  spend: number
  subscription_cost: number
}

export interface DailySpend {
  date: string
  total: number
  by_vendor: Record<string, number>
}

export interface UsageTrends {
  daily_spend: DailySpend[]
  forecast_total?: number
  days_projected: number
}

export interface PollingStatus {
  vendor_slug: string
  is_enabled: boolean
  interval_minutes: number
  last_polled_at?: string
  last_success_at?: string
  last_error?: string
  consecutive_failures: number
  display_name?: string
}

export interface PaginatedUsage {
  items: UsageRecord[]
  total: number
  page: number
  pages: number
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  page_size: number
}
