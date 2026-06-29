<template>
  <view class="progress-bar">
    <view class="progress-bar__header">
      <text class="progress-bar__text">学习进度</text>
      <text class="progress-bar__count">{{ current }} / {{ total }}</text>
    </view>
    <view class="progress-bar__track">
      <view
        class="progress-bar__fill"
        :style="{ width: percent + '%' }"
      ></view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // 当前进度
  current: {
    type: Number,
    default: 0
  },
  // 总数
  total: {
    type: Number,
    default: 0
  }
})

// 进度百分比
const percent = computed(() => {
  if (!props.total || props.total <= 0) return 0
  const p = Math.round((props.current / props.total) * 100)
  return Math.min(Math.max(p, 0), 100)
})
</script>

<style lang="scss" scoped>
.progress-bar {
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $uni-spacing-row-sm;
  }

  &__text {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
  }

  &__count {
    font-size: $uni-font-size-sm;
    color: $uni-color-primary;
    font-weight: 600;
  }

  &__track {
    height: 16rpx;
    background-color: $uni-border-color;
    border-radius: 999rpx;
    overflow: hidden;
  }

  &__fill {
    height: 100%;
    background-color: $uni-color-primary;
    border-radius: 999rpx;
    transition: width 0.3s ease-out;
  }
}
</style>
