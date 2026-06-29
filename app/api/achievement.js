/**
 * 成就相关接口
 * 对应后端：backend/api/v1/achievement.py
 * - GET /achievements         成就列表
 * - GET /achievements/mine    我的成就
 * - GET /achievements/ranking 成就排行榜
 */
import { get } from './request'

/**
 * 获取全部成就列表
 * @returns {Promise<Array>}
 */
export function getAchievements() {
  return get('/achievements')
}

/**
 * 获取我的成就（已解锁 + 进行中）
 * @returns {Promise<{unlocked: Array, in_progress: Array}>}
 */
export function getMyAchievements() {
  return get('/achievements/mine')
}

/**
 * 获取成就排行榜
 * @param {object} params
 * @param {number} params.limit 返回条数，默认 50
 * @returns {Promise<Array>}
 */
export function getRanking(params = {}) {
  return get('/achievements/ranking', params)
}

export default {
  getAchievements,
  getMyAchievements,
  getRanking
}
