/**
 * 路由配置
 * 统一维护页面路径常量，避免硬编码字符串
 */

// Tab 页路径
export const ROUTES = {
  // 翻译 Tab
  INDEX: '/pages/index/index',
  // 热词 Tab
  HOT: '/pages/hot/index',
  // 词条 Tab
  DICT: '/pages/dict/index',
  // 我的 Tab
  MINE: '/pages/mine/index',

  // 非 Tab 页
  WORD_DETAIL: '/pages/word-detail/index',
  HOT_LEARN: '/pages/hot/learn',
  HOT_RANKING: '/pages/hot/ranking',
  DICT_SEARCH: '/pages/dict/search',
  DICT_CATEGORY: '/pages/dict/category',
  MINE_FAVORITES: '/pages/mine/favorites',
  MINE_HISTORY: '/pages/mine/history',
  MINE_SETTINGS: '/pages/mine/settings',
  MINE_SUBMISSIONS: '/pages/mine/submissions'
}

/**
 * 跳转到指定页面
 * @param {string} path 路由路径（ROUTES 常量）
 * @param {object} params 查询参数
 */
export function navigateTo(path, params = {}) {
  const query = Object.keys(params)
    .filter((k) => params[k] !== undefined && params[k] !== null)
    .map((k) => `${encodeURIComponent(k)}=${encodeURIComponent(params[k])}`)
    .join('&')
  const url = query ? `${path}?${query}` : path
  uni.navigateTo({ url })
}

/**
 * 切换 Tab 页
 * @param {string} path Tab 路由路径
 */
export function switchTab(path) {
  uni.switchTab({ url: path })
}

/**
 * 返回上一页
 */
export function navigateBack(delta = 1) {
  uni.navigateBack({ delta })
}

export default ROUTES
