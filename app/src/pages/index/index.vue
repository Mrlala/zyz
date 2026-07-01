<template>
  <view class="chat-page">
    <!-- 顶部栏 -->
    <view class="chat-header" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="chat-header__inner">
        <view class="chat-header__btn" @click="drawerOpen = true" aria-label="菜单">
          <Menu :size="20" color="#6B7280" />
        </view>
        <view class="chat-header__btn chat-header__btn--sunken" @click="handleNewChat" aria-label="新对话">
          <Plus :size="18" color="#6B7280" />
        </view>
      </view>
    </view>

    <!-- 主内容区 -->
    <scroll-view
      scroll-y
      class="chat-body"
      :style="{ height: 'calc(100vh - ' + (statusBarHeight + 54) + 'px - 72px)' }"
      :scroll-into-view="scrollAnchor"
    >
      <!-- 空状态 -->
      <view v-if="!translateStore.currentResult && !translateStore.isLoading" class="chat-empty">
        <view class="chat-empty__title">中译中</view>
        <view class="chat-empty__subtitle">看不懂的中文，翻成人话</view>
        <view class="chat-empty__modes">
          <view
            v-for="m in modes"
            :key="m.key"
            class="chat-empty__mode"
            :class="{ 'chat-empty__mode--active': translateStore.mode === m.key }"
            @click="switchMode(m.key)"
          >{{ m.label }}</view>
        </view>
      </view>

      <!-- 加载状态 -->
      <view v-else-if="translateStore.isLoading" class="chat-loading">
        <view class="chat-loading__spinner"></view>
        <view class="chat-loading__text">正在把黑话翻译成人话...</view>
      </view>

      <!-- 对话结果 -->
      <view v-else-if="translateStore.currentResult" class="chat-result">
        <!-- 用户消息气泡 -->
        <view class="chat-user-msg">
          <view class="chat-user-msg__bubble">
            {{ translateStore.currentResult.original_text }}
          </view>
        </view>

        <!-- 系统结果头 -->
        <view class="chat-result__header">
          {{ modeLabel(translateStore.currentResult.mode) }} · 刚刚
        </view>

        <!-- 结构化结果卡片 -->
        <ResultCards
          :result="translateStore.currentResult"
          @keywordClick="handleKeywordClick"
          @relatedClick="handleRelatedClick"
          @copy="handleCopy"
          @feedback="handleFeedback"
        />
      </view>

      <view id="chat-bottom-anchor" class="chat-body__anchor"></view>
    </scroll-view>

    <!-- 底部输入框 -->
    <view class="chat-input" :style="{ paddingBottom: 'calc(8px + env(safe-area-inset-bottom, 0px))' }">
      <view class="chat-input__box">
        <view class="chat-input__plus" aria-label="能力菜单">
          <Plus :size="16" color="#6B7280" />
        </view>
        <textarea
          class="chat-input__textarea"
          v-model="inputText"
          :maxlength="MAX_LEN"
          placeholder="输入黑话、梗、暗语…"
          placeholder-class="chat-input__placeholder"
          :auto-height="true"
          :adjust-position="false"
          :show-confirm-bar="false"
          confirm-type="send"
          @confirm="handleTranslate"
        />
        <view
          v-if="!inputText.trim()"
          class="chat-input__mic"
          aria-label="语音输入"
        >
          <Mic :size="18" color="#9CA3AF" />
        </view>
        <view
          v-else
          class="chat-input__send"
          :class="{ 'chat-input__send--disabled': translateStore.isLoading }"
          @click="handleTranslate"
          aria-label="发送"
        >
          <ArrowUp :size="18" color="#FFFFFF" />
        </view>
      </view>
    </view>

    <!-- 左侧抽屉 -->
    <Drawer
      :open="drawerOpen"
      @close="drawerOpen = false"
      @navigate="handleNavigate"
      @selectHistory="handleSelectHistory"
      @newChat="handleNewChat"
    />
  </view>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { onLoad, onShow, onUnload } from '@dcloudio/uni-app'
import { Menu, Plus, ArrowUp, Mic } from 'lucide-vue-next'
import { useTranslateStore } from '@/store/modules/translate'
import { useUserStore } from '@/store/modules/user'
import ResultCards from '@/components/chat/ResultCards.vue'
import Drawer from '@/components/chat/Drawer.vue'
import * as feedbackApi from '@/api/feedback'
import storage from '@/utils/storage'

const translateStore = useTranslateStore()
const userStore = useUserStore()

const MAX_LEN = 50

// 状态栏高度
const statusBarHeight = ref(0)
// 输入文本
const inputText = ref('')
// 抽屉开关
const drawerOpen = ref(false)
// 滚动锚点（用于滚到底部）
const scrollAnchor = ref('')

// 模式配置
const modes = [
  { key: 'quick', label: '快速解析' },
  { key: 'deep', label: '深度解析' },
  { key: 'dict', label: '词典模式' }
]

function modeLabel(m) {
  const found = modes.find(x => x.key === m)
  return found ? found.label : '快速解析'
}

// 历史回填
function onFillText(text) {
  if (!text) return
  inputText.value = text
  handleTranslate()
}

onLoad(() => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }

  translateStore.restore()

  if (userStore.preferences && userStore.preferences.default_mode) {
    translateStore.setMode(userStore.preferences.default_mode)
  }

  uni.$off('translate:fill', onFillText)
  uni.$on('translate:fill', onFillText)
})

