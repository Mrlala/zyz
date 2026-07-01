<template>
  <view class="ranking-page">
    <!-- 顶部栏 -->
    <view class="top-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="top-bar__inner">
        <view class="top-bar__btn" @click="handleBack">
          <ArrowLeft :size="20" color="#6B7280" />
        </view>
        <text class="top-bar__title">热词排行</text>
        <view class="top-bar__btn" @click="handleFilter">
          <SlidersHorizontal :size="18" color="#6B7280" />
        </view>
      </view>
    </view>
    <view class="top-bar-placeholder" :style="{ height: (statusBarHeight + 54) + 'px' }"></view>

    <!-- 时段标签 -->
    <view class="period-tabs">
      <view
        v-for="tab in periods"
        :key="tab.value"
        class="period-tabs__tab"
        :class="{ 'period-tabs__tab--active': period === tab.value }"
        @click="switchPeriod(tab.value)"
      >{{ tab.label }}</view>
    </view>

    <!-- 加载中 -->
    <view v-if="loading" class="state-tip">
      <text>加载中...</text>
    </view>

    <template v-else>
      <!-- 空状态 -->
      <view v-if="!list.length" class="state-tip state-tip--empty">
        <text>暂无排行数据</text>
      </view>

      <template v-else>
        <!-- TOP3 领奖台 -->
        <view v-if="top3.length" class="podium">
          <!-- 2nd -->
          <view v-if="top3[1]" class="podium__item podium__item--2nd" @click="handleItemClick(top3[1])">
            <view class="podium__circle podium__circle--2nd">
              <text class="podium__circle-text">2</text>
            </view>
            <text class="podium__word podium__word--2nd">{{ top3[1].word || top3[1].name }}</text>
            <text class="podium__count">{{ formatCount(top3[1]) }}</text>
          </view>

          <!-- 1st -->
          <view v-if="top3[0]" class="podium__item podium__item--1st" @click="handleItemClick(top3[0])">
            <view class="podium__circle podium__circle--1st">
              <text class="podium__circle-text">1</text>
            </view>
            <text class="podium__word podium__word--1st">{{ top3[0].word || top3[0].name }}</text>
            <text class="podium__count">{{ formatCount(top3[0]) }}</text>
          </view>

          <!-- 3rd -->
          <view v-if="top3[2]" class="podium__item podium__item--3rd" @click="handleItemClick(top3[2])">
            <view class="podium__circle podium__circle--3rd">
              <text class="podium__circle-text">3</text>
            </view>
            <text class="podium__word podium__word--3rd">{{ top3[2].word || top3[2].name }}</text>
            <text class="podium__count">{{ formatCount(top3[2]) }}</text>
          </view>
        </view>

        <!-- #4+ 列表 -->
        <view v-if="rest.length" class="rest-list">
          <view
            v-for="(item, idx) in rest"
            :key="item.id || idx"
            class="rest-list__row"
            :class="{ 'rest-list__row--border': idx < rest.length - 1 }"
            @click="handleItemClick(item)"
          >
            <text class="rest-list__rank">{{ idx + 4 }}</text>
            <text class="rest-list__word">{{ item.word || item.name }}</text>
            <text class="rest-list__count">{{ formatCount(item) }}</text>
          </view>
        </view>
      </template>
    </template>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { ArrowLeft, SlidersHorizontal } from 'lucide-vue-next'
import * as hotApi from '@/api/hot'

const statusBarHeight = ref(0)
const period = ref('daily')
const list = ref([])
const loading = ref(true)

// 时段标签（文案对齐：daily→今日, weekly→本周, monthly→本月）
const periods = [
  { label: '今日', value: 'daily' },
  { label: '本周', value: 'weekly' },
  { label: '本月', value: 'monthly' }
]

// TOP3 与剩余列表
const top3 = computed(() => list.value.slice(0, 3))
const rest = computed(() => list.value.slice(3))

onLoad(() => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
  fetchRanking()
})

