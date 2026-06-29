<template>
  <view class="page index-page">
    <!-- 顶部自定义导航栏 -->
    <view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="nav-bar__inner">
        <text class="nav-bar__title">中译中</text>
        <view class="nav-bar__mode">
          <view
            class="nav-bar__mode-item"
            :class="{ 'nav-bar__mode-item--active': translateStore.mode === 'translate' }"
            @click="switchMode('translate')"
          >中译中</view>
          <view
            class="nav-bar__mode-item"
            :class="{ 'nav-bar__mode-item--active': translateStore.mode === 'dict' }"
            @click="switchMode('dict')"
          >词典</view>
        </view>
      </view>
    </view>

    <!-- 占位，避免内容被固定导航栏遮挡 -->
    <view class="nav-placeholder" :style="{ height: (statusBarHeight + 44) + 'px' }"></view>

    <!-- 主体内容 -->
    <scroll-view scroll-y class="index-page__body" :style="{ height: 'calc(100vh - ' + (statusBarHeight + 44) + 'px)' }">
      <!-- 输入区 -->
      <view class="index-page__input card">
        <textarea
          class="index-page__textarea"
          v-model="inputText"
          :maxlength="MAX_LEN"
          :placeholder="placeholderText"
          placeholder-class="index-page__placeholder"
          auto-height
          :adjust-position="true"
          @confirm="handleTranslate"
        />
        <view class="index-page__input-footer">
          <text class="index-page__count" :class="{ 'index-page__count--max': inputText.length >= MAX_LEN }">
            {{ inputText.length }}/{{ MAX_LEN }}
          </text>
          <view class="index-page__clear" v-if="inputText" @click="handleClear">清空</view>
        </view>
      </view>

      <!-- 翻译按钮 -->
      <view
        class="index-page__translate-btn btn btn-primary"
        :class="{ 'btn-disabled': translateStore.isLoading || !inputText.trim() }"
        @click="handleTranslate"
      >
        <view v-if="translateStore.isLoading" class="index-page__spinner"></view>
        <text>{{ translateStore.isLoading ? '翻译中...' : '翻译' }}</text>
      </view>

      <!-- 快捷示例 -->
      <view class="index-page__examples">
        <view class="index-page__examples-title">快捷示例</view>
        <scroll-view scroll-x class="index-page__examples-scroll" :show-scrollbar="false">
          <view class="index-page__examples-list">
            <view
              v-for="(item, idx) in examples"
              :key="idx"
              class="index-page__example-tag"
              @click="handleExampleClick(item)"
            >
              {{ item }}
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- 翻译结果区 -->
      <view class="index-page__result">
        <!-- 加载中骨架 -->
        <view v-if="translateStore.isLoading" class="index-page__loading card">
          <view class="index-page__loading-icon">🤔</view>
          <text class="index-page__loading-text">正在把黑话翻译成人话...</text>
        </view>

        <!-- 翻译结果 -->
        <TranslateResult
          v-else-if="translateStore.currentResult"
          :result="translateStore.currentResult"
          @keywordClick="handleKeywordClick"
          @relatedClick="handleRelatedClick"
          @feedback="handleFeedback"
          @copy="handleCopy"
        />

        <!-- 空状态 -->
        <view v-else class="index-page__empty card">
          <view class="index-page__empty-icon">📝</view>
          <view class="index-page__empty-title">输入一句黑话试试</view>
          <view class="index-page__empty-desc">
            支持「黑话 / 梗 / 术语」翻译，{{ translateStore.mode === 'dict' ? '词典模式快速匹配词条' : 'AI 帮你翻译成人话' }}
          </view>
        </view>
      </view>

      <!-- 底部留白 -->
      <view class="index-page__bottom-space"></view>
    </scroll-view>

    <!-- 新手引导蒙层 -->
    <view v-if="showGuide" class="guide" @click.stop>
      <view class="guide__mask"></view>
      <view class="guide__panel">
        <view class="guide__step">第 {{ guideStep + 1 }} / 3 步</view>
        <view class="guide__icon">{{ guideSteps[guideStep].icon }}</view>
        <view class="guide__title">{{ guideSteps[guideStep].title }}</view>
        <view class="guide__desc">{{ guideSteps[guideStep].desc }}</view>
        <view class="guide__btns">
          <view class="guide__btn guide__btn--skip" @click="finishGuide">跳过</view>
          <view v-if="guideStep > 0" class="guide__btn guide__btn--prev" @click="prevGuide">上一步</view>
          <view class="guide__btn guide__btn--next" @click="nextGuide">
            {{ guideStep < guideSteps.length - 1 ? '下一步' : '开始翻译' }}
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onShow, onUnload } from '@dcloudio/uni-app'
import { useTranslateStore } from '@/store/modules/translate'
import { useUserStore } from '@/store/modules/user'
import TranslateResult from '@/components/translate/TranslateResult.vue'
import * as feedbackApi from '@/api/feedback'
import storage from '@/utils/storage'

const translateStore = useTranslateStore()
const userStore = useUserStore()

