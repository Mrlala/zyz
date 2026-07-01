<template>
  <div class="page-container">
    <!-- 统计卡片 -->
    <el-row :gutter="16">
      <el-col :span="6">
        <div class="stat-card">
          <span class="stat-label">总调用数</span>
          <span class="stat-value">{{ formatNumber(stats.total) }}</span>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <span class="stat-label">成功率</span>
          <span class="stat-value" :style="{ color: rateColor }">{{ formatPercent(stats.success_rate) }}</span>
          <span class="stat-suffix">（成功 {{ formatNumber(stats.success_count) }}）</span>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <span class="stat-label">错误数</span>
          <span class="stat-value" :style="{ color: stats.error_count ? '#f56c6c' : '#303133' }">
            {{ formatNumber(stats.error_count) }}
          </span>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <span class="stat-label">平均耗时</span>
          <span class="stat-value">{{ formatNumber(stats.avg_duration_ms) }}</span>
          <span class="stat-suffix">ms</span>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="14">
        <div class="page-card">
          <h3 style="margin: 0 0 12px">近 7 天调用趋势</h3>
          <ECharts :option="trendOption" height="320px" />
        </div>
      </el-col>
      <el-col :span="10">
        <div class="page-card">
          <h3 style="margin: 0 0 12px">按模块调用分布</h3>
          <ECharts :option="moduleOption" height="320px" />
        </div>
      </el-col>
    </el-row>

    <!-- 模块明细表 -->
    <div class="page-card" style="margin-top: 16px">
      <h3 style="margin: 0 0 12px">模块明细</h3>
      <el-table v-loading="loading" :data="stats.by_module || []" border stripe>
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="module" label="模块" min-width="120" />
        <el-table-column prop="count" label="调用次数" width="120" sortable />
        <el-table-column prop="avg_duration_ms" label="平均耗时(ms)" width="140" sortable>
          <template #default="{ row }">{{ formatNumber(row.avg_duration_ms) }}</template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && (!stats.by_module || stats.by_module.length === 0)" description="暂无数据" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import ECharts from '@/components/ECharts.vue'
import { monitorApi } from '@/api/manage'
import { formatNumber, formatPercent } from '@/utils/format'

const loading = ref(false)
const stats = ref<Record<string, any>>({})

const rateColor = computed(() => {
  const r = stats.value.success_rate ?? 0
  if (r >= 0.95) return '#67c23a'
  if (r >= 0.8) return '#e6a23c'
  return '#f56c6c'
})

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
        name: '调用次数',
        type: 'line',
        smooth: true,
        data: trend.map((t) => t.count),
        itemStyle: { color: '#409eff' },
        areaStyle: { color: 'rgba(64,158,255,0.15)' },
      },
    ],
  }
})

const moduleOption = computed(() => {
  const list: any[] = stats.value.by_module || []
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 80, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'value', axisLabel: { color: '#909399' } },
    yAxis: {
      type: 'category',
      data: list.map((m) => m.module).reverse(),
      axisLabel: { color: '#606266' },
    },
    series: [
      {
        name: '调用次数',
        type: 'bar',
        data: list.map((m) => m.count).reverse(),
        itemStyle: { color: '#67c23a', borderRadius: [0, 4, 4, 0] },
      },
    ],
  }
})

async function loadStats() {
  loading.value = true
  try {
    stats.value = await monitorApi.getApiStats()
  } catch {
  } finally {
    loading.value = false
  }
}

onMounted(loadStats)
</script>
