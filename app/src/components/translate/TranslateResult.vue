<template>
  <view class="translate-result">
    <!-- a) 对比展示区（SRS-094）：原文 vs 人话翻译，关键词高亮 -->
    <view class="translate-result__compare">
      <!-- 原文区 -->
      <view class="translate-result__original">
        <view class="translate-result__label">原文</view>
        <view class="translate-result__original-text">
          <text
            v-for="(seg, i) in originalSegments"
            :key="i"
            :class="{ 'translate-result__highlight': seg.highlight }"
            @click="seg.highlight && handleKeywordClick(seg.text)"
          >{{ seg.text }}</text>
        </view>
      </view>

      <!-- 视觉引导 -->
      <view class="translate-result__arrow">
        <text class="translate-result__arrow-text">↓ 翻译为</text>
      </view>

      <!-- 人话翻译区 -->
      <view class="translate-result__human">
        <view class="translate-result__label translate-result__label--primary">人话</view>
        <view class="translate-result__human-text">
          {{ translation || '翻译失败，请重试' }}
        </view>
        <view v-if="isSameText" class="translate-result__tip">
          该句已是普通人表达
        </view>
      </view>
    </view>

    <!-- b) 关键词解释区（SRS-099 来源标签 + SRS-100 多语境） -->
    <view v-if="keywords && keywords.length" class="translate-result__keywords">
      <view class="translate-result__block-title">
        <Key :size="16" color="#FE2C55" />
        <text>关键词解释</text>
      </view>
      <view
        v-for="(kw, idx) in keywords"
        :key="idx"
        class="translate-result__keyword"
      >
        <view class="translate-result__keyword-header">
          <text class="translate-result__keyword-word">{{ kw.word }}</text>
          <WordTag v-if="kw.category" type="category" :text="kw.category" />
        </view>

        <view class="translate-result__keyword-meaning">
          {{ kw.current_meaning || kw.meaning || kw.definition || '' }}
        </view>

        <!-- 多语境（SRS-100） -->
        <view
          v-if="kw.contexts && kw.contexts.length"
          class="translate-result__contexts"
        >
          <view
            v-for="(ctx, ci) in kw.contexts"
            :key="ci"
            class="translate-result__context"
            :class="{ 'translate-result__context--active': isCurrentContext(kw, ctx) }"
          >
            <text class="translate-result__context-name">{{ ctx.context }}</text>
            <text class="translate-result__context-meaning">{{ ctx.meaning }}</text>
          </view>
        </view>

        <!-- 来源标签（SRS-099） -->
        <view class="translate-result__keyword-footer">
          <SourceTag
            v-if="kw.source"
            :source="kw.source"
            :confidence="kw.confidence"
          />
        </view>

        <!-- 关键词风险信息（SRS-101） -->
        <RiskWarning
          v-if="kw.risk_level && kw.risk_level !== 'low'"
          :risk-level="kw.risk_level"
          :risk-types="kw.risk_types || []"
          :advice="kw.advice || ''"
        />
      </view>
    </view>

    <!-- c) 语境判断区 -->
    <view v-if="context" class="translate-result__block">
      <view class="translate-result__block-title">
        <Pin :size="16" color="#FE2C55" />
        <text>语境判断</text>
      </view>
      <view class="translate-result__block-content">{{ context }}</view>
    </view>

    <!-- d) 潜台词分析区 -->
    <SubtextSection v-if="subtext" :text="subtext" />

    <!-- e) + f) 行动建议 + 建议回复区 -->
    <SuggestionSection
      v-if="suggestion || suggestedReply"
      :suggestion="suggestion"
      :suggested-reply="suggestedReply"
      @copy="handleCopy"
    />

    <!-- g) 风险提示区（SRS-101，整体风险） -->
    <RiskWarning
      v-if="riskLevel && riskLevel !== 'low'"
      :risk-level="riskLevel"
      :risk-types="result.risk_types || []"
      :advice="result.advice || ''"
    />

    <!-- h) 相关推荐区 -->
    <view v-if="related && related.length" class="translate-result__block">
      <view class="translate-result__block-title">
        <Link2 :size="16" color="#FE2C55" />
        <text>相关推荐</text>
      </view>
      <view class="translate-result__related">
        <view
          v-for="(item, idx) in related"
          :key="idx"
          class="translate-result__related-item"
          @click="handleRelatedClick(item)"
        >
          {{ item.word || item.name || '' }}
        </view>
      </view>
    </view>

    <!-- i) 反馈按钮区（SRS-103）：三个按钮 -->
    <view class="translate-result__feedback">
      <view class="translate-result__feedback-title">解释质量反馈</view>
      <view class="translate-result__feedback-btns">
        <view
          v-for="btn in feedbackBtns"
          :key="btn.type"
          class="translate-result__feedback-btn"
          :class="{
            'translate-result__feedback-btn--active': feedbackType === btn.type,
            'translate-result__feedback-btn--disabled': feedbackType && feedbackType !== btn.type
          }"
          @click="handleFeedback(btn.type)"
        >
          {{ btn.label }}
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Key, Pin, Link2 } from 'lucide-vue-next'
import WordTag from '../word/WordTag.vue'
import SourceTag from '../common/SourceTag.vue'
import RiskWarning from '../common/RiskWarning.vue'
import SubtextSection from './SubtextSection.vue'
import SuggestionSection from './SuggestionSection.vue'

