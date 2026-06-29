<template>
  <view class="load-more" @click="handleClick">
    <!-- 加载中 -->
    <view v-if="status === 'loading'" class="load-more__inner">
      <view class="load-more__spinner"></view>
      <text class="load-more__text">加载中...</text>
    </view>
    <!-- 没有更多 -->
    <view v-else-if="status === 'noMore'" class="load-more__inner">
      <text class="load-more__text">没有更多了</text>
    </view>
    <!-- 加载失败 -->
    <view v-else-if="status === 'error'" class="load-more__inner">
      <text class="load-more__text load-more__text--error">加载失败，点击重试</text>
    </view>
    <!-- 可加载更多 -->
    <view v-else class="load-more__inner">
      <text class="load-more__text">点击加载更多</text>
    </view>
  </view>
</template>

<script setup>
const props = defineProps({
  // 加载状态：loading 加载中 / noMore 没有更多 / error 加载失败 / more 可加载
  status: {
    type: String,
    default: 'loading'
  }
})

const emit = defineEmits(['loadMore'])

function handleClick() {
  // 加载失败或可加载时，点击触发重新加载
  if (props.status === 'error' || props.status === 'more') {
    emit('loadMore')
  }
}
</script>

<style lang="scss" scoped>
.load-more {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: $uni-spacing-col-base 0;

  &__inner {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__text {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;

    &--error {
      color: $uni-color-error;
    }
  }

  &__spinner {
    width: 32rpx;
    height: 32rpx;
    margin-right: $uni-spacing-row-sm;
    border: 4rpx solid $uni-border-color;
    border-top-color: $uni-color-primary;
    border-radius: 50%;
    animation: load-more-spin 0.8s linear infinite;
  }
}

@keyframes load-more-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