// 翻译历史回填：由「翻译历史」页通过事件触发
function onFillText(text) {
  if (!text) return
  inputText.value = text
  handleTranslate()
}

// 输入最大字数
const MAX_LEN = 50
// 新手引导本地存储键
const GUIDE_KEY = 'zyz_guide_shown'

// 状态栏高度（自定义导航栏适配）
const statusBarHeight = ref(0)
// 输入文本
const inputText = ref('')
// 是否显示新手引导
const showGuide = ref(false)
// 引导当前步骤
const guideStep = ref(0)

// 快捷示例（本地预置，覆盖常见黑话/梗/术语）
const examples = [
  '今天又 996 了',
  'yyds',
  '这波操作很 6',
  '打工人打工魂',
  'emo 了',
  'u1s1 讲道理'
]

// 引导步骤配置
const guideSteps = [
  {
    icon: '🔄',
    title: '中译中是什么',
    desc: '把网络黑话、梗、专业术语翻译成「人话」，让你秒懂对方在说什么。'
  },
  {
    icon: '✍️',
    title: '怎么玩',
    desc: '在输入框输入或粘贴一句含黑话的话，点击翻译，即可获得对比展示与关键词解释。'
  },
  {
    icon: '🚀',
    title: '开始翻译',
    desc: '也可以点击「快捷示例」直接体验，左上角可切换词典模式快速匹配词条。'
  }
]

// 输入框占位文案
const placeholderText = computed(() => {
  return translateStore.mode === 'dict'
    ? '输入关键词，词典模式快速匹配词条'
    : '输入一句含黑话的话，如「今天又 996 了」'
})

onLoad(() => {
  // 获取状态栏高度
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }

  // 恢复翻译历史与模式
  translateStore.restore()

  // 同步用户默认翻译模式偏好
  if (userStore.preferences && userStore.preferences.default_mode) {
    translateStore.setMode(userStore.preferences.default_mode)
  }

  // 首次打开展示新手引导
  const shown = storage.get(GUIDE_KEY)
  if (!shown) {
    showGuide.value = true
  }

  // 监听翻译历史回填事件
  uni.$off('translate:fill', onFillText)
  uni.$on('translate:fill', onFillText)
})

onShow(() => {
  // 用户偏好可能在设置页变更，回到首页时同步默认模式
  if (userStore.preferences && userStore.preferences.default_mode) {
    // 仅在用户未手动切换时同步
  }
})

onUnload(() => {
  uni.$off('translate:fill', onFillText)
})

// 切换翻译模式
function switchMode(m) {
  translateStore.setMode(m)
  translateStore.clearResult()
}

// 点击快捷示例：填充并自动翻译
function handleExampleClick(text) {
  inputText.value = text
  handleTranslate()
}

// 清空输入与结果
function handleClear() {
  inputText.value = ''
  translateStore.clearResult()
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
  } catch (err) {
    // 请求层已统一 toast，这里仅兜底
    console.error('翻译失败', err)
  }
}

// 点击结果中的关键词，跳转词条详情（若有关键词条目 id 则跳转，否则填入输入框翻译）
function handleKeywordClick(word) {
  inputText.value = word
  handleTranslate()
}

// 点击相关推荐，跳转词条详情
function handleRelatedClick(item) {
  const id = item.id || item.word_id
  if (id) {
    uni.navigateTo({ url: `/pages/word-detail/index?id=${id}` })
  }
}

// 复制建议回复
function handleCopy(text) {
  if (!text) return
  uni.setClipboardData({
    data: text,
    success: () => {
      uni.showToast({ title: '已复制', icon: 'success' })
    }
  })
}

// 翻译质量反馈
function handleFeedback(type) {
  const result = translateStore.currentResult
  if (!result || !result.translation_id) return
  feedbackApi.submitFeedback({
    translation_id: result.translation_id,
    type
  }).catch(() => {})
}

// 引导：下一步
function nextGuide() {
  if (guideStep.value < guideSteps.length - 1) {
    guideStep.value++
  } else {
    finishGuide()
  }
}

// 引导：上一步
function prevGuide() {
  if (guideStep.value > 0) guideStep.value--
}

// 引导：完成/跳过
function finishGuide() {
  showGuide.value = false
  storage.set(GUIDE_KEY, true)
}
</script>

