/**
 * 环境配置
 * 统一管理 API 地址与运行时配置
 *
 * 开发环境：Vite proxy 将 /api 代理到 localhost:8000（见 vite.config.js）
 * 生产环境：前后端同域部署，nginx 将 /api 反向代理到后端
 */
const isDev = import.meta.env.DEV
const BASE_URL = isDev ? 'http://localhost:8000/api' : '/api'

// 应用版本号
const APP_VERSION = '1.0.0'

// 网络超时（毫秒）
const REQUEST_TIMEOUT = 15000

export default {
  BASE_URL,
  APP_VERSION,
  REQUEST_TIMEOUT
}

export { BASE_URL, APP_VERSION, REQUEST_TIMEOUT }
