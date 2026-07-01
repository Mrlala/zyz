<template>
  <view class="source-tag">
    <!-- 来源标签：database 绿色 / ai_temp 橙色 -->
    <view
      class="source-tag__source"
      :class="`source-tag__source--${sourceType}`"
    >
      {{ sourceText }}
      <text v-if="sourceType === 'ai_temp'" class="source-tag__sub">未审核</text>
    </view>

    <!-- 置信度小标签 -->
    <view
      v-if="confidence"
      class="source-tag__confidence"
      :class="`source-tag__confidence--${confidence}`"
    >
      置信度：{{ confidenceText }}
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // 来源：database 内置词条库 / ai_temp AI临时解释
  source: {
    type: String,
    default: 'ai_temp',
    validator: (v) => ['database', 'ai_temp'].includes(v)
  },
  // 置信度：high 高 / medium 中 / low 低
  confidence: {
    type: String,
    default: '',
    validator: (v) => !v || ['high', 'medium', 'low'].includes(v)
  }
})

// 来源类型（缺失或未知均按 AI 临时解释处理）
const sourceType = computed(() => {
  return props.source === 'database' ? 'database' : 'ai_temp'
})

// 来源文案
const sourceText = computed(() => {
  return sourceType.value === 'database' ? '内置词条库' : 'AI 临时解释'
})

// 置信度文案
const confidenceText = computed(() => {
  const map = { high: '高', medium: '中', low: '低' }
  return map[props.confidence] || ''
})
</script>

<style lang="scss" scoped>
.source-tag {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;

  &__source {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 9999px;
    font-size: 13px;
    line-height: 1.4;

    &--database {
      background-color: rgba(16, 185, 129, 0.12);
      color: $color-success;
    }

    &--ai_temp {
      background-color: rgba(245, 158, 11, 0.12);
      color: $color-warning;
    }
  }

  &__sub {
    margin-left: 2px;
    font-size: 13px;
    opacity: 0.85;
  }

  &__confidence {
    margin-left: 8px;
    padding: 1px 8px;
    border-radius: 9999px;
    font-size: 13px;
    line-height: 1.4;
    background-color: $bg-sunken;
    color: $text-secondary;

    &--high {
      color: $color-success;
      background-color: rgba(16, 185, 129, 0.08);
    }

    &--medium {
      color: $color-warning;
      background-color: rgba(245, 158, 11, 0.08);
    }

    &--low {
      color: $text-secondary;
      background-color: $bg-sunken;
    }
  }
}
</style>
