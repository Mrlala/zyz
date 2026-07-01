<template>
  <view class="suggestion-section">
    <!-- 行动建议 -->
    <view v-if="suggestion" class="suggestion-section__block">
      <view class="suggestion-section__header">
        <Target :size="16" color="#FE2C55" />
        <text class="suggestion-section__title">行动建议</text>
      </view>
      <view class="suggestion-section__content">{{ suggestion }}</view>
    </view>

    <!-- 建议回复（可复制） -->
    <view v-if="suggestedReply" class="suggestion-section__block suggestion-section__reply">
      <view class="suggestion-section__header">
        <MessageSquare :size="16" color="#FE2C55" />
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
import { Target, MessageSquare } from 'lucide-vue-next'

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
    background-color: $bg-card;
    border-radius: 12px;
    box-shadow: $shadow-xs;
    padding: 16px;
    margin-bottom: 8px;
  }

  &__reply {
    background-color: rgba(254, 44, 85, 0.04);
  }

  &__header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }

  &__title {
    font-size: 14px;
    font-weight: 600;
    color: $text-primary;
    flex: 1;
  }

  &__copy {
    padding: 4px 12px;
    background-color: $color-primary;
    border-radius: 9999px;

    &:active {
      opacity: 0.8;
    }
  }

  &__copy-text {
    font-size: 13px;
    color: #FFFFFF;
  }

  &__content {
    font-size: 14px;
    color: $text-primary;
    line-height: 1.7;
  }

  &__reply-content {
    color: $color-primary;
  }

  &__empty {
    font-size: 13px;
    color: $text-secondary;
    text-align: center;
    padding: 16px;
  }
}
</style>
