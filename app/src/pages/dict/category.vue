<template>
  <view class="page category-page">
    <!-- 顶部自定义导航栏 -->
    <view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="nav-bar__inner">
        <view class="nav-bar__back" @click="handleBack">‹</view>
        <text class="nav-bar__title">{{ categoryInfo.name || '分类词条' }}</text>
        <view class="nav-bar__placeholder"></view>
      </view>
    </view>
    <view class="nav-placeholder" :style="{ height: (statusBarHeight + 44) + 'px' }"></view>

    <view class="category-page__body">
      <!-- 分类信息卡 -->
      <view v-if="categoryInfo.name" class="category-page__info card">
        <view class="category-page__info-name">
          <text class="category-page__info-icon">{{ categoryInfo.icon || '📁' }}</text>
          <text>{{ categoryInfo.name }}</text>
        </view>
        <view v-if="categoryInfo.description" class="category-page__info-desc">
          {{ categoryInfo.description }}
        </view>
        <view class="category-page__info-stat">共 {{ total }} 个词条</view>
      </view>

      <!-- 排序条 -->
      <view class="category-page__sort">
        <view
          v-for="item in sortOptions"
          :key="item.value"
          class="category-page__sort-item"
          :class="{ 'category-page__sort-item--active': sort === item.value }"
          @click="switchSort(item.value)"
        >{{ item.label }}</view>
      </view>

      <!-- 词条列表 -->
      <view class="category-page__list">
        <WordCard
          v-for="word in words"
          :key="word.id"
          :word="word"
          @click="goDetail"
          @favorite="handleFavorite"
        />

        <EmptyState
          v-if="!loading && words.length === 0"
          icon="📂"
          text="该分类下暂无词条"
        />

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
import * as categoryApi from '@/api/category'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()

const statusBarHeight = ref(0)
const categoryId = ref(null)
const categoryInfo = ref({})
const words = ref([])
const sort = ref('hot')
const page = ref(1)
const pageSize = 20
const total = ref(0)
const loading = ref(false)

const sortOptions = [
  { label: '热门', value: 'hot' },
  { label: '最新', value: 'new' },
  { label: '名称', value: 'name' }
]

const loadMoreStatus = computed(() => {
  if (loading.value) return 'loading'
  if (words.value.length >= total.value && words.value.length > 0) return 'noMore'
  return 'more'
})

onLoad((options) => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
  categoryId.value = Number(options && options.id)
  if (categoryId.value) {
    fetchWords(true)
  }
})

onPullDownRefresh(() => {
  fetchWords(true).finally(() => {
    uni.stopPullDownRefresh()
  })
})

onReachBottom(() => {
  loadMore()
})

// 获取分类词条
async function fetchWords(reset = false) {
  if (!categoryId.value) return
  if (loading.value) return
  loading.value = true
  if (reset) {
    page.value = 1
    words.value = []
  }
  try {
    const data = await categoryApi.getCategoryWords(categoryId.value, {
      page: page.value,
      page_size: pageSize,
      sort: sort.value
    })
    const list = (data && data.list) || []
    total.value = (data && data.total) || 0
    words.value = reset ? list : words.value.concat(list)
    // 更新分类信息
    if (data && data.category) {
      categoryInfo.value = data.category
    }
  } catch (err) {
    console.error('获取分类词条失败', err)
  } finally {
    loading.value = false
  }
}

function loadMore() {
  if (loading.value || words.value.length >= total.value) return
  page.value++
  fetchWords(false)
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
    const target = words.value.find((w) => w.id === id)
    if (target) target.is_favorited = userStore.isFavorited(id)
    uni.showToast({
      title: userStore.isFavorited(id) ? '已收藏' : '已取消收藏',
      icon: 'none'
    })
  } catch (err) {
    console.error('收藏失败', err)
  }
}

function goDetail(word) {
  const id = word.id || word.word_id
  if (id) {
    uni.navigateTo({ url: `/pages/word-detail/index?id=${id}` })
  }
}

function handleBack() {
  uni.navigateBack({ delta: 1 })
}
</script>

<style lang="scss" scoped>
.category-page {
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
      justify-content: space-between;
      padding: 0 $uni-spacing-row-base;
    }

    &__back {
      width: 56rpx;
      height: 56rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 56rpx;
      color: $uni-text-color;
      line-height: 1;
    }

    &__title {
      font-size: $uni-font-size-lg;
      font-weight: 600;
      color: $uni-text-color;
    }

    &__placeholder {
      width: 56rpx;
    }
  }

  &__body {
    padding: $uni-spacing-col-base $uni-spacing-row-base;
    padding-bottom: 60rpx;
  }

  // 分类信息卡
  &__info {
    margin-bottom: $uni-spacing-col-base;
  }

  &__info-name {
    display: flex;
    align-items: center;
    font-size: $uni-font-size-lg;
    font-weight: 600;
    color: $uni-text-color;
    margin-bottom: $uni-spacing-row-sm;
  }

  &__info-icon {
    font-size: $uni-font-size-title;
    margin-right: $uni-spacing-row-sm;
  }

  &__info-desc {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
    line-height: 1.6;
    margin-bottom: $uni-spacing-row-sm;
  }

  &__info-stat {
    font-size: $uni-font-size-sm;
    color: $uni-color-primary;
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
    }
  }

  &__list {
    padding-top: $uni-spacing-col-sm;
  }
}
</style>
