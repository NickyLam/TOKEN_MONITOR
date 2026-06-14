import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Building2,
  CreditCard,
  BarChart3,
  Bell,
  Settings,
} from 'lucide-react'

const navItems = [
  { to: '/dashboard', label: '仪表盘', icon: LayoutDashboard },
  { to: '/vendors', label: '厂商管理', icon: Building2 },
  { to: '/plans', label: '套餐管理', icon: CreditCard },
  { to: '/usage', label: '用量详情', icon: BarChart3 },
  { to: '/alerts', label: '告警中心', icon: Bell },
  { to: '/settings', label: '系统设置', icon: Settings },
]

export default function Sidebar() {
  return (
    <aside className="flex w-60 flex-col border-r border-slate-200 bg-white">
      <div className="flex h-16 items-center gap-2 border-b border-slate-200 px-6">
        <BarChart3 className="h-6 w-6 text-indigo-600" />
        <span className="text-lg font-bold text-slate-800">Token 监管</span>
      </div>
      <nav className="flex-1 space-y-1 p-4">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-indigo-50 text-indigo-700'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`
            }
          >
            <item.icon className="h-5 w-5" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
