import { create } from 'zustand'

interface AlertStore {
  unreadCount: number
  setUnreadCount: (count: number) => void
  decrement: () => void
}

export const useAlertStore = create<AlertStore>((set) => ({
  unreadCount: 0,
  setUnreadCount: (count) => set({ unreadCount: count }),
  decrement: () => set((s) => ({ unreadCount: Math.max(0, s.unreadCount - 1) })),
}))
