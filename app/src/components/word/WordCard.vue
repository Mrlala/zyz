<template>
  <view class="word-card" @click="handleCardClick">
    <view class="word-card__main">
      <view class="word-card__header">
        <text class="word-card__word">{{ word.word }}</text>
        <view class="word-card__tags">
          <WordTag
            v-if="categoryText"
            type="category"
            :text="categoryText"
          />
          <RiskBadge :level="word.risk_level || word.risk" />
        </view>
      </view>

      <view class="word-card__meaning">
        {{ meaningText }}
      </view>
    </view>

    <!-- 右侧收藏按钮 -->
    <view
      class="word-card__fav"
      @click.stop="handleFavClick"
    >
      <text class="word-card__fav-icon">{{ isFavorited ? '★' : '☆' }}</text>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import WordTag from './WordTag.vue'
import RiskBadge from '../common/RiskBadge.vue'

const props = defineProps({
  // 词条对象：含 word / meaning / category / risk_level 等
  word: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['click', 'favorite'])

// 是否已收藏
const isFavorited = computed(() => {
  return !!(props.word.is_favorited || props.word.favorited)
})

// 分类文案
const categoryText = computed(() => {
  return props.word.category || props.word.category_name || ''
})

// 解释文案（截断展示，由 CSS 控制行数）
const meaningText = computed(() => {
  return props.word.meaning || props.word.definition || props.word.summary || ''
})

function handleCardClick() {
  emit('click', props.word)
}

function handleFavClick() {
  emit('favorite', props.word)
}
</script>

<style lang="scss" scoped>
.word-card {
  display: flex;
  align-items: center;
  background-color: #FFFFFF;
  border-radius: $uni-border-radius;
  box-shadow: $uni-box-shadow;
  padding: $uni-spacing-col-base $uni-spacing-row-base;
  margin-bottom: $uni-spacing-col-sm;
  transition: transform 0.2s;

  &:active {
    transform: scale(0.98);
  }

  &__main {
    flex: 1;
    min-width: 0;
  }

  &__header {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: $uni-spacing-row-sm;
  }

  &__word {
    font-size: $uni-font-size-lg;
    font-weight: 600;
    color: $uni-text-color;
    margin-right: $uni-spacing-row-sm;
  }

  &__tags {
    display: flex;
    align-items: center;
    gap: $uni-spacing-row-sm;
  }

  &__meaning {
    font-size: $uni-font-size-base;
    color: $uni-text-color-grey;
    line-height: 1.5;
    // 两行截断
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    overflow: hidden;
  }

  &__fav {
    flex-shrink: 0;
    width: 64rpx;
    height: 64rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-left: $uni-spacing-row-sm;
  }

  &__fav-icon {
    font-size: 44rpx;
    color: $uni-color-warning;
  }
}
</style>
