<template>
  <view class="favorites-page">
    <!-- 顶部栏 -->
    <view class="top-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="top-bar__inner">
        <view class="top-bar__btn" @click="handleBack">
          <ArrowLeft :size="20" color="#6B7280" />
        </view>
        <text class="top-bar__title">收藏</text>
        <view class="top-bar__edit" @click="handleEdit">
          <text class="top-bar__edit-text">{{ editMode ? '完成' : '编辑' }}</text>
        </view>
      </view>
    </view>
    <view class="top-bar-placeholder" :style="{ height: (statusBarHeight + 54) + 'px' }"></view>

    <!-- Tab 筛选 -->
    <view class="tab-filters">
      <view
        v-for="tab in tabs"
        :key="tab.value"
        class="tab-filters__tab"
        :class="{ 'tab-filters__tab--active': activeTab === tab.value }"
        @click="switchTab(tab.value)"
      >{{ tab.label }}</view>
    </view>

    <!-- 词条收藏 -->
    <template v-if="activeTab === 'words'">
      <!-- 加载中 -->
      <view v-if="loading" class="state-tip">
        <text>加载中...</text>
      </view>

      <template v-else>
        <!-- 收藏计数 -->
        <view v-if="words.length" class="count-row">
          <text class="count-row__text">共 {{ words.length }} 个收藏</text>
        </view>

        <!-- 收藏列表 -->
        <view v-if="words.length" class="fav-list">
          <view
            v-for="word in words"
            :key="word.id"
            class="fav-card"
            @click="goDetail(word)"
          >
            <view class="fav-card__info">
              <text class="fav-card__word">{{ word.word || word.name }}</text>
              <text class="fav-card__definition">{{ word.definition || word.meaning || word.summary || '' }}</text>
              <view class="fav-card__meta">
                <text v-if="word.category_name || word.category" class="fav-card__cat">{{ word.category_name || word.category }}</text>
                <text class="fav-card__time">{{ formatTime(word.favorited_at || word.created_at) }}</text>
              </view>
            </view>
            <view class="fav-card__heart" @click.stop="handleFavorite(word)">
              <Heart
                :size="20"
                :color="editMode ? '#D1D5DB' : '#FE2C55'"
                :fill="editMode ? 'none' : '#FE2C55'"
              />
            </view>
          </view>
        </view>

        <!-- 空状态 -->
        <view v-else class="empty-state">
          <view class="empty-state__icon">
            <Heart :size="32" color="#9CA3AF" />
          </view>
          <text class="empty-state__text">暂无收藏</text>
          <text class="empty-state__sub">收藏的词条将显示在这里</text>
          <view class="empty-state__btn" @click="goDict">
            <text class="empty-state__btn-text">去词库逛逛</text>
          </view>
        </view>
      </template>
    </template>

    <!-- 翻译结果收藏（D12） -->
    <template v-else>
      <view v-if="tLoading" class="state-tip">
        <text>加载中...</text>
      </view>
      <template v-else>
        <view v-if="translations.length" class="count-row">
          <text class="count-row__text">共 {{ tTotal }} 个收藏</text>
        </view>
        <view v-if="translations.length" class="fav-list">
          <view
            v-for="item in translations"
            :key="item.id"
            class="fav-card"
          >
            <view class="fav-card__info">
              <text class="fav-card__word">{{ item.original_text }}</text>
              <text class="fav-card__definition">{{ summarizeResult(item.result) }}</text>
              <view class="fav-card__meta">
                <text class="fav-card__time">{{ formatTime(item.favorited_at) }}</text>
              </view>
            </view>
          </view>
        </view>
        <view v-else class="empty-state">
          <view class="empty-state__icon">
            <Heart :size="32" color="#9CA3AF" />
          </view>
          <text class="empty-state__text">暂无翻译收藏</text>
          <text class="empty-state__sub">在翻译结果页点击收藏即可保存</text>
        </view>
      </template>
    </template>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad, onShow, onReachBottom } from '@dcloudio/uni-app'
