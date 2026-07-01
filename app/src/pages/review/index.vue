<template>
  <view class="review-page">
    <!-- 顶部栏 -->
    <view class="top-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="top-bar__inner">
        <view class="top-bar__btn" @click="handleBack">
          <ArrowLeft :size="20" color="#6B7280" />
        </view>
        <text class="top-bar__title">词条审核</text>
        <view class="top-bar__btn" @click="handleMenu">
          <BarChart3 :size="18" color="#6B7280" />
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
      <!-- 空状态 -->
      <view v-if="!loading && !list.length" class="review-empty">
        <text class="review-empty__text">暂无{{ filterTabs.find(t => t.value === activeFilter)?.label || '' }}数据</text>
      </view>

      <view
        v-for="item in list"
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

        <!-- 驳回原因（已拒绝且有关键词） -->
        <view v-if="item.status === 'rejected' && item.reviewComment" class="review-card__example">
          <MessageSquare :size="14" color="#EF4444" />
          <text class="review-card__example-text">驳回原因：{{ item.reviewComment }}</text>
        </view>

        <!-- 例句气泡（仅待审核） -->
        <view v-if="item.status === 'pending' && item.example" class="review-card__example">
          <MessageSquare :size="14" color="#9CA3AF" />
          <text class="review-card__example-text">例句：「{{ item.example }}」</text>
        </view>

        <!-- 提交人 -->
        <view class="review-card__submitter">
          <view class="review-card__avatar">
            <text class="review-card__avatar-text">{{ (item.submitter || '?').charAt(0) }}</text>
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
import { onLoad, onShow } from '@dcloudio/uni-app'
import {
  ArrowLeft, BarChart3, Check, Pencil, X,
  CheckCircle, XCircle, MessageSquare
} from 'lucide-vue-next'
import * as adminApi from '@/api/admin'

const statusBarHeight = ref(0)
const activeFilter = ref('pending')
const loading = ref(true)

// 统计数据
const stats = ref({
  pending: 0,
  approved: 0,
  rejected: 0,
  today: 0
})

// 筛选标签
const filterTabs = [
  { label: '待审核', value: 'pending' },
  { label: '已通过', value: 'approved' },
  { label: '已拒绝', value: 'rejected' }
]

// 审核列表
const list = ref([])

onLoad(() => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
})

onShow(() => {
  fetchList()
  fetchStats()
})

// 拉取审核列表
async function fetchList() {
  loading.value = true
  try {
    const data = await adminApi.getSubmissions({
      status: activeFilter.value,
      page: 1,
      page_size: 50
    })
    list.value = (data?.list || []).map(formatItem)
  } catch (err) {
    console.error('获取审核列表失败', err)
    list.value = []
    if (err.statusCode === 403) {
      uni.showToast({ title: '需要管理员权限', icon: 'none' })
    }
  } finally {
    loading.value = false
  }
}

// 拉取统计数据
async function fetchStats() {
  try {
    const data = await adminApi.getStats()
    stats.value = {
      pending: data?.submission_count_pending || 0,
      approved: 0,
      rejected: 0,
      today: data?.translation_count_today || 0
    }
    // 补充 approved/rejected 计数
    try {
      const [approved, rejected] = await Promise.all([
        adminApi.getSubmissions({ status: 'approved', page: 1, page_size: 1 }),
        adminApi.getSubmissions({ status: 'rejected', page: 1, page_size: 1 })
      ])
      stats.value.approved = approved?.total || 0
      stats.value.rejected = rejected?.total || 0
    } catch (e) {
      // 忽略
    }
  } catch (err) {
    console.warn('获取统计失败', err)
  }
}

// 格式化后端数据为前端展示格式
function formatItem(s) {
  return {
    id: s.submission_id,
    status: s.status,
    word: s.word || '',
    category: s.category_name || '未分类',
    definition: s.definition || '',
    example: s.example || '',
    submitter: s.submitter?.nickname || '匿名',
    time: formatTime(s.submitted_at),
    reviewComment: s.review_comment || ''
  }
}

function switchFilter(value) {
  activeFilter.value = value
  fetchList()
}

function statusText(s) {
  const map = { pending: '待审核', approved: '已通过', rejected: '已拒绝' }
  return map[s] || s
}

// 通过审核
async function handleApprove(item) {
  uni.showModal({
    title: '确认审核',
    content: `通过「${item.word}」的提交？`,
    success: async (res) => {
      if (res.confirm) {
        try {
          await adminApi.reviewSubmission(item.id, { action: 'approve' })
          uni.showToast({ title: '已通过', icon: 'success' })
          fetchList()
          fetchStats()
        } catch (err) {
          uni.showToast({ title: '操作失败', icon: 'none' })
          console.error(err)
        }
      }
    }
  })
}

// 拒绝审核（弹出输入框填写原因）
function handleReject(item) {
  uni.showModal({
    title: '拒绝提交',
    editable: true,
    placeholderText: '请输入拒绝原因',
    success: async (res) => {
      if (res.confirm) {
        const comment = res.content || ''
        try {
          await adminApi.reviewSubmission(item.id, {
            action: 'reject',
            comment: comment
          })
          uni.showToast({ title: '已拒绝', icon: 'success' })
          fetchList()
          fetchStats()
        } catch (err) {
          uni.showToast({ title: '操作失败', icon: 'none' })
          console.error(err)
        }
      }
    }
  })
}

// 修改并审核通过（D13）：编辑释义后以 approve 方式提交，后端用新释义创建词条
function handleEdit(item) {
  uni.showModal({
    title: '修改并通过',
    editable: true,
    placeholderText: '请输入修改后的释义',
    content: item.definition || '',
    success: async (res) => {
      if (res.confirm) {
        const meaning = (res.content || '').trim()
        if (!meaning) {
          uni.showToast({ title: '释义不能为空', icon: 'none' })
          return
        }
        try {
          await adminApi.reviewSubmission(item.id, {
            action: 'approve',
            meaning
          })
          uni.showToast({ title: '已修改并通过', icon: 'success' })
          fetchList()
          fetchStats()
        } catch (err) {
          uni.showToast({ title: '操作失败', icon: 'none' })
          console.error(err)
        }
      }
    }
  })
}

// 顶部栏菜单：跳转数据统计 / 词条管理
function handleMenu() {
  uni.showActionSheet({
    itemList: ['数据统计', '词条管理'],
    success: (res) => {
      if (res.tapIndex === 0) {
        uni.navigateTo({ url: '/pages/admin/stats' })
      } else if (res.tapIndex === 1) {
        uni.navigateTo({ url: '/pages/admin/words' })
      }
    }
  })
}

// 格式化时间
function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  if (isNaN(d.getTime())) return ''
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  if (diff < 86400000 * 7) return Math.floor(diff / 86400000) + '天前'
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${m}-${day} ${hh}:${mm}`
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

.review-empty {
  padding: 60px 0;
  text-align: center;

  &__text {
    font-size: 14px;
    color: $text-tertiary;
  }
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
