import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import api from '../api/client'
import type { Vendor } from '../types'

export default function VendorsPage() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Vendor | null>(null)
  const [form, setForm] = useState({ slug: '', display_name: '', icon_url: '', is_active: true })
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)

  const { data: vendors } = useQuery<Vendor[]>({
    queryKey: ['vendors'],
    queryFn: () => api.get('/vendors').then((r) => r.data),
  })

  const createMut = useMutation({
    mutationFn: (data: typeof form) => api.post('/vendors', data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['vendors'] }); setShowForm(false) },
  })

  const updateMut = useMutation({
    mutationFn: ({ slug, data }: { slug: string; data: Partial<typeof form> }) => api.put(`/vendors/${slug}`, data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['vendors'] }); setEditing(null) },
  })

  const deleteMut = useMutation({
    mutationFn: (slug: string) => api.delete(`/vendors/${slug}`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['vendors'] }); setConfirmDelete(null) },
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (editing) {
      updateMut.mutate({ slug: editing.slug, data: form })
    } else {
      createMut.mutate(form)
    }
  }

  function openEdit(v: Vendor) {
    setEditing(v)
    setForm({ slug: v.slug, display_name: v.display_name, icon_url: v.icon_url ?? '', is_active: v.is_active })
    setShowForm(true)
  }

  function closeForm() {
    setShowForm(false)
    setEditing(null)
    setForm({ slug: '', display_name: '', icon_url: '', is_active: true })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">厂商管理</h1>
        <button
          onClick={() => setShowForm(true)}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          添加厂商
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {vendors?.map((v) => (
          <div key={v.slug} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50 text-lg font-bold text-indigo-600">
                  {v.display_name.charAt(0)}
                </div>
                <div>
                  <h3 className="font-semibold text-slate-800">{v.display_name}</h3>
                  <p className="text-xs text-slate-400">{v.slug}</p>
                </div>
              </div>
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${v.is_active ? 'bg-green-50 text-green-700' : 'bg-slate-100 text-slate-500'}`}>
                {v.is_active ? '启用' : '禁用'}
              </span>
            </div>
            <div className="mt-4 flex gap-2">
              <button onClick={() => openEdit(v)} className="text-xs text-indigo-600 hover:underline">编辑</button>
              <button onClick={() => setConfirmDelete(v.slug)} className="text-xs text-red-500 hover:underline">删除</button>
            </div>
          </div>
        ))}
      </div>

      {/* 添加/编辑表单 */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={closeForm}>
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h2 className="mb-4 text-lg font-semibold">{editing ? '编辑厂商' : '添加厂商'}</h2>
            <form onSubmit={handleSubmit} className="space-y-3">
              {!editing && (
                <div>
                  <label className="text-sm font-medium text-slate-700">唯一标识 (slug)</label>
                  <input
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    value={form.slug}
                    onChange={(e) => setForm({ ...form, slug: e.target.value })}
                    placeholder="例：cursor"
                    required
                  />
                </div>
              )}
              <div>
                <label className="text-sm font-medium text-slate-700">显示名称</label>
                <input
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  value={form.display_name}
                  onChange={(e) => setForm({ ...form, display_name: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">图标 URL（可选）</label>
                <input
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  value={form.icon_url}
                  onChange={(e) => setForm({ ...form, icon_url: e.target.value })}
                />
              </div>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
                启用
              </label>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={closeForm} className="rounded-lg border border-slate-300 px-4 py-2 text-sm">取消</button>
                <button type="submit" className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
                  {editing ? '保存' : '添加'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 删除确认 */}
      {confirmDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setConfirmDelete(null)}>
          <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg font-semibold text-slate-800">确认删除</h2>
            <p className="mt-2 text-sm text-slate-600">确定要删除厂商 "{confirmDelete}" 吗？该操作不可撤销。</p>
            <div className="mt-4 flex justify-end gap-2">
              <button onClick={() => setConfirmDelete(null)} className="rounded-lg border border-slate-300 px-4 py-2 text-sm">取消</button>
              <button onClick={() => deleteMut.mutate(confirmDelete)} className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700">删除</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
