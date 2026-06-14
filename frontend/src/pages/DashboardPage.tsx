import { useQuery } from '@tanstack/react-query'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Legend,
} from 'recharts'
import api from '../api/client'
import type { SpendOverview, UsageTrends, QuotaStatus, AlertEvent } from '../types'

export default function DashboardPage() {
  const { data: overview } = useQuery<SpendOverview>({
    queryKey: ['dashboard', 'overview'],
    queryFn: () => api.get('/dashboard/overview').then((r) => r.data),
  })

  const { data: trends } = useQuery<UsageTrends>({
    queryKey: ['dashboard', 'trends'],
    queryFn: () => api.get('/dashboard/trends?days=30').then((r) => r.data),
  })

  const { data: quotas } = useQuery<QuotaStatus[]>({
    queryKey: ['dashboard', 'quota'],
    queryFn: () => api.get('/dashboard/quota-status').then((r) => r.data),
  })

  const { data: alerts } = useQuery<AlertEvent[]>({
    queryKey: ['dashboard', 'alerts'],
    queryFn: () => api.get('/alerts/events?is_read=false&limit=3').then((r) => r.data),
  })

  const trendData = trends?.daily_spend.map((d) => ({
    date: d.date,
    total: d.total,
  })) ?? []

  const vendorBarData = overview?.vendor_breakdown.map((v) => ({
    name: v.vendor_name,
    spend: v.spend,
    subscription: v.subscription_cost,
  })) ?? []

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">仪表盘</h1>

      {/* 告警横幅 */}
      {alerts && alerts.length > 0 && (
        <div className="space-y-2">
          {alerts.map((a) => (
            <div
              key={a.id}
              className={`rounded-lg px-4 py-3 text-sm ${
                a.severity === 'critical'
                  ? 'bg-red-50 text-red-800 border border-red-200'
                  : a.severity === 'warning'
                  ? 'bg-amber-50 text-amber-800 border border-amber-200'
                  : 'bg-blue-50 text-blue-800 border border-blue-200'
              }`}
            >
              {a.message}
            </div>
          ))}
        </div>
      )}

      {/* 消费概览 */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="rounded-xl bg-white p-6 shadow-sm border border-slate-200">
          <p className="text-sm text-slate-500">本月总消费</p>
          <p className="mt-1 text-3xl font-bold text-slate-900">
            ${overview?.total_spend?.toFixed(2) ?? '0.00'}
          </p>
        </div>
        <div className="rounded-xl bg-white p-6 shadow-sm border border-slate-200">
          <p className="text-sm text-slate-500">月末预估</p>
          <p className="mt-1 text-3xl font-bold text-slate-900">
            ${trends?.forecast_total?.toFixed(2) ?? '0.00'}
          </p>
          <p className="mt-1 text-xs text-slate-400">剩余 {trends?.days_projected} 天</p>
        </div>
        <div className="rounded-xl bg-white p-6 shadow-sm border border-slate-200">
          <p className="text-sm text-slate-500">活跃套餐</p>
          <p className="mt-1 text-3xl font-bold text-slate-900">{quotas?.length ?? 0}</p>
        </div>
      </div>

      {/* 配额状态 */}
      {quotas && quotas.filter(q => q.quota_percent != null).length > 0 && (
        <div className="rounded-xl bg-white p-6 shadow-sm border border-slate-200">
          <h2 className="mb-4 text-lg font-semibold text-slate-700">配额状态</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {quotas?.filter(q => q.quota_percent != null).map((q) => (
              <div key={q.plan_id} className="flex flex-col items-center rounded-lg border border-slate-100 p-4">
                <p className="text-sm font-medium text-slate-700">{q.plan_name}</p>
                <p className="text-xs text-slate-400">{q.vendor_name}</p>
                <div className="mt-2 text-2xl font-bold" style={{
                  color: q.quota_percent! > 90 ? '#ef4444' : q.quota_percent! > 70 ? '#f59e0b' : '#22c55e'
                }}>
                  {q.quota_percent?.toFixed(1)}%
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  {q.quota_used?.toLocaleString()} / {q.quota_total?.toLocaleString()} {q.quota_unit}
                </p>
                {q.days_until_renewal != null && (
                  <p className="mt-1 text-xs text-slate-400">{q.days_until_renewal} 天后续费</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 消费趋势图 */}
      {trendData.length > 0 && (
        <div className="rounded-xl bg-white p-6 shadow-sm border border-slate-200">
          <h2 className="mb-4 text-lg font-semibold text-slate-700">每日消费趋势（近30天）</h2>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `$${v}`} />
              <Tooltip formatter={(value: number) => [`$${value.toFixed(4)}`, '消费']} />
              <Area type="monotone" dataKey="total" stroke="#6366f1" fill="#e0e7ff" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* 厂商消费分布 */}
      {vendorBarData.length > 0 && (
        <div className="rounded-xl bg-white p-6 shadow-sm border border-slate-200">
          <h2 className="mb-4 text-lg font-semibold text-slate-700">厂商消费分布</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={vendorBarData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" tickFormatter={(v) => `$${v}`} />
              <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 12 }} />
              <Tooltip formatter={(value: number) => `$${value.toFixed(2)}`} />
              <Legend />
              <Bar dataKey="subscription" stackId="a" fill="#6366f1" name="订阅费用" />
              <Bar dataKey="spend" stackId="a" fill="#a5b4fc" name="Token 用量" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
