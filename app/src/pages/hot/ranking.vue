<template>
  <view class="page ranking-page">
    <!-- 顶部自定义导航栏 -->
    <view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="nav-bar__inner">
        <view class="nav-bar__back" @click="handleBack">‹</view>
        <text class="nav-bar__title">热词排行</text>
        <view class="nav-bar__placeholder"></view>
      </view>
    </view>
    <view class="nav-placeholder" :style="{ height: (statusBarHeight + 44) + 'px' }"></view>

    <view class="ranking-page__body">
      <!-- 时间范围切换 -->
      <view class="ranking-page__tabs">
        <view
          v-for="tab in periods"
          :key="tab.value"
          class="ranking-page__tab"
          :class="{ 'ranking-page__tab--active': period === tab.value }"
          @click="switchPeriod(tab.value)"
        >{{ tab.label }}</view>
      </view>

      <!-- 排行榜列表 -->
      <view class="ranking-page__list">
        <!-- 加载中 -->
        <view v-if="loading" class="ranking-page__loading">
          <view class="ranking-page__loading-icon">⏳</view>
          <text class="ranking-page__loading-text">加载中...</text>
        </view>

        <template v-else>
          <HotRankItem
            v-for="(item, idx) in list"
            :key="item.id || idx"
            :rank="idx + 1"
            :word="item"
            :hot-score="item.hotness || item.hot_score || item.vote_count || 0"
            :trend="item.trend"
            @click="handleItemClick"
          />

          <EmptyState
            v-if="!list.length"
            icon="🏆"
            text="暂无排行数据"
          />
        </template>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import HotRankItem from '@/components/hot/HotRankItem.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import * as hotApi from '@/api/hot'

const statusBarHeight = ref(0)
const period = ref('daily')
const list = ref([])
const loading = ref(true)

// 时间范围选项
const periods = [
  { label: '日榜', value: 'daily' },
  { label: '周榜', value: 'weekly' },
  { label: '月榜', value: 'monthly' }
]

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

// 切换时间范围
function switchPeriod(value) {
  if (period.value === value) return
  period.value = value
  fetchRanking()
}

// 点击词条进入详情
function handleItemClick(word) {
  const id = word.id || word.word_id
  if (id) {
    uni.navigateTo({ url: `/pages/word-detail/index?id=${id}` })
  }
}

function handleBack() {
  uni.navigateBack({ delta: 1 })
}
</script>

<style lang="scss" scoped>
.ranking-page {
  min-height: 100vh;
  background-color: $uni-bg-color;

  .nav-bar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
    background-color: #FFFFFF;
    box-shadow: $uni-box-shadow;

    &__inner {
      height: 88rpx;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 $uni-spacing-row-base;
    }

    &__back {
      width: 56rpx;
      height: 56rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 56rpx;
      color: $uni-text-color;
      line-height: 1;
    }

    &__title {
      font-size: $uni-font-size-lg;
      font-weight: 600;
      color: $uni-text-color;
    }

    &__placeholder {
      width: 56rpx;
    }
  }

  &__body {
    padding: $uni-spacing-col-base $uni-spacing-row-base;
    padding-bottom: 60rpx;
  }

  // 时间范围切换
  &__tabs {
    display: flex;
    background-color: #FFFFFF;
    border-radius: $uni-border-radius;
    padding: 6rpx;
    margin-bottom: $uni-spacing-col-base;
  }

  &__tab {
    flex: 1;
    text-align: center;
    padding: 16rpx 0;
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
    border-radius: $uni-border-radius;
    transition: all 0.2s;

    &--active {
      background-color: $uni-color-primary;
      color: #FFFFFF;
      font-weight: 600;
    }
  }

  &__list {
    padding-top: $uni-spacing-row-sm;
  }

  &__loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: $uni-spacing-col-xl 0;
  }

  &__loading-icon {
    font-size: 96rpx;
    margin-bottom: $uni-spacing-col-base;
  }

  &__loading-text {
    font-size: $uni-font-size-base;
    color: $uni-text-color-grey;
  }
}
</style>
