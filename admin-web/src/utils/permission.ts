/** 权限工具：基于当前用户 permissions 列表判断 */

import { useAuthStore } from '@/store/modules/auth'

/** 判断当前登录管理员是否拥有指定权限点 */
export function hasPermission(code: string): boolean {
  const auth = useAuthStore()
  return auth.permissions.includes(code)
}

/** 判断是否拥有任一权限点 */
export function hasAnyPermission(codes: string[]): boolean {
  const auth = useAuthStore()
  return codes.some((c) => auth.permissions.includes(c))
}
