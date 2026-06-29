/**
 * 环境配置
 * 统一管理 API 地址与运行时配置
 */
const BASE_URL = 'http://localhost:8000/api'

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
