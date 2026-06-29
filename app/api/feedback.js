/**
 * 反馈接口
 * 对应后端：backend/api/v1/feedback.py
 * - POST /feedback 提交质量反馈
 */
import { post } from './request'

/**
 * 提交质量反馈
 * @param {object} data
 * @param {number} data.translation_id 翻译记录 ID
 * @param {string} data.type 反馈类型：accurate/inaccurate/outdated
 * @param {string} data.comment 备注（可选）
 * @returns {Promise<{success: boolean, message: string, feedback_id: number}>}
 */
export function submitFeedback(data) {
  return post('/feedback', data)
}

export default {
  submitFeedback
}
