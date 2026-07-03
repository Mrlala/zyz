<template>
  <view class="result-cards">
    <!-- 1. 人话翻译 Hero Card（只保留复制按钮） -->
    <view v-if="translation" class="hero-card">
      <view class="hero-card__header">
        <view class="hero-card__title-wrap">
          <Languages :size="16" color="#FE2C55" />
          <text class="hero-card__title">人话翻译</text>
        </view>
        <view class="hero-card__tag">{{ modeLabel }}</view>
      </view>
      <view class="hero-card__body">{{ translation }}</view>
      <view class="hero-card__actions">
        <view class="hero-card__action" @click="handleCopy(translation)">
          <Copy :size="14" color="#6B7280" />
          <text class="hero-card__action-text">复制</text>
        </view>
        <view class="hero-card__action" @click="handleShare">
          <Share2 :size="14" color="#6B7280" />
          <text class="hero-card__action-text">分享</text>
        </view>
        <view class="hero-card__action" @click="handleFavorite">
          <Heart
            :size="14"
            :color="isFavorited ? '#FE2C55' : '#6B7280'"
            :fill="isFavorited ? '#FE2C55' : 'none'"
          />
          <text class="hero-card__action-text" :class="{ 'hero-card__action-text--active': isFavorited }">
            {{ isFavorited ? '已收藏' : '收藏' }}
          </text>
        </view>
      </view>
    </view>

    <!-- 2. 潜台词卡片（有 subtext 时显示） -->
    <view v-if="subtext" class="tier3-card">
      <view class="tier3-card__header">
        <Lightbulb :size="16" color="#FE2C55" />
        <text class="tier3-card__title">潜台词</text>
      </view>
      <view class="tier3-card__body">{{ subtext }}</view>
    </view>

    <!-- 3. 建议回复卡片（仅句子才显示） -->
    <view v-if="showSuggestion" class="tier3-card">
      <view class="tier3-card__header">
        <MessageCircle :size="16" color="#FE2C55" />
        <text class="tier3-card__title">建议回复</text>
      </view>
      <view class="tier3-card__quote">
        <text class="tier3-card__quote-text">{{ suggestedReply || suggestion }}</text>
      </view>
    </view>

    <!-- 4. 命中词条（含收藏 + 纠错按钮） -->
    <view v-if="keywords && keywords.length" class="keyword-list">
      <view class="keyword-list__header">
        <Bookmark :size="14" color="#9CA3AF" />
        <text class="keyword-list__title">命中词条</text>
      </view>
      <view class="keyword-list__items">
        <view
          v-for="(kw, idx) in keywords"
          :key="idx"
          class="keyword-list__item"
          :class="{ 'keyword-list__item--last': idx === keywords.length - 1 }"
        >
          <view class="keyword-list__main" @click="emit('keywordClick', kw)">
            <view class="keyword-list__word-row">
              <text class="keyword-list__word">{{ kw.word }}</text>
              <view v-if="kw.source === 'ai_temp'" class="keyword-list__ai-badge">AI</view>
            </view>
            <text class="keyword-list__meaning">{{ kw.current_meaning || kw.meaning || kw.definition || '' }}</text>
          </view>
          <view class="keyword-list__actions">
            <view class="keyword-list__btn" @click.stop="emit('keywordFavorite', kw)">
              <Heart
                :size="16"
                :color="kw.is_favorited ? '#FE2C55' : '#D1D5DB'"
                :fill="kw.is_favorited ? '#FE2C55' : 'none'"
              />
            </view>
            <view v-if="kw.source === 'ai_temp'" class="keyword-list__btn keyword-list__btn--submit" @click.stop="emit('keywordSubmit', kw)">
              <Send :size="16" color="#FE2C55" />
            </view>
            <view v-else class="keyword-list__btn" @click.stop="emit('keywordCorrect', kw)">
              <AlertCircle :size="16" color="#9CA3AF" />
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 5. 风险提示卡片（risk_level ≠ low 时显示） -->
    <view v-if="riskLevel && riskLevel !== 'low'" class="tier3-card tier3-card--risk">
      <view class="tier3-card__header">
        <ShieldAlert :size="16" :color="riskColor" />
        <text class="tier3-card__title" :style="{ color: riskColor }">风险提示</text>
      </view>
      <view class="tier3-card__body">{{ result.advice || result.risk_note || (result.risk && result.risk.advice) || '请注意使用场景' }}</view>
    </view>

    <!-- 6. 语境判断标签行 -->
    <view v-if="context" class="tag-row">
      <view class="tag-row__header">
        <MapPin :size="14" color="#9CA3AF" />
        <text class="tag-row__title">语境判断</text>
      </view>
      <view class="tag-row__tags">
        <view class="tag-row__tag">{{ context }}</view>
      </view>
    </view>

    <!-- 7. 相关词条标签行 -->
    <view v-if="related && related.length" class="tag-row">
      <view class="tag-row__header">
        <Hash :size="14" color="#9CA3AF" />
        <text class="tag-row__title">相关词条</text>
      </view>
      <view class="tag-row__tags">
        <view
          v-for="(item, idx) in related"
          :key="idx"
          class="tag-row__tag tag-row__tag--link"
          @click="emit('relatedClick', item)"
        >{{ item.word || item.name }}</view>
      </view>
    </view>

    <!-- 8. 反馈按钮行 -->
    <view class="feedback-row">
      <view class="feedback-row__btn" @click="handleFeedback('accurate')">
        <ThumbsUp :size="14" color="#9CA3AF" />
      </view>
      <view class="feedback-row__btn" @click="handleFeedback('inaccurate')">
        <ThumbsDown :size="14" color="#9CA3AF" />
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import {
  Languages, Copy, Heart, MessageCircle, Bookmark,
  Lightbulb, ShieldAlert, MapPin, Hash, ThumbsUp, ThumbsDown, AlertCircle, Share2, Send
} from 'lucide-vue-next'

