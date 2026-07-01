<template>
  <view class="review-page">
    <!-- 顶部栏 -->
    <view class="top-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="top-bar__inner">
        <view class="top-bar__btn" @click="handleBack">
          <ArrowLeft :size="20" color="#6B7280" />
        </view>
        <text class="top-bar__title">词条审核</text>
        <view class="top-bar__btn" @click="handleFilter">
          <SlidersHorizontal :size="18" color="#6B7280" />
        </view>
      </view>
    </view>
    <view class="top-bar-placeholder" :style="{ height: (statusBarHeight + 54) + 'px' }"></view>

    <!-- 统计行 -->
    <view class="stats-row">
      <view class="stats-row__item">
        <text class="stats-row__num stats-row__num--primary">{{ stats.pending }}</text>
        <text class="stats-row__label">待审核</text>
      </view>
      <view class="stats-row__divider"></view>
      <view class="stats-row__item">
        <text class="stats-row__num stats-row__num--success">{{ stats.approved }}</text>
        <text class="stats-row__label">已通过</text>
      </view>
      <view class="stats-row__divider"></view>
      <view class="stats-row__item">
        <text class="stats-row__num stats-row__num--error">{{ stats.rejected }}</text>
        <text class="stats-row__label">已拒绝</text>
      </view>
      <view class="stats-row__divider"></view>
      <view class="stats-row__item">
        <text class="stats-row__num stats-row__num--text">{{ stats.today }}</text>
        <text class="stats-row__label">今日</text>
      </view>
    </view>

    <!-- 筛选标签 -->
    <view class="filter-tabs">
      <view
        v-for="tab in filterTabs"
        :key="tab.value"
        class="filter-pill"
        :class="{ 'filter-pill--active': activeFilter === tab.value }"
        @click="switchFilter(tab.value)"
      >{{ tab.label }}</view>
    </view>

    <!-- 审核卡片列表 -->
    <view class="review-list">
      <view
        v-for="item in filteredList"
        :key="item.id"
        class="review-card"
        :class="`review-card--${item.status}`"
      >
        <!-- 顶部色条 -->
        <view class="review-card__bar" :class="`review-card__bar--${item.status}`"></view>

        <!-- 状态行 -->
        <view class="review-card__status-row">
          <text class="review-card__badge" :class="`review-card__badge--${item.status}`">{{ statusText(item.status) }}</text>
          <text class="review-card__time">{{ item.time }}</text>
        </view>

        <!-- 词 + 分类 -->
        <view class="review-card__word-row">
          <text class="review-card__word" :class="{ 'review-card__word--rejected': item.status === 'rejected' }">{{ item.word }}</text>
          <text class="review-card__cat" :class="{ 'review-card__cat--rejected': item.status === 'rejected' }">{{ item.category }}</text>
        </view>

        <!-- 释义 -->
        <text class="review-card__definition" :class="{ 'review-card__definition--rejected': item.status === 'rejected' }">{{ item.definition }}</text>

        <!-- 例句气泡（仅待审核） -->
        <view v-if="item.status === 'pending' && item.example" class="review-card__example">
          <MessageSquare :size="14" color="#9CA3AF" />
          <text class="review-card__example-text">例句：「{{ item.example }}」</text>
        </view>

        <!-- 提交人 -->
        <view class="review-card__submitter">
          <view class="review-card__avatar">
            <text class="review-card__avatar-text">{{ item.submitter.charAt(0) }}</text>
          </view>
          <text class="review-card__submitter-text">用户·{{ item.submitter }} 提交</text>
          <CheckCircle
            v-if="item.status === 'approved'"
            :size="14"
            color="#10B981"
            class="review-card__state-icon"
          />
          <XCircle
            v-if="item.status === 'rejected'"
            :size="14"
            color="#EF4444"
            class="review-card__state-icon"
          />
        </view>

        <!-- 操作按钮（仅待审核） -->
        <view v-if="item.status === 'pending'" class="review-card__actions">
          <view class="review-card__btn review-card__btn--approve" @click="handleApprove(item)">
            <Check :size="16" color="#FFFFFF" />
            <text class="review-card__btn-text review-card__btn-text--white">通过</text>
          </view>
          <view class="review-card__btn review-card__btn--edit" @click="handleEdit(item)">
            <Pencil :size="16" color="#6B7280" />
            <text class="review-card__btn-text review-card__btn-text--secondary">修改</text>
          </view>
          <view class="review-card__btn review-card__btn--reject" @click="handleReject(item)">
            <X :size="16" color="#EF4444" />
            <text class="review-card__btn-text review-card__btn-text--error">拒绝</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import {
  ArrowLeft, SlidersHorizontal, Check, Pencil, X,
  CheckCircle, XCircle, MessageSquare
} from 'lucide-vue-next'

const statusBarHeight = ref(0)
const activeFilter = ref('all')

// 静态统计数据
const stats = ref({
  pending: 12,
  approved: 156,
  rejected: 8,
  today: 5
})

// 筛选标签
const filterTabs = [
  { label: '全部', value: 'all' },
  { label: '待审核', value: 'pending' },
  { label: '已通过', value: 'approved' },
  { label: '已拒绝', value: 'rejected' }
]

