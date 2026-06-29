<template>
  <view class="page search-page">
    <!-- 顶部搜索栏（含返回按钮） -->
    <view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="nav-bar__inner">
        <view class="nav-bar__back" @click="handleBack">‹</view>
        <view class="nav-bar__search">
          <text class="nav-bar__search-icon">🔍</text>
          <input
            class="nav-bar__search-input"
            v-model="keyword"
            placeholder="搜索词条"
            placeholder-class="nav-bar__search-placeholder"
            :confirm-type="search"
            @confirm="handleSearch"
            @input="onInput"
          />
          <view v-if="keyword" class="nav-bar__search-clear" @click="clearKeyword">✕</view>
        </view>
        <view class="nav-bar__action" @click="handleSearch">搜索</view>
      </view>
    </view>
    <view class="nav-placeholder" :style="{ height: (statusBarHeight + 44) + 'px' }"></view>

    <view class="search-page__body">
      <!-- 搜索结果 -->
      <view v-if="searched" class="search-page__result">
        <WordCard
          v-for="word in results"
          :key="word.id"
          :word="word"
          @click="goDetail"
          @favorite="handleFavorite"
        />

        <EmptyState
          v-if="!loading && results.length === 0"
          icon="🔍"
          text="没有找到相关词条"
          btn-text="提交新词条"
          @btnClick="goSubmit"
        />

        <LoadMore
          v-if="results.length > 0"
          :status="loadMoreStatus"
          @loadMore="loadMore"
        />
      </view>

      <!-- 搜索引导：历史 + 热门 -->
      <view v-else class="search-page__guide">
        <!-- 搜索历史 -->
        <view v-if="history.length" class="search-page__section">
          <view class="search-page__section-header">
            <text class="search-page__section-title">搜索历史</text>
            <text class="search-page__section-action" @click="clearHistory">清空</text>
          </view>
          <view class="search-page__tags">
            <view
              v-for="(item, idx) in history"
              :key="idx"
              class="search-page__tag"
              @click="searchFromTag(item)"
            >{{ item }}</view>
          </view>
        </view>

        <!-- 热门搜索 -->
        <view class="search-page__section">
          <view class="search-page__section-header">
            <text class="search-page__section-title">热门搜索</text>
          </view>
          <view class="search-page__tags">
            <view
              v-for="(item, idx) in hotKeywords"
              :key="idx"
              class="search-page__tag search-page__tag--hot"
              @click="searchFromTag(item)"
            >
              <text class="search-page__tag-rank">{{ idx + 1 }}</text>
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
import WordCard from '@/components/word/WordCard.vue'
import LoadMore from '@/components/common/LoadMore.vue'
import EmptyState from '@/components/common/EmptyState.vue'
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

const loadMoreStatus = computed(() => {
  if (loading.value) return 'loading'
  if (results.value.length >= total.value && results.value.length > 0) return 'noMore'
  return 'more'
})

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
  doSearch(false)
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
  background-color: $uni-bg-color;

  .nav-bar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
    background-color: #FFFFFF;
    box-shadow: $uni-box-shadow;

    &__inner {
      height: 88rpx;
      display: flex;
      align-items: center;
      padding: 0 $uni-spacing-row-base;
      gap: $uni-spacing-row-sm;
    }

    &__back {
      width: 48rpx;
      font-size: 56rpx;
      color: $uni-text-color;
      line-height: 1;
      text-align: center;
    }

    &__search {
      flex: 1;
      display: flex;
      align-items: center;
      height: 60rpx;
      padding: 0 $uni-spacing-row-base;
      background-color: $uni-bg-color;
      border-radius: 999rpx;
    }

    &__search-icon {
      font-size: $uni-font-size-base;
      margin-right: $uni-spacing-row-sm;
    }

    &__search-input {
      flex: 1;
      font-size: $uni-font-size-sm;
      color: $uni-text-color;
    }

    &__search-placeholder {
      color: $uni-text-color-placeholder;
      font-size: $uni-font-size-sm;
    }

    &__search-clear {
      width: 40rpx;
      text-align: center;
      color: $uni-text-color-placeholder;
      font-size: $uni-font-size-sm;
    }

    &__action {
      font-size: $uni-font-size-sm;
      color: $uni-color-primary;
      padding: 0 $uni-spacing-row-sm;
    }
  }

  &__body {
    padding: $uni-spacing-col-base $uni-spacing-row-base;
    padding-bottom: 60rpx;
  }

  // 引导区
  &__section {
    margin-bottom: $uni-spacing-col-lg;
  }

  &__section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $uni-spacing-row-base;
  }

  &__section-title {
    font-size: $uni-font-size-base;
    font-weight: 600;
    color: $uni-text-color;
  }

  &__section-action {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
  }

  &__tags {
    display: flex;
    flex-wrap: wrap;
    gap: $uni-spacing-row-sm;
  }

  &__tag {
    display: inline-flex;
    align-items: center;
    padding: 12rpx $uni-spacing-row-base;
    background-color: #FFFFFF;
    border-radius: 999rpx;
    font-size: $uni-font-size-sm;
    color: $uni-text-color;

    &--hot {
      color: $uni-text-color;
    }
  }

  &__tag-rank {
    width: 32rpx;
    height: 32rpx;
    line-height: 32rpx;
    text-align: center;
    background-color: $uni-bg-color;
    color: $uni-text-color-grey;
    border-radius: 50%;
    font-size: $uni-font-size-xs;
    margin-right: $uni-spacing-row-sm;

    .search-page__tag--hot:nth-child(-n + 3) & {
      background-color: rgba(245, 158, 11, 0.15);
      color: $uni-color-warning;
    }
  }

  // 结果区
  &__result {
    padding-top: $uni-spacing-row-sm;
  }
}
</style>
