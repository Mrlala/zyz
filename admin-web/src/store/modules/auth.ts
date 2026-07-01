import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '@/api/manage'

export interface AdminProfile {
  admin_id: number
  username: string
  nickname: string
  role_id: number
  role_code: string
  role_name: string
  permissions: string[]
  last_login_at: string | null
  must_change_password: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('admin_token') || '')
  const profile = ref<AdminProfile | null>(null)
  const permissions = ref<string[]>([])

  /** 设置 token 并持久化 */
  function setToken(t: string) {
    token.value = t
    localStorage.setItem('admin_token', t)
  }

  /** 设置用户资料 + 权限 */
  function setProfile(p: AdminProfile) {
    profile.value = p
    permissions.value = p.permissions || []
    localStorage.setItem('admin_profile', JSON.stringify(p))
  }

  /** 从 localStorage 恢复 profile（页面刷新时） */
  function restoreProfile() {
    const cached = localStorage.getItem('admin_profile')
    if (cached) {
      try {
        const p = JSON.parse(cached) as AdminProfile
        profile.value = p
        permissions.value = p.permissions || []
      } catch {
        localStorage.removeItem('admin_profile')
      }
    }
  }

  /** 登录 */
  async function login(username: string, password: string) {
    const data: any = await authApi.login(username, password)
    setToken(data.token)
    return data
  }

  /** 拉取个人资料 + 权限 */
  async function fetchProfile() {
    const data: any = await authApi.getProfile()
    setProfile(data as AdminProfile)
    return data
  }

  /** 登出 */
  async function logout() {
    try {
      await authApi.logout()
    } catch {
      // 忽略登出接口错误
    }
    token.value = ''
    profile.value = null
    permissions.value = []
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_profile')
  }

  return {
    token,
    profile,
    permissions,
    setToken,
    setProfile,
    restoreProfile,
    login,
    fetchProfile,
    logout,
  }
})
