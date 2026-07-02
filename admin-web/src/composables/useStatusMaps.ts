/** 词条状态映射 */
const STATUS_LABELS: Record<string, string> = {
  pending: '待审核',
  approved: '已通过',
  rejected: '已拒绝',
  published: '已发布',
}

const STATUS_TAG_TYPES: Record<string, string> = {
  pending: 'warning',
  approved: 'success',
  rejected: 'danger',
  published: 'primary',
}

/** 风险等级映射 */
const RISK_LABELS: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
}

const RISK_TAG_TYPES: Record<string, string> = {
  low: 'success',
  medium: 'warning',
  high: 'danger',
}

/** 角色代码映射 */
function roleTagType(code: string): string {
  if (code === 'sys_admin') return 'danger'
  if (code === 'sec_admin') return 'warning'
  return 'info'
}

/** 分类层级映射 */
function levelTagType(level: number): string {
  return ({ 1: 'primary', 2: 'success', 3: 'warning' } as Record<number, string>)[level] || 'info'
}

/** 权限模块中文映射 */
const MODULE_LABELS: Record<string, string> = {
  system: '系统管理',
  content: '内容管理',
  ai: 'AI 配置',
  monitor: '监控统计',
  audit: '审计日志',
}

function moduleLabel(code: string): string {
  return MODULE_LABELS[code] || code
}

/** 根据成功率返回颜色（>=95% 绿，>=80% 橙，否则红） */
function rateColor(rate: number | undefined | null): string {
  const r = rate ?? 0
  if (r >= 0.95) return '#67c23a'
  if (r >= 0.8) return '#e6a23c'
  return '#f56c6c'
}

/** 成本格式化（6 位小数） */
function formatCost(v: any): string {
  if (v === null || v === undefined || v === '') return '-'
  const n = Number(v)
  if (Number.isNaN(n)) return '-'
  return n.toFixed(6)
}

/**
 * 状态映射 composable
 * 提供词条状态、风险等级、角色、层级、模块的标签和 Tag 类型映射
 */
export function useStatusMaps() {
  function statusLabel(s?: string): string {
    return STATUS_LABELS[s || ''] || s || ''
  }
  function statusTagType(s?: string): string {
    return STATUS_TAG_TYPES[s || ''] || 'info'
  }
  function riskLabel(s?: string): string {
    return RISK_LABELS[s || ''] || s || ''
  }
  function riskTagType(s?: string): string {
    return RISK_TAG_TYPES[s || ''] || 'info'
  }

  return {
    statusLabel,
    statusTagType,
    riskLabel,
    riskTagType,
    roleTagType,
    levelTagType,
    moduleLabel,
    rateColor,
    formatCost,
  }
}