import { ArrowLeft, Heart } from 'lucide-vue-next'
import * as userApi from '@/api/user'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()

const statusBarHeight = ref(0)
const words = ref([])
const loading = ref(true)
const activeTab = ref('words')
const editMode = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)
const loadingMore = ref(false)

// 翻译结果收藏状态
const translations = ref([])
const tLoading = ref(false)
const tTotal = ref(0)
const tPage = ref(1)
const tLoadingMore = ref(false)

const tabs = [
  { label: '词条', value: 'words' },
  { label: '翻译结果', value: 'translate' }
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
  if (activeTab.value === 'words') {
    fetchFavorites()
  } else {
    fetchTranslationFavorites(true)
  }
})

// 获取词条收藏列表：服务端分页
async function fetchFavorites() {
  loading.value = true
  page.value = 1
  try {
    const data = await userApi.getFavorites({ page: 1, page_size: pageSize })
    words.value = data?.list || []
    total.value = data?.total || 0
  } catch (err) {
    console.error('获取收藏列表失败', err)
    words.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 获取翻译结果收藏列表：服务端分页
async function fetchTranslationFavorites(reset = false) {
  tLoading.value = true
  if (reset) {
    tPage.value = 1
    translations.value = []
  }
  try {
    const data = await userApi.getTranslationFavorites({ page: tPage.value, page_size: pageSize })
    const list = data?.list || []
    translations.value = reset ? list : translations.value.concat(list)
    tTotal.value = data?.total || 0
  } catch (err) {
    console.error('获取翻译收藏失败', err)
    translations.value = []
    tTotal.value = 0
  } finally {
    tLoading.value = false
  }
}

// 翻译结果摘要：从结果 JSON 提取翻译文本，截断 60 字
function summarizeResult(result) {
  if (!result) return ''
  let text = ''
  if (typeof result === 'string') {
    try { text = JSON.parse(result).translation || '' } catch (e) { text = result }
  } else if (typeof result === 'object') {
    text = result.translation || result.summary || result.subtext || ''
  }
  if (text.length > 60) text = text.slice(0, 60) + '...'
  return text
}

// 加载更多（词条）
async function loadMore() {
  if (activeTab.value === 'translate') {
    loadMoreTranslations()
    return
  }
  if (loadingMore.value || words.value.length >= total.value) return
  loadingMore.value = true
  try {
    const next = page.value + 1
    const data = await userApi.getFavorites({ page: next, page_size: pageSize })
    if (data?.list?.length) {
      words.value.push(...data.list)
      page.value = next
    }
  } catch (e) {
    console.warn('加载更多失败', e)
  } finally {
    loadingMore.value = false
  }
}

// 加载更多（翻译结果）
async function loadMoreTranslations() {
  if (tLoadingMore.value || translations.value.length >= tTotal.value) return
  tLoadingMore.value = true
  try {
    const next = tPage.value + 1
    const data = await userApi.getTranslationFavorites({ page: next, page_size: pageSize })
    if (data?.list?.length) {
      translations.value.push(...data.list)
      tPage.value = next
    }
  } catch (e) {
    console.warn('加载更多失败', e)
  } finally {
    tLoadingMore.value = false
  }
}

onReachBottom(() => {
  loadMore()
})

// 取消收藏
async function handleFavorite(word) {
  const id = word.id || word.word_id
  if (!id) return
  try {
    await userStore.toggleFavorite(id)
    // 从列表中移除
    words.value = words.value.filter((w) => w.id !== id)
    uni.showToast({ title: '已取消收藏', icon: 'none' })
  } catch (err) {
    console.error('取消收藏失败', err)
  }
}

function switchTab(value) {
  activeTab.value = value
  if (value === 'words') {
    if (!words.value.length) fetchFavorites()
  } else if (value === 'translate') {
    if (!translations.value.length) fetchTranslationFavorites(true)
  }
}

function handleEdit() {
  editMode.value = !editMode.value
}

function goDetail(word) {
  if (editMode.value) return
  const id = word.id || word.word_id
  if (id) {
    uni.navigateTo({ url: `/pages/word-detail/index?id=${id}` })
  }
}

function goDict() {
  uni.reLaunch({ url: '/pages/index/index' })
}

function handleBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    uni.navigateBack({ delta: 1 })
  } else {
    uni.reLaunch({ url: '/pages/index/index' })
  }
}

