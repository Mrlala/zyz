<template>
  <div class="page-container">
    <!-- 工具栏 -->
    <div class="page-card" style="margin-bottom: 16px">
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        value-format="YYYY-MM-DD"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        :shortcuts="shortcuts"
        :clearable="false"
        @change="loadStats"
      />
      <el-button type="primary" :icon="Search" style="margin-left: 12px" @click="loadStats">查询</el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16">
      <el-col :xs="12" :sm="8" :md="6" :lg="5" :xl="5">
        <div class="stat-card">
          <span class="stat-label">总调用数</span>
          <span class="stat-value">{{ formatNumber(stats.total) }}</span>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6" :lg="5" :xl="5">
        <div class="stat-card">
          <span class="stat-label">成功率</span>
          <span class="stat-value" :style="{ color: rateColor }">{{ formatPercent(stats.success_rate) }}</span>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6" :lg="5" :xl="5">
        <div class="stat-card">
          <span class="stat-label">降级数</span>
          <span class="stat-value" :style="{ color: stats.fallback_count ? '#e6a23c' : '#303133' }">
            {{ formatNumber(stats.fallback_count) }}
          </span>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6" :lg="5" :xl="5">
        <div class="stat-card">
          <span class="stat-label">总 Token</span>
          <span class="stat-value">{{ formatNumber(stats.total_tokens) }}</span>
        </div>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6" :lg="4" :xl="4">
        <div class="stat-card">
          <span class="stat-label">总成本(元)</span>
          <span class="stat-value">{{ formatCost(stats.total_cost) }}</span>
        </div>
      </el-col>
    </el-row>

    <!-- 消耗对账卡片 -->
    <div class="page-card" style="margin-top: 16px">
      <div class="table-header">
        <h3 style="margin: 0">消耗对账</h3>
        <el-button link type="primary" size="small" @click="loadReconcile">刷新</el-button>
      </div>
      <el-row :gutter="16" style="margin-top: 12px" v-loading="reconcileLoading">
        <el-col :xs="24" :sm="8">
          <div class="reconcile-item">
            <span class="reconcile-label">本地估算消耗</span>
            <span class="reconcile-value">¥{{ formatCost(reconcile.estimated_cost) }}</span>
            <span class="reconcile-hint">累计自 ai_call_logs</span>
          </div>
        </el-col>
        <el-col :xs="24" :sm="8">
          <div class="reconcile-item">
            <span class="reconcile-label">DeepSeek 账户余额</span>
            <span class="reconcile-value" :class="{ 'balance-warn': reconcileWarn }">
              ¥{{ reconcile.balance_total || '--' }}
            </span>
            <span class="reconcile-hint">{{ reconcile.balance_available ? '可用' : '不可用' }}</span>
          </div>
        </el-col>
        <el-col :xs="24" :sm="8">
          <div class="reconcile-item">
            <span class="reconcile-label">偏差分析</span>
            <span class="reconcile-value" :class="reconcileDeviation >= 0 ? 'deviation-up' : 'deviation-down'">
              {{ reconcileDeviation >= 0 ? '+' : '' }}¥{{ formatCost(Math.abs(reconcileDeviation).toString()) }}
            </span>
            <span class="reconcile-hint">
              {{ reconcileDeviation >= 0 ? '估算偏高（缓存命中未计）' : '估算偏低（可能含其他扣费）' }}
            </span>
          </div>
        </el-col>
      </el-row>
      <el-alert
        v-if="reconcileWarn"
        type="warning"
        :closable="false"
        show-icon
        style="margin-top: 12px"
        title="账户余额低于 10 元，请及时充值"
      />
    </div>

    <!-- 趋势图 -->
    <div class="page-card" style="margin-top: 16px">
      <h3 style="margin: 0 0 12px">近 7 天 AI 调用趋势</h3>
      <ECharts :option="trendOption" height="300px" />
    </div>

    <!-- 明细列表 -->
    <div class="page-card" style="margin-top: 16px">
      <div class="table-header">
        <h3 style="margin: 0">AI 调用明细</h3>
        <div>
          <el-button :icon="Download" :loading="exportLoading" @click="exportAiLogs">导出明细</el-button>
          <el-button :icon="Refresh" @click="loadLogs">刷新</el-button>
        </div>
      </div>
      <el-form inline style="margin-top: 12px" @submit.prevent>
        <el-form-item label="时间">
          <el-date-picker
            v-model="logDateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
            start-placeholder="开始"
            end-placeholder="结束"
            :shortcuts="shortcuts"
            clearable
            style="width: 260px"
          />
        </el-form-item>
        <el-form-item label="接口">
          <el-input v-model="logFilter.endpoint" placeholder="接口路径" clearable style="width: 180px" @keyup.enter="searchLogs" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="logFilter.success" placeholder="全部" clearable style="width: 110px" @change="searchLogs">
            <el-option label="成功" :value="true" />
            <el-option label="失败" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="降级">
          <el-select v-model="logFilter.fallback_used" placeholder="全部" clearable style="width: 110px" @change="searchLogs">
            <el-option label="降级" :value="true" />
            <el-option label="未降级" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="错误">
          <el-input v-model="logFilter.keyword" placeholder="错误关键词" clearable style="width: 160px" @keyup.enter="searchLogs" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="searchLogs">查询</el-button>
          <el-button @click="resetLogFilter">重置</el-button>
        </el-form-item>
      </el-form>
      <el-table v-loading="loading" :data="logs" border stripe style="margin-top: 12px">
        <el-table-column prop="created_at" label="时间" width="170">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="endpoint" label="接口" min-width="140" show-overflow-tooltip />
        <el-table-column prop="mode" label="模式" width="100" />
        <el-table-column prop="prompt_tokens" label="输入Token" width="100" align="right" />
        <el-table-column prop="completion_tokens" label="输出Token" width="100" align="right" />
        <el-table-column prop="total_tokens" label="总Token" width="100" align="right" />
        <el-table-column prop="duration_ms" label="耗时(ms)" width="100" align="right">
          <template #default="{ row }">{{ formatNumber(row.duration_ms) }}</template>
        </el-table-column>
        <el-table-column label="成功" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.success ? 'success' : 'danger'" size="small">
              {{ row.success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="降级" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.fallback_used" type="warning" size="small">降级</el-tag>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="cost_estimate" label="成本(元)" width="100" align="right">
          <template #default="{ row }">{{ formatCost(row.cost_estimate) }}</template>
        </el-table-column>
        <el-table-column prop="error_msg" label="错误信息" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.error_msg" style="color: #f56c6c">{{ row.error_msg }}</span>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > 0"
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        style="margin-top: 16px; justify-content: flex-end"
        @size-change="loadLogs"
        @current-change="loadLogs"
      />
      <el-empty v-if="!loading && logs.length === 0" description="暂无 AI 调用记录" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Search, Download } from '@element-plus/icons-vue'
import ECharts from '@/components/ECharts.vue'
import { monitorApi, aiConfigApi } from '@/api/manage'
import { formatDateTime, formatNumber, formatPercent } from '@/utils/format'
import { exportToExcel } from '@/utils/excel'
import { useDateRange } from '@/composables/useDateRange'
import { useStatusMaps } from '@/composables/useStatusMaps'

const { dateRange, shortcuts, toParams } = useDateRange()
const { rateColor: rateColorFn, formatCost } = useStatusMaps()

const loading = ref(false)
const exportLoading = ref(false)
const stats = ref<Record<string, any>>({})
const logs = ref<any[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 消耗对账
const reconcileLoading = ref(false)
const reconcile = reactive({
  estimated_cost: '0',
  balance_total: '',
  balance_available: false,
})
const reconcileWarn = computed(() => {
  if (!reconcile.balance_total) return false
  return parseFloat(reconcile.balance_total) < 10
})
const reconcileDeviation = computed(() => {
  const est = parseFloat(reconcile.estimated_cost || '0')
  const bal = parseFloat(reconcile.balance_total || '0')
  if (!bal) return 0
  // 偏差 = 估算消耗 - 余额减少量（简化：估算 - 当前余额，仅当有过充值时为参考）
  return est - bal
})

// 明细筛选：与统计卡片的 dateRange 独立，默认不限制日期
const logDateRange = ref<[string, string] | null>(null)
const logFilter = reactive({
  endpoint: '',
  success: undefined as boolean | undefined,
  fallback_used: undefined as boolean | undefined,
  keyword: '',
})

const rateColor = computed(() => rateColorFn(stats.value.success_rate))

const trendOption = computed(() => {
  const trend: any[] = stats.value.daily_trend || []
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: {
      type: 'category',
      data: trend.map((t) => t.date),
      axisLabel: { color: '#909399' },
    },
    yAxis: { type: 'value', axisLabel: { color: '#909399' } },
    series: [
      {
        name: 'AI 调用次数',
        type: 'line',
        smooth: true,
        data: trend.map((t) => t.count),
        itemStyle: { color: '#9c27b0' },
        areaStyle: { color: 'rgba(156,39,176,0.15)' },
      },
    ],
  }
})

async function loadStats() {
  try {
    stats.value = await monitorApi.getAiStats(toParams())
  } catch {}
}

async function loadReconcile() {
  reconcileLoading.value = true
  try {
    // 本地估算消耗来自 ai-stats 的 total_cost（全量）
    const statsData: any = await monitorApi.getAiStats({})
    reconcile.estimated_cost = String(statsData.total_cost || '0')
    // 余额来自 DeepSeek 官方接口
    const balanceData: any = await aiConfigApi.getBalance()
    reconcile.balance_available = !!balanceData.is_available
    const infos = balanceData.balance_infos || []
    const cny = infos.find((b: any) => b.currency === 'CNY') || infos[0]
    reconcile.balance_total = cny?.total_balance || ''
  } catch {
    reconcile.balance_total = ''
  } finally {
    reconcileLoading.value = false
  }
}

function getLogParams() {
  return {
    page: page.value,
    page_size: pageSize.value,
    start_date: logDateRange.value?.[0] || undefined,
    end_date: logDateRange.value?.[1] || undefined,
    endpoint: logFilter.endpoint || undefined,
    success: logFilter.success,
    fallback_used: logFilter.fallback_used,
    keyword: logFilter.keyword || undefined,
  }
}

async function loadLogs() {
  loading.value = true
  try {
    const data: any = await monitorApi.listAiLogs(getLogParams())
    logs.value = data.list || []
    total.value = data.total || 0
  } catch {
  } finally {
    loading.value = false
  }
}

function searchLogs() {
  page.value = 1
  loadLogs()
}

function resetLogFilter() {
  logDateRange.value = null
  Object.assign(logFilter, { endpoint: '', success: undefined, fallback_used: undefined, keyword: '' })
  page.value = 1
  loadLogs()
}

async function exportAiLogs() {
  exportLoading.value = true
  try {
    // 分页拉取当前筛选条件下的全部明细
    const allRows: any[] = []
    let exportPage = 1
    const exportPageSize = 100
    while (true) {
      const data: any = await monitorApi.listAiLogs({
        ...getLogParams(),
        page: exportPage,
        page_size: exportPageSize,
      })
      const rows = data.list || []
      allRows.push(...rows)
      if (allRows.length >= (data.total || 0) || rows.length < exportPageSize) break
      exportPage++
    }
    if (allRows.length === 0) {
      ElMessage.info('当前筛选条件下无 AI 调用记录可导出')
      return
    }
    const exportRows = allRows.map((r) => ({
      '时间': formatDateTime(r.created_at),
      '接口': r.endpoint || '',
      '模式': r.mode || '',
      '输入Token': r.prompt_tokens || 0,
      '输出Token': r.completion_tokens || 0,
      '总Token': r.total_tokens || 0,
      '耗时(ms)': r.duration_ms || 0,
      '成功': r.success ? '成功' : '失败',
      '降级': r.fallback_used ? '降级' : '-',
      '成本(元)': r.cost_estimate || 0,
      '错误信息': r.error_msg || '',
    }))
    exportToExcel(exportRows, 'ai_logs', 'AI调用明细')
    ElMessage.success(`已导出 ${allRows.length} 条 AI 调用记录`)
  } catch {
  } finally {
    exportLoading.value = false
  }
}

onMounted(() => {
  loadStats()
  loadLogs()
  loadReconcile()
})
</script>

<style scoped lang="scss">
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.reconcile-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  border-radius: 8px;
  background: var(--el-fill-color-light);
}
.reconcile-label {
  font-size: 13px;
  color: #909399;
}
.reconcile-value {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
}
.reconcile-hint {
  font-size: 12px;
  color: #c0c4cc;
}
.balance-warn {
  color: #f56c6c;
}
.deviation-up {
  color: #e6a23c;
}
.deviation-down {
  color: #67c23a;
}
</style>
