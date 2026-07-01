<template>
  <view v-if="text" class="subtext-section">
    <view class="subtext-section__header">
      <MessageCircle :size="16" color="#FE2C55" />
      <text class="subtext-section__title">潜台词分析</text>
    </view>
    <view class="subtext-section__content">{{ text }}</view>
  </view>
</template>

<script setup>
import { MessageCircle } from 'lucide-vue-next'

defineProps({
  // 潜台词内容
  text: {
    type: String,
    default: ''
  }
})
</script>

<style lang="scss" scoped>
.subtext-section {
  background-color: $bg-card;
  border-radius: 12px;
  box-shadow: $shadow-xs;
  padding: 16px;
  margin-bottom: 8px;

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
  }

  &__content {
    font-size: 14px;
    color: $text-primary;
    line-height: 1.7;
  }
}
</style>
