<template>
  <view v-if="show" class="ai-popover" @click="handleClose">
    <view class="ai-popover__mask"></view>
    <view class="ai-popover__panel" @click.stop>
      <!-- 头部 -->
      <view class="ai-popover__header">
        <view class="ai-popover__title-row">
          <text class="ai-popover__word">{{ keyword?.word || '' }}</text>
          <view class="ai-popover__ai-badge">AI</view>
        </view>
        <view class="ai-popover__close" @click="handleClose">
          <X :size="18" color="#9CA3AF" />
        </view>
      </view>

      <!-- 来源说明 -->
      <view class="ai-popover__source-note">
        <Sparkles :size="12" color="#F59E0B" />
        <text>AI 临时生成，未入词库</text>
      </view>

      <!-- AI 释义 -->
      <view class="ai-popover__section">
        <view class="ai-popover__section-title">AI 释义</view>
        <view class="ai-popover__section-body">{{ keyword?.meaning || keyword?.definition || '暂无释义' }}</view>
      </view>

      <!-- 操作按钮 -->
      <view class="ai-popover__actions">
        <view class="ai-popover__btn ai-popover__btn--correct" @click="handleCorrect">
          <Pencil :size="16" color="#FE2C55" />
          <text>纠错 AI 释义</text>
        </view>
        <view class="ai-popover__btn ai-popover__btn--submit" @click="handleSubmit">
          <Send :size="16" color="#FFFFFF" />
          <text class="ai-popover__btn-text--white">提交到词库</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { X, Sparkles, Pencil, Send } from 'lucide-vue-next'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  keyword: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['close', 'correct', 'submit'])

function handleClose() {
  emit('close')
}

function handleCorrect() {
  emit('correct', props.keyword)
}

function handleSubmit() {
  emit('submit', props.keyword)
}
</script>

<style lang="scss" scoped>
.ai-popover {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;

  &__mask {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
  }

  &__panel {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #FFFFFF;
    border-radius: 20px 20px 0 0;
    padding: 20px 16px;
    padding-bottom: calc(20px + env(safe-area-inset-bottom));
  }

  &__header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 8px;
  }

  &__title-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  &__word {
    font-size: 18px;
    font-weight: 700;
    color: $text-primary;
  }

  &__ai-badge {
    font-size: 10px;
    font-weight: 600;
    color: $color-warning;
    background-color: rgba(245, 158, 11, 0.12);
    border-radius: 4px;
    padding: 2px 6px;
    line-height: 1.4;
  }

  &__close {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__source-note {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: $text-tertiary;
    margin-bottom: 16px;
  }

  &__section {
    margin-bottom: 20px;
  }

  &__section-title {
    font-size: 13px;
    font-weight: 600;
    color: $text-secondary;
    margin-bottom: 8px;
  }

  &__section-body {
    font-size: 14px;
    color: $text-primary;
    line-height: 1.7;
    padding: 12px;
    background-color: $bg-sunken;
    border-radius: 10px;
  }

  &__actions {
    display: flex;
    gap: 12px;
  }

  &__btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 12px 0;
    border-radius: 12px;
    font-size: 14px;
    font-weight: 500;

    &:active {
      opacity: 0.7;
    }

    &--correct {
      background-color: rgba(254, 44, 85, 0.08);
      color: $color-primary;
    }

    &--submit {
      background-color: $color-primary;
      color: #FFFFFF;
    }
  }

  &__btn-text--white {
    color: #FFFFFF;
  }
}
</style>
