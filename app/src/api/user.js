/**
 * 用户相关接口
 * 对应后端：backend/api/v1/user.py
 * - POST /user/register          用户注册（设备 ID，保留兼容）
 * - POST /user/login             用户登录（设备 ID，保留兼容）
 * - POST /user/register-account  账号密码注册
 * - POST /user/login-account     账号密码登录
 * - GET  /user/profile           用户信息
 * - PUT  /user/profile           更新昵称头像
 * - PUT  /user/preferences       更新偏好设置
 */
import { get, post, put } from './request'

/**
 * 用户注册（基于设备 ID，保留兼容）
 */
export function register(data) {
  return post('/user/register', data)
}

/**
 * 用户登录（基于设备 ID，保留兼容）
 */
export function login(data) {
  return post('/user/login', data)
}

/**
 * 账号密码注册
 * @param {object} data
 * @param {string} data.username 用户名
 * @param {string} data.password 密码
 * @returns {Promise<{user_id: number, token: string, expires_in: number, is_new: boolean}>}
 */
export function registerAccount(data) {
  return post('/user/register-account', data)
}

/**
 * 账号密码登录
 * @param {object} data
 * @param {string} data.username 用户名
 * @param {string} data.password 密码
 * @returns {Promise<{user_id: number, token: string, expires_in: number, is_new: boolean}>}
 */
export function loginAccount(data) {
  return post('/user/login-account', data)
}

/**
 * 更新用户资料（昵称、头像）
 * @param {object} data
 * @param {string} [data.nickname] 昵称
 * @param {string} [data.avatar] 头像标识
 */
export function updateProfile(data) {
  return put('/user/profile', data)
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

/**
 * 获取当前用户收藏的词条列表（分页）
 * @param {object} params
 * @param {number} params.page 页码
 * @param {number} params.page_size 每页数量
 * @returns {Promise<{list: array, total: number, page: number, page_size: number}>}
 */
export function getFavorites(params) {
  return get('/user/favorites', params)
}

/**
 * 收藏/取消收藏翻译结果（toggle 切换）
 * @param {number} translationId 翻译记录 ID
 * @returns {Promise<{is_favorited: boolean, message: string}>}
 */
export function toggleTranslationFavorite(translationId) {
  return post(`/user/translations/${translationId}/favorite`)
}

/**
 * 获取当前用户收藏的翻译结果列表（分页）
 * @param {object} params
 * @param {number} params.page 页码
 * @param {number} params.page_size 每页数量
 * @returns {Promise<{list: array, total: number, page: number, page_size: number}>}
 */
export function getTranslationFavorites(params) {
  return get('/user/translation-favorites', params)
}

export default {
  registerAccount,
  loginAccount,
  updateProfile,
  getProfile,
  updatePreferences,
  getFavorites,
  toggleTranslationFavorite,
  getTranslationFavorites
}
