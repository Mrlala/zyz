/**
 * 用户相关接口
 * 对应后端：backend/api/v1/user.py
 * - POST /user/register      用户注册（设备 ID）
 * - POST /user/login         用户登录（设备 ID）
 * - GET  /user/profile       用户信息
 * - PUT  /user/preferences   更新偏好设置
 */
import { get, post, put } from './request'

/**
 * 用户注册（基于设备 ID）
 * @param {object} data
 * @param {string} data.device_id 设备 ID
 * @param {string} data.nickname 昵称（可选）
 * @returns {Promise<{user_id: number, token: string, expires_in: number}>}
 */
export function register(data) {
  return post('/user/register', data)
}

/**
 * 用户登录（基于设备 ID）
 * @param {object} data
 * @param {string} data.device_id 设备 ID
 * @returns {Promise<{user_id: number, token: string, expires_in: number}>}
 */
export function login(data) {
  return post('/user/login', data)
}

/**
 * 获取用户信息（含等级、经验、统计）
 * @returns {Promise<object>}
 */
export function getProfile() {
  return get('/user/profile')
}

/**
 * 更新用户偏好设置
 * @param {object} data
 * @param {string} data.default_mode 默认翻译模式 translate/dict
 * @param {boolean} data.show_risk_advice 是否显示风险提示
 * @param {string} data.font_size 字体大小 small/medium/large
 * @param {string} data.theme 主题 light/dark/auto
 * @returns {Promise<object>} 更新后的偏好
 */
export function updatePreferences(data) {
  return put('/user/preferences', data)
}

export default {
  register,
  login,
  getProfile,
  updatePreferences
}
