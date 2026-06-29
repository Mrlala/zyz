<template>
  <!-- 低风险不展示警示条 -->
  <view
    v-if="riskLevel && riskLevel !== 'low'"
    class="risk-warning"
    :class="`risk-warning--${riskLevel}`"
  >
    <view class="risk-warning__header">
      <text class="risk-warning__icon">⚠</text>
      <text class="risk-warning__title">风险提示</text>
      <text class="risk-warning__level">{{ levelText }}</text>
    </view>

    <view v-if="riskTypes && riskTypes.length" class="risk-warning__row">
      <text class="risk-warning__label">风险类型：</text>
      <text class="risk-warning__value">{{ riskTypes.join(' / ') }}</text>
    </view>

    <view v-if="advice" class="risk-warning__row">
      <text class="risk-warning__label">建议：</text>
      <text class="risk-warning__value">{{ advice }}</text>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // 风险等级：low / medium / high
  riskLevel: {
    type: String,
    default: '',
    validator: (v) => !v || ['low', 'medium', 'high'].includes(v)
  },
  // 风险类型数组，如 ['标签化', '调侃']
  riskTypes: {
    type: Array,
    default: () => []
  },
  // 风险建议文案
  advice: {
    type: String,
    default: ''
  }
})

// 风险等级文案
const levelText = computed(() => {
  const map = {
    low: '低风险',
    medium: '中风险',
    high: '高风险'
  }
  return map[props.riskLevel] || ''
})
</script>

<style lang="scss" scoped>
.risk-warning {
  border-radius: $uni-border-radius;
  padding: $uni-spacing-col-base $uni-spacing-row-base;
  margin: $uni-spacing-col-sm 0;

  &--medium {
    background-color: rgba(245, 158, 11, 0.1);
    border: 2rpx solid rgba(245, 158, 11, 0.3);
  }

  &--high {
    background-color: rgba(239, 68, 68, 0.1);
    border: 2rpx solid rgba(239, 68, 68, 0.3);
  }

  &__header {
    display: flex;
    align-items: center;
    margin-bottom: $uni-spacing-col-sm;
  }

  &__icon {
    font-size: $uni-font-size-base;
    margin-right: $uni-spacing-row-sm;
  }

  &__title {
    font-size: $uni-font-size-base;
    font-weight: 600;
    color: $uni-text-color;
  }

  &__level {
    margin-left: $uni-spacing-row-sm;
    font-size: $uni-font-size-sm;
    padding: 2rpx $uni-spacing-row-sm;
    border-radius: 999rpx;
    background-color: rgba(255, 255, 255, 0.6);
  }

  &__row {
    display: flex;
    flex-wrap: wrap;
    margin-top: $uni-spacing-row-sm;
    font-size: $uni-font-size-sm;
    line-height: 1.6;
  }

  &__label {
    color: $uni-text-color-grey;
    flex-shrink: 0;
  }

  &__value {
    color: $uni-text-color;
    flex: 1;
  }
}

.risk-warning--medium .risk-warning__level {
  color: $uni-risk-medium;
}

.risk-warning--high .risk-warning__level {
  color: $uni-risk-high;
}
</style>
