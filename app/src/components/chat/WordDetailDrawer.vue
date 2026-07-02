<template>
  <view v-if="showMask" class="word-drawer-mask" @click="handleClose"></view>
  <view class="word-drawer" :class="{ 'word-drawer--open': open }">
    <!-- 加载中 -->
    <view v-if="loading" class="word-drawer__loading">
      <text>加载中...</text>
    </view>

    <!-- 内容 -->
    <scroll-view v-else-if="detail" scroll-y class="word-drawer__scroll">
      <!-- 头部 -->
      <view class="word-drawer__header">
        <view class="word-drawer__title-row">
          <text class="word-drawer__word">{{ detail.word }}</text>
          <text v-if="detail.pinyin" class="word-drawer__pinyin">{{ detail.pinyin }}</text>
        </view>
        <view class="word-drawer__meta">
          <view v-if="detail.category_name" class="word-drawer__tag">{{ detail.category_name }}</view>
          <view v-if="riskLevelText" class="word-drawer__tag" :class="`word-drawer__tag--${detail.risk_level}`">{{ riskLevelText }}</view>
        </view>
        <view class="word-drawer__close" @click="handleClose">
          <X :size="20" color="#9CA3AF" />
        </view>
      </view>

      <!-- 释义 -->
      <view class="word-drawer__section">
        <view class="word-drawer__section-title">
          <BookOpen :size="14" color="#9CA3AF" />
          <text>释义</text>
        </view>
        <view class="word-drawer__section-body">{{ detail.definition || detail.meaning || '' }}</view>
      </view>

      <!-- 词源 -->
      <view v-if="detail.origin" class="word-drawer__section">
        <view class="word-drawer__section-title">
          <Sparkles :size="14" color="#9CA3AF" />
          <text>词源</text>
        </view>
        <view class="word-drawer__section-body">{{ detail.origin }}</view>
      </view>

      <!-- 出处/示例 -->
      <view v-if="detail.example" class="word-drawer__section">
        <view class="word-drawer__section-title">
          <Quote :size="14" color="#9CA3AF" />
          <text>出处/示例</text>
        </view>
        <view class="word-drawer__section-body word-drawer__section-body--quote">{{ detail.example }}</view>
      </view>

      <!-- 多语境 -->
      <view v-if="detail.contexts && detail.contexts.length" class="word-drawer__section">
        <view class="word-drawer__section-title">
          <Layers :size="14" color="#9CA3AF" />
          <text>多语境释义</text>
        </view>
        <view v-for="ctx in detail.contexts" :key="ctx.id" class="word-drawer__ctx-item">
          <text class="word-drawer__ctx-name">{{ ctx.context_name }}</text>
          <text class="word-drawer__ctx-meaning">{{ ctx.meaning }}</text>
        </view>
      </view>

      <!-- 演化历程 -->
      <view v-if="detail.evolutions && detail.evolutions.length" class="word-drawer__section">
        <view class="word-drawer__section-title">
          <TrendingUp :size="14" color="#9CA3AF" />
          <text>演化历程</text>
        </view>
        <view class="word-drawer__timeline">
          <view v-for="ev in detail.evolutions" :key="ev.id" class="word-drawer__timeline-item">
            <view class="word-drawer__timeline-dot"></view>
            <view class="word-drawer__timeline-content">
              <text class="word-drawer__timeline-period">{{ ev.period }}</text>
              <text class="word-drawer__timeline-meaning">{{ ev.meaning }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 相关场景 -->
      <view v-if="detail.scenes && detail.scenes.length" class="word-drawer__section">
        <view class="word-drawer__section-title">
          <Compass :size="14" color="#9CA3AF" />
          <text>相关场景</text>
        </view>
        <view class="word-drawer__scene-list">
          <view v-for="sc in detail.scenes" :key="sc.id" class="word-drawer__scene-item">
            <text class="word-drawer__scene-name">{{ sc.scene_name }}</text>
            <text v-if="sc.example" class="word-drawer__scene-example">{{ sc.example }}</text>
          </view>
        </view>
      </view>

      <!-- 别名 -->
      <view v-if="detail.aliases && detail.aliases.length" class="word-drawer__section">
        <view class="word-drawer__section-title">
          <Tag :size="14" color="#9CA3AF" />
          <text>别名</text>
        </view>
        <view class="word-drawer__tags">
          <view v-for="(alias, idx) in detail.aliases" :key="idx" class="word-drawer__chip">{{ alias }}</view>
        </view>
      </view>

      <!-- 风险提示 -->
      <view v-if="detail.risk_level && detail.risk_level !== 'low'" class="word-drawer__section">
        <view class="word-drawer__section-title">
          <ShieldAlert :size="14" :color="riskColor" />
          <text :style="{ color: riskColor }">风险提示</text>
        </view>
        <view v-if="detail.risk_types && detail.risk_types.length" class="word-drawer__tags">
          <view v-for="(rt, idx) in detail.risk_types" :key="idx" class="word-drawer__chip" :class="`word-drawer__chip--${detail.risk_level}`">{{ rt }}</view>
        </view>
        <view v-if="detail.risk_advice" class="word-drawer__section-body">{{ detail.risk_advice }}</view>
      </view>

      <!-- 相关词条 -->
      <view v-if="detail.related && detail.related.length" class="word-drawer__section">
        <view class="word-drawer__section-title">
          <Hash :size="14" color="#9CA3AF" />
          <text>相关词条</text>
        </view>
        <view class="word-drawer__related-list">
          <view
            v-for="item in detail.related"
            :key="item.word_id"
            class="word-drawer__related-item"
            @click="handleRelatedClick(item)"
          >
            <text class="word-drawer__related-word">{{ item.word }}</text>
            <text class="word-drawer__related-meaning">{{ item.meaning }}</text>
          </view>
        </view>
      </view>

      <!-- 使用频率 -->
      <view class="word-drawer__section">
        <view class="word-drawer__section-title">
          <BarChart :size="14" color="#9CA3AF" />
          <text>使用频率</text>
        </view>
        <view class="word-drawer__usage">
          <view class="word-drawer__usage-num">
            <text class="word-drawer__usage-value">{{ detail.view_count || 0 }}</text>
            <text class="word-drawer__usage-label">次浏览</text>
          </view>
          <view class="word-drawer__usage-meta">
            <text>收藏 {{ detail.favorite_count || 0 }} 次</text>
            <text>投票 {{ detail.vote_count || 0 }} 分</text>
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- 空状态 -->
    <view v-else class="word-drawer__empty">
      <text>未找到词条</text>
    </view>

    <!-- 底部操作栏 -->
    <view v-if="detail" class="word-drawer__footer">
      <view class="word-drawer__footer-btn" @click="handleFavorite">
        <Heart
          :size="16"
          :color="detail.is_favorited ? '#FE2C55' : '#6B7280'"
          :fill="detail.is_favorited ? '#FE2C55' : 'none'"
        />
        <text class="word-drawer__footer-btn-text">{{ detail.is_favorited ? '已收藏' : '收藏' }}</text>
      </view>
      <view class="word-drawer__footer-btn word-drawer__footer-btn--primary" @click="handleCorrect">
        <AlertCircle :size="16" color="#FFFFFF" />
        <text class="word-drawer__footer-btn-text word-drawer__footer-btn-text--white">纠错</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import {
  X, BookOpen, Quote, Layers, Tag, ShieldAlert, Hash,
  Heart, AlertCircle, Sparkles, TrendingUp, Compass, BarChart
} from 'lucide-vue-next'
import * as wordApi from '@/api/word'
import * as correctionApi from '@/api/correction'
import { useUserStore } from '@/store/modules/user'

const props = defineProps({
  open: { type: Boolean, default: false },
  wordId: { type: Number, default: null }
})
const emit = defineEmits(['update:open', 'favorite', 'correct'])

const userStore = useUserStore()
const detail = ref(null)
const loading = ref(false)
const showMask = ref(false)

const riskLevelText = computed(() => {
  const r = detail.value?.risk_level
  if (r === 'high') return '高风险'
  if (r === 'medium') return '中风险'
  return ''
})

const riskColor = computed(() => {
  const r = detail.value?.risk_level
  if (r === 'high') return '#EF4444'
  if (r === 'medium') return '#F59E0B'
  return '#10B981'
})

// 监听 wordId 变化拉取详情
watch(
  () => props.wordId,
  async (id) => {
    if (id && props.open) {
      await fetchDetail(id)
    }
  }
)

// 监听 open 变化
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      showMask.value = true
      if (props.wordId && !detail.value) {
        fetchDetail(props.wordId)
      }
    } else {
      // 延迟隐藏 mask，等动画结束
      setTimeout(() => {
        showMask.value = false
        detail.value = null
      }, 300)
    }
  }
)

