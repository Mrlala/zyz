/**
 * 纠错接口
 * 对应后端：backend/api/v1/correction.py
 * - POST /corrections 提交纠错
 */
import { post } from './request'

/**
 * 提交词条纠错报告
 * @param {object} data
 * @param {number} data.word_id 词条 ID
 * @param {string} data.type 纠错类型：meaning_wrong/example_wrong/outdated/other
 * @param {string} data.content 纠错内容
 * @returns {Promise<{correction_id: number, status: string, submitted_at: string}>}
 */
export function submitCorrection(data) {
  return post('/corrections', data)
}

export default {
  submitCorrection
}
