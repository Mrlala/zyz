<template>
  <view
    class="word-card"
    :class="`word-card--${variant}`"
    @click="handleCardClick"
  >
    <!-- featured 变体：左侧渐变色条 -->
    <view v-if="variant === 'featured'" class="word-card__bar"></view>

    <view class="word-card__body">
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
            <!-- featured 变体：热度徽章 -->
            <view v-if="variant === 'featured' && heatText" class="word-card__heat">
              <Flame :size="11" color="#F59E0B" />
              <text class="word-card__heat-text">{{ heatText }}</text>
            </view>
          </view>
        </view>

        <view class="word-card__meaning">
          {{ meaningText }}
        </view>

        <!-- featured 变体：示例预览 -->
        <view v-if="variant === 'featured' && examplePreview" class="word-card__example">
          <text class="word-card__example-quote">"</text>
          <text class="word-card__example-text">{{ examplePreview }}</text>
        </view>

        <!-- 底部元信息行：热度 + 浏览量 -->
        <view v-if="heatText || viewCount" class="word-card__meta">
          <view v-if="heatText" class="word-card__meta-item">
            <Flame :size="11" color="#F59E0B" />
            <text class="word-card__meta-text">{{ heatText }}</text>
          </view>
          <view v-if="viewCount" class="word-card__meta-item">
            <Eye :size="11" color="#9CA3AF" />
            <text class="word-card__meta-text">{{ viewCount }}</text>
          </view>
        </view>
      </view>

      <!-- 右侧收藏按钮 -->
      <view
        class="word-card__fav"
        @click.stop="handleFavClick"
      >
        <Heart
          :size="20"
          :color="isFavorited ? '#FE2C55' : '#D1D5DB'"
          :fill="isFavorited ? '#FE2C55' : 'none'"
        />
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { Heart, Flame, Eye } from 'lucide-vue-next'
import WordTag from './WordTag.vue'
import RiskBadge from '../common/RiskBadge.vue'

const props = defineProps({
  // 词条对象：含 word / meaning / category / risk_level / hot_score 等
  word: {
    type: Object,
    default: () => ({})
  },
  // 卡片变体：default 常规 / featured 精选（渐变色条 + 热度徽章）
  variant: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'featured'].includes(v)
  }
})

const emit = defineEmits(['click', 'favorite'])

// 是否已收藏
const isFavorited = computed(() => {
  return !!(props.word.is_favorited || props.word.favorited)
})

// 分类文案
const categoryText = computed(() => {
  const cat = props.word.category
  if (cat && typeof cat === 'object') {
    return cat.name || ''
  }
  return cat || props.word.category_name || ''
})

// 解释文案（截断展示，由 CSS 控制行数）
const meaningText = computed(() => {
  return props.word.meaning || props.word.definition || props.word.summary || '暂无释义'
})

// 热度文案
const heatText = computed(() => {
  const score = props.word.hot_score || props.word.hotness || props.word.hot || 0
  if (!score) return ''
  if (score >= 10000) return (score / 10000).toFixed(1) + 'w'
  return String(score)
})

// 示例预览（featured 变体展示，截断 30 字符）
const examplePreview = computed(() => {
  const ex = props.word.example || ''
  if (!ex) return ''
  return ex.length > 30 ? ex.slice(0, 30) + '...' : ex
})

// 浏览量
const viewCount = computed(() => props.word.view_count || 0)

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
  background-color: $bg-card;
  border-radius: 12px;
  transition: transform 0.2s;

  &:active {
    transform: scale(0.98);
  }

  /* ---- featured 变体：渐变色条 + 更大阴影 ---- */
  &--featured {
    box-shadow: $shadow-sm;
    overflow: hidden;
  }

  &--default {
    align-items: center;
    box-shadow: $shadow-xs;
    padding: 12px 16px;
  }

  /* ---- featured 左侧色条 ---- */
  &__bar {
    width: 3px;
    flex-shrink: 0;
    background: $gradient-primary;
  }

  /* ---- 主体（featured 下含色条后的内容区） ---- */
  &__body {
    flex: 1;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    min-width: 0;

    .word-card--featured & {
      padding: 16px;
    }
  }

  &__main {
    flex: 1;
    min-width: 0;
  }

  &__header {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 8px;
  }

  &__word {
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
    margin-right: 8px;

    .word-card--featured & {
      font-size: 18px;
    }
  }

  &__tags {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  /* ---- 热度徽章（仅 featured） ---- */
  &__heat {
    display: inline-flex;
    align-items: center;
    gap: 2px;
    padding: 2px 8px;
    border-radius: 9999px;
    background-color: rgba(245, 158, 11, 0.12);
  }

  &__heat-text {
    font-size: 13px;
    line-height: 1.4;
    color: $color-warning;
  }

  &__meaning {
    font-size: 14px;
    color: $text-secondary;
    line-height: 1.5;
    // 两行截断
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    overflow: hidden;
  }

  /* ---- featured 示例预览 ---- */
  &__example {
    display: flex;
    align-items: flex-start;
    gap: 2px;
    margin-top: 6px;
    padding: 6px 10px;
    background-color: $bg-sunken;
    border-radius: 6px;
  }

  &__example-quote {
    font-size: 13px;
    color: $color-primary;
    font-weight: 600;
  }

  &__example-text {
    font-size: 12px;
    color: $text-secondary;
    line-height: 1.4;
    flex: 1;
  }

  /* ---- 底部元信息行 ---- */
  &__meta {
    display: flex;
    gap: 12px;
    margin-top: 8px;
  }

  &__meta-item {
    display: flex;
    align-items: center;
    gap: 2px;
  }

  &__meta-text {
    font-size: 11px;
    color: $text-tertiary;
  }

  &__fav {
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-left: 8px;
  }
}
</style>
