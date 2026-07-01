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

    <!-- 趋势图 -->
    <div class="page-card" style="margin-top: 16px">
      <h3 style="margin: 0 0 12px">近 7 天 AI 调用趋势</h3>
      <ECharts :option="trendOption" height="300px" />
    </div>

    <!-- 明细列表 -->
    <div class="page-card" style="margin-top: 16px">
      <div class="table-header">
        <h3 style="margin: 0">AI 调用明细</h3>
        <el-button :icon="Refresh" @click="loadLogs">刷新</el-button>
      </div>
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
import { ref, computed, onMounted } from 'vue'
import { Refresh, Search } from '@element-plus/icons-vue'
import ECharts from '@/components/ECharts.vue'
import { monitorApi } from '@/api/manage'
import { formatDateTime, formatNumber, formatPercent } from '@/utils/format'

const loading = ref(false)
const stats = ref<Record<string, any>>({})
const logs = ref<any[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

function fmtDate(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function defaultDateRange(): [string, string] {
  const end = new Date()
  const start = new Date()
  start.setTime(start.getTime() - 6 * 24 * 3600 * 1000)
  return [fmtDate(start), fmtDate(end)]
}

const dateRange = ref<[string, string] | null>(defaultDateRange())

const shortcuts = [
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

const rateColor = computed(() => {
  const r = stats.value.success_rate ?? 0
  if (r >= 0.95) return '#67c23a'
  if (r >= 0.8) return '#e6a23c'
  return '#f56c6c'
})

function formatCost(v: any): string {
  if (v === null || v === undefined || v === '') return '-'
  const n = Number(v)
  if (Number.isNaN(n)) return '-'
  return n.toFixed(6)
}

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
    const params: { start_date?: string; end_date?: string } = {}
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    stats.value = await monitorApi.getAiStats(params)
  } catch {}
}

async function loadLogs() {
  loading.value = true
  try {
    const data: any = await monitorApi.listAiLogs({ page: page.value, page_size: pageSize.value })
    logs.value = data.list || []
    total.value = data.total || 0
  } catch {
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
  loadLogs()
})
</script>

<style scoped lang="scss">
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
