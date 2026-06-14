import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import api from '../api/client'
import type { Plan, Vendor } from '../types'

interface ConfigField {
  key: string
  label: string
  type: string
  placeholder: string
  help: string
}

export default function PlansPage() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    vendor_id: 0, name: '', plan_type: 'subscription', monthly_cost: 0,
    quota_limit: 0, quota_unit: 'requests', billing_day: 1, renewal_date: '',
    api_key_ref: '', extra_config: '{}',
  })
  const [configFields, setConfigFields] = useState<ConfigField[]>([])
  const [configValues, setConfigValues] = useState<Record<string, string>>({})

  const { data: plans } = useQuery<Plan[]>({
    queryKey: ['plans'],
    queryFn: () => api.get('/plans').then((r) => r.data),
  })

  const { data: vendors } = useQuery<Vendor[]>({
    queryKey: ['vendors'],
    queryFn: () => api.get('/vendors').then((r) => r.data),
  })

  // Fetch config fields when vendor changes
  useEffect(() => {
    const vendor = vendors?.find(v => v.id === form.vendor_id)
    if (vendor) {
      api.get(`/vendors/${vendor.slug}/config-fields`).then(r => {
        setConfigFields(r.data.fields || [])
      }).catch(() => setConfigFields([]))
    } else {
      setConfigFields([])
    }
  }, [form.vendor_id, vendors])

  const createMut = useMutation({
    mutationFn: (data: typeof form) => {
      // Merge config values into extra_config
      let extra: Record<string, unknown> = {}
      try { extra = JSON.parse(data.extra_config || '{}') } catch {}
      const mergedExtra = { ...extra, ...configValues }
      return api.post('/plans', { ...data, extra_config: JSON.stringify(mergedExtra) })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans'] })
      setShowForm(false)
      setConfigValues({})
    },
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    createMut.mutate(form)
  }

  const typeColors: Record<string, string> = {
    subscription: 'bg-indigo-50 text-indigo-700',
    token_credits: 'bg-emerald-50 text-emerald-700',
    free_tier: 'bg-slate-100 text-slate-600',
  }

  const typeLabels: Record<string, string> = {
    subscription: '订阅',
    token_credits: 'Token 额度',
    free_tier: '免费层',
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">套餐管理</h1>
        <button
          onClick={() => setShowForm(true)}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          添加套餐
        </button>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-200 bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-slate-600">厂商</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">套餐名</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">类型</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">月费</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">配额进度</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">续费日</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">API 配置</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {plans?.map((p) => {
              const vendor = vendors?.find((v) => v.id === p.vendor_id)
              const pct = p.quota_limit ? (p.quota_used! / p.quota_limit) * 100 : 0
              const hasKey = !!p.api_key_ref || (p.extra_config && Object.keys(p.extra_config).some(k => k.includes('key') || k.includes('token')))
              return (
                <tr key={p.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 text-slate-700">{vendor?.display_name ?? '-'}</td>
                  <td className="px-4 py-3 font-medium text-slate-800">{p.name}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${typeColors[p.plan_type] ?? ''}`}>
                      {typeLabels[p.plan_type] ?? p.plan_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600">${p.monthly_cost?.toFixed(2)}</td>
                  <td className="px-4 py-3">
                    {p.quota_limit ? (
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-24 rounded-full bg-slate-200">
                          <div
                            className={`h-2 rounded-full ${pct > 90 ? 'bg-red-500' : pct > 70 ? 'bg-amber-500' : 'bg-green-500'}`}
                            style={{ width: `${Math.min(pct, 100)}%` }}
                          />
                        </div>
                        <span className="text-xs text-slate-500">{pct.toFixed(1)}%</span>
                      </div>
                    ) : (
                      <span className="text-xs text-slate-400">按量付费</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{p.renewal_date ?? '-'}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${hasKey ? 'bg-green-50 text-green-700' : 'bg-amber-50 text-amber-700'}`}>
                      {hasKey ? '已配置' : '未配置'}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* 添加套餐表单 */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowForm(false)}>
          <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h2 className="mb-4 text-lg font-semibold">添加套餐</h2>
            <form onSubmit={handleSubmit} className="space-y-3">
              <div>
                <label className="text-sm font-medium text-slate-700">厂商</label>
                <select
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  value={form.vendor_id}
                  onChange={(e) => setForm({ ...form, vendor_id: Number(e.target.value) })}
                  required
                >
                  <option value={0}>选择厂商</option>
                  {vendors?.map((v) => <option key={v.id} value={v.id}>{v.display_name}</option>)}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">套餐名称</label>
                <input
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="例：Cursor Pro / Claude Max"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-sm font-medium text-slate-700">类型</label>
                  <select
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    value={form.plan_type}
                    onChange={(e) => setForm({ ...form, plan_type: e.target.value })}
                  >
                    <option value="subscription">订阅</option>
                    <option value="token_credits">Token 额度</option>
                    <option value="free_tier">免费层</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700">月费 (USD)</label>
                  <input
                    type="number" step="0.01"
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    value={form.monthly_cost}
                    onChange={(e) => setForm({ ...form, monthly_cost: Number(e.target.value) })}
                  />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-sm font-medium text-slate-700">配额上限</label>
                  <input
                    type="number"
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    value={form.quota_limit}
                    onChange={(e) => setForm({ ...form, quota_limit: Number(e.target.value) })}
                    placeholder="0=按量"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700">单位</label>
                  <input
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    value={form.quota_unit}
                    onChange={(e) => setForm({ ...form, quota_unit: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700">计费日</label>
                  <input
                    type="number" min="1" max="31"
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    value={form.billing_day}
                    onChange={(e) => setForm({ ...form, billing_day: Number(e.target.value) })}
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">续费日期</label>
                <input
                  type="date"
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  value={form.renewal_date}
                  onChange={(e) => setForm({ ...form, renewal_date: e.target.value })}
                />
              </div>

              {/* 厂商特定的配置字段 */}
              {configFields.length > 0 && (
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
                  <h3 className="mb-2 text-sm font-semibold text-amber-800">API 密钥配置</h3>
                  <div className="space-y-2">
                    {configFields.map((field) => (
                      <div key={field.key}>
                        <label className="text-sm font-medium text-slate-700">{field.label}</label>
                        <input
                          type={field.type}
                          className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                          value={configValues[field.key] ?? ''}
                          onChange={(e) => setConfigValues({ ...configValues, [field.key]: e.target.value })}
                          placeholder={field.placeholder}
                        />
                        {field.help && <p className="mt-0.5 text-xs text-slate-400">{field.help}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

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
