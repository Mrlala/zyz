<template>
  <view class="page learn-page">
    <!-- 顶部自定义导航栏（含返回按钮） -->
    <view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="nav-bar__inner">
        <view class="nav-bar__back" @click="handleBack">‹</view>
        <text class="nav-bar__title">沉浸学习</text>
        <text class="nav-bar__count">{{ learnedCount }} / {{ totalCount }}</text>
      </view>
    </view>
    <view class="nav-placeholder" :style="{ height: (statusBarHeight + 44) + 'px' }"></view>

    <view class="learn-page__body">
      <!-- 加载中 -->
      <view v-if="loading" class="learn-page__status">
        <view class="learn-page__status-icon">⏳</view>
        <text class="learn-page__status-text">热词加载中...</text>
      </view>

      <!-- 空数据 -->
      <view v-else-if="!words.length" class="learn-page__status">
        <view class="learn-page__status-icon">☀️</view>
        <text class="learn-page__status-text">今日还没有热词</text>
        <view class="learn-page__status-btn btn btn-primary" @click="handleBack">返回</view>
      </view>

      <!-- 全部学完 -->
      <view v-else-if="currentIndex >= words.length" class="learn-page__status">
        <view class="learn-page__status-icon">🎉</view>
        <text class="learn-page__status-title">今日学习完成</text>
        <text class="learn-page__status-text">掌握 {{ masteredCount }} 个，未掌握 {{ notMasteredCount }} 个</text>
        <view class="learn-page__status-btns">
          <view class="learn-page__status-btn btn btn-outline" @click="handleBack">返回</view>
          <view class="learn-page__status-btn btn btn-primary" @click="handleRestart">再来一轮</view>
        </view>
      </view>

      <!-- 沉浸式卡片 -->
      <view v-else class="learn-page__stage">
        <view class="learn-page__stack-bg learn-page__stack-bg--2"></view>
        <view class="learn-page__stack-bg learn-page__stack-bg--1"></view>
        <HotSwiperCard
          :key="currentWord.id || currentIndex"
          :word="currentWord"
          :index="currentIndex"
          @swipe="handleSwipe"
          @click="handleCardClick"
        />
      </view>
    </view>

    <!-- 底部操作提示 -->
    <view v-if="words.length && currentIndex < words.length" class="learn-page__footer">
      <view class="learn-page__footer-btn learn-page__footer-btn--left" @click="manualSwipe('left')">
        <text class="learn-page__footer-emoji">🙅</text>
        <text>看不懂</text>
      </view>
      <view class="learn-page__footer-btn learn-page__footer-btn--right" @click="manualSwipe('right')">
        <text class="learn-page__footer-emoji">🙆</text>
        <text>能看懂</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import HotSwiperCard from '@/components/hot/HotSwiperCard.vue'
import * as hotApi from '@/api/hot'

const statusBarHeight = ref(0)
const words = ref([])
const currentIndex = ref(0)
const loading = ref(true)
const results = ref({})

const currentWord = computed(() => words.value[currentIndex.value] || {})
const totalCount = computed(() => words.value.length)
const learnedCount = computed(() => Math.min(currentIndex.value, totalCount.value))
const masteredCount = computed(() => Object.values(results.value).filter((r) => r === 'right').length)
const notMasteredCount = computed(() => Object.values(results.value).filter((r) => r === 'left').length)

onLoad(() => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
  fetchDaily()
})

async function fetchDaily() {
  loading.value = true
  try {
    const data = await hotApi.getDaily()
    words.value = (data && data.list) || []
    currentIndex.value = 0
    results.value = {}
  } catch (err) {
    console.error('获取每日热词失败', err)
    words.value = []
  } finally {
    loading.value = false
  }
}

// 卡片滑动结果
function handleSwipe(direction) {
  const word = currentWord.value
  const id = word.id || word.word_id
  if (id !== undefined) {
    results.value[id] = direction
    if (direction === 'right') {
      hotApi.vote(id, 'upvote').catch(() => {})
    }
  }
  currentIndex.value++
}

// 手动按钮触发滑动（通过切换 currentIndex 实现，简化交互）
function manualSwipe(direction) {
  handleSwipe(direction)
}

// 点击卡片进入详情
function handleCardClick(word) {
  const id = word.id || word.word_id
  if (id) {
    uni.navigateTo({ url: `/pages/word-detail/index?id=${id}` })
  }
}

function handleRestart() {
  currentIndex.value = 0
  results.value = {}
}

function handleBack() {
  uni.navigateBack({ delta: 1 })
}
</script>

<style lang="scss" scoped>
.learn-page {
  min-height: 100vh;
  // 沉浸式深色背景
  background: linear-gradient(180deg, #1F2937 0%, #374151 100%);

  .nav-bar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
    background-color: transparent;

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
      color: #FFFFFF;
      line-height: 1;
    }

    &__title {
      font-size: $uni-font-size-lg;
      font-weight: 600;
      color: #FFFFFF;
    }

    &__count {
      font-size: $uni-font-size-sm;
      color: rgba(255, 255, 255, 0.8);
    }
  }

  &__body {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: $uni-spacing-col-lg $uni-spacing-row-base;
    min-height: calc(100vh - 88rpx);
  }

  // 状态展示
  &__status {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: $uni-spacing-col-xl 0;
  }

  &__status-icon {
    font-size: 120rpx;
    margin-bottom: $uni-spacing-col-base;
  }

  &__status-title {
    font-size: $uni-font-size-title;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: $uni-spacing-row-sm;
  }

  &__status-text {
    font-size: $uni-font-size-base;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: $uni-spacing-col-lg;
    text-align: center;
  }

  &__status-btns {
    display: flex;
    gap: $uni-spacing-row-base;
  }

  &__status-btn {
    padding: 0 $uni-spacing-row-lg;
  }

  // 卡片舞台
  &__stage {
    position: relative;
    width: 100%;
  }

  // 堆叠底层卡片
  &__stack-bg {
    position: absolute;
    left: 24rpx;
    right: 24rpx;
    background-color: #FFFFFF;
    border-radius: $uni-border-radius-lg;
    box-shadow: $uni-box-shadow;

    &--1 {
      top: 16rpx;
      bottom: -16rpx;
      opacity: 0.6;
      transform: scale(0.96);
    }

    &--2 {
      top: 32rpx;
      bottom: -32rpx;
      opacity: 0.3;
      transform: scale(0.92);
    }
  }

  // 底部操作
  &__footer {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    padding: $uni-spacing-col-base $uni-spacing-row-lg;
    padding-bottom: calc(#{$uni-spacing-col-base} + env(safe-area-inset-bottom));
    gap: $uni-spacing-row-lg;
  }

  &__footer-btn {
    flex: 1;
    height: 96rpx;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border-radius: $uni-border-radius-lg;
    font-size: $uni-font-size-sm;
    font-weight: 600;

    &--left {
      background-color: rgba(239, 68, 68, 0.9);
      color: #FFFFFF;
    }

    &--right {
      background-color: rgba(16, 185, 129, 0.9);
      color: #FFFFFF;
    }
  }

  &__footer-emoji {
    font-size: $uni-font-size-lg;
    margin-bottom: 4rpx;
  }
}
</style>