async function fetchDetail(id) {
  loading.value = true
  detail.value = null
  try {
    detail.value = await wordApi.getWordDetail(id)
  } catch (err) {
    console.error('获取词条详情失败', err)
  } finally {
    loading.value = false
  }
}

function handleClose() {
  emit('update:open', false)
}

async function handleFavorite() {
  if (!detail.value) return
  const id = detail.value.id
  try {
    await userStore.toggleFavorite(id)
    detail.value.is_favorited = userStore.isFavorited(id)
    uni.showToast({
      title: detail.value.is_favorited ? '已收藏' : '已取消收藏',
      icon: 'none'
    })
    emit('favorite', detail.value)
  } catch (err) {
    uni.showToast({ title: '收藏失败', icon: 'none' })
  }
}

function handleCorrect() {
  if (!detail.value) return
  const wordId = detail.value.id
  const wordText = detail.value.word
  const correctionTypes = [
    { label: '释义错误', value: 'meaning_wrong' },
    { label: '例句/出处错误', value: 'example_wrong' },
    { label: '拼音错误', value: 'pinyin_wrong' },
    { label: '分类错误', value: 'category_wrong' },
    { label: '风险标注错误', value: 'risk_wrong' },
    { label: '已过时', value: 'outdated' },
    { label: '其他', value: 'other' }
  ]
  uni.showActionSheet({
    itemList: correctionTypes.map(t => t.label),
    success: (res) => {
      const type = correctionTypes[res.tapIndex].value
      uni.showModal({
        title: `纠错：${wordText}`,
        editable: true,
        placeholderText: '请描述正确的内容或问题',
        success: (r) => {
          if (r.confirm && r.content) {
            correctionApi.submitCorrection({
              word_id: wordId,
              type,
              content: r.content
            }).then(() => {
              uni.showToast({ title: '已提交，感谢纠错', icon: 'success' })
              emit('correct', { word_id: wordId, type, content: r.content })
            }).catch(() => {
              uni.showToast({ title: '提交失败', icon: 'none' })
            })
          }
        }
      })
    }
  })
}