const props = defineProps({
  result: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['keywordClick', 'relatedClick', 'copy', 'feedback', 'keywordFavorite', 'keywordCorrect', 'share', 'favorite'])

const translation = computed(() => props.result.translation || '')
const keywords = computed(() => props.result.keywords || [])
const context = computed(() => props.result.context || '')
const subtext = computed(() => props.result.subtext || '')
const suggestion = computed(() => props.result.suggestion || '')
const suggestedReply = computed(() => props.result.suggested_reply || props.result.suggestedReply || '')
const riskLevel = computed(() => props.result.risk_level || props.result.risk || (props.result.risk && props.result.risk.risk_level) || '')
const related = computed(() => props.result.related || [])
const isFavorited = computed(() => !!props.result.is_translation_favorited)

const modeLabel = computed(() => {
  const m = props.result.mode
  if (m === 'deep') return '深度解析'
  if (m === 'dict') return '词典模式'
  if (props.result.dict_only) return '词库命中'
  return '快速解析'
})

// 建议回复仅句子显示：输入文本长度 > 8 或包含标点/空格
const isSentence = computed(() => {
  const t = props.result.original_text || ''
  return t.length > 8 || /[，。！？\s,!.?]/.test(t)
})
const showSuggestion = computed(() => isSentence.value && (suggestedReply.value || suggestion.value))

const riskColor = computed(() => {
  if (riskLevel.value === 'high') return '#EF4444'
  if (riskLevel.value === 'medium') return '#F59E0B'
  return '#10B981'
})

function handleCopy(text) {
  emit('copy', text)
}

function handleShare() {
  emit('share', {
    translation: translation.value,
    original_text: props.result.original_text || '',
    keywords: keywords.value,
    context: context.value,
    subtext: subtext.value,
  })
}

function handleFavorite() {
  emit('favorite')
}

function handleFeedback(type) {
  emit('feedback', type)
}
</script>

<style lang="scss" scoped>
.result-cards {
  display: flex;
  flex-direction: column;
}

/* ============ Hero Card ============ */
.hero-card {
  background-color: $bg-card;
  border-radius: 16px;
  padding: 16px;
  box-shadow: $shadow-sm;
  background-image: linear-gradient(135deg, rgba(254, 44, 85, 0.03), rgba(37, 244, 238, 0.02));

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }

  &__title-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  &__title {
    font-size: 14px;
    font-weight: 600;
    color: $text-primary;
  }

  &__tag {
    font-size: 11px;
    color: $color-primary;
    background-color: rgba(254, 44, 85, 0.08);
    border-radius: 6px;
    padding: 2px 8px;
  }

  &__body {
    font-size: 15px;
    color: $text-primary;
    line-height: 1.7;
  }

  &__actions {
    display: flex;
    gap: 16px;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid $border-color-light;
  }

  &__action {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  &__action-text {
    font-size: 12px;
    color: $text-secondary;

    &--active {
      color: $primary;
    }
  }
}

/* ============ 潜台词/建议回复/风险 小卡 ============ */
.tier3-card {
  background-color: $bg-card;
  border-radius: 12px;
  padding: 14px;
  box-shadow: $shadow-xs;
  margin-top: 10px;

  &--risk {
    border-left: 3px solid $color-warning;
  }

  &__header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }

  &__title {
    font-size: 14px;
    font-weight: 600;
    color: $text-primary;
  }

  &__body {
    font-size: 13px;
    color: $text-secondary;
    line-height: 1.6;
  }

  &__quote {
    background-color: $bg-sunken;
    border-radius: 8px;
    padding: 10px;
  }

  &__quote-text {
    font-size: 13px;
    color: $text-primary;
    line-height: 1.6;
  }
}

