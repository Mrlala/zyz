/**
 * 后台管理接口
 * 对应后端：backend/api/v1/admin.py
 * - GET  /admin/words               词条管理列表
 * - PUT  /admin/words/{word_id}     修改词条
 * - DELETE /admin/words/{word_id}   删除词条
 * - PUT  /admin/words/{word_id}/risk 标记风险
 * - GET  /admin/submissions         待审核提交列表
 * - PUT  /admin/submissions/{id}/review 审核提交
 * - GET  /admin/stats               数据统计
 * - GET  /admin/corrections         纠错列表
 * - PUT  /admin/corrections/{id}/review 审核纠错
 */
import { get, put, del } from './request'

/* ============ 词条管理 ============ */

/**
 * 词条管理列表
 * @param {object} params
 * @param {number} params.page 页码
 * @param {number} params.page_size 每页数量
 * @param {string} [params.keyword] 关键词
 * @param {string} [params.status] 状态筛选 normal/flagged/hidden
 * @param {string} [params.risk_level] 风险等级 low/medium/high
 */
export function getWordList(params) {
  return get('/admin/words', params)
}

/**
 * 修改词条
 * @param {number} wordId 词条 ID
 * @param {object} data
 * @param {string} [data.definition] 释义
 * @param {string[]} [data.tags] 标签
 * @param {number} [data.category_id] 分类 ID
 */
export function updateWord(wordId, data) {
  return put(`/admin/words/${wordId}`, data)
}

/**
 * 删除词条（软删除）
 * @param {number} wordId 词条 ID
 */
export function deleteWord(wordId) {
  return del(`/admin/words/${wordId}`)
}

/**
 * 标记词条风险
 * @param {number} wordId 词条 ID
 * @param {object} data
 * @param {string} data.risk_level 风险等级 low/medium/high
 * @param {string[]} data.risk_types 风险类型
 * @param {string} data.advice 建议
 */
export function updateWordRisk(wordId, data) {
  return put(`/admin/words/${wordId}/risk`, data)
}

/* ============ 提交审核 ============ */

/**
 * 待审核提交列表
 * @param {object} params
 * @param {string} [params.status] 状态 pending/approved/rejected
 * @param {number} [params.page] 页码
 * @param {number} [params.page_size] 每页数量
 */
export function getSubmissions(params) {
  return get('/admin/submissions', params)
}

/**
 * 审核提交
 * @param {number} submissionId 提交 ID
 * @param {object} data
 * @param {string} data.action 审核动作 approve/reject
 * @param {string} [data.comment] 审核评论/驳回原因
 */
export function reviewSubmission(submissionId, data) {
  return put(`/admin/submissions/${submissionId}/review`, data)
}

/* ============ 数据统计 ============ */

/**
 * 数据统计
 * @param {object} [params]
 * @param {string} [params.start_date] 起始日期 YYYY-MM-DD
 * @param {string} [params.end_date] 截止日期 YYYY-MM-DD
 */
export function getStats(params) {
  return get('/admin/stats', params)
}

/* ============ 纠错审核 ============ */

/**
 * 纠错列表
 * @param {object} params
 * @param {string} [params.status] 状态 pending/approved/rejected
 * @param {number} [params.page] 页码
 * @param {number} [params.page_size] 每页数量
 */
export function getCorrections(params) {
  return get('/admin/corrections', params)
}

/**
 * 审核纠错
 * @param {number} correctionId 纠错 ID
 * @param {object} data
 * @param {string} data.action 审核动作 approve/reject
 * @param {string} [data.comment] 审核评论
 */
export function reviewCorrection(correctionId, data) {
  return put(`/admin/corrections/${correctionId}/review`, data)
}

export default {
  getWordList,
  updateWord,
  deleteWord,
  updateWordRisk,
  getSubmissions,
  reviewSubmission,
  getStats,
  getCorrections,
  reviewCorrection
}