// 静态审核数据（占位）
const list = ref([
  {
    id: 1,
    status: 'pending',
    word: '电子榨菜',
    category: '网络用语',
    definition: '吃饭时看的下饭视频或内容，像榨菜一样开胃提味',
    example: '今晚的电子榨菜准备好了吗？',
    submitter: '李**',
    time: '2025-06-30 14:23'
  },
  {
    id: 2,
    status: 'approved',
    word: '尊嘟假嘟',
    category: '流行语',
    definition: '真的假的的谐音卖萌说法，表示惊讶或质疑',
    example: '',
    submitter: '王**',
    time: '2025-06-30 11:05'
  },
  {
    id: 3,
    status: 'rejected',
    word: 'yyds',
    category: '字母缩写',
    definition: '该词条已存在于词库中，无需重复收录',
    example: '',
    submitter: '赵**',
    time: '2025-06-29 18:47'
  }
])

// 按筛选过滤
const filteredList = computed(() => {
  if (activeFilter.value === 'all') return list.value
  return list.value.filter((item) => item.status === activeFilter.value)
})

onLoad(() => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
})

function switchFilter(value) {
  activeFilter.value = value
}

function statusText(s) {
  const map = { pending: '待审核', approved: '已通过', rejected: '已拒绝' }
  return map[s] || s
}

// 占位逻辑：按钮点击弹Toast
function handleApprove(item) {
  uni.showToast({ title: '功能开发中', icon: 'none' })
}

function handleEdit(item) {
  uni.showToast({ title: '功能开发中', icon: 'none' })
}

function handleReject(item) {
  uni.showToast({ title: '功能开发中', icon: 'none' })
}

function handleFilter() {
  uni.showToast({ title: '筛选功能开发中', icon: 'none' })
}

function handleBack() {
  uni.navigateBack({ delta: 1 })
}
</script>

<style lang="scss" scoped>
.review-page {
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

/* ============ 统计行 ============ */
.stats-row {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px 0;

  &__item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  &__num {
    font-size: 22px;
    font-weight: 700;
    line-height: 1.2;

    &--primary { color: $color-primary; }
    &--success { color: $color-success; }
    &--error { color: $color-danger; }
    &--text { color: $text-primary; }
  }

  &__label {
    font-size: 11px;
    color: $text-tertiary;
    margin-top: 2px;
  }

  &__divider {
    width: 1px;
    height: 32px;
    background-color: $border-color;
  }
}

/* ============ 筛选标签 ============ */
.filter-tabs {
  display: flex;
  gap: 8px;
  padding: 4px 16px 16px;
}

.filter-pill {
  padding: 6px 12px;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 500;
  background-color: $bg-sunken;
  color: $text-secondary;
  white-space: nowrap;

  &--active {
    background-color: $color-primary;
    color: #FFFFFF;
  }
}

/* ============ 审核卡片 ============ */
.review-list {
  padding: 0 16px 32px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.review-card {
  position: relative;
  border-radius: 16px;
  padding: 16px;
  background-color: $bg-card;
  box-shadow: $shadow-sm;
  overflow: hidden;

  &--approved, &--rejected {
    opacity: 0.7;
  }

  &__bar {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;

    &--pending { background-color: $color-warning; }
    &--approved { background-color: $color-success; }
    &--rejected { background-color: $color-danger; }
  }

  &__status-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 4px;
  }

  &__badge {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 500;

    &--pending {
      background-color: rgba(245, 158, 11, 0.1);
      color: #D97706;
    }
    &--approved {
      background-color: rgba(16, 185, 129, 0.1);
      color: #059669;
    }
    &--rejected {
      background-color: rgba(239, 68, 68, 0.1);
      color: #DC2626;
    }
  }

  &__time {
    font-size: 11px;
    color: $text-tertiary;
  }

  &__word-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 10px;
  }

  &__word {
    font-size: 20px;
    font-weight: 700;
    color: $text-primary;
    line-height: 1.3;

    &--rejected {
      text-decoration: line-through;
    }
  }

  &__cat {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    background-color: $bg-sunken;
    color: $text-secondary;

    &--rejected {
      color: $text-tertiary;
    }
  }

  &__definition {
    display: block;
    margin-top: 8px;
    font-size: 14px;
    line-height: 1.6;
    color: $text-secondary;

    &--rejected {
      color: $text-tertiary;
    }
  }

  &__example {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    margin-top: 10px;
    padding: 12px;
    border-radius: 10px;
    background-color: $bg-sunken;
  }

  &__example-text {
    flex: 1;
    font-size: 12px;
    line-height: 1.6;
    color: $text-tertiary;
  }

  &__submitter {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 10px;
  }

  &__avatar {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background-color: $bg-sunken;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__avatar-text {
    font-size: 10px;
    font-weight: 500;
    color: $text-tertiary;
  }

  &__submitter-text {
    font-size: 12px;
    color: $text-tertiary;
  }

  &__state-icon {
    margin-left: auto;
  }

  &__actions {
    display: flex;
    gap: 10px;
    margin-top: 14px;
  }

  &__btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    height: 38px;
    border-radius: 10px;

    &--approve {
      background-color: $color-success;
    }
    &--edit {
      background-color: $bg-sunken;
    }
    &--reject {
      background-color: rgba(239, 68, 68, 0.06);
    }
  }

  &__btn-text {
    font-size: 13px;

    &--white { color: #FFFFFF; font-weight: 500; }
    &--secondary { color: $text-secondary; }
    &--error { color: $color-danger; }
  }
}
</style>