const props = defineProps({
  // 翻译结果对象
  result: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['keywordClick', 'relatedClick', 'feedback', 'copy'])

// 原文（兼容 original / text 字段）
const original = computed(() => {
  return props.result.original || props.result.text || ''
})

// 人话翻译
const translation = computed(() => {
  return props.result.translation || ''
})

// 关键词列表
const keywords = computed(() => {
  return props.result.keywords || []
})

// 语境判断
const context = computed(() => {
  return props.result.context || ''
})

// 潜台词
const subtext = computed(() => {
  return props.result.subtext || ''
})

// 行动建议
const suggestion = computed(() => {
  return props.result.suggestion || ''
})

// 建议回复（兼容 suggested_reply / suggestedReply）
const suggestedReply = computed(() => {
  return props.result.suggested_reply || props.result.suggestedReply || ''
})

// 整体风险等级（兼容 risk / risk_level）
const riskLevel = computed(() => {
  return props.result.risk_level || props.result.risk || ''
})

// 相关推荐
const related = computed(() => {
  return props.result.related || []
})

// 原文与翻译是否相同
const isSameText = computed(() => {
  return original.value && translation.value && original.value === translation.value
})

// 反馈按钮配置
const feedbackBtns = [
  { type: 'accurate', label: '解释准确' },
  { type: 'inaccurate', label: '解释不准' },
  { type: 'outdated', label: '这个词过时了' }
]

// 当前已选反馈类型（不可重复反馈）
const feedbackType = ref('')

// 原文按关键词拆分，用于高亮展示
const originalSegments = computed(() => {
  return highlightText(original.value, keywords.value)
})

/**
 * 将原文按命中关键词拆分为段落数组
 * @param {string} text 原文
 * @param {Array} kws 关键词列表
 * @returns {Array<{text: string, highlight: boolean}>}
 */
function highlightText(text, kws) {
  if (!text) return []
  if (!kws || !kws.length) return [{ text, highlight: false }]
  // 提取关键词词面
  const words = kws
    .map((k) => (typeof k === 'string' ? k : k.word))
    .filter(Boolean)
  if (!words.length) return [{ text, highlight: false }]
  // 按长度降序，避免短词先匹配破坏长词
  words.sort((a, b) => b.length - a.length)
  // 转义正则特殊字符
  const escaped = words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
  const re = new RegExp(`(${escaped.join('|')})`, 'g')
  const parts = text.split(re).filter((p) => p !== '')
  return parts.map((p) => ({
    text: p,
    highlight: words.includes(p)
  }))
}

// 是否当前语境
function isCurrentContext(kw, ctx) {
  const current = kw.current_context
  if (!current) return false
  return ctx.context === current
}

// 点击原文中高亮的关键词
function handleKeywordClick(word) {
  emit('keywordClick', word)
}

// 点击相关推荐
function handleRelatedClick(item) {
  emit('relatedClick', item)
}

// 复制建议回复
function handleCopy(text) {
  emit('copy', text)
}

// 反馈点击（已反馈则拦截）
function handleFeedback(type) {
  if (feedbackType.value) return
  feedbackType.value = type
  uni.showToast({
    title: '感谢反馈',
    icon: 'success'
  })
  emit('feedback', type)
}
</script>

<style lang="scss" scoped>
.translate-result {
  // 对比展示区
  &__compare {
    background-color: $bg-card;
    border-radius: 12px;
    box-shadow: $shadow-xs;
    padding: 16px;
    margin-bottom: 8px;
  }

  &__original {
    margin-bottom: 12px;
  }

  &__label {
    display: inline-block;
    font-size: 13px;
    color: $text-secondary;
    background-color: $bg-sunken;
    padding: 2px 12px;
    border-radius: 9999px;
    margin-bottom: 12px;

    &--primary {
      color: $color-primary;
      background-color: rgba(254, 44, 85, 0.1);
    }
  }

  &__original-text {
    font-size: 14px;
    color: $text-primary;
    line-height: 1.7;
  }

  &__highlight {
    color: $color-primary;
    font-weight: 600;
  }

  &__arrow {
    display: flex;
    justify-content: center;
    margin: 12px 0;
  }

  &__arrow-text {
    font-size: 13px;
    color: $text-secondary;
  }

  &__human {
    background-color: rgba(254, 44, 85, 0.04);
    border-radius: 12px;
    padding: 16px;
  }

  &__human-text {
    font-size: 16px;
    color: $text-primary;
    line-height: 1.7;
    font-weight: 500;
  }

  &__tip {
    margin-top: 12px;
    font-size: 13px;
    color: $color-success;
  }

  // 关键词解释区
  &__keywords {
    background-color: $bg-card;
    border-radius: 12px;
    box-shadow: $shadow-xs;
    padding: 16px;
    margin-bottom: 8px;
  }

  &__keyword {
    padding: 12px 0;
    border-bottom: 1px solid $border-color-light;

    &:last-child {
      border-bottom: none;
    }
  }

  &__keyword-header {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 12px;
  }

  &__keyword-word {
    font-size: 16px;
    font-weight: 600;
    color: $color-primary;
  }

  &__keyword-meaning {
    font-size: 14px;
    color: $text-primary;
    line-height: 1.6;
    margin-bottom: 12px;
  }

  &__contexts {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 12px;
  }

  &__context {
    display: flex;
    align-items: flex-start;
    padding: 12px 16px;
    background-color: $bg-sunken;
    border-radius: 12px;
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
    margin-right: 12px;
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

  &__keyword-footer {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 12px;
  }

  // 通用区块
  &__block {
    background-color: $bg-card;
    border-radius: 12px;
    box-shadow: $shadow-xs;
    padding: 16px;
    margin-bottom: 8px;
  }

  &__block-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: 12px;
  }

  &__block-content {
    font-size: 14px;
    color: $text-primary;
    line-height: 1.7;
  }

  // 相关推荐
  &__related {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }

  &__related-item {
    padding: 12px 16px;
    background-color: rgba(254, 44, 85, 0.08);
    color: $color-primary;
    border-radius: 9999px;
    font-size: 13px;

    &:active {
      opacity: 0.7;
    }
  }

  // 反馈按钮区
  &__feedback {
    background-color: $bg-card;
    border-radius: 12px;
    box-shadow: $shadow-xs;
    padding: 16px;
    margin-top: 8px;
  }

  &__feedback-title {
    font-size: 13px;
    color: $text-secondary;
    margin-bottom: 12px;
  }

  &__feedback-btns {
    display: flex;
    gap: 12px;
  }

  &__feedback-btn {
    flex: 1;
    text-align: center;
    padding: 12px 0;
    border-radius: 12px;
    font-size: 13px;
    background-color: $bg-sunken;
    color: $text-primary;

    &--active {
      background-color: $color-primary;
      color: #FFFFFF;
    }

    &--disabled {
      opacity: 0.5;
    }

    &:active {
      opacity: 0.8;
    }
  }
}
</style>
