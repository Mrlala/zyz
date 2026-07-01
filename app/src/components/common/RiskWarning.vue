<template>
  <!-- 低风险不展示警示条 -->
  <view
    v-if="riskLevel && riskLevel !== 'low'"
    class="risk-warning"
    :class="`risk-warning--${riskLevel}`"
  >
    <view class="risk-warning__header">
      <AlertTriangle :size="14" />
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
import { AlertTriangle } from 'lucide-vue-next'

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
  border-radius: 10px;
  padding: 12px 16px;
  margin: 8px 0;

  &--medium {
    background-color: rgba(245, 158, 11, 0.1);
    border: 1px solid rgba(245, 158, 11, 0.3);
  }

  &--high {
    background-color: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
  }

  &__header {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-bottom: 8px;
  }

  &__title {
    font-size: 14px;
    font-weight: 600;
    color: $text-primary;
  }

  &__level {
    margin-left: 8px;
    font-size: 13px;
    padding: 1px 8px;
    border-radius: 9999px;
    background-color: rgba(255, 255, 255, 0.6);
  }

  &__row {
    display: flex;
    flex-wrap: wrap;
    margin-top: 8px;
    font-size: 13px;
    line-height: 1.6;
  }

  &__label {
    color: $text-secondary;
    flex-shrink: 0;
  }

  &__value {
    color: $text-primary;
    flex: 1;
  }
}

.risk-warning--medium .risk-warning__level {
  color: $risk-medium;
}

.risk-warning--high .risk-warning__level {
  color: $risk-high;
}
</style>
