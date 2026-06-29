/**
 * 分类相关接口
 * 对应后端：backend/api/v1/category.py
 * - GET /categories                 分类树
 * - GET /categories/{id}/words      分类下词条列表
 */
import { get } from './request'

/**
 * 获取分类树（支持自引用三级层级）
 * @returns {Promise<Array>} 分类树节点数组
 */
export function getCategories() {
  return get('/categories')
}

/**
 * 获取分类下词条列表
 * @param {number} id 分类 ID
 * @param {object} params
 * @param {number} params.page 页码
 * @param {number} params.page_size 每页数量
 * @param {string} params.sort 排序：hot/new/name
 * @returns {Promise<{category: object, list: Array, total: number, page: number, page_size: number}>}
 */
export function getCategoryWords(id, params = {}) {
  return get(`/categories/${id}/words`, params)
}

export default {
  getCategories,
  getCategoryWords
}
