import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import api from '../api/client'
import type { AlertRule, AlertEvent, Plan } from '../types'

export default function AlertsPage() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    plan_id: 0, rule_type: 'quota_percent', threshold_value: 80, is_enabled: true,
  })

  const { data: rules } = useQuery<AlertRule[]>({
    queryKey: ['alertRules'],
    queryFn: () => api.get('/alerts/rules').then((r) => r.data),
  })

  const { data: events } = useQuery<AlertEvent[]>({
    queryKey: ['alertEvents'],
    queryFn: () => api.get('/alerts/events?limit=20').then((r) => r.data),
  })

  const { data: plans } = useQuery<Plan[]>({
    queryKey: ['plans'],
    queryFn: () => api.get('/plans').then((r) => r.data),
  })

  const createRuleMut = useMutation({
    mutationFn: (data: typeof form) => api.post('/alerts/rules', data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['alertRules'] }); setShowForm(false) },
  })

  const deleteRuleMut = useMutation({
    mutationFn: (id: number) => api.delete(`/alerts/rules/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alertRules'] }),
  })

  const dismissMut = useMutation({
    mutationFn: (id: number) => api.post(`/alerts/events/${id}/dismiss`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alertEvents'] })
      queryClient.invalidateQueries({ queryKey: ['alertUnreadCount'] })
    },
  })

  const dismissAllMut = useMutation({
    mutationFn: () => api.post('/alerts/events/dismiss-all'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alertEvents'] })
      queryClient.invalidateQueries({ queryKey: ['alertUnreadCount'] })
    },
  })

  const ruleTypeLabels: Record<string, string> = {
    quota_percent: '配额百分比',
    spend_dollars: '消费金额 (USD)',
    plan_expiring_days: '即将到期（天）',
    daily_spend_spike: '每日消费峰值 (%)',
    token_threshold: 'Token 阈值',
  }

  const severityColors: Record<string, string> = {
    info: 'bg-blue-50 text-blue-700 border-blue-200',
    warning: 'bg-amber-50 text-amber-700 border-amber-200',
    critical: 'bg-red-50 text-red-700 border-red-200',
  }

  const severityLabels: Record<string, string> = {
    info: '提示',
    warning: '警告',
    critical: '严重',
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">告警中心</h1>
        <button
          onClick={() => setShowForm(true)}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          添加规则
        </button>
      </div>

      {/* 告警规则 */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <h2 className="border-b border-slate-200 px-6 py-4 text-lg font-semibold text-slate-700">告警规则</h2>
        <div className="divide-y divide-slate-100">
          {rules?.map((r) => {
            const plan = plans?.find((p) => p.id === r.plan_id)
            return (
              <div key={r.id} className="flex items-center justify-between px-6 py-3">
                <div>
                  <p className="text-sm font-medium text-slate-800">{plan?.name ?? `Plan #${r.plan_id}`}</p>
                  <p className="text-xs text-slate-500">
                    {ruleTypeLabels[r.rule_type] ?? r.rule_type} &ge; {r.threshold_value}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${r.is_enabled ? 'bg-green-50 text-green-700' : 'bg-slate-100 text-slate-500'}`}>
                    {r.is_enabled ? '启用' : '禁用'}
                  </span>
                  <button onClick={() => deleteRuleMut.mutate(r.id)} className="text-xs text-red-500 hover:underline">删除</button>
                </div>
              </div>
            )
          })}
          {rules?.length === 0 && <p className="px-6 py-4 text-sm text-slate-400">暂无告警规则</p>}
        </div>
      </div>

      {/* 告警事件 */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-slate-700">告警事件</h2>
          <button
            onClick={() => dismissAllMut.mutate()}
            className="text-xs text-indigo-600 hover:underline"
          >
            全部标记已读
          </button>
        </div>
        <div className="divide-y divide-slate-100">
          {events?.map((e) => (
            <div key={e.id} className={`px-6 py-3 ${e.is_read ? 'opacity-60' : ''}`}>
              <div className="flex items-start justify-between">
                <div>
                  <span className={`mr-2 inline-block rounded-full border px-2 py-0.5 text-xs font-medium ${severityColors[e.severity] ?? ''}`}>
                    {severityLabels[e.severity] ?? e.severity}
                  </span>
                  <span className="text-sm text-slate-700">{e.message}</span>
                </div>
                {!e.is_read && (
                  <button onClick={() => dismissMut.mutate(e.id)} className="text-xs text-indigo-600 hover:underline">标记已读</button>
                )}
              </div>
              <p className="mt-1 text-xs text-slate-400">
                {new Date(e.triggered_at).toLocaleString('zh-CN')}
              </p>
            </div>
          ))}
          {events?.length === 0 && <p className="px-6 py-4 text-sm text-slate-400">暂无告警事件</p>}
        </div>
      </div>

      {/* 添加规则表单 */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowForm(false)}>
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h2 className="mb-4 text-lg font-semibold">添加告警规则</h2>
            <form onSubmit={(e) => { e.preventDefault(); createRuleMut.mutate(form) }} className="space-y-3">
              <div>
                <label className="text-sm font-medium text-slate-700">套餐</label>
                <select
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  value={form.plan_id}
                  onChange={(e) => setForm({ ...form, plan_id: Number(e.target.value) })}
                  required
                >
                  <option value={0}>选择套餐</option>
                  {plans?.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">规则类型</label>
                <select
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  value={form.rule_type}
                  onChange={(e) => setForm({ ...form, rule_type: e.target.value })}
                >
                  <option value="quota_percent">配额百分比 (%)</option>
                  <option value="spend_dollars">消费金额 (USD)</option>
                  <option value="plan_expiring_days">即将到期（天）</option>
                  <option value="daily_spend_spike">每日消费峰值 (%)</option>
                  <option value="token_threshold">Token 阈值</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">阈值</label>
                <input
                  type="number" step="any"
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  value={form.threshold_value}
                  onChange={(e) => setForm({ ...form, threshold_value: Number(e.target.value) })}
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowForm(false)} className="rounded-lg border border-slate-300 px-4 py-2 text-sm">取消</button>
                <button type="submit" className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">添加</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
