<template>
  <div class="page-container">
    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <!-- 操作日志 Tab -->
      <el-tab-pane label="操作日志" name="operation">
        <div class="page-card">
          <el-form inline style="margin-bottom: 12px">
            <el-form-item label="模块">
              <el-select v-model="opFilter.module" placeholder="全部" clearable style="width: 160px">
                <el-option v-for="m in moduleOptions" :key="m" :label="m" :value="m" />
              </el-select>
            </el-form-item>
            <el-form-item label="时间范围">
              <el-date-picker
                v-model="opDateRange"
                type="daterange"
                value-format="YYYY-MM-DD"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                style="width: 260px"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :icon="Search" @click="searchOp">查询</el-button>
              <el-button @click="resetOpFilter">重置</el-button>
              <el-button
                v-if="hasPermission('audit:log:export')"
                type="success"
                :icon="Download"
                :loading="exportLoading"
                @click="exportLogs"
              >
                导出 CSV
              </el-button>
            </el-form-item>
          </el-form>

          <el-table v-loading="opLoading" :data="opLogs" border stripe>
            <el-table-column prop="created_at" label="时间" width="170">
              <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
            </el-table-column>
            <el-table-column prop="username" label="操作者" width="120" show-overflow-tooltip />
            <el-table-column prop="module" label="模块" width="110" />
            <el-table-column prop="action" label="动作" width="100" />
            <el-table-column prop="method" label="方法" width="80" />
            <el-table-column prop="path" label="路径" min-width="200" show-overflow-tooltip />
            <el-table-column label="状态码" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status_code < 400 ? 'success' : 'danger'" size="small">
                  {{ row.status_code }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="duration_ms" label="耗时(ms)" width="100" align="right">
              <template #default="{ row }">{{ formatNumber(row.duration_ms) }}</template>
            </el-table-column>
            <el-table-column prop="ip" label="IP" width="130" />
            <el-table-column label="操作" width="80" align="center" fixed="right">
              <template #default="{ row }">
                <el-button size="small" text type="primary" @click="showDetail(row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-if="opTotal > 0"
            v-model:current-page="opPage"
            v-model:page-size="opPageSize"
            :total="opTotal"
            :page-sizes="[20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            style="margin-top: 16px; justify-content: flex-end"
            @size-change="loadOpLogs"
            @current-change="loadOpLogs"
          />
          <el-empty v-if="!opLoading && opLogs.length === 0" description="暂无操作日志" />
        </div>
      </el-tab-pane>

      <!-- 登录日志 Tab -->
      <el-tab-pane label="登录日志" name="login">
        <div class="page-card">
          <el-form inline style="margin-bottom: 12px">
            <el-form-item label="时间范围">
              <el-date-picker
                v-model="loginDateRange"
                type="daterange"
                value-format="YYYY-MM-DD"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                style="width: 260px"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :icon="Search" @click="searchLogin">查询</el-button>
              <el-button @click="resetLoginFilter">重置</el-button>
            </el-form-item>
          </el-form>

          <el-table v-loading="loginLoading" :data="loginLogs" border stripe>
            <el-table-column prop="created_at" label="时间" width="170">
              <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
            </el-table-column>
            <el-table-column prop="username" label="用户名" width="130" />
            <el-table-column prop="ip" label="IP" width="140" />
            <el-table-column label="UA" min-width="240" show-overflow-tooltip>
              <template #default="{ row }">
                <span style="color: #909399">{{ truncate(row.user_agent, 60) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="状态码" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status_code < 400 ? 'success' : 'danger'" size="small">
                  {{ row.status_code }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="error_msg" label="错误信息" min-width="180" show-overflow-tooltip>
              <template #default="{ row }">
                <span v-if="row.error_msg" style="color: #f56c6c">{{ row.error_msg }}</span>
                <span v-else style="color: #c0c4cc">-</span>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-if="loginTotal > 0"
            v-model:current-page="loginPage"
            v-model:page-size="loginPageSize"
            :total="loginTotal"
            :page-sizes="[20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            style="margin-top: 16px; justify-content: flex-end"
            @size-change="loadLoginLogs"
            @current-change="loadLoginLogs"
          />
          <el-empty v-if="!loginLoading && loginLogs.length === 0" description="暂无登录日志" />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 操作日志详情弹窗 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="`操作日志详情 #${currentLog?.id ?? ''}`"
      width="700px"
      destroy-on-close
    >
      <template v-if="currentLog">
        <h4 class="detail-section-title">基本信息</h4>
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="时间">{{ formatDateTime(currentLog.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="操作者">{{ currentLog.username || '-' }}</el-descriptions-item>
          <el-descriptions-item label="模块">{{ currentLog.module || '-' }}</el-descriptions-item>
          <el-descriptions-item label="动作">{{ currentLog.action || '-' }}</el-descriptions-item>
          <el-descriptions-item label="方法">{{ currentLog.method || '-' }}</el-descriptions-item>
          <el-descriptions-item label="路径">{{ currentLog.path || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态码">
            <el-tag :type="currentLog.status_code < 400 ? 'success' : 'danger'" size="small">
              {{ currentLog.status_code }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="耗时(ms)">{{ formatNumber(currentLog.duration_ms) }}</el-descriptions-item>
          <el-descriptions-item label="IP">{{ currentLog.ip || '-' }}</el-descriptions-item>
          <el-descriptions-item label="UA" :span="2">{{ currentLog.user_agent || '-' }}</el-descriptions-item>
        </el-descriptions>

        <h4 class="detail-section-title" style="margin-top: 16px">请求参数</h4>
        <JsonViewer
          :value="paramsObj"
          :expand-depth="3"
          copyable
          boxed
          sort
        />
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Download } from '@element-plus/icons-vue'
import { auditLogApi } from '@/api/manage'
import { formatDateTime, formatNumber } from '@/utils/format'
import { hasPermission } from '@/utils/permission'

const activeTab = ref<'operation' | 'login'>('operation')

// 操作日志
const opLoading = ref(false)
const opLogs = ref<any[]>([])
const opPage = ref(1)
const opPageSize = ref(20)
const opTotal = ref(0)
const opFilter = ref<{ module?: string }>({})
const opDateRange = ref<[string, string] | null>(null)

// 登录日志
const loginLoading = ref(false)
const loginLogs = ref<any[]>([])
const loginPage = ref(1)
const loginPageSize = ref(20)
const loginTotal = ref(0)
const loginDateRange = ref<[string, string] | null>(null)

// 导出
const exportLoading = ref(false)

// 详情弹窗
const detailDialogVisible = ref(false)
const currentLog = ref<any>(null)
const paramsObj = computed(() => {
  if (!currentLog.value || !currentLog.value.params) return {}
  try {
    return JSON.parse(currentLog.value.params)
  } catch {
    return { _parseError: '参数解析失败', raw: currentLog.value.params }
  }
})

function showDetail(row: any) {
  currentLog.value = row
  detailDialogVisible.value = true
}

const moduleOptions = ['auth', 'account', 'role', 'word', 'category', 'content', 'ai_config', 'monitor', 'audit']

function truncate(s: string | null | undefined, max: number): string {
  if (!s) return '-'
  return s.length > max ? s.slice(0, max) + '…' : s
}

function getOpParams() {
  return {
    page: opPage.value,
    page_size: opPageSize.value,
    module: opFilter.value.module || undefined,
    start_date: opDateRange.value?.[0] || undefined,
    end_date: opDateRange.value?.[1] || undefined,
  }
}

function getLoginParams() {
  return {
    page: loginPage.value,
    page_size: loginPageSize.value,
    start_date: loginDateRange.value?.[0] || undefined,
    end_date: loginDateRange.value?.[1] || undefined,
  }
}

async function loadOpLogs() {
  opLoading.value = true
  try {
    const data: any = await auditLogApi.listOperation(getOpParams())
    opLogs.value = data.list || []
    opTotal.value = data.total || 0
  } catch {
  } finally {
    opLoading.value = false
  }
}

async function loadLoginLogs() {
  loginLoading.value = true
  try {
    const data: any = await auditLogApi.listLogin(getLoginParams())
    loginLogs.value = data.list || []
    loginTotal.value = data.total || 0
  } catch {
  } finally {
    loginLoading.value = false
  }
}

function searchOp() {
  opPage.value = 1
  loadOpLogs()
}

function resetOpFilter() {
  opFilter.value = {}
  opDateRange.value = null
  opPage.value = 1
  loadOpLogs()
}

function searchLogin() {
  loginPage.value = 1
  loadLoginLogs()
}

function resetLoginFilter() {
  loginDateRange.value = null
  loginPage.value = 1
  loadLoginLogs()
}

function onTabChange(name: string | number) {
  if (name === 'login' && loginLogs.value.length === 0) {
    loadLoginLogs()
  }
}

// 导出 CSV：后端返回 JSON list，前端转 CSV 并下载
async function exportLogs() {
  exportLoading.value = true
  try {
    const list: any = await auditLogApi.export({
      module: opFilter.value.module || undefined,
      start_date: opDateRange.value?.[0] || undefined,
      end_date: opDateRange.value?.[1] || undefined,
    })
    if (!Array.isArray(list) || list.length === 0) {
      ElMessage.info('当前筛选条件下无操作日志可导出')
      return
    }
    downloadCsv(list)
    ElMessage.success(`已导出 ${list.length} 条操作日志`)
  } catch {
  } finally {
    exportLoading.value = false
  }
}

function downloadCsv(list: any[]) {
  const headers = [
    'id',
    'created_at',
    'username',
    'module',
    'action',
    'method',
    'path',
    'params',
    'ip',
    'user_agent',
    'status_code',
    'duration_ms',
    'error_msg',
  ]
  const headerLabels = [
    'ID',
    '时间',
    '操作者',
    '模块',
    '动作',
    '方法',
    '路径',
    '参数',
    'IP',
    'UA',
    '状态码',
    '耗时(ms)',
    '错误信息',
  ]
  const escape = (v: any) => {
    if (v === null || v === undefined) return ''
    const s = String(v).replace(/"/g, '""')
    return `"${s}"`
  }
  // UTF-8 BOM 防止 Excel 中文乱码
  const bom = '\uFEFF'
  const lines = [headerLabels.map(escape).join(',')]
  for (const item of list) {
    lines.push(headers.map((h) => escape(item[h])).join(','))
  }
  const csv = bom + lines.join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const today = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  const a = document.createElement('a')
  a.href = url
  a.download = `operation_logs_${today}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

onMounted(loadOpLogs)
</script>

<style scoped lang="scss">
.detail-section-title {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
</style>
