<template>
  <view class="page history-page">
    <!-- 顶部自定义导航栏 -->
    <view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="nav-bar__inner">
        <view class="nav-bar__back" @click="handleBack">‹</view>
        <text class="nav-bar__title">{{ isTranslate ? '翻译历史' : '学习历史' }}</text>
        <view v-if="records.length" class="nav-bar__clear" @click="handleClear">清空</view>
        <view v-else class="nav-bar__placeholder"></view>
      </view>
    </view>
    <view class="nav-placeholder" :style="{ height: (statusBarHeight + 44) + 'px' }"></view>

    <view class="history-page__body">
      <!-- 翻译历史（本地存储） -->
      <template v-if="isTranslate">
        <view
          v-for="(item, idx) in translateRecords"
          :key="idx"
          class="history-page__item card"
          @click="retranslate(item)"
        >
          <view class="history-page__item-text">{{ item.text }}</view>
          <view class="history-page__item-footer">
            <text class="history-page__item-mode">{{ item.mode === 'dict' ? '词典' : '中译中' }}</text>
            <text class="history-page__item-time">{{ formatTime(item.created_at) }}</text>
          </view>
        </view>

        <EmptyState
          v-if="!translateRecords.length"
          icon="🔄"
          text="暂无翻译历史"
          btn-text="去翻译"
          @btnClick="goTranslate"
        />
      </template>

      <!-- 学习历史（接口数据） -->
      <template v-else>
        <view v-if="loading" class="history-page__loading">
          <view class="history-page__loading-icon">⏳</view>
          <text class="history-page__loading-text">加载中...</text>
        </view>

        <template v-else>
          <view
            v-for="item in records"
            :key="item.id || item.word_id"
            class="history-page__item card"
            @click="goDetail(item)"
          >
            <view class="history-page__item-header">
              <text class="history-page__item-word">{{ item.word || item.name }}</text>
              <text
                class="history-page__item-status"
                :class="item.mastered ? 'history-page__item-status--ok' : 'history-page__item-status--no'"
              >{{ item.mastered ? '已掌握' : '未掌握' }}</text>
            </view>
            <view v-if="item.summary || item.meaning" class="history-page__item-text">
              {{ item.summary || item.meaning }}
            </view>
            <view class="history-page__item-footer">
              <text class="history-page__item-time">{{ formatTime(item.learned_at || item.created_at) }}</text>
            </view>
          </view>

          <EmptyState
            v-if="!records.length"
            icon="📖"
            text="暂无学习记录"
            btn-text="去学热词"
            @btnClick="goHot"
          />

          <LoadMore
            v-if="records.length > 0"
            :status="loadMoreStatus"
            @loadMore="loadMore"
          />
        </template>
      </template>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onShow, onReachBottom } from '@dcloudio/uni-app'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadMore from '@/components/common/LoadMore.vue'
import * as hotApi from '@/api/hot'
import { useTranslateStore } from '@/store/modules/translate'

const translateStore = useTranslateStore()

const statusBarHeight = ref(0)
// 历史类型：translate 翻译历史 / 默认学习历史
const type = ref('')
const records = ref([])
const page = ref(1)
const pageSize = 20
const total = ref(0)
const loading = ref(false)

// 是否翻译历史
const isTranslate = computed(() => type.value === 'translate')
// 翻译历史记录（来自 store）
const translateRecords = computed(() => translateStore.history)

const loadMoreStatus = computed(() => {
  if (loading.value) return 'loading'
  if (records.value.length >= total.value && records.value.length > 0) return 'noMore'
  return 'more'
})

onLoad((options) => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
  type.value = (options && options.type) || ''
  if (!isTranslate.value) {
    fetchHistory(true)
  }
})

onShow(() => {
  if (isTranslate.value) {
    translateStore.restore()
  }
})

onReachBottom(() => {
  if (!isTranslate.value) loadMore()
})

// 获取学习历史
async function fetchHistory(reset = false) {
  if (loading.value) return
  loading.value = true
  if (reset) {
    page.value = 1
    records.value = []
  }
  try {
    const data = await hotApi.getHistory({ page: page.value, page_size: pageSize })
    const list = (data && data.list) || []
    total.value = (data && data.total) || 0
    records.value = reset ? list : records.value.concat(list)
  } catch (err) {
    console.error('获取学习历史失败', err)
  } finally {
    loading.value = false
  }
}

function loadMore() {
  if (loading.value || records.value.length >= total.value) return
  page.value++
  fetchHistory(false)
}

// 清空历史
function handleClear() {
  uni.showModal({
    title: '提示',
    content: isTranslate.value ? '确定清空翻译历史？' : '确定清空学习历史？',
    success: (res) => {
      if (res.confirm) {
        if (isTranslate.value) {
          translateStore.clearHistory()
          uni.showToast({ title: '已清空', icon: 'success' })
        }
      }
    }
  })
}

// 重新翻译
function retranslate(item) {
  // 通过全局事件或直接跳转首页并填入（简化：跳转首页）
  uni.switchTab({
    url: '/pages/index/index',
    success: () => {
      // 通知首页填入文本
      uni.$emit('translate:fill', item.text)
    }
  })
}

// 跳转词条详情
function goDetail(item) {
  const id = item.id || item.word_id
  if (id) {
    uni.navigateTo({ url: `/pages/word-detail/index?id=${id}` })
  }
}

function goTranslate() {
  uni.switchTab({ url: '/pages/index/index' })
}

function goHot() {
  uni.switchTab({ url: '/pages/hot/index' })
}

function handleBack() {
  uni.navigateBack({ delta: 1 })
}

// 格式化时间戳为可读时间
function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(typeof ts === 'number' ? ts : Date.parse(ts))
  if (isNaN(d.getTime())) return ''
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${m}-${day} ${h}:${min}`
}
</script>

<style lang="scss" scoped>
.history-page {
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

    &__clear {
      font-size: $uni-font-size-sm;
      color: $uni-color-error;
      padding: 0 $uni-spacing-row-sm;
    }

    &__placeholder {
      width: 80rpx;
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

  // 历史记录项
  &__item {
    margin-bottom: $uni-spacing-col-sm;
  }

  &__item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $uni-spacing-row-sm;
  }

  &__item-word {
    font-size: $uni-font-size-lg;
    font-weight: 600;
    color: $uni-text-color;
  }

  &__item-status {
    font-size: $uni-font-size-xs;
    padding: 4rpx $uni-spacing-row-sm;
    border-radius: 999rpx;

    &--ok {
      background-color: rgba(16, 185, 129, 0.1);
      color: $uni-color-success;
    }

    &--no {
      background-color: rgba(245, 158, 11, 0.1);
      color: $uni-color-warning;
    }
  }

  &__item-text {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
    line-height: 1.6;
    margin-bottom: $uni-spacing-row-sm;
    // 两行截断
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    overflow: hidden;
  }

  &__item-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  &__item-mode {
    font-size: $uni-font-size-xs;
    color: $uni-color-primary;
    background-color: rgba(79, 70, 229, 0.08);
    padding: 4rpx $uni-spacing-row-sm;
    border-radius: 999rpx;
  }

  &__item-time {
    font-size: $uni-font-size-xs;
    color: $uni-text-color-placeholder;
  }
}
</style>
