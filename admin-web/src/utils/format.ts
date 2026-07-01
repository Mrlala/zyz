/** 时间/数字格式化工具 */

/** ISO 时间字符串转 YYYY-MM-DD HH:mm:ss */
export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '-'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

/** ISO 时间字符串转 YYYY-MM-DD */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '-'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

/** 数字千分位 */
export function formatNumber(n: number | undefined | null): string {
  if (n === undefined || n === null) return '-'
  return n.toLocaleString('zh-CN')
}

/** 百分比（0-1 → x%） */
export function formatPercent(rate: number | undefined | null, digits = 2): string {
  if (rate === undefined || rate === null) return '-'
  return `${(rate * 100).toFixed(digits)}%`
}