// 获取排行榜
async function fetchRanking() {
  loading.value = true
  try {
    const data = await hotApi.getRanking({ period: period.value, limit: 50 })
    list.value = (data && data.list) || []
  } catch (err) {
    console.error('获取排行榜失败', err)
    list.value = []
  } finally {
    loading.value = false
  }
}

function switchPeriod(value) {
  if (period.value === value) return
  period.value = value
  fetchRanking()
}

// 格式化热度次数
function formatCount(item) {
  const count = item.hotness || item.hot_score || item.vote_count || 0
  if (count >= 10000) {
    return (count / 10000).toFixed(1) + '万次'
  }
  return count.toLocaleString() + '次'
}

// 点击词条进入详情
function handleItemClick(word) {
  const id = word.id || word.word_id
  if (id) {
    uni.navigateTo({ url: `/pages/word-detail/index?id=${id}` })
  }
}

function handleFilter() {
  uni.showToast({ title: '筛选功能开发中', icon: 'none' })
}

function handleBack() {
  uni.navigateBack({ delta: 1 })
}
</script>

<style lang="scss" scoped>
.ranking-page {
  min-height: 100vh;
  background-color: $bg-page;
}

/* ============ 顶部栏 ============ */
.top-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 30;
  background-color: $bg-page;

  &__inner {
    height: 54px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 16px;
  }

  &__btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__title {
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
  }
}

.top-bar-placeholder {
  width: 100%;
}

/* ============ 时段标签 ============ */
.period-tabs {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  padding: 4px 0 16px;

  &__tab {
    padding-bottom: 8px;
    font-size: 14px;
    font-weight: 500;
    color: $text-tertiary;
    border-bottom: 2px solid transparent;

    &--active {
      color: $text-primary;
      border-bottom-color: $color-primary;
    }
  }
}

/* ============ 状态提示 ============ */
.state-tip {
  padding: 64px 0;
  text-align: center;
  font-size: 14px;
  color: $text-secondary;

  &--empty {
    color: $text-tertiary;
  }
}

/* ============ TOP3 领奖台 ============ */
.podium {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 12px;
  margin: 0 16px;
  padding: 20px;
  border-radius: 16px;
  background-color: $bg-card;
  box-shadow: $shadow-sm;

  &__item {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 80px;

    &--2nd { padding-top: 16px; }
    &--1st { padding-top: 0; }
    &--3rd { padding-top: 24px; }
  }

  &__circle {
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    color: #FFFFFF;

    &--1st {
      width: 48px;
      height: 48px;
      background-color: $color-primary;
    }
    &--2nd {
      width: 40px;
      height: 40px;
      background-color: $text-secondary;
    }
    &--3rd {
      width: 40px;
      height: 40px;
      background-color: $text-tertiary;
    }
  }

  &__circle-text {
    font-size: 16px;
    font-weight: 700;
  }

  &__word {
    margin-top: 8px;
    text-align: center;
    width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;

    &--1st {
      font-size: 16px;
      font-weight: 700;
      color: $text-primary;
    }
    &--2nd {
      font-size: 14px;
      font-weight: 500;
      color: $text-primary;
    }
    &--3rd {
      font-size: 13px;
      font-weight: 500;
      color: $text-primary;
    }
  }

  &__count {
    margin-top: 2px;
    font-size: 11px;
    color: $text-tertiary;
  }
}

/* ============ #4+ 列表 ============ */
.rest-list {
  margin: 12px 16px 32px;
  border-radius: 12px;
  overflow: hidden;
  background-color: $bg-card;
  box-shadow: $shadow-sm;

  &__row {
    display: flex;
    align-items: center;
    height: 52px;
    padding: 0 16px;

    &--border {
      border-bottom: 1px solid $border-color-light;
    }
  }

  &__rank {
    width: 28px;
    flex-shrink: 0;
    font-size: 14px;
    font-weight: 600;
    color: $text-tertiary;
  }

  &__word {
    flex: 1;
    min-width: 0;
    margin-left: 4px;
    font-size: 14px;
    font-weight: 500;
    color: $text-primary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__count {
    flex-shrink: 0;
    margin-left: 8px;
    font-size: 12px;
    color: $text-tertiary;
  }
}
</style>
