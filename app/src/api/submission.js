/**
 * 用户提交接口
 * 对应后端：backend/api/v1/submission.py
 * - POST /submissions 提交新词条
 * - GET  /submissions 我的提交列表
 */
import { get, post } from './request'

/**
 * 提交新词条（进入 pending 队列等待审核）
 * @param {object} data
 * @param {string} data.word 词条
 * @param {string} data.definition 释义
 * @param {string} data.example 示例（可选）
 * @param {number} data.category_id 分类 ID（可选）
 * @returns {Promise<{submission_id: number, status: string, submitted_at: string}>}
 */
export function submitWord(data) {
  return post('/submissions', data)
}

/**
 * 获取我的提交列表
 * @param {object} params
 * @param {string} params.status 状态筛选：pending/approved/rejected
 * @param {number} params.page 页码
 * @param {number} params.page_size 每页数量
 * @returns {Promise<{list: Array, total: number, page: number, page_size: number}>}
 */
export function getMySubmissions(params = {}) {
  return get('/submissions', params)
}

export default {
  submitWord,
  getMySubmissions
}