// 格式化时间
function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(typeof ts === 'number' ? ts : Date.parse(ts))
  if (isNaN(d.getTime())) return ''
  const now = Date.now()
  const diff = now - d.getTime()
  if (diff < 86400000) return '今天'
  if (diff < 86400000 * 2) return '昨天'
  if (diff < 86400000 * 7) return Math.floor(diff / 86400000) + '天前'
  if (diff < 86400000 * 14) return '1周前'
  if (diff < 86400000 * 30) return Math.floor(diff / (86400000 * 7)) + '周前'
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${m}-${day}`
}
</script>

<style lang="scss" scoped>
.favorites-page {
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

  &__edit {
    padding: 4px 8px;
  }

  &__edit-text {
    font-size: 14px;
    font-weight: 500;
    color: $color-primary;
  }
}

.top-bar-placeholder {
  width: 100%;
}

/* ============ Tab 筛选 ============ */
.tab-filters {
  display: flex;
  gap: 24px;
  padding: 0 16px;
  border-bottom: 1px solid $border-color-light;

  &__tab {
    padding-bottom: 12px;
    font-size: 14px;
    color: $text-tertiary;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;

    &--active {
      color: $text-primary;
      font-weight: 600;
      border-bottom-color: $color-primary;
    }
  }
}

/* ============ 收藏计数 ============ */
.count-row {
  display: flex;
  justify-content: flex-end;
  padding: 12px 16px 4px;

  &__text {
    font-size: 11px;
    color: $text-tertiary;
  }
}

/* ============ 收藏列表 ============ */
.fav-list {
  padding: 8px 16px 32px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.fav-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 14px;
  border-radius: 12px;
  background-color: $bg-card;
  box-shadow: $shadow-sm;

  &__info {
    flex: 1;
    min-width: 0;
    padding-right: 12px;
  }

  &__word {
    display: block;
    font-size: 15px;
    font-weight: 600;
    color: $text-primary;
    line-height: 1.3;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__definition {
    display: block;
    margin-top: 4px;
    font-size: 13px;
    color: $text-secondary;
    line-height: 1.6;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__meta {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 8px;
  }

  &__cat {
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 11px;
    background-color: $bg-sunken;
    color: $text-tertiary;
    white-space: nowrap;
  }

  &__time {
    font-size: 11px;
    color: $text-tertiary;
  }

  &__heart {
    flex-shrink: 0;
    margin-top: 2px;
    padding: 4px;
  }
}

/* ============ 状态提示 ============ */
.state-tip {
  padding: 64px 0;
  text-align: center;
  font-size: 14px;
  color: $text-secondary;
}

/* ============ 空状态 ============ */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80px 0 40px;

  &__icon {
    width: 56px;
    height: 56px;
    border-radius: 16px;
    background-color: $bg-sunken;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 12px;
  }

  &__text {
    font-size: 14px;
    color: $text-secondary;
    margin-bottom: 4px;
  }

  &__sub {
    font-size: 12px;
    color: $text-tertiary;
  }

  &__btn {
    margin-top: 16px;
    padding: 8px 20px;
    border-radius: 9999px;
    background-color: $color-primary;
  }

  &__btn-text {
    font-size: 13px;
    font-weight: 500;
    color: #FFFFFF;
  }
}
</style>
