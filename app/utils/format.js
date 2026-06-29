/**
 * 格式化工具
 * 时间格式化、文本截断、数字格式化等
 */

/**
 * 格式化时间为相对时间（如：刚刚、3 分钟前、2 小时前、昨天、YYYY-MM-DD）
 * @param {string|number|Date} input 时间
 * @returns {string}
 */
export function formatRelativeTime(input) {
  if (!input) return ''
  const date = new Date(input)
  if (Number.isNaN(date.getTime())) return ''

  const now = new Date()
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000)

  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`
  if (diff < 86400 * 2) return '昨天'
  if (diff < 86400 * 30) return `${Math.floor(diff / 86400)} 天前`

  return formatDate(date)
}

/**
 * 格式化日期 YYYY-MM-DD
 * @param {string|number|Date} input
 * @returns {string}
 */
export function formatDate(input) {
  const d = new Date(input)
  if (Number.isNaN(d.getTime())) return ''
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

/**
 * 格式化日期时间 YYYY-MM-DD HH:mm
 * @param {string|number|Date} input
 * @returns {string}
 */
export function formatDateTime(input) {
  const d = new Date(input)
  if (Number.isNaN(d.getTime())) return ''
  const date = formatDate(d)
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${date} ${h}:${min}`
}

/**
 * 截断文本，超出长度加省略号
 * @param {string} text 原文本
 * @param {number} maxLen 最大长度
 * @returns {string}
 */
export function truncate(text, maxLen = 50) {
  if (!text) return ''
  if (text.length <= maxLen) return text
  return text.slice(0, maxLen) + '...'
}

/**
 * 数字千分位格式化（如 12345 → 12,345）
 * @param {number} num
 * @returns {string}
 */
export function formatNumber(num) {
  if (num === null || num === undefined) return '0'
  return String(num).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

/**
 * 数字缩写格式化（如 12345 → 1.2w，1000 → 1k）
 * @param {number} num
 * @returns {string}
 */
export function formatCompact(num) {
  if (num === null || num === undefined) return '0'
  if (num < 1000) return String(num)
  if (num < 10000) return `${(num / 1000).toFixed(1)}k`
  return `${(num / 10000).toFixed(1)}w`
}

/**
 * 风险等级文本映射
 * @param {string} level low / medium / high
 * @returns {{text: string, color: string}}
 */
export function formatRiskLevel(level) {
  const map = {
    low: { text: '低风险', color: '#10B981' },
    medium: { text: '中风险', color: '#F59E0B' },
    high: { text: '高风险', color: '#EF4444' }
  }
  return map[level] || map.low
}

export default {
  formatRelativeTime,
  formatDate,
  formatDateTime,
  truncate,
  formatNumber,
  formatCompact,
  formatRiskLevel
}
