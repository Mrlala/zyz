<template>
  <view class="page hot-page">
    <!-- 顶部自定义导航栏 -->
    <view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="nav-bar__inner">
        <text class="nav-bar__title">热词学习</text>
        <view class="nav-bar__date">{{ dailyDate }}</view>
      </view>
    </view>
    <view class="nav-placeholder" :style="{ height: (statusBarHeight + 44) + 'px' }"></view>

    <view class="hot-page__body">
      <!-- 学习统计 -->
      <view class="hot-page__stats card">
        <view class="hot-page__stat">
          <text class="hot-page__stat-value">{{ learnedCount }}</text>
          <text class="hot-page__stat-label">已学</text>
        </view>
        <view class="hot-page__stat-divider"></view>
        <view class="hot-page__stat">
          <text class="hot-page__stat-value hot-page__stat-value--success">{{ masteredCount }}</text>
          <text class="hot-page__stat-label">已掌握</text>
        </view>
        <view class="hot-page__stat-divider"></view>
        <view class="hot-page__stat">
          <text class="hot-page__stat-value hot-page__stat-value--warning">{{ notMasteredCount }}</text>
          <text class="hot-page__stat-label">未掌握</text>
        </view>
        <view class="hot-page__stat-divider"></view>
        <view class="hot-page__stat">
          <text class="hot-page__stat-value">{{ totalCount }}</text>
          <text class="hot-page__stat-label">今日</text>
        </view>
      </view>

      <!-- 进度条 -->
      <view class="hot-page__progress">
        <ProgressBar :current="learnedCount" :total="totalCount" />
      </view>

      <!-- 卡片区 -->
      <view class="hot-page__cards">
        <!-- 加载中 -->
        <view v-if="loading" class="hot-page__loading card">
          <view class="hot-page__loading-icon">⏳</view>
          <text class="hot-page__loading-text">热词加载中...</text>
        </view>

        <!-- 空数据 -->
        <EmptyState
          v-else-if="!words.length"
          icon="☀️"
          text="今日还没有热词，稍后再来看看吧"
        />

        <!-- 全部学完 -->
        <view v-else-if="currentIndex >= words.length" class="hot-page__done card">
          <view class="hot-page__done-icon">🎉</view>
          <view class="hot-page__done-title">今日学习完成</view>
          <view class="hot-page__done-desc">已学习 {{ learnedCount }} 个热词，掌握 {{ masteredCount }} 个</view>
          <view class="hot-page__done-btn btn btn-primary" @click="handleRestart">再学一遍</view>
        </view>

        <!-- 卡片堆叠：只渲染当前卡片及下一张作为底层 -->
        <view v-else class="hot-page__stack">
          <view class="hot-page__stack-bg"></view>
          <HotSwiperCard
            :key="currentWord.id || currentIndex"
            :word="currentWord"
            :index="currentIndex"
            @swipe="handleSwipe"
            @click="handleCardClick"
          />
        </view>
      </view>

      <!-- 操作引导 -->
      <view v-if="words.length && currentIndex < words.length" class="hot-page__guide">
        <view class="hot-page__guide-item hot-page__guide-item--left">
          <text class="hot-page__guide-emoji">👈</text>
          <text>左滑 看不懂</text>
        </view>
        <view class="hot-page__guide-item hot-page__guide-item--right">
          <text>右滑 能看懂</text>
          <text class="hot-page__guide-emoji">👉</text>
        </view>
      </view>

      <!-- 底部按钮 -->
      <view class="hot-page__footer">
        <view class="hot-page__footer-btn btn btn-outline" @click="goRanking">
          <text class="hot-page__footer-emoji">🏆</text>
          <text>排行榜</text>
        </view>
        <view class="hot-page__footer-btn btn btn-outline" @click="goHistory">
          <text class="hot-page__footer-emoji">📖</text>
          <text>学习历史</text>
        </view>
        <view class="hot-page__footer-btn btn btn-primary" @click="goLearn">
          <text class="hot-page__footer-emoji">🎯</text>
          <text>沉浸学习</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import HotSwiperCard from '@/components/hot/HotSwiperCard.vue'
import ProgressBar from '@/components/hot/ProgressBar.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import * as hotApi from '@/api/hot'

const statusBarHeight = ref(0)
// 热词列表
const words = ref([])
// 当前卡片序号
const currentIndex = ref(0)
// 加载中
const loading = ref(true)
// 每日热词日期
const dailyDate = ref('')
// 学习结果：记录每个词是否掌握（right=掌握，left=未掌握）
const results = ref({})

// 当前词条
const currentWord = computed(() => words.value[currentIndex.value] || {})

// 总数
const totalCount = computed(() => words.value.length)
// 已学数量
const learnedCount = computed(() => Math.min(currentIndex.value, totalCount.value))
// 已掌握数量
const masteredCount = computed(() => {
  return Object.values(results.value).filter((r) => r === 'right').length
})
// 未掌握数量
const notMasteredCount = computed(() => {
  return Object.values(results.value).filter((r) => r === 'left').length
})

onLoad(() => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
  fetchDaily()
})

onShow(() => {
  // 从沉浸学习页返回后刷新进度（若已在学习中则不重复加载）
  if (!loading.value && words.value.length === 0) {
    fetchDaily()
  }
})

