<template>
  <view v-if="text" class="subtext-section">
    <view class="subtext-section__header">
      <text class="subtext-section__icon">💭</text>
      <text class="subtext-section__title">潜台词分析</text>
    </view>
    <view class="subtext-section__content">{{ text }}</view>
  </view>
</template>

<script setup>
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
  background-color: #FFFFFF;
  border-radius: $uni-border-radius;
  box-shadow: $uni-box-shadow;
  padding: $uni-spacing-col-base $uni-spacing-row-base;
  margin-bottom: $uni-spacing-col-sm;

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
  }

  &__content {
    font-size: $uni-font-size-base;
    color: $uni-text-color;
    line-height: 1.7;
  }
}
</style>
