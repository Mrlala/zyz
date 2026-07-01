<template>
  <view class="dict-page">
    <!-- 顶部栏 -->
    <view class="top-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="top-bar__inner">
        <view class="top-bar__btn" @click="handleBack">
          <ChevronLeft :size="20" color="#6B7280" />
        </view>
        <text class="top-bar__title">词库</text>
        <view class="top-bar__btn top-bar__btn--sunken" @click="goSearch">
          <Search :size="16" color="#6B7280" />
        </view>
      </view>
    </view>
    <view class="top-bar-placeholder" :style="{ height: (statusBarHeight + 54) + 'px' }"></view>

    <!-- 搜索栏 -->
    <view class="search-bar" @click="goSearch">
      <Search :size="15" color="#9CA3AF" />
      <text class="search-bar__placeholder">搜索词条、释义或例句</text>
    </view>

    <!-- 分类胶囊 -->
    <scroll-view scroll-x class="category-scroll" :show-scrollbar="false">
      <view class="category-scroll__list">
        <view
          class="category-pill"
          :class="{ 'category-pill--active': activeCategoryId === 0 }"
          @click="switchCategory(0)"
        >全部</view>
        <view
          v-for="cat in categories"
          :key="cat.id"
          class="category-pill"
          :class="{ 'category-pill--active': activeCategoryId === cat.id }"
          @click="switchCategory(cat.id)"
        >{{ cat.name }}</view>
      </view>
    </scroll-view>

    <!-- 排序条 -->
    <SortBar v-model="sort" :options="sortOptions">
      <template #extra>
        <view class="sort-extra" @click="goCategoryList">
          <text>分类专区</text>
          <ChevronRight :size="12" color="#FE2C55" />
        </view>
      </template>
    </SortBar>

    <!-- 词条列表 -->
    <view class="word-list">
      <WordCard
        v-for="(word, idx) in words"
        :key="word.id"
        :word="word"
        :variant="idx < 3 && page === 1 ? 'featured' : 'default'"
        @click="goDetail"
        @favorite="handleFavorite"
      />

      <!-- 加载中 -->
      <view v-if="loading && !words.length" class="state-tip">
        <text>加载中...</text>
      </view>

      <!-- 空状态 -->
      <EmptyState
        v-if="!loading && !words.length"
        :icon="BookOpen"
        text="该分类下暂无词条"
        sub="去其他分类看看"
      />

      <!-- 加载更多 -->
      <view v-if="words.length > 0 && words.length < total" class="load-more" @click="loadMore">
        <text>{{ loading ? '加载中...' : '加载更多' }}</text>
      </view>
      <view v-if="words.length > 0 && words.length >= total" class="load-more load-more--end">
        <text>没有更多了</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, watch } from 'vue'
import { onLoad, onReachBottom, onPullDownRefresh } from '@dcloudio/uni-app'
import { ChevronLeft, Search, ChevronRight, BookOpen } from 'lucide-vue-next'
import WordCard from '@/components/word/WordCard.vue'
import SortBar from '@/components/dict/SortBar.vue'
import EmptyState from '@/components/dict/EmptyState.vue'
import * as wordApi from '@/api/word'
import * as categoryApi from '@/api/category'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()

const statusBarHeight = ref(0)
const categories = ref([])
const activeCategoryId = ref(0)
const sort = ref('hot')
const words = ref([])
const page = ref(1)
const pageSize = 20
const total = ref(0)
const loading = ref(false)

const sortOptions = [
  { label: '热门', value: 'hot' },
  { label: '最新', value: 'new' },
  { label: '名称', value: 'name' }
]

// 排序变化时重新拉取
watch(sort, () => fetchWords(true))

onLoad(() => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
  fetchCategories()
  fetchWords(true)
})

onPullDownRefresh(() => {
  fetchWords(true).finally(() => {
    uni.stopPullDownRefresh()
  })
})

onReachBottom(() => {
  loadMore()
})

async function fetchCategories() {
  try {
    const list = await categoryApi.getCategories()
    categories.value = (list || []).slice(0, 12)
  } catch (err) {
    console.error('获取分类失败', err)
  }
}

async function fetchWords(reset = false) {
  if (loading.value) return
  loading.value = true
  if (reset) {
    page.value = 1
    words.value = []
  }
  try {
    const params = { page: page.value, page_size: pageSize, sort: sort.value }
    if (activeCategoryId.value) {
      params.category_id = activeCategoryId.value
    }
    const data = await wordApi.getWords(params)
    const list = (data && data.list) || []
    total.value = (data && data.total) || 0
    words.value = reset ? list : words.value.concat(list)
  } catch (err) {
    console.error('获取词条失败', err)
  } finally {
    loading.value = false
  }
}

function loadMore() {
  if (loading.value || words.value.length >= total.value) return
  page.value++
  fetchWords(false)
}

function switchCategory(id) {
  if (activeCategoryId.value === id) return
  activeCategoryId.value = id
  fetchWords(true)
}

async function handleFavorite(word) {
  const id = word.id || word.word_id
  if (!id) return
  try {
    await userStore.toggleFavorite(id)
    uni.showToast({
      title: userStore.isFavorited(id) ? '已收藏' : '已取消收藏',
      icon: 'none'
    })
    const target = words.value.find((w) => w.id === id)
    if (target) {
      target.is_favorited = userStore.isFavorited(id)
    }
  } catch (err) {
    console.error('收藏操作失败', err)
  }
}

function goDetail(word) {
  const id = word.id || word.word_id
  if (id) {
    uni.navigateTo({ url: `/pages/word-detail/index?id=${id}` })
  }
}

function goSearch() {
  uni.navigateTo({ url: '/pages/dict/search' })
}

function goCategoryList() {
  uni.navigateTo({ url: `/pages/dict/category?id=${activeCategoryId.value}` })
}

function handleBack() {
  uni.navigateBack({ delta: 1 })
}
</script>

<style lang="scss" scoped>
.dict-page {
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

    &--sunken {
      background-color: $bg-sunken;
      border-radius: 50%;
    }
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
  height: 36px;
  margin: 12px 16px 8px;
  padding: 0 12px;
  background-color: $bg-sunken;
  border-radius: 10px;

  &__placeholder {
    font-size: 13px;
    color: $text-tertiary;
  }
}

/* ============ 分类胶囊 ============ */
.category-scroll {
  white-space: nowrap;
  padding: 8px 16px;

  &__list {
    display: inline-flex;
    gap: 8px;
  }
}

.category-pill {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 500;
  background-color: $bg-card;
  color: $text-secondary;
  border: 1px solid $border-color;
  white-space: nowrap;

  &--active {
    background-color: $color-primary;
    color: #FFFFFF;
    border-color: $color-primary;
  }
}

/* ============ 排序条额外内容 ============ */
.sort-extra {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 12px;
  font-weight: 500;
  color: $color-primary;
}

/* ============ 词条列表 ============ */
.word-list {
  padding: 8px 16px 32px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* ============ 状态提示 ============ */
.state-tip {
  padding: 48px 0;
  text-align: center;
  font-size: 14px;
  color: $text-secondary;
}

.load-more {
  text-align: center;
  padding: 16px 0;
  font-size: 12px;
  color: $text-tertiary;

  &--end {
    color: $text-tertiary;
  }
}
</style>
