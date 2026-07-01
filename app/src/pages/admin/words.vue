<template>
  <view class="words-page">
    <!-- 顶部栏 -->
    <view class="top-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="top-bar__inner">
        <view class="top-bar__btn" @click="handleBack">
          <ArrowLeft :size="20" color="#6B7280" />
        </view>
        <text class="top-bar__title">词条管理</text>
        <view class="top-bar__btn" @click="toggleSearch">
          <Search :size="18" color="#6B7280" />
        </view>
      </view>
    </view>
    <view class="top-bar-placeholder" :style="{ height: (statusBarHeight + 54) + 'px' }"></view>

    <!-- 搜索栏 -->
    <view v-if="searchVisible" class="search-bar">
      <input
        v-model="keyword"
        class="search-bar__input"
        placeholder="搜索词条"
        confirm-type="search"
        @confirm="onSearch"
      />
      <view class="search-bar__btn" @click="onSearch">搜索</view>
    </view>

    <!-- 状态筛选 -->
    <view class="filter-tabs">
      <view
        v-for="tab in filterTabs"
        :key="tab.value"
        class="filter-pill"
        :class="{ 'filter-pill--active': activeStatus === tab.value }"
        @click="switchStatus(tab.value)"
      >{{ tab.label }}</view>
    </view>

    <!-- 权限不足 -->
    <view v-if="noPermission" class="state-tip">
      <text class="state-tip__text">需要管理员权限</text>
    </view>

    <template v-else>
      <!-- 列表 -->
      <view class="word-list">
        <view v-if="!loading && !list.length" class="word-empty">
          <text class="word-empty__text">暂无词条</text>
        </view>

        <view
          v-for="item in list"
          :key="item.id"
          class="word-card"
        >
          <view class="word-card__head">
            <text class="word-card__word">{{ item.word }}</text>
            <view class="word-card__badges">
              <text class="word-card__badge" :class="`word-card__badge--${item.status}`">{{ statusText(item.status) }}</text>
              <text
                v-if="item.risk_level && item.risk_level !== 'low'"
                class="word-card__badge"
                :class="`word-card__badge--risk-${item.risk_level}`"
              >{{ riskText(item.risk_level) }}</text>
            </view>
          </view>
          <view class="word-card__meta">
            <text class="word-card__meta-text">浏览 {{ item.view_count || 0 }}</text>
            <text class="word-card__meta-time">{{ formatTime(item.created_at) }}</text>
          </view>
          <view class="word-card__actions">
            <view class="word-card__btn" @click="handleEdit(item)">
              <Pencil :size="14" color="#6B7280" />
              <text class="word-card__btn-text">编辑</text>
            </view>
            <view class="word-card__btn" @click="handleRisk(item)">
              <ShieldAlert :size="14" color="#F59E0B" />
              <text class="word-card__btn-text word-card__btn-text--warning">风险</text>
            </view>
            <view class="word-card__btn" @click="handleDelete(item)">
              <Trash2 :size="14" color="#EF4444" />
              <text class="word-card__btn-text word-card__btn-text--danger">删除</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 加载更多提示 -->
      <view v-if="loadingMore" class="load-tip">加载中...</view>
      <view v-else-if="noMore && list.length" class="load-tip">没有更多了</view>
    </template>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onShow, onReachBottom } from '@dcloudio/uni-app'
import { ArrowLeft, Search, Pencil, ShieldAlert, Trash2 } from 'lucide-vue-next'
import * as adminApi from '@/api/admin'

const statusBarHeight = ref(0)
const loading = ref(true)
const loadingMore = ref(false)
const noPermission = ref(false)
const list = ref([])
const page = ref(1)
const pageSize = 20
const total = ref(0)
const keyword = ref('')
const activeStatus = ref('')  // 空 = 全部
const searchVisible = ref(false)

const noMore = computed(() => list.value.length >= total.value)

const filterTabs = [
  { label: '全部', value: '' },
  { label: '正常', value: 'normal' },
  { label: '标记', value: 'flagged' },
  { label: '隐藏', value: 'hidden' }
]

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
})

onReachBottom(() => {
  loadMore()
})

async function fetchList() {
  loading.value = true
  noPermission.value = false
  page.value = 1
  try {
    const data = await adminApi.getWordList({
      page: 1,
      page_size: pageSize,
      keyword: keyword.value || undefined,
      status: activeStatus.value || undefined
    })
    list.value = data?.list || []
    total.value = data?.total || 0
  } catch (err) {
    console.error('获取词条列表失败', err)
    if (err.statusCode === 403) {
      noPermission.value = true
    } else {
      uni.showToast({ title: '加载失败', icon: 'none' })
    }
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loadingMore.value || noMore.value) return
  loadingMore.value = true
  try {
    const next = page.value + 1
    const data = await adminApi.getWordList({
      page: next,
      page_size: pageSize,
      keyword: keyword.value || undefined,
      status: activeStatus.value || undefined
    })
    if (data?.list?.length) {
      list.value.push(...data.list)
      page.value = next
    }
  } catch (e) {
    console.warn('加载更多失败', e)
  } finally {
    loadingMore.value = false
  }
}

function toggleSearch() {
  searchVisible.value = !searchVisible.value
  if (!searchVisible.value && keyword.value) {
    keyword.value = ''
    fetchList()
  }
}

