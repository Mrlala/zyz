<template>
  <div class="page-container">
    <!-- 工具栏：自动刷新 -->
    <div class="refresh-toolbar">
      <div class="refresh-left">
        <span class="refresh-label">自动刷新</span>
        <el-switch v-model="autoRefresh" @change="onAutoRefreshChange" />
        <el-select
          v-model="refreshInterval"
          style="width: 110px; margin-left: 8px"
          :disabled="!autoRefresh"
          @change="onIntervalChange"
        >
          <el-option label="30秒" :value="30" />
          <el-option label="60秒" :value="60" />
          <el-option label="5分钟" :value="300" />
        </el-select>
      </div>
      <el-button type="primary" :icon="Refresh" plain @click="loadOverview">手动刷新</el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16">
      <el-col :span="6">
        <div class="stat-card">
          <span class="stat-label">词条总数</span>
          <span class="stat-value">{{ overview.word_count ?? '-' }}</span>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <span class="stat-label">用户总数</span>
          <span class="stat-value">{{ overview.user_count ?? '-' }}</span>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <span class="stat-label">今日翻译</span>
          <span class="stat-value">{{ overview.translation_count_today ?? '-' }}</span>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <span class="stat-label">待审核</span>
          <span class="stat-value">{{ pendingTotal }}</span>
          <span class="stat-suffix">（提交 {{ overview.submission_pending ?? 0 }} + 纠错 {{ overview.correction_pending ?? 0 }}）</span>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="14">
        <div class="page-card">
          <h3 style="margin: 0 0 12px">近 7 天翻译趋势</h3>
          <ECharts :option="trendOption" height="320px" />
        </div>
      </el-col>
      <el-col :span="10">
        <div class="page-card">
          <h3 style="margin: 0 0 12px">热词 Top10</h3>
          <ECharts :option="hotOption" height="320px" />
        </div>
      </el-col>
    </el-row>

    <!-- 次要统计 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="8">
        <div class="page-card mini-stat">
          <span class="mini-label">管理员数</span>
          <span class="mini-value">{{ overview.admin_count ?? '-' }}</span>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="page-card mini-stat">
          <span class="mini-label">待审核提交</span>
          <span class="mini-value">{{ overview.submission_pending ?? '-' }}</span>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="page-card mini-stat">
          <span class="mini-label">待审核纠错</span>
          <span class="mini-value">{{ overview.correction_pending ?? '-' }}</span>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import ECharts from '@/components/ECharts.vue'
import { dashboardApi } from '@/api/manage'

const overview = ref<Record<string, any>>({})

// 自动刷新
const autoRefresh = ref(false)
const refreshInterval = ref(60)
let refreshTimer: ReturnType<typeof setInterval> | null = null

function clearRefreshTimer() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

function startRefreshTimer() {
  clearRefreshTimer()
  refreshTimer = setInterval(() => {
    loadOverview()
  }, refreshInterval.value * 1000)
}

function onAutoRefreshChange(val: boolean | string | number) {
  if (val) {
    startRefreshTimer()
  } else {
    clearRefreshTimer()
  }
}

function onIntervalChange() {
  if (autoRefresh.value) {
    startRefreshTimer()
  }
}

const pendingTotal = computed(() => (overview.value.submission_pending ?? 0) + (overview.value.correction_pending ?? 0))

const trendOption = computed(() => {
  const trend: any[] = overview.value.translation_trend || []
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
        name: '翻译次数',
        type: 'line',
        smooth: true,
        data: trend.map((t) => t.count),
        itemStyle: { color: '#409eff' },
        areaStyle: { color: 'rgba(64,158,255,0.15)' },
      },
    ],
  }
})

const hotOption = computed(() => {
  const hot: any[] = (overview.value.hot_top10 || []).slice().reverse()
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 80, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'value', axisLabel: { color: '#909399' } },
    yAxis: {
      type: 'category',
      data: hot.map((h) => h.word),
      axisLabel: { color: '#606266' },
    },
    series: [
      {
        name: '浏览量',
        type: 'bar',
        data: hot.map((h) => h.heat),
        itemStyle: { color: '#67c23a', borderRadius: [0, 4, 4, 0] },
      },
    ],
  }
})

async function loadOverview() {
  try {
    overview.value = await dashboardApi.getOverview()
  } catch {}
}

onMounted(() => {
  loadOverview()
})

onUnmounted(() => {
  clearRefreshTimer()
})
</script>

<style scoped lang="scss">
.refresh-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #fff;
  border-radius: 6px;
  margin-bottom: 16px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}
.refresh-left {
  display: flex;
  align-items: center;
}
.refresh-label {
  font-size: 14px;
  color: #606266;
  margin-right: 8px;
}
.mini-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
}
.mini-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}
.mini-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}
.stat-suffix {
  font-size: 12px;
  color: #c0c4cc;
  margin-left: 4px;
}
</style>
