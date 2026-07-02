import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'

/**
 * 将数据导出为 Excel (.xlsx) 文件。
 *
 * @param data 行数据数组
 * @param filename 文件名（不含扩展名）
 * @param sheetName 工作表名，默认 Sheet1
 * @param headerMap 字段名→中文表头映射；提供时按映射顺序输出列，未映射字段保留原名
 */
export function exportToExcel(
  data: Record<string, any>[],
  filename: string,
  sheetName = 'Sheet1',
  headerMap?: Record<string, string>,
) {
  if (!data || data.length === 0) {
    return
  }

  let rows: Record<string, any>[]
  if (headerMap) {
    const keys = Object.keys(headerMap)
    rows = data.map((r) => {
      const obj: Record<string, any> = {}
      for (const k of keys) {
        const label = headerMap[k] || k
        obj[label] = r[k] ?? ''
      }
      return obj
    })
  } else {
    rows = data
  }

  const ws = XLSX.utils.json_to_sheet(rows)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, sheetName)
  const buf = XLSX.write(wb, { type: 'array', bookType: 'xlsx' })
  const today = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  saveAs(new Blob([buf], { type: 'application/octet-stream' }), `${filename}_${today}.xlsx`)
}