function onSearch() {
  fetchList()
}

function switchStatus(value) {
  activeStatus.value = value
  fetchList()
}

function statusText(s) {
  const map = { published: '正常', pending: '待审', rejected: '隐藏' }
  return map[s] || s || '-'
}

function riskText(r) {
  const map = { low: '低风险', medium: '中风险', high: '高风险' }
  return map[r] || r
}

// 编辑释义
function handleEdit(item) {
  uni.showModal({
    title: '编辑释义',
    editable: true,
    placeholderText: '请输入新的释义',
    content: '',
    success: async (res) => {
      if (res.confirm) {
        const definition = (res.content || '').trim()
        if (!definition) {
          uni.showToast({ title: '释义不能为空', icon: 'none' })
          return
        }
        try {
          await adminApi.updateWord(item.id, { definition })
          uni.showToast({ title: '已更新', icon: 'success' })
          fetchList()
        } catch (err) {
          uni.showToast({ title: '更新失败', icon: 'none' })
          console.error(err)
        }
      }
    }
  })
}

// 标记风险等级
function handleRisk(item) {
  uni.showActionSheet({
    itemList: ['低风险', '中风险', '高风险'],
    success: async (res) => {
      const levels = ['low', 'medium', 'high']
      const level = levels[res.tapIndex]
      try {
        await adminApi.updateWordRisk(item.id, {
          risk_level: level,
          risk_types: item.risk_types || [],
          advice: ''
        })
        uni.showToast({ title: '已标记', icon: 'success' })
        fetchList()
      } catch (err) {
        uni.showToast({ title: '标记失败', icon: 'none' })
        console.error(err)
      }
    }
  })
}

// 删除词条
function handleDelete(item) {
  uni.showModal({
    title: '确认删除',
    content: `删除词条「${item.word}」？此操作可恢复。`,
    success: async (res) => {
      if (res.confirm) {
        try {
          await adminApi.deleteWord(item.id)
          uni.showToast({ title: '已删除', icon: 'success' })
          list.value = list.value.filter((w) => w.id !== item.id)
          total.value = Math.max(0, total.value - 1)
        } catch (err) {
          uni.showToast({ title: '删除失败', icon: 'none' })
          console.error(err)
        }
      }
    }
  })
}

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  if (isNaN(d.getTime())) return ''
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${m}-${day}`
}

function handleBack() {
  uni.navigateBack({ delta: 1 })
}
</script>

<style lang="scss" scoped>
.words-page {
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

/* ============ 搜索栏 ============ */
.search-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;

  &__input {
    flex: 1;
    height: 36px;
    padding: 0 12px;
    border-radius: 18px;
    background-color: $bg-card;
    font-size: 14px;
    color: $text-primary;
    box-shadow: $shadow-xs;
  }

  &__btn {
    padding: 0 12px;
    height: 36px;
    line-height: 36px;
    font-size: 14px;
    color: $color-primary;
    font-weight: 500;
  }
}

/* ============ 状态筛选 ============ */
.filter-tabs {
  display: flex;
  gap: 8px;
  padding: 4px 16px 12px;
  overflow-x: auto;
}

.filter-pill {
  padding: 6px 14px;
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

/* ============ 状态提示 ============ */
.state-tip {
  padding: 80px 0;
  text-align: center;

  &__text {
    font-size: 14px;
    color: $text-tertiary;
  }
}

/* ============ 词条列表 ============ */
.word-list {
  padding: 0 16px 32px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.word-empty {
  padding: 60px 0;
  text-align: center;

  &__text {
    font-size: 14px;
    color: $text-tertiary;
  }
}

.word-card {
  background-color: $bg-card;
  border-radius: 12px;
  padding: 14px;
  box-shadow: $shadow-sm;

  &__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  &__word {
    font-size: 15px;
    font-weight: 600;
    color: $text-primary;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__badges {
    display: flex;
    gap: 4px;
    flex-shrink: 0;
  }

  &__badge {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 500;

    &--published {
      background-color: rgba(16, 185, 129, 0.1);
      color: #059669;
    }
    &--pending {
      background-color: rgba(245, 158, 11, 0.1);
      color: #D97706;
    }
    &--rejected {
      background-color: rgba(239, 68, 68, 0.1);
      color: #DC2626;
    }
    &--risk-medium {
      background-color: rgba(245, 158, 11, 0.12);
      color: #D97706;
    }
    &--risk-high {
      background-color: rgba(239, 68, 68, 0.12);
      color: #DC2626;
    }
  }

  &__meta {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 8px;

    &-text {
      font-size: 12px;
      color: $text-tertiary;
    }

    &-time {
      font-size: 12px;
      color: $text-tertiary;
    }
  }

  &__actions {
    display: flex;
    gap: 8px;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid $border-color-light;
  }

  &__btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    padding: 8px 0;
    border-radius: 8px;
    background-color: $bg-sunken;

    &:active {
      opacity: 0.7;
    }

    &-text {
      font-size: 12px;
      color: $text-secondary;

      &--warning { color: $color-warning; }
      &--danger { color: $color-danger; }
    }
  }
}

/* ============ 加载提示 ============ */
.load-tip {
  padding: 16px 0 24px;
  text-align: center;
  font-size: 12px;
  color: $text-tertiary;
}
</style>
