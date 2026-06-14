import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import api from '../api/client'
import type { PaginatedUsage, UsageRecord, TokenBreakdown, CostBreakdown } from '../types'

const COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899']

export default function UsagePage() {
  const [page, setPage] = useState(1)
  const [vendor, setVendor] = useState('')
  const [model, setModel] = useState('')

  const { data } = useQuery<PaginatedUsage>({
    queryKey: ['usage', page, vendor, model],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), page_size: '20' })
      if (vendor) params.set('vendor_slug', vendor)
      if (model) params.set('model', model)
      return api.get(`/usage?${params}`).then((r) => r.data)
    },
  })

  const { data: tokenBreakdown } = useQuery<TokenBreakdown[]>({
    queryKey: ['usage', 'token-breakdown', vendor],
    queryFn: () => {
      const params = new URLSearchParams({ days: '7', group_by: 'model' })
      if (vendor) params.set('vendor_slug', vendor)
      return api.get(`/usage/token-breakdown?${params}`).then((r) => r.data)
    },
  })

  const { data: costBreakdown } = useQuery<CostBreakdown[]>({
    queryKey: ['usage', 'cost-breakdown', vendor],
    queryFn: () => {
      const params = new URLSearchParams({ days: '7' })
      if (vendor) params.set('vendor_slug', vendor)
      return api.get(`/usage/model-breakdown?${params}`).then((r) => r.data)
    },
  })

  const costPieData = costBreakdown?.map((c) => ({
    name: c.model,
    value: c.cost,
  })) ?? []

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">用量详情</h1>

      {/* 筛选条件 */}
      <div className="flex gap-3">
        <input
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          placeholder="按厂商过滤 (slug)"
          value={vendor}
          onChange={(e) => { setVendor(e.target.value); setPage(1) }}
        />
        <input
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          placeholder="按模型过滤"
          value={model}
          onChange={(e) => { setModel(e.target.value); setPage(1) }}
        />
        <a
          href={`/api/usage/export?days=30${vendor ? `&vendor_slug=${vendor}` : ''}`}
          className="ml-auto rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50"
        >
          导出 CSV
        </a>
      </div>

      {/* 用量表格 */}
      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-200 bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-slate-600">日期</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">厂商</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">类型</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">模型</th>
              <th className="px-4 py-3 text-right font-medium text-slate-600">输入 Tokens</th>
              <th className="px-4 py-3 text-right font-medium text-slate-600">输出 Tokens</th>
              <th className="px-4 py-3 text-right font-medium text-slate-600">费用</th>
              <th className="px-4 py-3 text-right font-medium text-slate-600">配额</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {data?.items?.map((r: UsageRecord) => (
              <tr key={r.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 text-slate-600">{new Date(r.recorded_at).toLocaleString('zh-CN')}</td>
                <td className="px-4 py-3 text-slate-700">{r.vendor_slug}</td>
                <td className="px-4 py-3 text-slate-600">{r.record_type}</td>
                <td className="px-4 py-3 font-medium text-slate-800">{r.model_name ?? '-'}</td>
                <td className="px-4 py-3 text-right text-slate-600">{r.input_tokens?.toLocaleString() ?? '-'}</td>
                <td className="px-4 py-3 text-right text-slate-600">{r.output_tokens?.toLocaleString() ?? '-'}</td>
                <td className="px-4 py-3 text-right text-slate-600">{r.total_cost_usd != null ? `$${r.total_cost_usd.toFixed(4)}` : '-'}</td>
                <td className="px-4 py-3 text-right text-slate-600">
                  {r.quota_used != null ? `${r.quota_used}/${r.quota_total} ${r.quota_unit}` : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 分页 */}
      {data && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm disabled:opacity-40"
          >
            上一页
          </button>
          <span className="text-sm text-slate-600">第 {page} 页 / 共 {data.pages} 页</span>
          <button
            onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
            disabled={page >= data.pages}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm disabled:opacity-40"
          >
            下一页
          </button>
        </div>
      )}

      {/* Token 分布图 */}
      {tokenBreakdown && tokenBreakdown.length > 0 && (
        <div className="rounded-xl bg-white p-6 shadow-sm border border-slate-200">
          <h2 className="mb-4 text-lg font-semibold text-slate-700">Token 用量分布（按模型，近7天）</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={tokenBreakdown}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="model" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
              <Tooltip />
              <Legend />
              <Bar dataKey="input_tokens" fill="#6366f1" name="输入 Tokens" />
              <Bar dataKey="output_tokens" fill="#22c55e" name="输出 Tokens" />
              <Bar dataKey="cache_read_tokens" fill="#a5b4fc" name="缓存读取" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* 模型费用分布 */}
      {costPieData.length > 0 && (
        <div className="rounded-xl bg-white p-6 shadow-sm border border-slate-200">
          <h2 className="mb-4 text-lg font-semibold text-slate-700">模型费用占比（近7天）</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={costPieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                {costPieData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(v: number) => `$${v.toFixed(4)}`} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
