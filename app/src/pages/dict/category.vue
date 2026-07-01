<template>
  <view class="category-page">
    <!-- 顶部栏 -->
    <view class="top-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="top-bar__inner">
        <view class="top-bar__btn" @click="handleBack">
          <ArrowLeft :size="20" color="#6B7280" />
        </view>
        <text class="top-bar__title">{{ categoryInfo.name || '分类词条' }}</text>
        <view class="top-bar__placeholder"></view>
      </view>
    </view>
    <view class="top-bar-placeholder" :style="{ height: (statusBarHeight + 54) + 'px' }"></view>

    <view class="category-body">
      <!-- 分类信息卡 -->
      <view v-if="categoryInfo.name" class="info-card">
        <view class="info-card__name">
          <Folder :size="20" color="#FE2C55" />
          <text>{{ categoryInfo.name }}</text>
        </view>
        <view v-if="categoryInfo.description" class="info-card__desc">
          {{ categoryInfo.description }}
        </view>
        <view class="info-card__stat">共 {{ total }} 个词条</view>
      </view>

      <!-- 排序条 -->
      <view class="sort-bar">
        <view
          v-for="item in sortOptions"
          :key="item.value"
          class="sort-bar__item"
          :class="{ 'sort-bar__item--active': sort === item.value }"
          @click="switchSort(item.value)"
        >{{ item.label }}</view>
      </view>

      <!-- 词条列表 -->
      <view class="word-list">
        <WordCard
          v-for="word in words"
          :key="word.id"
          :word="word"
          @click="goDetail"
          @favorite="handleFavorite"
        />

        <!-- 空状态 -->
        <view v-if="!loading && words.length === 0" class="empty-state">
          <view class="empty-state__icon">
            <FolderOpen :size="32" color="#9CA3AF" />
          </view>
          <text class="empty-state__text">该分类下暂无词条</text>
        </view>

        <!-- 加载更多 -->
        <view v-if="words.length > 0" class="load-more" @click="loadMore">
          <text>{{ loading ? '加载中...' : (words.length >= total ? '没有更多了' : '点击加载更多') }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onReachBottom, onPullDownRefresh } from '@dcloudio/uni-app'
import { ArrowLeft, Folder, FolderOpen } from 'lucide-vue-next'
import WordCard from '@/components/word/WordCard.vue'
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

  &__placeholder {
    width: 32px;
  }
}

.top-bar-placeholder {
  width: 100%;
}

/* ============ 主体 ============ */
.category-body {
  padding: 12px 16px 32px;
}

/* ============ 分类信息卡 ============ */
.info-card {
  padding: 16px;
  background-color: $bg-card;
  border-radius: 12px;
  box-shadow: $shadow-sm;
  margin-bottom: 12px;

  &__name {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: 8px;
  }

  &__desc {
    font-size: 13px;
    color: $text-secondary;
    line-height: 1.6;
    margin-bottom: 8px;
  }

  &__stat {
    font-size: 13px;
    color: $color-primary;
  }
}

/* ============ 排序条 ============ */
.sort-bar {
  display: flex;
  align-items: center;
  padding: 8px 0 12px;
  border-bottom: 1px solid $border-color-light;
  margin-bottom: 8px;
  gap: 16px;

  &__item {
    font-size: 13px;
    color: $text-secondary;

    &--active {
      color: $color-primary;
      font-weight: 600;
    }
  }
}

/* ============ 词条列表 ============ */
.word-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
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
