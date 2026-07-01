<template>
  <view class="history-page">
    <!-- 顶部栏 -->
    <view class="top-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="top-bar__inner">
        <view class="top-bar__btn" @click="handleBack">
          <ArrowLeft :size="20" color="#6B7280" />
        </view>
        <text class="top-bar__title">{{ isTranslate ? '翻译历史' : '浏览历史' }}</text>
        <view v-if="records.length || translateRecords.length" class="top-bar__action" @click="handleClear">清空</view>
        <view v-else class="top-bar__placeholder"></view>
      </view>
    </view>
    <view class="top-bar-placeholder" :style="{ height: (statusBarHeight + 54) + 'px' }"></view>

    <view class="history-body">
      <!-- 翻译历史（本地存储） -->
      <template v-if="isTranslate">
        <view
          v-for="(item, idx) in translateRecords"
          :key="idx"
          class="history-card"
          @click="retranslate(item)"
        >
          <text class="history-card__text">{{ item.text }}</text>
          <view class="history-card__footer">
            <text class="history-card__mode">{{ item.mode === 'dict' ? '词典' : '中译中' }}</text>
            <text class="history-card__time">{{ formatTime(item.created_at) }}</text>
          </view>
        </view>

        <!-- 翻译历史空状态 -->
        <view v-if="!translateRecords.length" class="empty-state">
          <view class="empty-state__icon">
            <RotateCcw :size="32" color="#9CA3AF" />
          </view>
          <text class="empty-state__text">暂无翻译历史</text>
          <view class="empty-state__btn" @click="goTranslate">
            <text class="empty-state__btn-text">去翻译</text>
          </view>
        </view>
      </template>

      <!-- 浏览历史（接口数据） -->
      <template v-else>
        <view v-if="loading" class="state-tip">
          <text>加载中...</text>
        </view>

        <template v-else>
          <view
            v-for="item in records"
            :key="item.id || item.word_id"
            class="history-card"
            @click="goDetail(item)"
          >
            <view class="history-card__header">
              <text class="history-card__word">{{ item.word || item.name }}</text>
              <text
                class="history-card__status"
                :class="item.mastered ? 'history-card__status--ok' : 'history-card__status--no'"
              >{{ item.mastered ? '已掌握' : '未掌握' }}</text>
            </view>
            <view v-if="item.summary || item.meaning" class="history-card__text">
              {{ item.summary || item.meaning }}
            </view>
            <view class="history-card__footer">
              <text class="history-card__time">{{ formatTime(item.learned_at || item.created_at) }}</text>
            </view>
          </view>

          <!-- 浏览历史空状态 -->
          <view v-if="!records.length" class="empty-state">
            <view class="empty-state__icon">
              <BookOpen :size="32" color="#9CA3AF" />
            </view>
            <text class="empty-state__text">暂无浏览记录</text>
            <view class="empty-state__btn" @click="goHot">
              <text class="empty-state__btn-text">去热词排行</text>
            </view>
          </view>

          <!-- 加载更多 -->
          <view v-if="records.length > 0" class="load-more" @click="loadMore">
            <text>{{ loading ? '加载中...' : (records.length >= total ? '没有更多了' : '点击加载更多') }}</text>
          </view>
        </template>
      </template>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onShow, onReachBottom } from '@dcloudio/uni-app'
import { ArrowLeft, RotateCcw, BookOpen } from 'lucide-vue-next'
import * as hotApi from '@/api/hot'
import { useTranslateStore } from '@/store/modules/translate'

const translateStore = useTranslateStore()

const statusBarHeight = ref(0)
// 历史类型：translate 翻译历史 / 默认浏览历史
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

// 获取浏览历史
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
    console.error('获取浏览历史失败', err)
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
    content: isTranslate.value ? '确定清空翻译历史？' : '确定清空浏览历史？',
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

// 重新翻译（修复失效 switchTab → reLaunch）
function retranslate(item) {
  uni.reLaunch({
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

// 去翻译（修复失效 switchTab → reLaunch）
function goTranslate() {
  uni.reLaunch({ url: '/pages/index/index' })
}

// 去热词排行（修复失效 switchTab + 路由不存在 → navigateTo ranking）
function goHot() {
  uni.navigateTo({ url: '/pages/hot/ranking' })
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

  &__action {
    font-size: 14px;
    color: $color-danger;
    padding: 0 4px;
  }

  &__placeholder {
    width: 32px;
  }
}

.top-bar-placeholder {
  width: 100%;
}

/* ============ 主体 ============ */
.history-body {
  padding: 12px 16px 32px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* ============ 历史记录卡 ============ */
.history-card {
  padding: 14px 16px;
  background-color: $bg-card;
  border-radius: 12px;
  box-shadow: $shadow-sm;

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  &__word {
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
  }

  &__status {
    font-size: 12px;
    padding: 2px 8px;
    border-radius: 9999px;

    &--ok {
      background-color: rgba(16, 185, 129, 0.1);
      color: $color-success;
    }

    &--no {
      background-color: rgba(245, 158, 11, 0.1);
      color: $color-warning;
    }
  }

  &__text {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    overflow: hidden;
    font-size: 13px;
    color: $text-secondary;
    line-height: 1.6;
    margin-bottom: 8px;
  }

  &__footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  &__mode {
    font-size: 12px;
    color: $color-primary;
    background-color: rgba(254, 44, 85, 0.08);
    padding: 2px 8px;
    border-radius: 9999px;
  }

  &__time {
    font-size: 12px;
    color: $text-tertiary;
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
