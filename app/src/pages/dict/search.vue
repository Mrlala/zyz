<template>
  <view class="search-page">
    <!-- 顶部搜索栏 -->
    <view class="top-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="top-bar__inner">
        <view class="top-bar__btn" @click="handleBack">
          <ArrowLeft :size="20" color="#6B7280" />
        </view>
        <view class="top-bar__search">
          <Search :size="16" color="#9CA3AF" />
          <input
            class="top-bar__search-input"
            v-model="keyword"
            placeholder="搜索词条"
            placeholder-class="top-bar__search-placeholder"
            :confirm-type="search"
            @confirm="handleSearch"
            @input="onInput"
          />
          <view v-if="keyword" class="top-bar__search-clear" @click="clearKeyword">
            <X :size="14" color="#9CA3AF" />
          </view>
        </view>
        <view class="top-bar__action" @click="handleSearch">搜索</view>
      </view>
    </view>
    <view class="top-bar-placeholder" :style="{ height: (statusBarHeight + 54) + 'px' }"></view>

    <view class="search-body">
      <!-- 搜索结果 -->
      <view v-if="searched" class="search-result">
        <WordCard
          v-for="word in results"
          :key="word.id"
          :word="word"
          @click="goDetail"
          @favorite="handleFavorite"
        />

        <!-- 空状态 -->
        <view v-if="!loading && results.length === 0" class="empty-state">
          <view class="empty-state__icon">
            <Search :size="32" color="#9CA3AF" />
          </view>
          <text class="empty-state__text">没有找到相关词条</text>
          <view class="empty-state__btn" @click="goSubmit">
            <text class="empty-state__btn-text">提交新词条</text>
          </view>
        </view>

        <!-- 加载更多 -->
        <view v-if="results.length > 0" class="load-more" @click="loadMore">
          <text>{{ loading ? '加载中...' : (results.length >= total ? '没有更多了' : '点击加载更多') }}</text>
        </view>
      </view>

      <!-- 搜索引导：历史 + 热门 -->
      <view v-else class="search-guide">
        <!-- 搜索历史 -->
        <view v-if="history.length" class="guide-section">
          <view class="guide-section__header">
            <text class="guide-section__title">搜索历史</text>
            <text class="guide-section__action" @click="clearHistory">清空</text>
          </view>
          <view class="guide-section__tags">
            <view
              v-for="(item, idx) in history"
              :key="idx"
              class="tag-pill"
              @click="searchFromTag(item)"
            >{{ item }}</view>
          </view>
        </view>

        <!-- 热门搜索 -->
        <view class="guide-section">
          <view class="guide-section__header">
            <text class="guide-section__title">热门搜索</text>
          </view>
          <view class="guide-section__tags">
            <view
              v-for="(item, idx) in hotKeywords"
              :key="idx"
              class="tag-pill tag-pill--hot"
              @click="searchFromTag(item)"
            >
              <text class="tag-pill__rank" :class="{ 'tag-pill__rank--top': idx < 3 }">{{ idx + 1 }}</text>
              <text>{{ item }}</text>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onReachBottom } from '@dcloudio/uni-app'
import { ArrowLeft, Search, X } from 'lucide-vue-next'
import WordCard from '@/components/word/WordCard.vue'
import * as wordApi from '@/api/word'
import { useUserStore } from '@/store/modules/user'
import storage from '@/utils/storage'

const userStore = useUserStore()

const HISTORY_KEY = 'zyz_search_history'

const statusBarHeight = ref(0)
const keyword = ref('')
const results = ref([])
const page = ref(1)
const pageSize = 20
const total = ref(0)
const loading = ref(false)
// 是否已发起搜索
const searched = ref(false)
// 搜索历史
const history = ref([])
// 热门搜索词（本地预置）
const hotKeywords = ['996', 'yyds', 'emo', '打工人', '躺平', '内卷', '破防', '社死']

onLoad(() => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
  history.value = storage.get(HISTORY_KEY) || []
})

onReachBottom(() => {
  loadMore()
})

// 输入框输入
function onInput() {
  // 输入变化时重置为引导态（仅当关键词为空）
  if (!keyword.value.trim() && searched.value) {
    searched.value = false
    results.value = []
  }
}

