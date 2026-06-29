<template>
  <view class="page favorites-page">
    <!-- 顶部自定义导航栏 -->
    <view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="nav-bar__inner">
        <view class="nav-bar__back" @click="handleBack">‹</view>
        <text class="nav-bar__title">我的收藏</text>
        <view class="nav-bar__placeholder"></view>
      </view>
    </view>
    <view class="nav-placeholder" :style="{ height: (statusBarHeight + 44) + 'px' }"></view>

    <view class="favorites-page__body">
      <!-- 加载中 -->
      <view v-if="loading" class="favorites-page__loading">
        <view class="favorites-page__loading-icon">⏳</view>
        <text class="favorites-page__loading-text">加载中...</text>
      </view>

      <template v-else>
        <WordCard
          v-for="word in words"
          :key="word.id"
          :word="word"
          @click="goDetail"
          @favorite="handleFavorite"
        />

        <EmptyState
          v-if="!words.length"
          icon="⭐"
          text="还没有收藏任何词条"
          btn-text="去逛逛词条"
          @btnClick="goDict"
        />
      </template>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import WordCard from '@/components/word/WordCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import * as wordApi from '@/api/word'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()

const statusBarHeight = ref(0)
const words = ref([])
const loading = ref(true)

onLoad(() => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
})

onShow(() => {
  fetchFavorites()
})

// 获取收藏列表：基于本地收藏 ID 拉取词条详情
async function fetchFavorites() {
  loading.value = true
  const ids = userStore.favoriteIds || []
  if (!ids.length) {
    words.value = []
    loading.value = false
    return
  }
  try {
    const tasks = ids.map((id) => wordApi.getWordDetail(id).catch(() => null))
    const list = await Promise.all(tasks)
    words.value = list.filter(Boolean)
  } catch (err) {
    console.error('获取收藏列表失败', err)
    words.value = []
  } finally {
    loading.value = false
  }
}

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

function goDetail(word) {
  const id = word.id || word.word_id
  if (id) {
    uni.navigateTo({ url: `/pages/word-detail/index?id=${id}` })
  }
}

function goDict() {
  uni.switchTab({ url: '/pages/dict/index' })
}

function handleBack() {
  uni.navigateBack({ delta: 1 })
}
</script>

<style lang="scss" scoped>
.favorites-page {
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

  &__loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: $uni-spacing-col-xl 0;
  }

  &__loading-icon {
    font-size: 96rpx;
    margin-bottom: $uni-spacing-col-base;
  }

  &__loading-text {
    font-size: $uni-font-size-base;
    color: $uni-text-color-grey;
  }
}
</style>
