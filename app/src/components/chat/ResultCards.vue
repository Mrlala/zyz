<template>
  <view class="result-cards">
    <!-- Tier1: 人话翻译 Hero Card -->
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
        <view class="hero-card__action" @click="handleFavorite">
          <Heart :size="14" color="#6B7280" />
          <text class="hero-card__action-text">收藏</text>
        </view>
        <view class="hero-card__action" @click="handleFollowUp">
          <MessageCircle :size="14" color="#6B7280" />
          <text class="hero-card__action-text">继续追问</text>
        </view>
      </view>
    </view>

    <!-- Tier2: 命中词条 -->
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
          <text class="keyword-list__word" @click="emit('keywordClick', kw.word)">{{ kw.word }}</text>
          <text class="keyword-list__meaning">{{ kw.current_meaning || kw.meaning || kw.definition || '' }}</text>
        </view>
      </view>
    </view>

    <!-- Tier3: 三小卡 -->
    <view class="tier3-cards">
      <!-- 潜台词 -->
      <view v-if="subtext" class="tier3-card">
        <view class="tier3-card__header">
          <Lightbulb :size="16" color="#FE2C55" />
          <text class="tier3-card__title">潜台词</text>
        </view>
        <view class="tier3-card__body">{{ subtext }}</view>
      </view>

      <!-- 建议回复 -->
      <view v-if="suggestedReply || suggestion" class="tier3-card">
        <view class="tier3-card__header">
          <MessageCircle :size="16" color="#FE2C55" />
          <text class="tier3-card__title">建议回复</text>
        </view>
        <view class="tier3-card__quote">
          <text class="tier3-card__quote-text">{{ suggestedReply || suggestion }}</text>
        </view>
      </view>

      <!-- 风险提示 -->
      <view v-if="riskLevel && riskLevel !== 'low'" class="tier3-card tier3-card--risk">
        <view class="tier3-card__header">
          <ShieldAlert :size="16" :color="riskColor" />
          <text class="tier3-card__title" :style="{ color: riskColor }">风险提示</text>
        </view>
        <view class="tier3-card__body">{{ result.advice || result.risk_note || '请注意使用场景' }}</view>
      </view>
    </view>

    <!-- Tier4: 标签行 -->
    <view v-if="context || (related && related.length)" class="tag-rows">
      <!-- 语境判断 -->
      <view v-if="context" class="tag-row">
        <view class="tag-row__header">
          <MapPin :size="14" color="#9CA3AF" />
          <text class="tag-row__title">语境判断</text>
        </view>
        <view class="tag-row__tags">
          <view class="tag-row__tag">{{ context }}</view>
        </view>
      </view>

      <!-- 相关词条 -->
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
    </view>

    <!-- 反馈按钮 -->
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
  Lightbulb, ShieldAlert, MapPin, Hash, ThumbsUp, ThumbsDown
} from 'lucide-vue-next'

const props = defineProps({
  result: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['keywordClick', 'relatedClick', 'copy', 'feedback'])

const translation = computed(() => props.result.translation || '')
const keywords = computed(() => props.result.keywords || [])
const context = computed(() => props.result.context || '')
const subtext = computed(() => props.result.subtext || '')
const suggestion = computed(() => props.result.suggestion || '')
const suggestedReply = computed(() => props.result.suggested_reply || props.result.suggestedReply || '')
const riskLevel = computed(() => props.result.risk_level || props.result.risk || '')
const related = computed(() => props.result.related || [])

const modeLabel = computed(() => {
  const m = props.result.mode
  if (m === 'deep') return '深度解析'
  if (m === 'dict') return '词典模式'
  return '快速解析'
})

const riskColor = computed(() => {
  if (riskLevel.value === 'high') return '#EF4444'
  if (riskLevel.value === 'medium') return '#F59E0B'
  return '#10B981'
})

function handleCopy(text) {
  emit('copy', text)
}

function handleFavorite() {
  uni.showToast({ title: '已收藏', icon: 'success' })
}

function handleFollowUp() {
  uni.showToast({ title: '继续追问', icon: 'none' })
}

function handleFeedback(type) {
  emit('feedback', type)
  uni.showToast({ title: '感谢反馈', icon: 'success' })
}
</script>

<style lang="scss" scoped>
.result-cards {
  display: flex;
  flex-direction: column;
}

/* ============ Tier1: Hero Card ============ */
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
  }
}

/* ============ Tier2: 命中词条 ============ */
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

  &__item {
    padding: 10px 0;
    border-bottom: 1px solid $border-color-light;

    &--last {
      border-bottom: none;
    }
  }

  &__word {
    display: block;
    font-size: 14px;
    font-weight: 600;
    color: $color-primary;
    line-height: 1.4;
  }

  &__meaning {
    display: block;
    font-size: 13px;
    color: $text-secondary;
    line-height: 1.5;
    margin-top: 4px;
  }
}

/* ============ Tier3: 三小卡 ============ */
.tier3-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 16px;
}

.tier3-card {
  background-color: $bg-card;
  border-radius: 12px;
  padding: 14px;
  box-shadow: $shadow-xs;

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

/* ============ Tier4: 标签行 ============ */
.tag-rows {
  margin-top: 16px;
}

.tag-row {
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
    margin-bottom: 16px;
  }

  &__tag {
    background-color: $bg-sunken;
    color: $text-secondary;
    font-size: 13px;
    border-radius: 6px;
    padding: 4px 10px;

    &--link {
      cursor: pointer;
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