// 执行搜索
async function handleSearch() {
  const kw = keyword.value.trim()
  if (!kw) {
    uni.showToast({ title: '请输入搜索关键词', icon: 'none' })
    return
  }
  searched.value = true
  page.value = 1
  results.value = []
  loading.value = true
  // 记录搜索历史
  addHistory(kw)
  try {
    const data = await wordApi.searchWords(kw, { page: page.value, page_size: pageSize })
    results.value = (data && data.list) || []
    total.value = (data && data.total) || 0
  } catch (err) {
    console.error('搜索失败', err)
  } finally {
    loading.value = false
  }
}

// 加载更多
function loadMore() {
  if (loading.value || results.value.length >= total.value) return
  page.value++
  doSearch(true)
}

// 搜索请求（追加模式）
async function doSearch(append) {
  loading.value = true
  try {
    const data = await wordApi.searchWords(keyword.value.trim(), {
      page: page.value,
      page_size: pageSize
    })
    const list = (data && data.list) || []
    results.value = append ? results.value.concat(list) : list
    total.value = (data && data.total) || 0
  } catch (err) {
    console.error('搜索失败', err)
  } finally {
    loading.value = false
  }
}

// 从标签搜索
function searchFromTag(text) {
  keyword.value = text
  handleSearch()
}

// 清空关键词
function clearKeyword() {
  keyword.value = ''
  searched.value = false
  results.value = []
}

// 添加搜索历史（去重，最多 10 条）
function addHistory(kw) {
  const list = history.value.filter((h) => h !== kw)
  list.unshift(kw)
  history.value = list.slice(0, 10)
  storage.set(HISTORY_KEY, history.value)
}

// 清空搜索历史
function clearHistory() {
  uni.showModal({
    title: '提示',
    content: '确定清空搜索历史？',
    success: (res) => {
      if (res.confirm) {
        history.value = []
        storage.remove(HISTORY_KEY)
      }
    }
  })
}

// 收藏
async function handleFavorite(word) {
  const id = word.id || word.word_id
  if (!id) return
  try {
    await userStore.toggleFavorite(id)
    const target = results.value.find((w) => w.id === id)
    if (target) target.is_favorited = userStore.isFavorited(id)
    uni.showToast({
      title: userStore.isFavorited(id) ? '已收藏' : '已取消收藏',
      icon: 'none'
    })
  } catch (err) {
    console.error('收藏失败', err)
  }
}

// 跳转词条详情
function goDetail(word) {
  const id = word.id || word.word_id
  if (id) {
    uni.navigateTo({ url: `/pages/word-detail/index?id=${id}` })
  }
}

// 跳转提交新词条（我的提交页）
function goSubmit() {
  uni.navigateTo({ url: '/pages/mine/submissions' })
}

function handleBack() {
  uni.navigateBack({ delta: 1 })
}
</script>

<style lang="scss" scoped>
.search-page {
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
    padding: 0 16px;
    gap: 8px;
  }

  &__btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__search {
    flex: 1;
    display: flex;
    align-items: center;
    height: 36px;
    padding: 0 12px;
    background-color: $bg-sunken;
    border-radius: 9999px;
    gap: 8px;
  }

  &__search-input {
    flex: 1;
    font-size: 14px;
    color: $text-primary;
  }

  &__search-placeholder {
    color: $text-tertiary;
    font-size: 14px;
  }

  &__search-clear {
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__action {
    font-size: 14px;
    color: $color-primary;
    padding: 0 4px;
  }
}

.top-bar-placeholder {
  width: 100%;
}

/* ============ 主体 ============ */
.search-body {
  padding: 12px 16px 32px;
}

/* ============ 搜索结果 ============ */
.search-result {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* ============ 引导区 ============ */
.guide-section {
  margin-bottom: 24px;

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  &__title {
    font-size: 14px;
    font-weight: 600;
    color: $text-primary;
  }

  &__action {
    font-size: 13px;
    color: $text-secondary;
  }

  &__tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
}

.tag-pill {
  display: inline-flex;
  align-items: center;
  padding: 8px 16px;
  background-color: $bg-card;
  border-radius: 9999px;
  font-size: 13px;
  color: $text-primary;
  box-shadow: $shadow-xs;

  &__rank {
    width: 18px;
    height: 18px;
    line-height: 18px;
    text-align: center;
    background-color: $bg-sunken;
    color: $text-secondary;
    border-radius: 50%;
    font-size: 11px;
    margin-right: 6px;

    &--top {
      background-color: rgba(245, 158, 11, 0.15);
      color: $color-warning;
    }
  }
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

/* ============ 加载更多 ============ */
.load-more {
  text-align: center;
  padding: 16px 0;
  font-size: 12px;
  color: $text-tertiary;
}
</style>
