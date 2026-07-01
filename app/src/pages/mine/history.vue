<template>
  <view class="history-page">
    <!-- 顶部栏 -->
    <view class="top-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="top-bar__inner">
        <view class="top-bar__btn" @click="handleBack">
          <ArrowLeft :size="20" color="#6B7280" />
        </view>
        <text class="top-bar__title">翻译历史</text>
        <view v-if="translateSessions.length" class="top-bar__action" @click="handleClear">清空</view>
        <view v-else class="top-bar__placeholder"></view>
      </view>
    </view>
    <view class="top-bar-placeholder" :style="{ height: (statusBarHeight + 54) + 'px' }"></view>

    <view class="history-body">
      <!-- 翻译历史（本地会话列表） -->
      <view
        v-for="item in translateSessions"
        :key="item.id"
        class="history-card"
        @click="restoreSession(item)"
      >
        <text class="history-card__text">{{ item.title }}</text>
        <view class="history-card__footer">
          <text class="history-card__mode">{{ item.messages.length }}条对话</text>
          <text class="history-card__time">{{ formatTime(item.updated_at) }}</text>
        </view>
      </view>

      <!-- 空状态 -->
      <view v-if="!translateSessions.length" class="empty-state">
        <view class="empty-state__icon">
          <RotateCcw :size="32" color="#9CA3AF" />
        </view>
        <text class="empty-state__text">暂无翻译历史</text>
        <view class="empty-state__btn" @click="goTranslate">
          <text class="empty-state__btn-text">去翻译</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { ArrowLeft, RotateCcw } from 'lucide-vue-next'
import { useTranslateStore } from '@/store/modules/translate'

const translateStore = useTranslateStore()

const statusBarHeight = ref(0)

// 翻译会话列表（来自 store，按更新时间倒序）
const translateSessions = computed(() =>
  [...(translateStore.sessions || [])].sort((a, b) => b.updated_at - a.updated_at)
)

onLoad(() => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
})

onShow(() => {
  translateStore.restore()
})

// 清空全部翻译会话
function handleClear() {
  uni.showModal({
    title: '提示',
    content: '确定清空全部翻译会话？',
    success: (res) => {
      if (res.confirm) {
        translateStore.clearAllSessions()
        uni.showToast({ title: '已清空', icon: 'success' })
      }
    }
  })
}

// 恢复某个会话：跳回首页并选中该会话
function restoreSession(item) {
  translateStore.selectSession(item.id)
  uni.reLaunch({ url: '/pages/index/index' })
}

// 去翻译
function goTranslate() {
  uni.reLaunch({ url: '/pages/index/index' })
}

// 返回：有返回栈则 navigateBack，无则回首页
function handleBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    uni.navigateBack({ delta: 1 })
  } else {
    uni.reLaunch({ url: '/pages/index/index' })
  }
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

  &__text {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    overflow: hidden;
    font-size: 14px;
    color: $text-primary;
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
</style>
