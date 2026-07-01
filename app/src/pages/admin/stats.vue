<template>
  <view class="stats-page">
    <!-- 顶部栏 -->
    <view class="top-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="top-bar__inner">
        <view class="top-bar__btn" @click="handleBack">
          <ArrowLeft :size="20" color="#6B7280" />
        </view>
        <text class="top-bar__title">数据统计</text>
        <view class="top-bar__btn" @click="fetchStats">
          <RefreshCw :size="18" color="#6B7280" />
        </view>
      </view>
    </view>
    <view class="top-bar-placeholder" :style="{ height: (statusBarHeight + 54) + 'px' }"></view>

    <!-- 加载中 -->
    <view v-if="loading" class="state-tip">
      <text class="state-tip__text">加载中...</text>
    </view>

    <!-- 权限不足 -->
    <view v-else-if="noPermission" class="state-tip">
      <text class="state-tip__text">需要管理员权限</text>
    </view>

    <template v-else>
      <!-- 核心指标网格 -->
      <view class="metric-grid">
        <view class="metric-card">
          <BookOpen :size="18" color="#FE2C55" />
          <text class="metric-card__num">{{ data.word_count || 0 }}</text>
          <text class="metric-card__label">词条总数</text>
        </view>
        <view class="metric-card">
          <Users :size="18" color="#25F4EE" />
          <text class="metric-card__num">{{ data.user_count || 0 }}</text>
          <text class="metric-card__label">用户总数</text>
        </view>
        <view class="metric-card">
          <Zap :size="18" color="#F59E0B" />
          <text class="metric-card__num">{{ data.translation_count_today || 0 }}</text>
          <text class="metric-card__label">今日翻译</text>
        </view>
        <view class="metric-card">
          <ClipboardList :size="18" color="#10B981" />
          <text class="metric-card__num">{{ data.submission_count_pending || 0 }}</text>
          <text class="metric-card__label">待审核提交</text>
        </view>
      </view>

      <!-- 待处理项 -->
      <text class="section-title">待处理事项</text>
      <view class="pending-card">
        <view class="pending-row" @click="goReview">
          <view class="pending-row__left">
            <ClipboardList :size="16" color="#6B7280" />
            <text class="pending-row__label">待审核提交</text>
          </view>
          <view class="pending-row__right">
            <text class="pending-row__num" :class="{ 'pending-row__num--active': data.submission_count_pending > 0 }">{{ data.submission_count_pending || 0 }}</text>
            <ChevronRight :size="16" color="#C0C4CC" />
          </view>
        </view>
        <view class="pending-divider"></view>
        <view class="pending-row">
          <view class="pending-row__left">
            <MessageSquare :size="16" color="#6B7280" />
            <text class="pending-row__label">待处理反馈</text>
          </view>
          <text class="pending-row__num" :class="{ 'pending-row__num--active': data.feedback_count_pending > 0 }">{{ data.feedback_count_pending || 0 }}</text>
        </view>
        <view class="pending-divider"></view>
        <view class="pending-row">
          <view class="pending-row__left">
            <Edit3 :size="16" color="#6B7280" />
            <text class="pending-row__label">待处理纠错</text>
          </view>
          <text class="pending-row__num" :class="{ 'pending-row__num--active': data.correction_count_pending > 0 }">{{ data.correction_count_pending || 0 }}</text>
        </view>
      </view>

      <!-- 热词 Top -->
      <text class="section-title">热词 Top 10</text>
      <view class="hot-card">
        <view v-if="!(data.hot_top && data.hot_top.length)" class="hot-empty">
          <text class="hot-empty__text">暂无数据</text>
        </view>
        <view
          v-for="(item, idx) in (data.hot_top || [])"
          :key="item.id"
          class="hot-row"
        >
          <view class="hot-row__rank" :class="`hot-row__rank--${idx < 3 ? idx + 1 : 'normal'}`">
            <text class="hot-row__rank-text">{{ idx + 1 }}</text>
          </view>
          <text class="hot-row__word">{{ item.word }}</text>
          <view class="hot-row__heat">
            <Flame :size="12" color="#FE2C55" />
            <text class="hot-row__heat-text">{{ item.heat }}</text>
          </view>
        </view>
      </view>

      <!-- 底部入口 -->
      <view class="entry-btn" @click="goWords">
        <BookOpen :size="16" color="#6B7280" />
        <text class="entry-btn__text">词条管理</text>
        <ChevronRight :size="16" color="#C0C4CC" />
      </view>
    </template>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import {
  ArrowLeft, RefreshCw, ChevronRight, BookOpen, Users, Zap,
  ClipboardList, MessageSquare, Edit3, Flame
} from 'lucide-vue-next'
import * as adminApi from '@/api/admin'

