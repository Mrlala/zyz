import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

/** 后端统一响应结构 BaseResponse */
interface BaseResponse<T = any> {
  code: number
  message: string
  data: T
}

const service: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截器：注入管理端 JWT
service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('admin_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// 响应拦截器：统一错误处理 + 解包 data
service.interceptors.response.use(
  (response: AxiosResponse<BaseResponse>) => {
    const res = response.data
    // 业务成功（code === 0）→ 直接返回 data 字段
    if (res.code === 0) {
      return res.data as any
    }
    // 业务失败
    ElMessage.error(res.message || '请求失败')
    return Promise.reject(new Error(res.message || 'Error'))
  },
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail || error.response?.data?.message

    if (status === 401) {
      // 认证失效：清 token 跳登录
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_profile')
      // 避免在 login 页重复跳转
      if (!window.location.pathname.endsWith('/login')) {
        ElMessage.error('登录已失效，请重新登录')
        window.location.href = '/login'
      }
    } else if (status === 403) {
      ElMessage.error(detail || '无权限执行此操作')
    } else if (status >= 400) {
      ElMessage.error(detail || `请求错误 (${status})`)
    } else {
      ElMessage.error(error.message || '网络异常')
    }
    return Promise.reject(error)
  },
)

/** 泛型请求方法，返回后端 data 字段 */
export function request<T = any>(config: AxiosRequestConfig): Promise<T> {
  return service(config) as unknown as Promise<T>
}

export default service