onShow(() => {})

onUnload(() => {
  uni.$off('translate:fill', onFillText)
})

// 切换模式
function switchMode(m) {
  translateStore.setMode(m)
  translateStore.clearResult()
}

// 新对话
function handleNewChat() {
  inputText.value = ''
  translateStore.clearResult()
  drawerOpen.value = false
}

// 执行翻译
async function handleTranslate() {
  const text = inputText.value.trim()
  if (!text) {
    uni.showToast({ title: '请输入要翻译的文本', icon: 'none' })
    return
  }
  if (translateStore.isLoading) return
  try {
    await translateStore.translate(text)
    // 翻译完成后滚到底部
    await nextTick()
    scrollAnchor.value = ''
    await nextTick()
    scrollAnchor.value = 'chat-bottom-anchor'
  } catch (err) {
    console.error('翻译失败', err)
  }
}

// 关键词点击：填入输入框翻译
function handleKeywordClick(word) {
  inputText.value = word
  handleTranslate()
}

// 相关推荐跳转
function handleRelatedClick(item) {
  const id = item.id || item.word_id
  if (id) {
    uni.navigateTo({ url: `/pages/word-detail/index?id=${id}` })
  }
}

// 复制
function handleCopy(text) {
  if (!text) return
  uni.setClipboardData({
    data: text,
    success: () => {
      uni.showToast({ title: '已复制', icon: 'success' })
    }
  })
}

// 反馈
function handleFeedback(type) {
  const result = translateStore.currentResult
  if (!result || !result.translation_id) return
  feedbackApi.submitFeedback({
    translation_id: result.translation_id,
    type
  }).catch(() => {})
}

// 抽屉导航
function handleNavigate(url) {
  drawerOpen.value = false
  setTimeout(() => {
    uni.navigateTo({ url })
  }, 200)
}

// 选择历史记录
function handleSelectHistory(item) {
  drawerOpen.value = false
  inputText.value = item.text
  handleTranslate()
}
</script>

<style lang="scss" scoped>
.chat-page {
  min-height: 100vh;
  background-color: $bg-page;
  display: flex;
  flex-direction: column;
}

/* ============ 顶部栏 ============ */
.chat-header {
  background-color: $bg-card;
  flex-shrink: 0;

  &__inner {
    height: 54px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 16px;
  }

  &__btn {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;

    &--sunken {
      background-color: $bg-sunken;
    }
  }
}

/* ============ 主内容区 ============ */
.chat-body {
  flex: 1;
  padding: 16px;
  box-sizing: border-box;

  &__anchor {
    height: 1px;
  }
}

/* ============ 空状态 ============ */
.chat-empty {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  &__title {
    font-size: 26px;
    font-weight: 700;
    color: $text-primary;
  }

  &__subtitle {
    margin-top: 8px;
    font-size: 15px;
    color: $text-tertiary;
    line-height: 1.6;
  }

  &__modes {
    display: flex;
    gap: 8px;
    margin-top: 16px;
  }

  &__mode {
    padding: 8px 16px;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 500;
    background-color: $bg-card;
    color: $text-secondary;
    border: 1px solid $border-color;

    &--active {
      background-color: $color-primary;
      color: #FFFFFF;
      border-color: $color-primary;
    }
  }
}

/* ============ 加载状态 ============ */
.chat-loading {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  &__spinner {
    width: 32px;
    height: 32px;
    border: 3px solid $border-color;
    border-top-color: $color-primary;
    border-radius: 50%;
    animation: chat-spin 0.8s linear infinite;
    margin-bottom: 12px;
  }

  &__text {
    font-size: 14px;
    color: $text-secondary;
  }
}

/* ============ 对话结果 ============ */
.chat-result {
  &__header {
    color: $text-tertiary;
    font-size: 12px;
    margin-bottom: 12px;
  }
}

/* ============ 用户消息气泡 ============ */
.chat-user-msg {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;

  &__bubble {
    display: inline-block;
    max-width: 80%;
    padding: 10px 16px;
    background-color: $bg-user-bubble;
    color: #FFFFFF;
    font-size: 14px;
    line-height: 1.6;
    border-radius: 18px 18px 4px 18px;
    word-break: break-word;
  }
}

/* ============ 底部输入框 ============ */
.chat-input {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 8px 16px;
  background: linear-gradient(to top, $bg-page 70%, transparent);
  z-index: 50;

  &__box {
    display: flex;
    align-items: flex-end;
    gap: 8px;
    background-color: $bg-elevated;
    border-radius: 20px;
    padding: 8px 12px;
    box-shadow: $shadow-sm;
  }

  &__plus {
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background-color: $bg-sunken;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__textarea {
    flex: 1;
    min-height: 20px;
    max-height: 120px;
    font-size: 14px;
    color: $text-primary;
    line-height: 1.5;
    background: transparent;
  }

  &__placeholder {
    color: $text-tertiary;
    font-size: 14px;
  }

  &__mic {
    flex-shrink: 0;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__send {
    flex-shrink: 0;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background-color: $color-primary;
    display: flex;
    align-items: center;
    justify-content: center;

    &--disabled {
      opacity: 0.5;
      pointer-events: none;
    }
  }
}

@keyframes chat-spin {
  to { transform: rotate(360deg); }
}
</style>
