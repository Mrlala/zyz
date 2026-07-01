/**
 * 热词相关接口
 * 对应后端：backend/api/v1/hot.py
 * - GET  /hot/daily          每日热词
 * - POST /hot/{word_id}/vote 热词投票
 * - GET  /hot/ranking        热词排行榜
 * - GET  /hot/history        学习历史
 */
import { get, post } from './request'

/**
 * 获取每日热词（固定 10 条）
 * @returns {Promise<{date: string, list: Array}>}
 */
export function getDaily() {
  return get('/hot/daily')
}

/**
 * 对热词投票（后端默认 upvote）
 * @param {number} wordId 词条 ID
 * @param {string} voteType 投票类型：upvote（后端当前仅支持 upvote）
 * @param {object} options 额外请求配置，如 { silent: true } 由调用方自定义错误提示
 * @returns {Promise<{word_id: number, vote_count: number, has_voted: boolean}>}
 */
export function vote(wordId, voteType = 'upvote', options = {}) {
  return post(`/hot/${wordId}/vote`, { vote_type: voteType }, options)
}

/**
 * 获取热词排行榜
 * @param {object} params
 * @param {string} params.period 周期：daily/weekly/monthly
 * @param {number} params.limit 返回条数，默认 50
 * @returns {Promise<{period: string, list: Array}>}
 */
export function getRanking(params = {}) {
  return get('/hot/ranking', params)
}

/**
 * 获取用户学习历史
 * @param {object} params
 * @param {number} params.page 页码
 * @param {number} params.page_size 每页数量
 * @returns {Promise<{list: Array, total: number, page: number, page_size: number}>}
 */
export function getHistory(params = {}) {
  return get('/hot/history', params)
}

export default {
  getDaily,
  vote,
  getRanking,
  getHistory
}
