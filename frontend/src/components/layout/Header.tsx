import { useQuery } from '@tanstack/react-query'
import { Bell } from 'lucide-react'
import api from '../../api/client'
import { useAlertStore } from '../../stores/alertStore'

export default function Header() {
  const { setUnreadCount } = useAlertStore()

  const { data } = useQuery({
    queryKey: ['alertUnreadCount'],
    queryFn: async () => {
      const res = await api.get('/alerts/events/unread-count')
      setUnreadCount(res.data.count)
      return res.data
    },
    refetchInterval: 30_000,
  })

  const count = data?.count ?? 0

  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6">
      <h2 className="text-sm text-slate-400">AI 编码工具用量监管平台</h2>
      <div className="relative">
        <Bell className="h-5 w-5 text-slate-500 cursor-pointer hover:text-slate-700" />
        {count > 0 && (
          <span className="absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs font-bold text-white">
            {count > 9 ? '9+' : count}
          </span>
        )}
      </div>
    </header>
  )
}
