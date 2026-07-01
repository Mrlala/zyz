<template>
  <!-- 低风险不展示 -->
  <view
    v-if="level && level !== 'low'"
    class="risk-badge"
    :class="`risk-badge--${level}`"
  >
    <AlertTriangle :size="12" />
    <text class="risk-badge__text">{{ levelText }}</text>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { AlertTriangle } from 'lucide-vue-next'

const props = defineProps({
  // 风险等级：low 低 / medium 中 / high 高
  level: {
    type: String,
    default: '',
    validator: (v) => !v || ['low', 'medium', 'high'].includes(v)
  }
})

// 风险等级文案映射
const levelText = computed(() => {
  const map = {
    low: '低风险',
    medium: '中风险',
    high: '高风险'
  }
  return map[props.level] || ''
})
</script>

<style lang="scss" scoped>
.risk-badge {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: 13px;
  line-height: 1.4;

  &--medium {
    background-color: rgba(245, 158, 11, 0.12);
    color: $risk-medium;
  }

  &--high {
    background-color: rgba(239, 68, 68, 0.12);
    color: $risk-high;
  }
}
</style>
