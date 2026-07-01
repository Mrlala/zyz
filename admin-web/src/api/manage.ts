import { request } from './request'

// ===================== 管理员认证 =====================
export const authApi = {
  login: (username: string, password: string) =>
    request({
      url: '/manage/auth/login',
      method: 'post',
      data: { username, password },
    }),
  getProfile: () => request({ url: '/manage/auth/profile', method: 'get' }),
  changePassword: (old_password: string, new_password: string) =>
    request({
      url: '/manage/auth/password',
      method: 'put',
      data: { old_password, new_password },
    }),
  logout: () => request({ url: '/manage/auth/logout', method: 'post' }),
}

// ===================== 工作台 =====================
export const dashboardApi = {
  getOverview: () => request({ url: '/manage/dashboard/overview', method: 'get' }),
}

// ===================== 管理员账号 =====================
export const accountApi = {
  list: (params: { page: number; page_size: number; role_id?: number; status?: string; keyword?: string }) =>
    request({ url: '/manage/accounts', method: 'get', params }),
  create: (data: { username: string; password: string; nickname?: string; role_id: number }) =>
    request({ url: '/manage/accounts', method: 'post', data }),
  update: (id: number, data: { nickname?: string; role_id?: number; status?: string }) =>
    request({ url: `/manage/accounts/${id}`, method: 'put', data }),
  remove: (id: number) => request({ url: `/manage/accounts/${id}`, method: 'delete' }),
  resetPassword: (id: number, new_password: string) =>
    request({ url: `/manage/accounts/${id}/reset-password`, method: 'post', data: { new_password } }),
}

// ===================== 角色权限 =====================
export const roleApi = {
  list: () => request({ url: '/manage/roles', method: 'get' }),
  listAllPermissions: () => request({ url: '/manage/roles/permissions/all', method: 'get' }),
  updateRolePermissions: (roleId: number, permission_ids: number[]) =>
    request({ url: `/manage/roles/${roleId}/permissions`, method: 'put', data: { permission_ids } }),
}

// ===================== 词库管理 =====================
export const wordApi = {
  list: (params: {
    page: number
    page_size: number
    keyword?: string
    status?: string
    risk_level?: string
    category_id?: number
  }) => request({ url: '/manage/words', method: 'get', params }),
  get: (id: number) => request({ url: `/manage/words/${id}`, method: 'get' }),
  create: (data: {
    word: string
    meaning: string
    category_id: number
    pinyin?: string
    example?: string
    risk_level?: string
  }) => request({ url: '/manage/words', method: 'post', data }),
  update: (id: number, data: { word?: string; pinyin?: string; meaning?: string; example?: string; category_id?: number }) =>
    request({ url: `/manage/words/${id}`, method: 'put', data }),
  remove: (id: number) => request({ url: `/manage/words/${id}`, method: 'delete' }),
  updateStatus: (id: number, status: string) =>
    request({ url: `/manage/words/${id}/status`, method: 'put', data: { status } }),
  updateRisk: (id: number, data: { risk_level: string; risk_types: string[]; advice: string }) =>
    request({ url: `/manage/words/${id}/risk`, method: 'put', data }),
}

// ===================== 分类管理 =====================
export const categoryApi = {
  list: () => request({ url: '/manage/categories', method: 'get' }),
  create: (data: { name: string; parent_id?: number; level?: number; sort_order?: number; icon?: string }) =>
    request({ url: '/manage/categories', method: 'post', data }),
  update: (id: number, data: { name?: string; parent_id?: number; sort_order?: number; icon?: string }) =>
    request({ url: `/manage/categories/${id}`, method: 'put', data }),
  remove: (id: number) => request({ url: `/manage/categories/${id}`, method: 'delete' }),
}

// ===================== 内容审核 =====================
export const contentAuditApi = {
  listSubmissions: (params: { page: number; page_size: number; status?: string }) =>
    request({ url: '/manage/audit/submissions', method: 'get', params }),
  reviewSubmission: (id: number, data: { action: string; comment?: string; meaning?: string }) =>
    request({ url: `/manage/audit/submissions/${id}/review`, method: 'put', data }),
  listCorrections: (params: { page: number; page_size: number; status?: string }) =>
    request({ url: '/manage/audit/corrections', method: 'get', params }),
  reviewCorrection: (id: number, data: { action: string; comment?: string }) =>
    request({ url: `/manage/audit/corrections/${id}/review`, method: 'put', data }),
}

// ===================== AI 配置 =====================
export const aiConfigApi = {
  get: () => request({ url: '/manage/ai-config', method: 'get' }),
  update: (data: Record<string, any>) => request({ url: '/manage/ai-config', method: 'put', data }),
  test: () => request({ url: '/manage/ai-config/test', method: 'post' }),
}

// ===================== 监控 =====================
export const monitorApi = {
  getApiStats: () => request({ url: '/manage/monitor/api-stats', method: 'get' }),
  getAiStats: () => request({ url: '/manage/monitor/ai-stats', method: 'get' }),
  listAiLogs: (params: { page: number; page_size: number }) =>
    request({ url: '/manage/monitor/ai-logs', method: 'get', params }),
}

// ===================== 操作审计日志 =====================
export const auditLogApi = {
  listOperation: (params: { page: number; page_size: number; module?: string; start_date?: string; end_date?: string }) =>
    request({ url: '/manage/audit-logs/operation', method: 'get', params }),
  listLogin: (params: { page: number; page_size: number; start_date?: string; end_date?: string }) =>
    request({ url: '/manage/audit-logs/login', method: 'get', params }),
  export: (params: { module?: string; action?: string; start_date?: string; end_date?: string }) =>
    request({ url: '/manage/audit-logs/export', method: 'get', params }),
}
