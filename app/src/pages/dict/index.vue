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
    <view class="sort-bar">
      <view class="sort-bar__tabs">
        <view
          v-for="item in sortOptions"
          :key="item.value"
          class="sort-bar__tab"
          :class="{ 'sort-bar__tab--active': sort === item.value }"
          @click="switchSort(item.value)"
        >{{ item.label }}</view>
      </view>
      <view class="sort-bar__extra" @click="goCategoryList">
        <text>分类专区</text>
        <ChevronRight :size="12" color="#FE2C55" />
      </view>
    </view>

    <!-- 词条列表 -->
    <view class="word-list">
      <view
        v-for="word in words"
        :key="word.id"
        class="word-card"
        @click="goDetail(word)"
      >
        <view class="word-card__bar"></view>
        <view class="word-card__body">
          <view class="word-card__info">
            <view class="word-card__title-row">
              <text class="word-card__word">{{ word.word || word.name }}</text>
              <text v-if="word.category_name || word.category" class="word-card__tag">{{ word.category_name || word.category }}</text>
            </view>
            <text class="word-card__definition">{{ word.definition || word.meaning || word.summary || '' }}</text>
          </view>
          <view class="word-card__fav" @click.stop="handleFavorite(word)">
            <Heart
              :size="18"
              :color="word.is_favorited ? '#FE2C55' : '#D1D5DB'"
              :fill="word.is_favorited ? '#FE2C55' : 'none'"
            />
          </view>
        </view>
      </view>

      <!-- 加载中 -->
      <view v-if="loading && !words.length" class="state-tip">
        <text>加载中...</text>
      </view>

      <!-- 空状态 -->
      <view v-if="!loading && !words.length" class="empty-state">
        <view class="empty-state__icon">
          <BookOpen :size="32" color="#9CA3AF" />
        </view>
        <text class="empty-state__text">该分类下暂无词条</text>
        <text class="empty-state__sub">去其他分类看看</text>
      </view>

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
import { ref, computed } from 'vue'
import { onLoad, onReachBottom, onPullDownRefresh } from '@dcloudio/uni-app'
import { ChevronLeft, Search, ChevronRight, Heart, BookOpen } from 'lucide-vue-next'
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

function switchSort(value) {
  if (sort.value === value) return
  sort.value = value
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

/* ============ 排序条 ============ */
.sort-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;

  &__tabs {
    display: flex;
    gap: 16px;
  }

  &__tab {
    font-size: 13px;
    color: $text-secondary;
    padding-bottom: 2px;
    border-bottom: 2px solid transparent;

    &--active {
      color: $text-primary;
      font-weight: 500;
      border-bottom-color: $color-primary;
    }
  }

  &__extra {
    display: flex;
    align-items: center;
    gap: 2px;
    font-size: 12px;
    font-weight: 500;
    color: $color-primary;
  }
}

/* ============ 词条列表 ============ */
.word-list {
  padding: 8px 16px 32px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.word-card {
  display: flex;
  border-radius: 12px;
  overflow: hidden;
  background-color: $bg-card;
  box-shadow: $shadow-xs;

  &__bar {
    width: 3px;
    flex-shrink: 0;
    background: linear-gradient(180deg, #FE2C55, #25F4EE);
  }

  &__body {
    flex: 1;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    padding: 14px 16px;
    min-width: 0;
  }

  &__info {
    flex: 1;
    min-width: 0;
  }

  &__title-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  &__word {
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__tag {
    flex-shrink: 0;
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 9999px;
    font-size: 10px;
    background-color: $bg-sunken;
    color: $text-tertiary;
    white-space: nowrap;
  }

  &__definition {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    overflow: hidden;
    margin-top: 6px;
    font-size: 13px;
    color: $text-secondary;
    line-height: 1.5;
  }

  &__fav {
    flex-shrink: 0;
    margin-left: 12px;
    margin-top: 2px;
    padding: 4px;
  }
}

/* ============ 状态提示 ============ */
.state-tip {
  padding: 48px 0;
  text-align: center;
  font-size: 14px;
  color: $text-secondary;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 64px 0;

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
