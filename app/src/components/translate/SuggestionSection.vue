<template>
  <view class="suggestion-section">
    <!-- 行动建议 -->
    <view v-if="suggestion" class="suggestion-section__block">
      <view class="suggestion-section__header">
        <text class="suggestion-section__icon">🎯</text>
        <text class="suggestion-section__title">行动建议</text>
      </view>
      <view class="suggestion-section__content">{{ suggestion }}</view>
    </view>

    <!-- 建议回复（可复制） -->
    <view v-if="suggestedReply" class="suggestion-section__block suggestion-section__reply">
      <view class="suggestion-section__header">
        <text class="suggestion-section__icon">💬</text>
        <text class="suggestion-section__title">建议回复</text>
        <view class="suggestion-section__copy" @click="handleCopy">
          <text class="suggestion-section__copy-text">{{ copied ? '已复制' : '复制' }}</text>
        </view>
      </view>
      <view class="suggestion-section__content suggestion-section__reply-content">
        {{ suggestedReply }}
      </view>
    </view>

    <!-- 两者都为空时的兜底提示 -->
    <view
      v-if="!suggestion && !suggestedReply"
      class="suggestion-section__empty"
    >
      暂无建议回复，可参考行动建议
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  // 行动建议
  suggestion: {
    type: String,
    default: ''
  },
  // 建议回复
  suggestedReply: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['copy'])

// 是否已复制（用于按钮文案切换）
const copied = ref(false)

// 复制建议回复到剪贴板
function handleCopy() {
  if (!props.suggestedReply) return
  uni.setClipboardData({
    data: props.suggestedReply,
    success: () => {
      copied.value = true
      emit('copy', props.suggestedReply)
      // 2 秒后恢复按钮文案
      setTimeout(() => {
        copied.value = false
      }, 2000)
    }
  })
}
</script>

<style lang="scss" scoped>
.suggestion-section {
  &__block {
    background-color: #FFFFFF;
    border-radius: $uni-border-radius;
    box-shadow: $uni-box-shadow;
    padding: $uni-spacing-col-base $uni-spacing-row-base;
    margin-bottom: $uni-spacing-col-sm;
  }

  &__reply {
    background-color: rgba(79, 70, 229, 0.04);
  }

  &__header {
    display: flex;
    align-items: center;
    margin-bottom: $uni-spacing-row-sm;
  }

  &__icon {
    font-size: $uni-font-size-lg;
    margin-right: $uni-spacing-row-sm;
  }

  &__title {
    font-size: $uni-font-size-base;
    font-weight: 600;
    color: $uni-text-color;
    flex: 1;
  }

  &__copy {
    padding: 4rpx $uni-spacing-row-sm;
    background-color: $uni-color-primary;
    border-radius: 999rpx;

    &:active {
      opacity: 0.8;
    }
  }

  &__copy-text {
    font-size: $uni-font-size-sm;
    color: #FFFFFF;
  }

  &__content {
    font-size: $uni-font-size-base;
    color: $uni-text-color;
    line-height: 1.7;
  }

  &__reply-content {
    color: $uni-color-primary;
  }

  &__empty {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
    text-align: center;
    padding: $uni-spacing-col-base;
  }
}
</style>
