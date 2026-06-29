<template>
  <view class="word-detail">
    <!-- 标题区：词语 + 拼音 -->
    <view class="word-detail__title">
      <text class="word-detail__word">{{ word.word }}</text>
      <text v-if="pinyin" class="word-detail__pinyin">{{ pinyin }}</text>
    </view>

    <!-- 分类 + 来源标签 -->
    <view class="word-detail__meta">
      <WordTag v-if="categoryText" type="category" :text="categoryText" />
      <SourceTag
        v-if="word.source"
        :source="word.source"
        :confidence="word.confidence"
      />
    </view>

    <!-- 释义区 -->
    <view v-if="definition" class="word-detail__section">
      <view class="word-detail__section-title">释义</view>
      <view class="word-detail__section-content">{{ definition }}</view>
    </view>

    <!-- 多语境解释（SRS-100） -->
    <view v-if="contexts && contexts.length" class="word-detail__section">
      <view class="word-detail__section-title">多语境解释</view>
      <view class="word-detail__contexts">
        <view
          v-for="(item, idx) in contexts"
          :key="idx"
          class="word-detail__context"
          :class="{ 'word-detail__context--active': isCurrentContext(item) }"
        >
          <text class="word-detail__context-name">{{ item.context }}</text>
          <text class="word-detail__context-meaning">{{ item.meaning }}</text>
        </view>
      </view>
    </view>

    <!-- 示例区 -->
    <view v-if="examples && examples.length" class="word-detail__section">
      <view class="word-detail__section-title">示例</view>
      <view
        v-for="(example, idx) in examples"
        :key="idx"
        class="word-detail__example"
      >
        {{ typeof example === 'string' ? example : (example.text || example.content || '') }}
      </view>
    </view>

    <!-- 风险信息（SRS-101） -->
    <RiskWarning
      v-if="riskLevel && riskLevel !== 'low'"
      :risk-level="riskLevel"
      :risk-types="word.risk_types || []"
      :advice="word.advice || ''"
    />

    <!-- 相关词条 -->
    <view v-if="related && related.length" class="word-detail__section">
      <view class="word-detail__section-title">相关词条</view>
      <view class="word-detail__related">
        <view
          v-for="(item, idx) in related"
          :key="idx"
          class="word-detail__related-item"
          @click="handleRelatedClick(item)"
        >
          {{ item.word || item.name || '' }}
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import WordTag from './WordTag.vue'
import SourceTag from '../common/SourceTag.vue'
import RiskWarning from '../common/RiskWarning.vue'

const props = defineProps({
  // 完整词条对象
  word: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['relatedClick'])

// 拼音
const pinyin = computed(() => props.word.pinyin || '')

// 释义（兼容多字段命名）
const definition = computed(() => {
  return props.word.definition || props.word.meaning || props.word.summary || ''
})

// 分类文案
const categoryText = computed(() => {
  return props.word.category || props.word.category_name || ''
})

// 风险等级（兼容 risk / risk_level）
const riskLevel = computed(() => {
  return props.word.risk_level || props.word.risk || ''
})

// 多语境列表
const contexts = computed(() => {
  return props.word.contexts || props.word.context_list || []
})

// 相关词条
const related = computed(() => {
  return props.word.related || []
})

// 是否当前语境
function isCurrentContext(item) {
  const current = props.word.current_context
  if (!current) return false
  return item.context === current
}

function handleRelatedClick(item) {
  emit('relatedClick', item)
}
</script>

<style lang="scss" scoped>
.word-detail {
  &__title {
    display: flex;
    align-items: baseline;
    flex-wrap: wrap;
    margin-bottom: $uni-spacing-col-sm;
  }

  &__word {
    font-size: $uni-font-size-title;
    font-weight: 700;
    color: $uni-text-color;
    margin-right: $uni-spacing-row-base;
  }

  &__pinyin {
    font-size: $uni-font-size-base;
    color: $uni-text-color-grey;
  }

  &__meta {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: $uni-spacing-row-sm;
    margin-bottom: $uni-spacing-col-base;
  }

  &__section {
    margin-bottom: $uni-spacing-col-base;
  }

  &__section-title {
    font-size: $uni-font-size-base;
    font-weight: 600;
    color: $uni-text-color;
    margin-bottom: $uni-spacing-row-sm;
    padding-left: $uni-spacing-row-sm;
    border-left: 6rpx solid $uni-color-primary;
  }

  &__section-content {
    font-size: $uni-font-size-base;
    color: $uni-text-color;
    line-height: 1.7;
  }

  &__contexts {
    display: flex;
    flex-direction: column;
    gap: $uni-spacing-row-sm;
  }

  &__context {
    display: flex;
    align-items: flex-start;
    padding: $uni-spacing-row-sm $uni-spacing-row-base;
    background-color: $uni-bg-color;
    border-radius: $uni-border-radius;
    border: 2rpx solid transparent;

    &--active {
      background-color: rgba(79, 70, 229, 0.08);
      border-color: rgba(79, 70, 229, 0.3);
    }
  }

  &__context-name {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
    flex-shrink: 0;
    margin-right: $uni-spacing-row-sm;
  }

  &__context--active &__context-name {
    color: $uni-color-primary;
    font-weight: 600;
  }

  &__context-meaning {
    font-size: $uni-font-size-sm;
    color: $uni-text-color;
    flex: 1;
    line-height: 1.6;
  }

  &__example {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
    line-height: 1.7;
    padding: $uni-spacing-row-sm $uni-spacing-row-base;
    background-color: $uni-bg-color;
    border-radius: $uni-border-radius;
    margin-bottom: $uni-spacing-row-sm;
  }

  &__related {
    display: flex;
    flex-wrap: wrap;
    gap: $uni-spacing-row-sm;
  }

  &__related-item {
    padding: $uni-spacing-row-sm $uni-spacing-row-base;
    background-color: rgba(79, 70, 229, 0.08);
    color: $uni-color-primary;
    border-radius: 999rpx;
    font-size: $uni-font-size-sm;

    &:active {
      opacity: 0.7;
    }
  }
}
</style>