<style lang="scss" scoped>
.index-page {
  min-height: 100vh;
  background-color: $uni-bg-color;

  // 自定义导航栏
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

    &__title {
      font-size: $uni-font-size-title;
      font-weight: 700;
      color: $uni-text-color;
    }

    &__mode {
      display: flex;
      background-color: $uni-bg-color;
      border-radius: 999rpx;
      padding: 4rpx;
    }

    &__mode-item {
      padding: 8rpx $uni-spacing-row-base;
      font-size: $uni-font-size-sm;
      color: $uni-text-color-grey;
      border-radius: 999rpx;
      transition: all 0.2s;

      &--active {
        background-color: $uni-color-primary;
        color: #FFFFFF;
        font-weight: 600;
      }
    }
  }

  &__body {
    box-sizing: border-box;
    padding: $uni-spacing-col-base $uni-spacing-row-base;
  }

  // 输入区
  &__input {
    margin-bottom: $uni-spacing-col-base;
  }

  &__textarea {
    width: 100%;
    min-height: 160rpx;
    font-size: $uni-font-size-base;
    color: $uni-text-color;
    line-height: 1.6;
    box-sizing: border-box;
  }

  &__placeholder {
    color: $uni-text-color-placeholder;
    font-size: $uni-font-size-base;
  }

  &__input-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: $uni-spacing-row-sm;
    padding-top: $uni-spacing-row-sm;
    border-top: 2rpx solid $uni-border-color;
  }

  &__count {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;

    &--max {
      color: $uni-color-error;
    }
  }

  &__clear {
    font-size: $uni-font-size-sm;
    color: $uni-color-primary;
    padding: 4rpx $uni-spacing-row-sm;
  }

  // 翻译按钮
  &__translate-btn {
    width: 100%;
    height: 88rpx;
    margin-bottom: $uni-spacing-col-base;
    font-size: $uni-font-size-lg;
    font-weight: 600;
  }

  &__spinner {
    width: 32rpx;
    height: 32rpx;
    margin-right: $uni-spacing-row-sm;
    border: 4rpx solid rgba(255, 255, 255, 0.4);
    border-top-color: #FFFFFF;
    border-radius: 50%;
    animation: index-spin 0.8s linear infinite;
  }

  // 快捷示例
  &__examples {
    margin-bottom: $uni-spacing-col-base;
  }

  &__examples-title {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
    margin-bottom: $uni-spacing-row-sm;
  }

  &__examples-scroll {
    white-space: nowrap;
  }

  &__examples-list {
    display: inline-flex;
    gap: $uni-spacing-row-sm;
    padding-bottom: 4rpx;
  }

  &__example-tag {
    display: inline-block;
    padding: 12rpx $uni-spacing-row-base;
    background-color: #FFFFFF;
    border-radius: 999rpx;
    font-size: $uni-font-size-sm;
    color: $uni-color-primary;
    border: 2rpx solid rgba(79, 70, 229, 0.2);
    flex-shrink: 0;

    &:active {
      background-color: rgba(79, 70, 229, 0.08);
    }
  }

  // 结果区
  &__result {
    margin-bottom: $uni-spacing-col-base;
  }

  &__loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: $uni-spacing-col-lg $uni-spacing-row-base;
  }

  &__loading-icon {
    font-size: 80rpx;
    margin-bottom: $uni-spacing-row-base;
    animation: index-bounce 1s ease-in-out infinite;
  }

  &__loading-text {
    font-size: $uni-font-size-base;
    color: $uni-text-color-grey;
  }

  // 空状态
  &__empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: $uni-spacing-col-lg $uni-spacing-row-base;
  }

  &__empty-icon {
    font-size: 96rpx;
    margin-bottom: $uni-spacing-col-base;
    opacity: 0.7;
  }

  &__empty-title {
    font-size: $uni-font-size-lg;
    color: $uni-text-color;
    font-weight: 600;
    margin-bottom: $uni-spacing-row-sm;
  }

  &__empty-desc {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
    text-align: center;
    line-height: 1.6;
  }

  &__bottom-space {
    height: 60rpx;
  }
}

// 新手引导蒙层
.guide {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;

  &__mask {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.6);
  }

  &__panel {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    width: 600rpx;
    background-color: #FFFFFF;
    border-radius: $uni-border-radius;
    padding: $uni-spacing-col-lg $uni-spacing-row-lg;
    text-align: center;
  }

  &__step {
    font-size: $uni-font-size-sm;
    color: $uni-color-primary;
    margin-bottom: $uni-spacing-col-base;
  }

  &__icon {
    font-size: 120rpx;
    line-height: 1;
    margin-bottom: $uni-spacing-col-base;
  }

  &__title {
    font-size: $uni-font-size-title;
    font-weight: 700;
    color: $uni-text-color;
    margin-bottom: $uni-spacing-row-base;
  }

  &__desc {
    font-size: $uni-font-size-base;
    color: $uni-text-color-grey;
    line-height: 1.7;
    margin-bottom: $uni-spacing-col-lg;
    text-align: left;
  }

  &__btns {
    display: flex;
    gap: $uni-spacing-row-sm;
  }

  &__btn {
    flex: 1;
    height: 72rpx;
    line-height: 72rpx;
    text-align: center;
    border-radius: $uni-border-radius;
    font-size: $uni-font-size-base;

    &--skip {
      background-color: $uni-bg-color;
      color: $uni-text-color-grey;
    }

    &--prev {
      background-color: $uni-bg-color;
      color: $uni-text-color;
    }

    &--next {
      background-color: $uni-color-primary;
      color: #FFFFFF;
      font-weight: 600;
    }
  }
}

@keyframes index-spin {
  to { transform: rotate(360deg); }
}

@keyframes index-bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-16rpx); }
}
</style>
