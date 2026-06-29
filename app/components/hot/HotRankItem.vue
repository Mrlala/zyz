<template>
  <view class="hot-rank-item" @click="handleClick">
    <!-- 排名：前三名特殊配色 -->
    <view
      class="hot-rank-item__rank"
      :class="`hot-rank-item__rank--${rankClass}`"
    >
      {{ rank }}
    </view>

    <!-- 词语 -->
    <view class="hot-rank-item__word">{{ wordText }}</view>

    <!-- 热度值 -->
    <view class="hot-rank-item__hot">
      <text class="hot-rank-item__hot-icon">🔥</text>
      <text class="hot-rank-item__hot-value">{{ hotScore }}</text>
    </view>

    <!-- 趋势 -->
    <view
      v-if="trend"
      class="hot-rank-item__trend"
      :class="`hot-rank-item__trend--${trend}`"
    >
      {{ trendIcon }}
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // 排名
  rank: {
    type: Number,
    default: 0
  },
  // 词条对象或词条名
  word: {
    type: [Object, String],
    default: () => ({})
  },
  // 热度值
  hotScore: {
    type: Number,
    default: 0
  },
  // 趋势：up 上升 / down 下降 / flat 持平
  trend: {
    type: String,
    default: '',
    validator: (v) => !v || ['up', 'down', 'flat'].includes(v)
  }
})

const emit = defineEmits(['click'])

// 词条名
const wordText = computed(() => {
  if (typeof props.word === 'string') return props.word
  return props.word.word || props.word.name || ''
})

// 排名样式类（前三名特殊处理）
const rankClass = computed(() => {
  if (props.rank === 1) return 'first'
  if (props.rank === 2) return 'second'
  if (props.rank === 3) return 'third'
  return 'normal'
})

// 趋势图标
const trendIcon = computed(() => {
  const map = { up: '↑', down: '↓', flat: '—' }
  return map[props.trend] || ''
})

function handleClick() {
  emit('click', props.word)
}
</script>

<style lang="scss" scoped>
.hot-rank-item {
  display: flex;
  align-items: center;
  padding: $uni-spacing-col-sm $uni-spacing-row-base;
  background-color: #FFFFFF;
  border-radius: $uni-border-radius;
  margin-bottom: $uni-spacing-row-sm;

  &:active {
    background-color: $uni-bg-color;
  }

  &__rank {
    width: 56rpx;
    height: 56rpx;
    line-height: 56rpx;
    text-align: center;
    border-radius: 50%;
    font-size: $uni-font-size-base;
    font-weight: 700;
    margin-right: $uni-spacing-row-base;
    background-color: $uni-bg-color;
    color: $uni-text-color-grey;

    &--first {
      background-color: rgba(245, 158, 11, 0.15);
      color: $uni-color-warning;
    }

    &--second {
      background-color: rgba(156, 163, 175, 0.2);
      color: $uni-text-color-grey;
    }

    &--third {
      background-color: rgba(217, 119, 6, 0.15);
      color: #D97706;
    }
  }

  &__word {
    flex: 1;
    font-size: $uni-font-size-base;
    color: $uni-text-color;
    font-weight: 500;
  }

  &__hot {
    display: flex;
    align-items: center;
    margin-left: $uni-spacing-row-sm;
  }

  &__hot-icon {
    font-size: $uni-font-size-sm;
    margin-right: 4rpx;
  }

  &__hot-value {
    font-size: $uni-font-size-sm;
    color: $uni-color-error;
    font-weight: 600;
  }

  &__trend {
    width: 40rpx;
    text-align: center;
    margin-left: $uni-spacing-row-sm;
    font-size: $uni-font-size-base;
    font-weight: 700;

    &--up {
      color: $uni-color-error;
    }

    &--down {
      color: $uni-color-success;
    }

    &--flat {
      color: $uni-text-color-grey;
    }
  }
}
</style>
