import { ref } from 'vue'

/** 日期格式化为 YYYY-MM-DD */
export function fmtDate(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

/** 生成默认日期范围（近 N 天，[start, end]） */
export function defaultDateRange(days = 7): [string, string] {
  const end = new Date()
  const start = new Date()
  start.setTime(start.getTime() - (days - 1) * 24 * 3600 * 1000)
  return [fmtDate(start), fmtDate(end)]
}

/** el-date-picker 快捷选项 */
export const dateShortcuts = [
  {
    text: '近7天',
    value: () => {
      const e = new Date()
      const s = new Date()
      s.setTime(s.getTime() - 6 * 24 * 3600 * 1000)
      return [s, e]
    },
  },
  {
    text: '近30天',
    value: () => {
      const e = new Date()
      const s = new Date()
      s.setTime(s.getTime() - 29 * 24 * 3600 * 1000)
      return [s, e]
    },
  },
  {
    text: '本月',
    value: () => {
      const e = new Date()
      const s = new Date()
      s.setDate(1)
      return [s, e]
    },
  },
]

/**
 * 日期范围 composable
 * @param defaultDays 默认天数（默认 7）
 */
export function useDateRange(defaultDays = 7) {
  const dateRange = ref<[string, string] | null>(defaultDateRange(defaultDays))

  /** 将当前 dateRange 转为 { start_date, end_date } 参数对象 */
  function toParams(): { start_date?: string; end_date?: string } {
    if (dateRange.value && dateRange.value.length === 2) {
      return { start_date: dateRange.value[0], end_date: dateRange.value[1] }
    }
    return {}
  }

  return { dateRange, shortcuts: dateShortcuts, toParams, fmtDate }
}
