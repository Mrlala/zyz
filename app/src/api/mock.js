/**
 * Mock 数据拦截层
 *
 * 在生产构建（无后端）环境下，拦截 API 请求返回本地假数据
 * 使用方式：在 request.js 中引入并包裹 uni.request
 *
 * 设计原则：
 * - URL 匹配 → 返回对应 mock 数据
 * - 不匹配 → 走真实请求（向后端发）
 * - 写操作（POST/PUT/DELETE）→ 返回成功响应，但不持久化
 */

// 静态导入 mock 数据（Vite 构建时会内联进 bundle）
import mockWords from '../../public/mock-data/words.json'
import mockCategories from '../../public/mock-data/categories.json'
import mockHotWords from '../../public/mock-data/hot-words.json'

// ============ 辅助函数 ============

/** 模拟网络延迟 */
function delay(ms = 200) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/** 统一成功响应 */
function success(data) {
  return { code: 0, message: 'success', data }
}

/** 从 URL 提取路径参数 */
function parseUrl(url) {
  // 去掉 BASE_URL 前缀，得到 /xxx/yyy
  const match = url.match(/\/api(\/.*)/)
  return match ? match[1] : url
}

/** 从 URL 提取查询参数 */
function parseQuery(url) {
  const queryMatch = url.match(/\?(.*)/)
  if (!queryMatch) return {}
  const params = new URLSearchParams(queryMatch[1])
  const result = {}
  for (const [key, value] of params.entries()) {
    result[key] = value
  }
  return result
}

// ============ 用户态 mock ============

const mockUser = {
  id: 1,
  username: 'demo_user',
  nickname: '体验官',
  avatar: 'avatar1',
  is_admin: false,
  preferences: { theme: 'light', fontSize: 'medium' }
}

const mockToken = 'mock-jwt-token-for-demo-only'

// ============ Mock 路由匹配 ============

/**
 * 根据 path 和 method 匹配 mock 数据
 * @returns {object|null} 匹配则返回 {data, status}，不匹配返回 null
 */