function handleRelatedClick(item) {
  if (item.word_id) {
    // 切换抽屉内容到相关词条
    fetchDetail(item.word_id)
    emit('update:wordId', item.word_id)
  }
}
</script>

<style lang="scss" scoped>
.word-drawer-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.4);
  z-index: 99;
}

.word-drawer {
  position: fixed;
  top: 0;
  right: 0;
  width: 85%;
  max-width: 360px;
  height: 100vh;
  background-color: $bg-page;
  z-index: 100;
  transform: translateX(100%);
  transition: transform 0.3s ease;
  display: flex;
  flex-direction: column;

  &--open {
    transform: translateX(0);
  }

  &__loading,
  &__empty {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    color: $text-secondary;
    font-size: 14px;
  }

  &__scroll {
    flex: 1;
    padding: 0 16px 100px;
  }

  &__header {
    position: relative;
    padding: 20px 16px 16px;
    margin-bottom: 16px;
    border-bottom: 1px solid $border-color-light;
    background-image: linear-gradient(135deg, rgba(254, 44, 85, 0.04), transparent);
  }

  &__title-row {
    display: flex;
    align-items: baseline;
    gap: 8px;
    padding-right: 32px;
  }

  &__word {
    font-size: 22px;
    font-weight: 700;
    color: $text-primary;
  }

  &__pinyin {
    font-size: 13px;
    color: $text-tertiary;
  }

  &__meta {
    display: flex;
    gap: 6px;
    margin-top: 10px;
  }

  &__tag {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 4px;
    background-color: $bg-sunken;
    color: $text-secondary;

    &--medium {
      background-color: rgba(245, 158, 11, 0.12);
      color: $color-warning;
    }

    &--high {
      background-color: rgba(239, 68, 68, 0.12);
      color: #EF4444;
    }
  }

  &__close {
    position: absolute;
    top: 20px;
    right: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__section {
    background-color: $bg-card;
    border-radius: 12px;
    padding: 14px;
    box-shadow: $shadow-xs;
    margin-bottom: 12px;
  }

  &__section-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 600;
    color: $text-tertiary;
    margin-bottom: 10px;
  }

  &__section-body {
    font-size: 14px;
    color: $text-primary;
    line-height: 1.7;

    &--quote {
      background-color: $bg-sunken;
      border-radius: 8px;
      padding: 12px;
      font-size: 13px;
      color: $text-secondary;
    }
  }

  &__ctx-item {
    padding: 10px 0;
    border-bottom: 1px solid $border-color-light;

    &:last-child {
      border-bottom: none;
    }
  }

  &__ctx-name {
    display: block;
    font-size: 13px;
    font-weight: 600;
    color: $color-primary;
    margin-bottom: 4px;
  }

  &__ctx-meaning {
    display: block;
    font-size: 13px;
    color: $text-secondary;
    line-height: 1.5;
  }

  &__tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  &__chip {
    font-size: 12px;
    padding: 4px 10px;
    border-radius: 4px;
    background-color: $bg-sunken;
    color: $text-secondary;

    &--medium {
      background-color: rgba(245, 158, 11, 0.12);
      color: $color-warning;
    }

    &--high {
      background-color: rgba(239, 68, 68, 0.12);
      color: #EF4444;
    }
  }

  &__related-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  &__related-item {
    padding: 10px 12px;
    background-color: $bg-card;
    border-radius: 8px;
    box-shadow: $shadow-xs;
  }

  &__related-word {
    display: block;
    font-size: 13px;
    font-weight: 600;
    color: $color-primary;
  }

  &__related-meaning {
    display: block;
    font-size: 12px;
    color: $text-secondary;
    margin-top: 2px;
    line-height: 1.4;
  }

  &__stats {
    display: flex;
    gap: 16px;
    padding: 16px 0;
    font-size: 12px;
    color: $text-tertiary;
    border-top: 1px solid $border-color-light;
  }

  /* ============ 演化历程时间线 ============ */
  &__timeline {
    position: relative;
    padding-left: 16px;

    &::before {
      content: '';
      position: absolute;
      left: 3px;
      top: 8px;
      bottom: 8px;
      width: 1px;
      background-color: $border-color-light;
    }
  }

  &__timeline-item {
    position: relative;
    padding: 8px 0;

    &:not(:last-child) {
      border-bottom: 1px solid $border-color-light;
    }
  }

  &__timeline-dot {
    position: absolute;
    left: -16px;
    top: 14px;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: $color-primary;
    border: 2px solid $bg-card;
  }

  &__timeline-content {
    padding-left: 4px;
  }

  &__timeline-period {
    display: block;
    font-size: 12px;
    color: $color-primary;
    font-weight: 600;
    margin-bottom: 4px;
  }

  &__timeline-meaning {
    display: block;
    font-size: 13px;
    color: $text-secondary;
    line-height: 1.5;
  }

  /* ============ 相关场景 ============ */
  &__scene-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  &__scene-item {
    padding: 10px 12px;
    background-color: $bg-sunken;
    border-radius: 8px;
  }

  &__scene-name {
    display: block;
    font-size: 13px;
    font-weight: 600;
    color: $color-primary;
    margin-bottom: 4px;
  }

  &__scene-example {
    display: block;
    font-size: 12px;
    color: $text-secondary;
    line-height: 1.5;
  }

  /* ============ 使用频率 ============ */
  &__usage {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  &__usage-num {
    display: flex;
    align-items: baseline;
    gap: 4px;
  }

  &__usage-value {
    font-size: 24px;
    font-weight: 700;
    color: $color-primary;
  }

  &__usage-label {
    font-size: 12px;
    color: $text-tertiary;
  }

  &__usage-meta {
    display: flex;
    gap: 12px;
    font-size: 12px;
    color: $text-secondary;
  }

  &__footer {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 56px;
    background-color: $bg-card;
    border-top: 1px solid $border-color-light;
    display: flex;
    align-items: center;
    padding: 0 16px;
    gap: 12px;
  }

  &__footer-btn {
    flex: 1;
    height: 36px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    background-color: $bg-sunken;

    &--primary {
      background-color: $color-primary;
    }
  }

  &__footer-btn-text {
    font-size: 13px;
    color: $text-primary;

    &--white {
      color: #FFFFFF;
    }
  }
}
</style>
