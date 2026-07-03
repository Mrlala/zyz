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

/**
 * 解析上传的 Excel/CSV 文件为行数据数组。
 * 支持 .xlsx / .xls / .csv
 */
export function parseImportFile(file: File): Promise<Record<string, any>[]> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target!.result as ArrayBuffer)
        const wb = XLSX.read(data, { type: 'array' })
        const ws = wb.Sheets[wb.SheetNames[0]]
        const rows = XLSX.utils.sheet_to_json<Record<string, any>>(ws, { defval: '' })
        resolve(rows)
      } catch {
        reject(new Error('文件解析失败，请检查格式是否为 .xlsx / .csv'))
      }
    }
    reader.onerror = () => reject(new Error('文件读取失败'))
    reader.readAsArrayBuffer(file)
  })
}

/**
 * 下载词条导入模板（.xlsx）。
 */
export function downloadWordImportTemplate(): void {
  const headers = ['word', 'meaning', 'category_name', 'pinyin', 'risk_level', 'example']
  const sample = [
    { word: '摸鱼', meaning: '工作时间偷懒不做事', category_name: '职场话术', pinyin: 'mō yú', risk_level: 'low', example: '他又在摸鱼了' },
    { word: '种草', meaning: '看到后想买', category_name: '消费话术', pinyin: 'zhǒng cǎo', risk_level: 'low', example: '这个产品种草了' },
  ]
  const ws = XLSX.utils.json_to_sheet(sample, { header: headers })
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '词条导入模板')
  const buf = XLSX.write(wb, { type: 'array', bookType: 'xlsx' })
  saveAs(new Blob([buf], { type: 'application/octet-stream' }), '词条导入模板.xlsx')
}
