/**
 * 词条相关接口
 * 对应后端：backend/api/v1/word.py
 * - GET    /words                词条列表（分页、分类筛选、排序）
 * - GET    /words/search         搜索词条
 * - GET    /words/{word_id}      词条详情
 * - POST   /words/{word_id}/favorite   收藏词条
 * - DELETE /words/{word_id}/favorite   取消收藏
 */
import { get, post, del } from './request'

/**
 * 获取词条列表
 * @param {object} params
 * @param {number} params.page 页码，默认 1
 * @param {number} params.page_size 每页数量，默认 20
 * @param {number} params.category_id 分类 ID
 * @param {string} params.tag 标签筛选
 * @param {string} params.sort 排序：hot/new/name
 * @returns {Promise<{list: Array, total: number, page: number, page_size: number}>}
 */
export function getWords(params = {}) {
  return get('/words', params)
}

/**
 * 获取词条详情
 * @param {number} id 词条 ID
 * @returns {Promise<object>} 词条详情（含 is_favorited、favorite_count）
 */
export function getWordDetail(id) {
  return get(`/words/${id}`)
}

/**
 * 搜索词条
 * @param {string} keyword 关键词（1-50 字符）
 * @param {object} params 额外参数 page/page_size
 * @returns {Promise<{list: Array, total: number, page: number, page_size: number}>}
 */
export function searchWords(keyword, params = {}) {
  return get('/words/search', { keyword, ...params })
}

/**
 * 收藏词条
 * @param {number} id 词条 ID
 * @returns {Promise<{word_id: number, is_favorited: boolean, favorite_count: number}>}
 */
export function favorite(id) {
  return post(`/words/${id}/favorite`)
}

/**
 * 取消收藏
 * @param {number} id 词条 ID
 * @returns {Promise<{word_id: number, is_favorited: boolean, favorite_count: number}>}
 */
export function unfavorite(id) {
  return del(`/words/${id}/favorite`)
}

export default {
  getWords,
  getWordDetail,
  searchWords,
  favorite,
  unfavorite
}