/* ============ 命中词条 ============ */
.keyword-list {
  margin-top: 16px;

  &__header {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 10px;
  }

  &__title {
    font-size: 12px;
    font-weight: 600;
    color: $text-tertiary;
  }

  &__items {
    background-color: $bg-card;
    border-radius: 12px;
    padding: 0 14px;
    box-shadow: $shadow-xs;
  }

  &__item {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    padding: 12px 0;
    border-bottom: 1px solid $border-color-light;

    &--last {
      border-bottom: none;
    }
  }

  &__main {
    flex: 1;
    min-width: 0;
  }

  &__word-row {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  &__word {
    font-size: 14px;
    font-weight: 600;
    color: $color-primary;
    line-height: 1.4;
  }

  &__ai-badge {
    flex-shrink: 0;
    font-size: 10px;
    font-weight: 600;
    color: $color-warning;
    background-color: rgba(245, 158, 11, 0.12);
    border-radius: 4px;
    padding: 1px 5px;
    line-height: 1.4;
  }

  &__meaning {
    display: block;
    font-size: 13px;
    color: $text-secondary;
    line-height: 1.5;
    margin-top: 4px;
  }

  &__actions {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    gap: 4px;
    margin-left: 12px;
    padding-top: 2px;
  }

  &__btn {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 6px;

    &:active {
      background-color: $bg-sunken;
    }
  }
}

/* ============ 标签行（语境/相关） ============ */
.tag-row {
  margin-top: 16px;

  &__header {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 8px;
  }

  &__title {
    font-size: 12px;
    font-weight: 600;
    color: $text-tertiary;
  }

  &__tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  &__tag {
    background-color: $bg-sunken;
    color: $text-secondary;
    font-size: 13px;
    border-radius: 6px;
    padding: 4px 10px;

    &--link {
      color: $color-primary;
    }
  }
}

/* ============ 反馈按钮 ============ */
.feedback-row {
  display: flex;
  gap: 16px;
  margin-top: 20px;
  margin-bottom: 8px;

  &__btn {
    padding: 4px 8px;
    border-radius: 8px;
  }
}
</style>
