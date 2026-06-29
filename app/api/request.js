/**
 * 统一请求封装
 * 基于 uni.request 实现，支持请求/响应拦截、错误统一处理
 *
 * 后端统一响应格式：
 * {
 *   "code": 0,            // 0 表示成功，非 0 表示业务错误
 *   "message": "success",
 *   "data": {...}
 * }
 *
 * 后端鉴权：Authorization: Bearer <token>
 */
import { BASE_URL, REQUEST_TIMEOUT } from '@/config/env'
import storage from '@/utils/storage'

// Token 与设备 ID 的本地存储键
const TOKEN_KEY = 'zyz_token'
const DEVICE_ID_KEY = 'zyz_device_id'

/**
 * 获取本地 Token
 * @returns {string}
 */
function getToken() {
  return storage.get(TOKEN_KEY) || ''
}

/**
 * 获取设备 ID（首次调用自动生成并持久化）
 * @returns {string}
 */
function getDeviceId() {
  let deviceId = storage.get(DEVICE_ID_KEY)
  if (!deviceId) {
    deviceId = `web_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
    storage.set(DEVICE_ID_KEY, deviceId)
  }
  return deviceId
}

/**
 * 401 处理：清除登录态并跳转登录页
 * 当前业务为设备 ID 自动登录，未注册则静默处理，由调用方决定是否引导注册
 */
function handleUnauthorized() {
  storage.remove(TOKEN_KEY)
  uni.showToast({
    title: '登录已失效，请重新进入',
    icon: 'none',
    duration: 2000
  })
}

/**
 * 网络错误统一提示
 * @param {string} message
 */
function showError(message) {
  uni.showToast({
    title: message || '网络异常，请稍后重试',
    icon: 'none',
    duration: 2000
  })
}

/**
 * 核心请求方法
 * @param {object} options
 * @param {string} options.url 相对路径（不含 BASE_URL）
 * @param {string} options.method 请求方法 GET/POST/PUT/DELETE
 * @param {object} options.data 请求参数
 * @param {object} options.header 自定义请求头
 * @param {boolean} options.silent 是否静默错误（不弹 toast）
 * @returns {Promise<any>} 返回 data 字段内容
 */
function request(options) {
  const {
    url,
    method = 'GET',
    data,
    header = {},
    silent = false
  } = options

  // 请求拦截：自动添加鉴权头与设备 ID
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    'X-Device-Id': getDeviceId(),
    ...header
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  return new Promise((resolve, reject) => {
    uni.request({
      url: `${BASE_URL}${url}`,
      method,
      data,
      header: headers,
      timeout: REQUEST_TIMEOUT,
      success: (res) => {
        // HTTP 状态码处理
        const statusCode = res.statusCode || 0

        if (statusCode === 401) {
          handleUnauthorized()
          reject(new Error('未授权或登录已失效'))
          return
        }

        if (statusCode < 200 || statusCode >= 300) {
          const errMsg = (res.data && res.data.detail) || `请求失败（${statusCode}）`
          if (!silent) showError(errMsg)
          reject(new Error(errMsg))
          return
        }

        // 业务响应处理
        const body = res.data || {}
        // 后端 BaseResponse 字段：code/message/data
        // FastAPI 默认 code=0/message="success"
        if (body.code !== undefined && body.code !== 0) {
          const msg = body.message || '请求失败'
          if (!silent) showError(msg)
          reject(new Error(msg))
          return
        }

        // 兼容两种结构：{ data } 或裸对象
        resolve(body.data !== undefined ? body.data : body)
      },
      fail: (err) => {
        console.error('[request fail]', url, err)
        if (!silent) showError('网络异常，请检查网络连接')
        reject(new Error(err.errMsg || '网络异常'))
      }
    })
  })
}

/**
 * GET 请求
 * @param {string} url 相对路径
 * @param {object} params 查询参数
 * @param {object} options 额外配置
 */
export function get(url, params = {}, options = {}) {
  const query = Object.keys(params)
    .filter((k) => params[k] !== undefined && params[k] !== null && params[k] !== '')
    .map((k) => `${encodeURIComponent(k)}=${encodeURIComponent(params[k])}`)
    .join('&')
  const fullUrl = query ? `${url}?${query}` : url
  return request({ ...options, url: fullUrl, method: 'GET' })
}

/**
 * POST 请求
 * @param {string} url 相对路径
 * @param {object} data 请求体
 * @param {object} options 额外配置
 */
export function post(url, data = {}, options = {}) {
  return request({ ...options, url, method: 'POST', data })
}

/**
 * PUT 请求
 * @param {string} url 相对路径
 * @param {object} data 请求体
 * @param {object} options 额外配置
 */
export function put(url, data = {}, options = {}) {
  return request({ ...options, url, method: 'PUT', data })
}

/**
 * DELETE 请求
 * @param {string} url 相对路径
 * @param {object} params 查询参数
 * @param {object} options 额外配置
 */
export function del(url, params = {}, options = {}) {
  const query = Object.keys(params)
    .filter((k) => params[k] !== undefined && params[k] !== null)
    .map((k) => `${encodeURIComponent(k)}=${encodeURIComponent(params[k])}`)
    .join('&')
  const fullUrl = query ? `${url}?${query}` : url
  return request({ ...options, url: fullUrl, method: 'DELETE' })
}

export default {
  request,
  get,
  post,
  put,
  del,
  getToken,
  getDeviceId
}
