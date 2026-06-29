/**
 * 翻译相关接口
 * 对应后端：backend/api/v1/translate.py
 * - POST /translate        中译中翻译（mode: translate/dict）
 * - POST /translate/dict   词典模式匹配
 */
import { post } from './request'

/**
 * 中译中翻译
 * @param {string} text 待翻译文本
 * @param {string} mode 翻译模式：translate（AI 翻译）/ dict（词典匹配）
 * @returns {Promise<object>} 翻译结果
 */
export function translate(text, mode = 'translate') {
  return post('/translate', { text, mode })
}

/**
 * 词典模式匹配（独立接口，直接返回命中词条列表）
 * @param {string} text 待匹配文本
 * @returns {Promise<{hits: Array, total: number}>}
 */
export function translateDict(text) {
  return post('/translate/dict', { text })
}

export default {
  translate,
  translateDict
}
