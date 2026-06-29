<template>
  <view
    class="hot-swiper-card"
    :class="{ 'hot-swiper-card--leaving': isLeaving }"
    @touchstart="onTouchStart"
    @touchmove="onTouchMove"
    @touchend="onTouchEnd"
    @click="handleClick"
  >
    <view
      class="hot-swiper-card__inner"
      :style="cardStyle"
    >
      <!-- 滑动提示覆盖层 -->
      <view
        v-if="dx < -threshold"
        class="hot-swiper-card__stamp hot-swiper-card__stamp--left"
      >看不懂</view>
      <view
        v-if="dx > threshold"
        class="hot-swiper-card__stamp hot-swiper-card__stamp--right"
      >能看懂</view>

      <!-- 词语 -->
      <view class="hot-swiper-card__word">{{ wordText }}</view>

      <!-- 分类标签 -->
      <view v-if="categoryText" class="hot-swiper-card__category">
        <WordTag type="category" :text="categoryText" />
      </view>

      <!-- 解释 -->
      <view v-if="meaningText" class="hot-swiper-card__section">
        <view class="hot-swiper-card__label">释义</view>
        <view class="hot-swiper-card__meaning">{{ meaningText }}</view>
      </view>

      <!-- 示例 -->
      <view v-if="exampleText" class="hot-swiper-card__section">
        <view class="hot-swiper-card__label">示例</view>
        <view class="hot-swiper-card__example">{{ exampleText }}</view>
      </view>

      <!-- 滑动操作引导 -->
      <view class="hot-swiper-card__guide">
        <text class="hot-swiper-card__guide-item">👈 左滑 看不懂</text>
        <text class="hot-swiper-card__guide-item">右滑 能看懂 👉</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import WordTag from '../word/WordTag.vue'

const props = defineProps({
  // 词条对象
  word: {
    type: Object,
    default: () => ({})
  },
  // 卡片序号
  index: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['swipe', 'click'])

// 触发滑动的水平距离阈值（px）
const threshold = 60

// 手指起始坐标
const startX = ref(0)
const startY = ref(0)
// 当前水平偏移
const dx = ref(0)
// 当前垂直偏移
const dy = ref(0)
// 是否正在拖动（拖动时禁用过渡动画，实现即时跟随）
const dragging = ref(false)
// 是否正在滑出（触发滑动后飞出动画）
const isLeaving = ref(false)

// 词语
const wordText = computed(() => props.word.word || props.word.name || '')

// 分类
const categoryText = computed(() => {
  return props.word.category || props.word.category_name || ''
})

// 释义
const meaningText = computed(() => {
  return props.word.meaning || props.word.definition || props.word.summary || ''
})

// 示例
const exampleText = computed(() => {
  const ex = props.word.examples || props.word.example
  if (!ex) return ''
  if (Array.isArray(ex)) {
    const first = ex[0]
    return typeof first === 'string' ? first : (first.text || first.content || '')
  }
  return ex
})

// 卡片样式：跟随手指移动 + 旋转 + 透明度
const cardStyle = computed(() => {
  // 旋转角度：随 dx 偏转，最大约 ±20°
  const rotate = (dx.value / 300) * 20
  // 透明度：随 |dx| 增大而降低，最低 0.5
  const opacity = Math.max(1 - Math.abs(dx.value) / 600, 0.5)
  const transition = dragging.value ? 'none' : 'transform 0.3s ease-out, opacity 0.3s ease-out'
  return {
    transform: `translate3d(${dx.value}px, ${dy.value}px, 0) rotate(${rotate}deg)`,
    opacity,
    transition
  }
})

// 触摸开始
function onTouchStart(e) {
  if (isLeaving.value) return
  const touch = e.touches[0]
  startX.value = touch.clientX
  startY.value = touch.clientY
  dx.value = 0
  dy.value = 0
  dragging.value = true
}

// 触摸移动
function onTouchMove(e) {
  if (isLeaving.value || !dragging.value) return
  const touch = e.touches[0]
  const moveX = touch.clientX - startX.value
  const moveY = touch.clientY - startY.value
  dx.value = moveX
  // 垂直方向只跟随一小部分，避免上下滑动时卡片大幅偏移
  dy.value = moveY * 0.3
}

// 触摸结束
function onTouchEnd() {
  if (isLeaving.value) return
  dragging.value = false

  // 超过阈值则触发滑动飞出
  if (dx.value > threshold) {
    triggerSwipe('right')
  } else if (dx.value < -threshold) {
    triggerSwipe('left')
  } else {
    // 未超过阈值，回弹归位
    dx.value = 0
    dy.value = 0
  }
}

// 触发滑动：卡片飞出屏幕并通知父组件
function triggerSwipe(direction) {
  isLeaving.value = true
  // 飞出距离取屏幕宽度的 1.5 倍，确保完全滑出
  const flyDistance = (typeof window !== 'undefined' ? window.innerWidth : 375) * 1.5
  dx.value = direction === 'right' ? flyDistance : -flyDistance
  // 动画结束后通知父组件
  setTimeout(() => {
    emit('swipe', direction)
    // 重置状态，供下次复用
    isLeaving.value = false
    dx.value = 0
    dy.value = 0
  }, 300)
}

function handleClick() {
  emit('click', props.word)
}
</script>

<style lang="scss" scoped>
.hot-swiper-card {
  position: relative;
  width: 100%;

  &__inner {
    position: relative;
    background-color: #FFFFFF;
    border-radius: $uni-border-radius-lg;
    box-shadow: $uni-box-shadow;
    padding: $uni-spacing-col-lg $uni-spacing-row-lg;
    min-height: 480rpx;
    will-change: transform, opacity;
  }

  // 滑动提示印章
  &__stamp {
    position: absolute;
    top: $uni-spacing-col-lg;
    padding: $uni-spacing-row-sm $uni-spacing-row-lg;
    border-radius: $uni-border-radius;
    font-size: $uni-font-size-lg;
    font-weight: 700;
    border: 4rpx solid;

    &--left {
      right: $uni-spacing-row-lg;
      color: $uni-color-error;
      border-color: $uni-color-error;
      background-color: rgba(239, 68, 68, 0.08);
    }

    &--right {
      left: $uni-spacing-row-lg;
      color: $uni-color-success;
      border-color: $uni-color-success;
      background-color: rgba(16, 185, 129, 0.08);
    }
  }

  &__word {
    font-size: $uni-font-size-xxl;
    font-weight: 700;
    color: $uni-text-color;
    text-align: center;
    margin-bottom: $uni-spacing-col-sm;
  }

  &__category {
    display: flex;
    justify-content: center;
    margin-bottom: $uni-spacing-col-base;
  }

  &__section {
    margin-bottom: $uni-spacing-col-base;
  }

  &__label {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
    margin-bottom: $uni-spacing-row-sm;
    padding-left: $uni-spacing-row-sm;
    border-left: 6rpx solid $uni-color-primary;
  }

  &__meaning {
    font-size: $uni-font-size-base;
    color: $uni-text-color;
    line-height: 1.7;
  }

  &__example {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
    line-height: 1.7;
    padding: $uni-spacing-row-sm $uni-spacing-row-base;
    background-color: $uni-bg-color;
    border-radius: $uni-border-radius;
  }

  &__guide {
    display: flex;
    justify-content: space-between;
    margin-top: $uni-spacing-col-base;
    padding-top: $uni-spacing-col-base;
    border-top: 2rpx solid $uni-border-color;
  }

  &__guide-item {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
  }
}
</style>
