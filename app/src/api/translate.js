/**
 * 翻译相关接口
 * 对应后端：backend/api/v1/translate.py
 * - POST /translate  中译中翻译（mode: translate/dict）
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

export default {
  translate
}