function matchMock(path, method, body, query) {
  // ---- config ----
  if (path === '/config/ai-status' && method === 'GET') {
    return success({ available: false, model: 'deepseek-chat', mode: '离线演示模式' })
  }

  // ---- categories ----
  if (path === '/categories' && method === 'GET') {
    return success(mockCategories)
  }

  if (path.match(/^\/categories\/(\d+)\/words$/) && method === 'GET') {
    const catId = parseInt(path.match(/^\/categories\/(\d+)\/words$/)[1])
    const page = parseInt(query.page) || 1
    const pageSize = parseInt(query.page_size) || 20
    const sort = query.sort || 'hot'
    let list = mockWords.filter((w) => w.category_id === catId)
    if (sort === 'new') list = list.slice().reverse()
    if (sort === 'name') list = list.slice().sort((a, b) => a.word.localeCompare(b.word))
    // 热门排序（默认）
    if (sort === 'hot') list = list.slice().sort((a, b) => b.vote_count - a.vote_count)
    const total = list.length
    const start = (page - 1) * pageSize
    const pageList = list.slice(start, start + pageSize)
    const cat = mockCategories.find((c) => c.id === catId)
    return success({ list: pageList, total, category: cat })
  }

  // ---- words ----
  if (path === '/words' && method === 'GET') {
    const page = parseInt(query.page) || 1
    const pageSize = parseInt(query.page_size) || 20
    const sort = query.sort || 'hot'
    const catId = query.category_id ? parseInt(query.category_id) : null
    let list = catId ? mockWords.filter((w) => w.category_id === catId) : mockWords.slice()
    if (sort === 'new') list = list.slice().reverse()
    if (sort === 'name') list = list.slice().sort((a, b) => a.word.localeCompare(b.word))
    if (sort === 'hot') list = list.slice().sort((a, b) => (b.vote_count + b.view_count) - (a.vote_count + a.view_count))
    const total = list.length
    const start = (page - 1) * pageSize
    const pageList = list.slice(start, start + pageSize)
    // 给每条加上 category_name
    pageList.forEach((w) => {
      const cat = mockCategories.find((c) => c.id === w.category_id)
      w.category_name = cat ? cat.name : ''
    })
    return success({ list: pageList, total })
  }

  if (path.match(/^\/words\/(\d+)$/) && method === 'GET') {
    const id = parseInt(path.match(/^\/words\/(\d+)$/)[1])
    const word = mockWords.find((w) => w.id === id)
    if (!word) return { code: 404, message: '词条不存在', data: null, status: 404 }
    const cat = mockCategories.find((c) => c.id === word.category_id)
    word.category_name = cat ? cat.name : ''
    return success(word)
  }

  if (path === '/words/search' && method === 'GET') {
    const kw = query.keyword || query.kw || ''
    const page = parseInt(query.page) || 1
    const pageSize = parseInt(query.page_size) || 20
    let list = mockWords.filter(
      (w) => w.word.includes(kw) || (w.meaning && w.meaning.includes(kw)) || (w.example && w.example.includes(kw))
    )
    const total = list.length
    const start = (page - 1) * pageSize
    const pageList = list.slice(start, start + pageSize)
    pageList.forEach((w) => {
      const cat = mockCategories.find((c) => c.id === w.category_id)
      w.category_name = cat ? cat.name : ''
    })
    return success({ list: pageList, total })
  }

  if (path.match(/^\/words\/(\d+)\/favorite$/) && (method === 'POST' || method === 'DELETE')) {
    return success({ favorited: method === 'POST' })
  }

  // ---- hot ----
  if (path === '/hot/daily' && method === 'GET') {
    const list = mockHotWords.slice(0, 10).map((w, idx) => ({
      rank: idx + 1,
      id: w.id,
      word: w.word,
      heat: w.vote_count + w.view_count,
      vote_count: w.vote_count,
      meaning: w.meaning
    }))
    return success({ list })
  }

  if (path === '/hot/ranking' && method === 'GET') {
    const page = parseInt(query.page) || 1
    const pageSize = parseInt(query.page_size) || 20
    const list = mockHotWords.slice().sort((a, b) => b.vote_count - a.vote_count)
    const total = list.length
    const start = (page - 1) * pageSize
    const pageList = list.slice(start, start + pageSize).map((w, idx) => ({
      rank: start + idx + 1,
      id: w.id,
      word: w.word,
      heat: w.vote_count + w.view_count,
      vote_count: w.vote_count,
      meaning: w.meaning,
      pinyin: w.pinyin
    }))
    return success({ list: pageList, total })
  }

  if (path.match(/^\/hot\/(\d+)\/vote$/) && method === 'POST') {
    return success({ voted: true })
  }

  // ---- translate ----
  if (path === '/translate' && method === 'POST') {
    const text = body?.text || ''
    const mode = body?.mode || 'normal'
    // 本地匹配词库
    const matched = mockWords.find((w) => w.word === text || text.includes(w.word))
    if (matched) {
      return success({
        translation: matched.meaning,
        subtext: matched.example || '',
        keywords: [{ word: matched.word, pinyin: matched.pinyin }],
        related: [],
        summary: matched.meaning.slice(0, 60),
        source: 'local_db',
        mode
      })
    }
    // 未匹配：返回 AI 翻译样式（假数据）
    return success({
      translation: `这是「${text}」的离线演示翻译。在线版本会通过 DeepSeek AI 进行智能翻译。`,
      subtext: '当前为离线演示模式，连接后端后可体验完整 AI 翻译功能。',
      keywords: [{ word: text, pinyin: '' }],
      related: mockWords.slice(0, 3).map((w) => ({ id: w.id, word: w.word })),
      summary: `「${text}」的释义摘要`,
      source: 'demo',
      mode
    })
  }

  // ---- user ----
  if (path === '/user/register-account' && method === 'POST') {
    return success({ token: mockToken, user: { ...mockUser, username: body?.username || 'demo' } })
  }

  if (path === '/user/login-account' && method === 'POST') {
    return success({ token: mockToken, user: mockUser })
  }

  if (path === '/user/profile' && method === 'GET') {
    return success(mockUser)
  }

  if (path === '/user/profile' && method === 'PUT') {
    return success({ ...mockUser, ...body })
  }

  if (path === '/user/preferences' && method === 'PUT') {
    return success({ ...mockUser.preferences, ...body })
  }

  if (path === '/user/favorites' && method === 'GET') {
    return success({ list: mockWords.slice(0, 3).map((w) => ({ ...w, is_favorited: true })), total: 3 })
  }

  if (path === '/user/translation-favorites' && method === 'GET') {
    return success({ list: [], total: 0 })
  }

  if (path.match(/^\/user\/translations\/(\d+)\/favorite$/) && method === 'POST') {
    return success({ favorited: true })
  }

  // ---- submissions ----
  if (path === '/submissions' && method === 'GET') {
    return success({ list: [], total: 0 })
  }

  if (path === '/submissions' && method === 'POST') {
    return success({ id: Date.now(), status: 'pending' })
  }

  // ---- feedback / corrections ----
  if (path === '/feedback' && method === 'POST') {
    return success({ id: Date.now() })
  }

  if (path === '/corrections' && method === 'POST') {
    return success({ id: Date.now() })
  }

  // ---- admin ----
  if (path === '/admin/words' && method === 'GET') {
    return success({ list: mockWords, total: mockWords.length })
  }

  if (path === '/admin/stats' && method === 'GET') {
    return success({
      total_words: mockWords.length,
      total_users: 128,
      total_translations: 1024,
      pending_submissions: 3
    })
  }

  // ---- achievements ----
  if (path === '/achievements' && method === 'GET') {
    return success([])
  }

  if (path === '/achievements/mine' && method === 'GET') {
    return success([])
  }

  // 未匹配
  return null
}

// ============ 导出 ============

/**
 * 尝试用 mock 数据响应请求
 * @param {string} fullUrl 完整 URL（含 BASE_URL）
 * @param {string} method HTTP 方法
 * @param {object} data 请求体
 * @returns {Promise<object|null>} 匹配则返回响应体，不匹配返回 null
 */
export async function tryMock(fullUrl, method, data) {
  const path = parseUrl(fullUrl)
  const query = parseQuery(fullUrl)
  const matched = matchMock(path, method, data || {}, query)
  if (matched === null) return null
  await delay(200 + Math.random() * 300)
  return matched
}
