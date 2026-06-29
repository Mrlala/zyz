<template>
  <view class="page dict-page">
    <!-- 顶部自定义导航栏 -->
    <view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="nav-bar__inner">
        <text class="nav-bar__title">词条</text>
        <view class="nav-bar__search" @click="goSearch">
          <text class="nav-bar__search-icon">🔍</text>
          <text class="nav-bar__search-placeholder">搜索词条</text>
        </view>
      </view>
    </view>
    <view class="nav-placeholder" :style="{ height: (statusBarHeight + 44) + 'px' }"></view>

    <view class="dict-page__body">
      <!-- 分类标签横向滚动 -->
      <scroll-view scroll-x class="dict-page__categories" :show-scrollbar="false">
        <view class="dict-page__category-list">
          <view
            class="dict-page__category-item"
            :class="{ 'dict-page__category-item--active': activeCategoryId === 0 }"
            @click="switchCategory(0)"
          >全部</view>
          <view
            v-for="cat in categories"
            :key="cat.id"
            class="dict-page__category-item"
            :class="{ 'dict-page__category-item--active': activeCategoryId === cat.id }"
            @click="switchCategory(cat.id)"
          >
            {{ cat.name }}
          </view>
        </view>
      </scroll-view>

      <!-- 排序条 -->
      <view class="dict-page__sort">
        <view
          v-for="item in sortOptions"
          :key="item.value"
          class="dict-page__sort-item"
          :class="{ 'dict-page__sort-item--active': sort === item.value }"
          @click="switchSort(item.value)"
        >{{ item.label }}</view>
        <view class="dict-page__sort-extra" @click="goCategoryList">分类专区 ›</view>
      </view>

      <!-- 词条列表 -->
      <view class="dict-page__list">
        <WordCard
          v-for="word in words"
          :key="word.id"
          :word="word"
          @click="goDetail"
          @favorite="handleFavorite"
        />

        <!-- 空状态 -->
        <EmptyState
          v-if="!loading && words.length === 0"
          icon="📚"
          text="该分类下暂无词条"
          btn-text="去其他分类看看"
          @btnClick="switchCategory(0)"
        />

        <!-- 加载更多 -->
        <LoadMore
          v-if="words.length > 0"
          :status="loadMoreStatus"
          @loadMore="loadMore"
        />
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onReachBottom, onPullDownRefresh } from '@dcloudio/uni-app'
import WordCard from '@/components/word/WordCard.vue'
import LoadMore from '@/components/common/LoadMore.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import * as wordApi from '@/api/word'
import * as categoryApi from '@/api/category'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()

const statusBarHeight = ref(0)
// 分类列表
const categories = ref([])
// 当前选中的分类 ID（0 表示全部）
const activeCategoryId = ref(0)
// 排序方式
const sort = ref('hot')
// 词条列表
const words = ref([])
// 分页
const page = ref(1)
const pageSize = 20
const total = ref(0)
// 加载状态
const loading = ref(false)

// 排序选项
const sortOptions = [
  { label: '热门', value: 'hot' },
  { label: '最新', value: 'new' },
  { label: '名称', value: 'name' }
]

// 加载更多组件状态
const loadMoreStatus = computed(() => {
  if (loading.value) return 'loading'
  if (words.value.length >= total.value && words.value.length > 0) return 'noMore'
  return 'more'
})

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

// 下拉刷新
onPullDownRefresh(() => {
  fetchWords(true).finally(() => {
    uni.stopPullDownRefresh()
  })
})

// 上拉加载更多
onReachBottom(() => {
  loadMore()
})

// 获取分类列表
async function fetchCategories() {
  try {
    const list = await categoryApi.getCategories()
    // 取一级分类，最多展示 12 个
    categories.value = (list || []).slice(0, 12)
  } catch (err) {
    console.error('获取分类失败', err)
  }
}

