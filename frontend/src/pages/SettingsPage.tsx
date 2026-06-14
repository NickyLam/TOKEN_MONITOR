import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'
import type { PollingStatus } from '../types'

export default function SettingsPage() {
  const queryClient = useQueryClient()

  const { data: configs } = useQuery<PollingStatus[]>({
    queryKey: ['pollingConfig'],
    queryFn: () => api.get('/polling/config').then((r) => r.data),
  })

  const toggleMut = useMutation({
    mutationFn: ({ slug, enabled }: { slug: string; enabled: boolean }) =>
      api.put(`/polling/config/${slug}`, { is_enabled: enabled }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pollingConfig'] }),
  })

  const triggerMut = useMutation({
    mutationFn: (slug: string) => api.post(`/polling/trigger/${slug}`),
  })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">系统设置</h1>

      {/* 轮询状态 */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <h2 className="border-b border-slate-200 px-6 py-4 text-lg font-semibold text-slate-700">轮询状态</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-200 bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-600">厂商</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">状态</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">间隔（分钟）</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">上次成功</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">连续失败</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {configs?.map((c) => (
                <tr key={c.vendor_slug} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-slate-800">{c.vendor_slug}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${c.is_enabled ? 'bg-green-50 text-green-700' : 'bg-slate-100 text-slate-500'}`}>
                      {c.is_enabled ? '启用' : '禁用'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{c.interval_minutes}</td>
                  <td className="px-4 py-3 text-slate-600">{c.last_success_at ? new Date(c.last_success_at).toLocaleString('zh-CN') : '-'}</td>
                  <td className="px-4 py-3">
                    <span className={c.consecutive_failures > 0 ? 'text-red-600 font-medium' : 'text-slate-500'}>
                      {c.consecutive_failures}
                    </span>
                    {c.last_error && <p className="mt-0.5 text-xs text-red-400 truncate max-w-xs">{c.last_error}</p>}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => toggleMut.mutate({ slug: c.vendor_slug, enabled: !c.is_enabled })}
                        className="text-xs text-indigo-600 hover:underline"
                      >
                        {c.is_enabled ? '禁用' : '启用'}
                      </button>
                      <button
                        onClick={() => triggerMut.mutate(c.vendor_slug)}
                        className="text-xs text-emerald-600 hover:underline"
                      >
                        立即轮询
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 数据导出 */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-700">数据导出</h2>
        <p className="mt-2 text-sm text-slate-500">导出全部用量记录为 CSV 文件。</p>
        <a
          href="/api/usage/export?days=90"
          className="mt-3 inline-block rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50"
        >
          下载 CSV（近90天）
        </a>
      </div>
    </div>
  )
}