// 获取每日热词
async function fetchDaily() {
  loading.value = true
  try {
    const data = await hotApi.getDaily()
    words.value = (data && data.list) || []
    dailyDate.value = (data && data.date) || formatDate(new Date())
    currentIndex.value = 0
    results.value = {}
  } catch (err) {
    console.error('获取每日热词失败', err)
    words.value = []
  } finally {
    loading.value = false
  }
}

// 处理卡片滑动结果
function handleSwipe(direction) {
  const word = currentWord.value
  const id = word.id || word.word_id
  if (id !== undefined) {
    results.value[id] = direction
  }
  // 对热词投票（右滑能看懂=点赞）
  if (id !== undefined) {
    hotApi.vote(id, 'upvote').catch(() => {})
  }
  // 推进到下一张
  currentIndex.value++
}

// 点击卡片进入词条详情
function handleCardClick(word) {
  const id = word.id || word.word_id
  if (id) {
    uni.navigateTo({ url: `/pages/word-detail/index?id=${id}` })
  }
}

// 重新学习
function handleRestart() {
  currentIndex.value = 0
  results.value = {}
}

// 跳转排行榜
function goRanking() {
  uni.navigateTo({ url: '/pages/hot/ranking' })
}

// 跳转学习历史
function goHistory() {
  uni.navigateTo({ url: '/pages/mine/history' })
}

// 跳转沉浸学习
function goLearn() {
  if (!words.value.length) {
    uni.showToast({ title: '暂无热词可学习', icon: 'none' })
    return
  }
  uni.navigateTo({ url: '/pages/hot/learn' })
}

// 格式化日期为 MM-DD
function formatDate(d) {
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${m}-${day}`
}
</script>

<style lang="scss" scoped>
.hot-page {
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

    &__title {
      font-size: $uni-font-size-title;
      font-weight: 700;
      color: $uni-text-color;
    }

    &__date {
      font-size: $uni-font-size-sm;
      color: $uni-text-color-grey;
    }
  }

  &__body {
    padding: $uni-spacing-col-base $uni-spacing-row-base;
    padding-bottom: 180rpx;
  }

  // 统计区
  &__stats {
    display: flex;
    align-items: center;
    justify-content: space-around;
    margin-bottom: $uni-spacing-col-base;
  }

  &__stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
  }

  &__stat-value {
    font-size: $uni-font-size-title;
    font-weight: 700;
    color: $uni-color-primary;

    &--success {
      color: $uni-color-success;
    }

    &--warning {
      color: $uni-color-warning;
    }
  }

  &__stat-label {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
    margin-top: 4rpx;
  }

  &__stat-divider {
    width: 2rpx;
    height: 48rpx;
    background-color: $uni-border-color;
  }

  &__progress {
    margin-bottom: $uni-spacing-col-base;
  }

  // 卡片区
  &__cards {
    min-height: 520rpx;
    position: relative;
  }

  &__stack {
    position: relative;
  }

  // 底层卡片阴影，营造堆叠感
  &__stack-bg {
    position: absolute;
    top: 12rpx;
    left: 16rpx;
    right: 16rpx;
    bottom: -12rpx;
    background-color: #FFFFFF;
    border-radius: $uni-border-radius;
    box-shadow: $uni-box-shadow;
    z-index: 0;
  }

  &__loading,
  &__done {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: $uni-spacing-col-xl 0;
  }

  &__loading-icon,
  &__done-icon {
    font-size: 96rpx;
    margin-bottom: $uni-spacing-col-base;
  }

  &__loading-text {
    font-size: $uni-font-size-base;
    color: $uni-text-color-grey;
  }

  &__done-title {
    font-size: $uni-font-size-title;
    font-weight: 700;
    color: $uni-text-color;
    margin-bottom: $uni-spacing-row-sm;
  }

  &__done-desc {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
    margin-bottom: $uni-spacing-col-lg;
  }

  &__done-btn {
    padding: 0 $uni-spacing-row-lg;
  }

  // 操作引导
  &__guide {
    display: flex;
    justify-content: space-between;
    margin-top: $uni-spacing-col-base;
    padding: 0 $uni-spacing-row-base;
  }

  &__guide-item {
    display: flex;
    align-items: center;
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;

    &--left {
      color: $uni-color-error;
    }

    &--right {
      color: $uni-color-success;
    }
  }

  &__guide-emoji {
    font-size: $uni-font-size-lg;
    margin: 0 $uni-spacing-row-sm;
  }

  // 底部按钮
  &__footer {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    gap: $uni-spacing-row-sm;
    padding: $uni-spacing-col-sm $uni-spacing-row-base;
    padding-bottom: calc(#{$uni-spacing-col-sm} + env(safe-area-inset-bottom));
    background-color: #FFFFFF;
    box-shadow: 0 -2rpx 12rpx rgba(0, 0, 0, 0.06);
    z-index: 50;
  }

  &__footer-btn {
    flex: 1;
    height: 72rpx;
    font-size: $uni-font-size-sm;
  }

  &__footer-emoji {
    margin-right: $uni-spacing-row-sm;
  }
}
</style>
