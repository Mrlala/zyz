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

    <!-- 出处区 -->
    <view v-if="origin" class="word-detail__section">
      <view class="word-detail__section-title">出处</view>
      <view class="word-detail__section-content">{{ origin }}</view>
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

// 出处（来源背景）
const origin = computed(() => props.word.origin || '')

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
    margin-bottom: 8px;
  }

  &__word {
    font-size: 18px;
    font-weight: 700;
    color: $text-primary;
    margin-right: 16px;
  }

  &__pinyin {
    font-size: 14px;
    color: $text-secondary;
  }

  &__meta {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
  }

  &__section {
    margin-bottom: 12px;
  }

  &__section-title {
    font-size: 14px;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: 8px;
    padding-left: 8px;
    border-left: 3px solid $color-primary;
  }

  &__section-content {
    font-size: 14px;
    color: $text-primary;
    line-height: 1.7;
  }

  &__contexts {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  &__context {
    display: flex;
    align-items: flex-start;
    padding: 8px 16px;
    background-color: $bg-sunken;
    border-radius: 10px;
    border: 1px solid transparent;

    &--active {
      background-color: rgba(254, 44, 85, 0.08);
      border-color: rgba(254, 44, 85, 0.3);
    }
  }

  &__context-name {
    font-size: 13px;
    color: $text-secondary;
    flex-shrink: 0;
    margin-right: 8px;
  }

  &__context--active &__context-name {
    color: $color-primary;
    font-weight: 600;
  }

  &__context-meaning {
    font-size: 13px;
    color: $text-primary;
    flex: 1;
    line-height: 1.6;
  }

  &__example {
    font-size: 13px;
    color: $text-secondary;
    line-height: 1.7;
    padding: 8px 16px;
    background-color: $bg-sunken;
    border-radius: 10px;
    margin-bottom: 8px;
  }

  &__related {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  &__related-item {
    padding: 8px 16px;
    background-color: rgba(254, 44, 85, 0.08);
    color: $color-primary;
    border-radius: 9999px;
    font-size: 13px;

    &:active {
      opacity: 0.7;
    }
  }
}
</style>