const statusBarHeight = ref(0)
const loading = ref(true)
const noPermission = ref(false)
const data = ref({})

onLoad(() => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
})

onShow(() => {
  fetchStats()
})

async function fetchStats() {
  loading.value = true
  noPermission.value = false
  try {
    const res = await adminApi.getStats()
    data.value = res || {}
  } catch (err) {
    console.error('获取统计失败', err)
    if (err.statusCode === 403) {
      noPermission.value = true
    } else {
      uni.showToast({ title: '加载失败', icon: 'none' })
    }
    data.value = {}
  } finally {
    loading.value = false
  }
}

function goReview() {
  uni.navigateTo({ url: '/pages/review/index' })
}

function goWords() {
  uni.navigateTo({ url: '/pages/admin/words' })
}

function handleBack() {
  uni.navigateBack({ delta: 1 })
}
</script>

<style lang="scss" scoped>
.stats-page {
  min-height: 100vh;
  background-color: $bg-page;
}

/* ============ 顶部栏 ============ */
.top-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 30;
  background-color: $bg-page;

  &__inner {
    height: 54px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 16px;
  }

  &__btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__title {
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
  }
}

.top-bar-placeholder {
  width: 100%;
}

/* ============ 状态提示 ============ */
.state-tip {
  padding: 80px 0;
  text-align: center;

  &__text {
    font-size: 14px;
    color: $text-tertiary;
  }
}

/* ============ 核心指标网格 ============ */
.metric-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  padding: 12px 16px 0;
}

.metric-card {
  background-color: $bg-card;
  border-radius: 14px;
  padding: 16px;
  box-shadow: $shadow-sm;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;

  &__num {
    font-size: 26px;
    font-weight: 700;
    color: $text-primary;
    line-height: 1.1;
    margin-top: 6px;
  }

  &__label {
    font-size: 12px;
    color: $text-tertiary;
  }
}

/* ============ 区块标题 ============ */
.section-title {
  display: block;
  margin: 20px 16px 8px;
  font-size: 12px;
  font-weight: 600;
  color: $text-secondary;
}

/* ============ 待处理卡片 ============ */
.pending-card {
  margin: 0 16px;
  background-color: $bg-card;
  border-radius: 12px;
  box-shadow: $shadow-xs;
  overflow: hidden;
}

.pending-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 50px;
  padding: 0 16px;

  &__left {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  &__label {
    font-size: 14px;
    color: $text-primary;
  }

  &__right {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  &__num {
    font-size: 14px;
    font-weight: 600;
    color: $text-tertiary;

    &--active {
      color: $color-primary;
    }
  }
}

.pending-divider {
  height: 1px;
  background-color: $border-color-light;
  margin-left: 42px;
}

/* ============ 热词卡片 ============ */
.hot-card {
  margin: 0 16px;
  background-color: $bg-card;
  border-radius: 12px;
  box-shadow: $shadow-xs;
  overflow: hidden;
}

.hot-empty {
  padding: 40px 0;
  text-align: center;

  &__text {
    font-size: 13px;
    color: $text-tertiary;
  }
}

.hot-row {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid $border-color-light;

  &:last-child {
    border-bottom: none;
  }

  &__rank {
    width: 22px;
    height: 22px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 12px;
    background-color: $bg-sunken;

    &--1 {
      background-color: rgba(254, 44, 85, 0.12);
      .hot-row__rank-text { color: $color-primary; }
    }
    &--2 {
      background-color: rgba(245, 158, 11, 0.12);
      .hot-row__rank-text { color: $color-warning; }
    }
    &--3 {
      background-color: rgba(156, 163, 175, 0.18);
    }

    &-text {
      font-size: 12px;
      font-weight: 700;
      color: $text-secondary;
    }
  }

  &__word {
    flex: 1;
    font-size: 14px;
    font-weight: 500;
    color: $text-primary;
  }

  &__heat {
    display: flex;
    align-items: center;
    gap: 3px;

    &-text {
      font-size: 12px;
      color: $color-primary;
      font-weight: 600;
    }
  }
}

/* ============ 底部入口 ============ */
.entry-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 16px;
  padding: 14px 16px;
  background-color: $bg-card;
  border-radius: 12px;
  box-shadow: $shadow-xs;

  &__text {
    flex: 1;
    font-size: 14px;
    color: $text-primary;
  }

  &:active {
    opacity: 0.7;
  }
}
</style>