// 获取词条列表
async function fetchWords(reset = false) {
  if (loading.value) return
  loading.value = true
  if (reset) {
    page.value = 1
    words.value = []
  }
  try {
    const params = {
      page: page.value,
      page_size: pageSize,
      sort: sort.value
    }
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

// 加载更多
function loadMore() {
  if (loading.value || words.value.length >= total.value) return
  page.value++
  fetchWords(false)
}

// 切换分类
function switchCategory(id) {
  if (activeCategoryId.value === id) return
  activeCategoryId.value = id
  fetchWords(true)
}

// 切换排序
function switchSort(value) {
  if (sort.value === value) return
  sort.value = value
  fetchWords(true)
}

// 收藏/取消收藏
async function handleFavorite(word) {
  const id = word.id || word.word_id
  if (!id) return
  try {
    await userStore.toggleFavorite(id)
    uni.showToast({
      title: userStore.isFavorited(id) ? '已收藏' : '已取消收藏',
      icon: 'none'
    })
    // 局部更新卡片收藏态
    const target = words.value.find((w) => w.id === id)
    if (target) {
      target.is_favorited = userStore.isFavorited(id)
    }
  } catch (err) {
    console.error('收藏操作失败', err)
  }
}

// 跳转词条详情
function goDetail(word) {
  const id = word.id || word.word_id
  if (id) {
    uni.navigateTo({ url: `/pages/word-detail/index?id=${id}` })
  }
}

// 跳转搜索页
function goSearch() {
  uni.navigateTo({ url: '/pages/dict/search' })
}

// 跳转分类专区
function goCategoryList() {
  uni.navigateTo({ url: `/pages/dict/category?id=${activeCategoryId.value}` })
}
</script>

<style lang="scss" scoped>
.dict-page {
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
      gap: $uni-spacing-row-base;
    }

    &__title {
      font-size: $uni-font-size-title;
      font-weight: 700;
      color: $uni-text-color;
    }

    &__search {
      flex: 1;
      display: flex;
      align-items: center;
      height: 56rpx;
      padding: 0 $uni-spacing-row-base;
      background-color: $uni-bg-color;
      border-radius: 999rpx;
    }

    &__search-icon {
      font-size: $uni-font-size-base;
      margin-right: $uni-spacing-row-sm;
    }

    &__search-placeholder {
      font-size: $uni-font-size-sm;
      color: $uni-text-color-placeholder;
    }
  }

  &__body {
    padding: $uni-spacing-col-sm $uni-spacing-row-base;
    padding-bottom: 60rpx;
  }

  // 分类标签
  &__categories {
    white-space: nowrap;
    margin-bottom: $uni-spacing-col-sm;
  }

  &__category-list {
    display: inline-flex;
    gap: $uni-spacing-row-sm;
    padding: 4rpx 0;
  }

  &__category-item {
    display: inline-block;
    padding: 12rpx $uni-spacing-row-base;
    background-color: #FFFFFF;
    border-radius: 999rpx;
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
    flex-shrink: 0;

    &--active {
      background-color: $uni-color-primary;
      color: #FFFFFF;
      font-weight: 600;
    }
  }

  // 排序条
  &__sort {
    display: flex;
    align-items: center;
    padding: $uni-spacing-col-sm 0;
    border-bottom: 2rpx solid $uni-border-color;
    margin-bottom: $uni-spacing-col-sm;
  }

  &__sort-item {
    margin-right: $uni-spacing-row-lg;
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;

    &--active {
      color: $uni-text-color;
      font-weight: 600;
      position: relative;

      &::after {
        content: '';
        position: absolute;
        left: 50%;
        bottom: -10rpx;
        transform: translateX(-50%);
        width: 32rpx;
        height: 4rpx;
        background-color: $uni-color-primary;
        border-radius: 2rpx;
      }
    }
  }

  &__sort-extra {
    margin-left: auto;
    font-size: $uni-font-size-sm;
    color: $uni-color-primary;
  }

  // 词条列表
  &__list {
    padding-top: $uni-spacing-col-sm;
  }
}
</style>
