<template>
  <view class="chat-page">
    <!-- 顶部栏 -->
    <view class="chat-header" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="chat-header__inner">
        <view class="chat-header__btn" @click="drawerOpen = true" aria-label="菜单">
          <Menu :size="20" color="#6B7280" />
        </view>
        <view class="chat-header__btn chat-header__btn--sunken" @click="handleHeaderNewChat" aria-label="新对话">
          <Plus :size="18" color="#6B7280" />
        </view>
      </view>
    </view>

    <!-- 主内容区 -->
    <scroll-view
      scroll-y
      class="chat-body"
      :style="{ height: 'calc(100vh - ' + (statusBarHeight + 54) + 'px)', marginTop: (statusBarHeight + 54) + 'px', padding: '16px', paddingBottom: '100px' }"
      :scroll-into-view="scrollAnchor"
    >
      <!-- 空状态：当前会话无消息 -->
      <view
        v-if="translateStore.isEmpty"
        class="chat-empty"
      >
        <view class="chat-empty__center">
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
          <!-- 热词推荐 -->
          <view v-if="hotWords.length" class="chat-empty__hot">
            <text class="chat-empty__hot-title">试试这些</text>
            <view class="chat-empty__hot-chips">
              <view
                v-for="w in hotWords"
                :key="w.id"
                class="hot-chip"
                @click="handleHotWordClick(w)"
              >{{ w.word }}</view>
            </view>
          </view>
          <!-- AI 出错提示（仅空状态显示一次） -->
          <view class="chat-empty__ai-tip">
            <AlertCircle :size="12" color="#9CA3AF" />
            <text>AI 翻译仅供参考，如遇错误欢迎点击纠错</text>
          </view>
        </view>
      </view>

      <!-- 消息列表 -->
      <template v-else>
        <view
          v-for="(msg, idx) in translateStore.currentMessages"
          :key="idx"
        >
          <!-- 用户消息气泡 -->
          <view v-if="msg.role === 'user'" class="chat-user-msg">
            <view class="chat-user-msg__bubble">{{ msg.text }}</view>
          </view>

          <!-- 助手回复 -->
          <view v-else class="chat-result">
            <view class="chat-result__header">
              {{ modeLabel(msg.mode) }} · {{ formatMsgTime(msg.created_at) }}
            </view>
            <ResultCards
              :result="msg.result"
              @keywordClick="handleKeywordClick"
              @relatedClick="handleRelatedClick"
              @copy="handleCopy"
              @feedback="handleFeedback"
              @keywordFavorite="handleKeywordFavorite"
              @keywordCorrect="handleKeywordCorrect"
              @keywordSubmit="handleKeywordSubmit"
              @share="handleShare"
              @favorite="handleFavorite(msg)"
            />
          </view>
        </view>

        <!-- 加载状态 -->
        <view v-if="translateStore.isLoading" class="chat-loading">
          <view class="chat-loading__spinner"></view>
          <view class="chat-loading__text">正在把黑话翻译成人话...</view>
        </view>
      </template>

      <view id="chat-bottom-anchor" class="chat-body__anchor"></view>
    </scroll-view>

    <!-- 底部输入框 -->
    <view class="chat-input" :style="{ paddingBottom: 'calc(8px + env(safe-area-inset-bottom, 0px))' }">
      <!-- +号浮窗：快捷功能 -->
      <view v-if="plusOpen" class="chat-popover">
        <view class="chat-popover__arrow"></view>
        <view class="chat-popover__grid">
          <view
            v-for="fn in functions"
            :key="fn.key"
            class="chat-popover__item"
            @click="handlePopoverNavigate(fn.url)"
          >
            <view class="chat-popover__icon">
              <component :is="fn.icon" :size="20" color="#FE2C55" />
            </view>
            <text class="chat-popover__label">{{ fn.label }}</text>
          </view>
        </view>
      </view>

      <view class="chat-input__box">
        <view class="chat-input__plus" :class="{ 'chat-input__plus--active': plusOpen }" @click="handlePlus" aria-label="能力菜单">
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
          v-if="inputText.trim()"
          class="chat-input__send"
          :class="{ 'chat-input__send--disabled': translateStore.isLoading }"
          @click="handleTranslate"
          aria-label="发送"
        >
          <ArrowUp :size="18" color="#FFFFFF" />
        </view>
      </view>
    </view>

    <!-- 浮窗遮罩（点击关闭浮窗） -->
    <view v-if="plusOpen" class="chat-popover-mask" @click="plusOpen = false"></view>

    <!-- 左侧抽屉 -->
    <Drawer
      :open="drawerOpen"
      @close="drawerOpen = false"
      @navigate="handleNavigate"
      @selectSession="handleSelectSession"
      @newChat="handleNewChat"
    />

    <!-- 右侧词条解析抽屉 -->
    <WordDetailDrawer
      v-model:open="wordDrawerOpen"
      :word-id="currentWordId"
    />
  </view>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { onLoad, onShow, onUnload } from '@dcloudio/uni-app'
import { Menu, Plus, ArrowUp, BookOpen, ShieldCheck, Trophy, History, Star, Send, AlertCircle } from 'lucide-vue-next'
import { useTranslateStore } from '@/store/modules/translate'
import { useUserStore } from '@/store/modules/user'
import ResultCards from '@/components/chat/ResultCards.vue'
import Drawer from '@/components/chat/Drawer.vue'
import WordDetailDrawer from '@/components/chat/WordDetailDrawer.vue'
import * as feedbackApi from '@/api/feedback'
import * as userApi from '@/api/user'
import * as hotApi from '@/api/hot'
import * as correctionApi from '@/api/correction'
import { submitWord } from '@/api/submission'

const translateStore = useTranslateStore()
const userStore = useUserStore()

const MAX_LEN = 50

// 状态栏高度
const statusBarHeight = ref(0)
// 输入文本
const inputText = ref('')
// 抽屉开关
const drawerOpen = ref(false)
// +号浮窗开关
const plusOpen = ref(false)
// 滚动锚点（用于滚到底部）
const scrollAnchor = ref('')
// 空状态热词推荐
const hotWords = ref([])

// 词条解析抽屉（右侧滑入）
const wordDrawerOpen = ref(false)
const currentWordId = ref(null)

// 最后一条助手消息（用于反馈/收藏定位翻译结果）
const lastAssistantMsg = computed(() => {
  const msgs = translateStore.currentMessages
  if (!msgs || !msgs.length) return null
  for (let i = msgs.length - 1; i >= 0; i--) {
    if (msgs[i].role === 'assistant') return msgs[i]
  }
  return null
})

// 模式配置
const modes = [
  { key: 'quick', label: '快速解析' },
  { key: 'deep', label: '深度解析' },
  { key: 'dict', label: '词典模式' }
]

// 快捷功能入口（按权限过滤：审核仅管理员可见）
const functions = computed(() => {
  const list = [
    { key: 'dict', label: '词库', url: '/pages/dict/index', icon: BookOpen },
    { key: 'ranking', label: '热词排行', url: '/pages/hot/ranking', icon: Trophy },
    { key: 'history', label: '翻译历史', url: '/pages/mine/history?type=translate', icon: History },
    { key: 'favorites', label: '收藏', url: '/pages/mine/favorites', icon: Star },
    { key: 'submissions', label: '我的提交', url: '/pages/mine/submissions', icon: Send }
  ]
  if (userStore.isAdmin) {
    list.push({ key: 'review', label: '审核', url: '/pages/review/index', icon: ShieldCheck })
  }
  return list
})

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

  // 拉取空状态热词推荐（前 8 条）
  fetchHotWords()

  uni.$off('translate:fill', onFillText)
  uni.$on('translate:fill', onFillText)
})

// 拉取每日热词用于空状态推荐
async function fetchHotWords() {
  try {
    const data = await hotApi.getDaily()
    hotWords.value = (data?.list || []).slice(0, 8)
  } catch (e) {
    console.warn('热词推荐拉取失败', e)
  }
}

onShow(() => {})

onUnload(() => {
  uni.$off('translate:fill', onFillText)
})

// 切换模式
function switchMode(m) {
  translateStore.setMode(m)
}

// 新对话：创建新会话
function handleNewChat() {
  inputText.value = ''
  translateStore.newSession()
  drawerOpen.value = false
}

// 右上角+号：空会话提示已在新对话，有消息则创建新对话
function handleHeaderNewChat() {
  if (translateStore.isEmpty && !translateStore.isLoading) {
    uni.showToast({ title: '已在新对话中', icon: 'none' })
    return
  }
  handleNewChat()
  uni.showToast({ title: '已创建新对话', icon: 'none' })
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

// 关键词点击：打开右侧词条解析抽屉
function handleKeywordClick(kw) {
  const id = kw?.word_id || kw?.id
  if (!id) {
    // AI 临时生成的词条，无 word_id，提示而非触发翻译
    uni.showToast({
      title: '该词条为 AI 临时生成，暂不支持查看详情',
      icon: 'none',
      duration: 2000
    })
    return
  }
  currentWordId.value = id
  wordDrawerOpen.value = true
}

// 词条收藏（ResultCards 命中词条的收藏按钮）
async function handleKeywordFavorite(kw) {
  const id = kw?.word_id || kw?.id
  if (!id) {
    uni.showToast({ title: '该词条暂不支持收藏', icon: 'none' })
    return
  }
  try {
    await userStore.toggleFavorite(id)
    kw.is_favorited = userStore.isFavorited(id)
    uni.showToast({
      title: kw.is_favorited ? '已收藏' : '已取消收藏',
      icon: 'none'
    })
  } catch (err) {
    console.error('收藏失败', err)
    uni.showToast({ title: '收藏失败', icon: 'none' })
  }
}

// 词条纠错（ResultCards 命中词条的纠错按钮）
function handleKeywordCorrect(kw) {
  const id = kw?.word_id || kw?.id
  if (!id) {
    uni.showToast({ title: '该词条暂不支持纠错', icon: 'none' })
    return
  }
  const wordText = kw?.word || ''
  const correctionTypes = [
    { label: '释义错误', value: 'meaning_wrong' },
    { label: '例句/出处错误', value: 'example_wrong' },
    { label: '拼音错误', value: 'pinyin_wrong' },
    { label: '分类错误', value: 'category_wrong' },
    { label: '风险标注错误', value: 'risk_wrong' },
    { label: '已过时', value: 'outdated' },
    { label: '其他', value: 'other' }
  ]
  uni.showActionSheet({
    itemList: correctionTypes.map(t => t.label),
    success: (res) => {
      const type = correctionTypes[res.tapIndex].value
      uni.showModal({
        title: `纠错：${wordText}`,
        editable: true,
        placeholderText: '请描述正确的内容或问题',
        success: (r) => {
          if (r.confirm && r.content) {
            correctionApi.submitCorrection({
              word_id: id,
              type,
              content: r.content
            }).then(() => {
              uni.showToast({ title: '已提交，感谢纠错', icon: 'success' })
            }).catch(() => {
              uni.showToast({ title: '提交失败', icon: 'none' })
            })
          }
        }
      })
    }
  })
}

// 空状态热词 chip 点击：填入并翻译
function handleHotWordClick(w) {
  inputText.value = w.word
  handleTranslate()
}

// AI 临时词条一键提交到词库（ResultCards 命中词条的提交按钮）
function handleKeywordSubmit(kw) {
  const word = kw?.word
  if (!word) return
  uni.showModal({
    title: '提交到词库',
    content: `是否将「${word}」提交到词库？提交后将进入审核队列。`,
    success: async (r) => {
      if (!r.confirm) return
      try {
        await submitWord({
          word,
          definition: kw.current_meaning || kw.meaning || kw.definition || '',
          example: kw.example || '',
          category_id: kw.category_id || null
        })
        uni.showToast({ title: '已提交，待审核', icon: 'success' })
      } catch (err) {
        const status = err?.statusCode || err?.status
        if (status === 409) {
          uni.showToast({ title: '该词条已存在或已提交', icon: 'none' })
        } else {
          uni.showToast({ title: '提交失败，请稍后重试', icon: 'none' })
        }
      }
    }
  })
}

// 继续追问：填入提示词，聚焦输入框，不自动发送
function handleFollowUp(result) {
  const kw = result?.keywords?.[0]?.word
  inputText.value = kw ? `详细说说「${kw}」` : '详细说说'
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

// 分享：生成纯文本卡片，复制到剪贴板或调用系统分享
function handleShare(shareData) {
  const { translation, original_text, keywords, context, subtext } = shareData
  // 组装分享文本：原文 → 翻译 → 关键词
  let shareText = `【中译中】\n原文：${original_text || '（无）'}\n人话：${translation || '（无）'}`
  if (keywords && keywords.length) {
    const kwText = keywords.slice(0, 3).map(k => `${k.word}${k.meaning ? '：' + k.meaning : ''}`).join('\n')
    shareText += `\n\n词条解析：\n${kwText}`
  }
  if (subtext) {
    shareText += `\n\n潜台词：${subtext}`
  }

  // H5 环境：复制到剪贴板 + 提示
  // #ifdef H5
  uni.setClipboardData({
    data: shareText,
    success: () => {
      uni.showToast({ title: '已复制翻译结果，可粘贴分享', icon: 'none', duration: 2500 })
    }
  })
  // #endif

  // 小程序/App 环境：调用系统分享
  // #ifndef H5
  uni.share({
    provider: 'weixin',
    scene: 'WXSceneSession',
    type: 1,
    summary: translation || '中译中翻译结果',
    title: '中译中翻译',
    href: '',
    success: () => {
      uni.showToast({ title: '分享成功', icon: 'success' })
    },
    fail: () => {
      // 分享失败则回退到复制
      uni.setClipboardData({
        data: shareText,
        success: () => {
          uni.showToast({ title: '已复制，可粘贴分享', icon: 'none' })
        }
      })
    }
  })
  // #endif
}

// 反馈：accurate 直接提交；inaccurate 弹输入框收集备注后提交
function handleFeedback(type) {
  const msg = lastAssistantMsg.value
  if (!msg || !msg.translation_id) return

  if (type === 'inaccurate') {
    uni.showModal({
      title: '反馈说明',
      editable: true,
      placeholderText: '请简要说明哪里不准确（可选）',
      success: (res) => {
        if (res.confirm) {
          submitFeedback(type, res.content || '')
        }
      }
    })
    return
  }
  submitFeedback(type, '')
}

// 提交反馈到后端
function submitFeedback(type, comment) {
  const msg = lastAssistantMsg.value
  if (!msg || !msg.translation_id) return
  feedbackApi.submitFeedback({
    translation_id: msg.translation_id,
    type,
    comment: comment || undefined
  }).then(() => {
    uni.showToast({ title: '感谢反馈', icon: 'success' })
  }).catch(() => {
    uni.showToast({ title: '反馈失败', icon: 'none' })
  })
}

// 收藏/取消收藏翻译结果（D12）
async function handleFavorite(msg) {
  if (!msg || !msg.translation_id) {
    uni.showToast({ title: '暂无可收藏的结果', icon: 'none' })
    return
  }
  try {
    const data = await userApi.toggleTranslationFavorite(msg.translation_id)
    // 同步更新消息中的收藏状态
    msg.result.is_translation_favorited = !!data?.is_favorited
    uni.showToast({ title: data?.message || '操作成功', icon: 'success' })
  } catch (err) {
    console.error('收藏失败', err)
    uni.showToast({ title: '收藏失败', icon: 'none' })
  }
}

// 抽屉导航
function handleNavigate(url) {
  drawerOpen.value = false
  setTimeout(() => {
    uni.navigateTo({ url })
  }, 200)
}

// +号按钮：切换浮窗
function handlePlus() {
  plusOpen.value = !plusOpen.value
}

// 浮窗内导航
function handlePopoverNavigate(url) {
  plusOpen.value = false
  setTimeout(() => {
    uni.navigateTo({ url })
  }, 200)
}

// 选择（恢复）某个会话
function handleSelectSession(sessionId) {
  translateStore.selectSession(sessionId)
  drawerOpen.value = false
  inputText.value = ''
  // 滚到底部
  nextTick(() => {
    scrollAnchor.value = ''
    nextTick(() => {
      scrollAnchor.value = 'chat-bottom-anchor'
    })
  })
}

// 格式化消息时间
function formatMsgTime(ts) {
  if (!ts) return '刚刚'
  const diff = Date.now() - ts
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return Math.floor(diff / 86400000) + '天前'
}
</script>

<style lang="scss" scoped>
.chat-page {
  height: 100vh;
  overflow: hidden;
  background-color: $bg-page;
  display: flex;
  flex-direction: column;
}

/* ============ 顶部栏 ============ */
.chat-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 40;
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
  padding-left: 16px;
  padding-right: 16px;
  box-sizing: border-box;

  &__anchor {
    height: 1px;
  }
}

/* ============ 空状态 ============ */
.chat-empty {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 24px 0;

  &__center {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

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

  &__hot {
    margin-top: 32px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  &__hot-title {
    font-size: 12px;
    color: $text-tertiary;
    margin-bottom: 12px;
  }

  &__hot-chips {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px;
    max-width: 320px;
  }
}

.hot-chip {
  padding: 6px 14px;
  border-radius: 9999px;
  background-color: rgba(254, 44, 85, 0.08);
  color: $color-primary;
  font-size: 13px;
  font-weight: 500;

  &:active {
    background-color: rgba(254, 44, 85, 0.16);
  }
}

/* AI 出错提示（仅空状态显示） */
.chat-empty__ai-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 24px;
  font-size: 11px;
  color: $text-tertiary;
}

/* ============ +号浮窗 ============ */
.chat-popover {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 12px;
  width: 260px;
  background-color: $bg-card;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.12);
  padding: 12px;
  z-index: 35;

  &__arrow {
    position: absolute;
    bottom: -6px;
    left: 20px;
    width: 12px;
    height: 12px;
    background-color: $bg-card;
    transform: rotate(45deg);
    box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.05);
  }

  &__grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
  }

  &__item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    padding: 10px 4px;
    border-radius: 10px;

    &:active {
      background-color: $bg-sunken;
    }
  }

  &__icon {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background-color: rgba(254, 44, 85, 0.08);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__label {
    font-size: 12px;
    color: $text-secondary;
  }
}

/* 浮窗遮罩：z-index 低于 chat-input(30)，避免遮挡 popover */
.chat-popover-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 29;
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
  z-index: 30;

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
    transition: background-color 0.2s;

    &--active {
      background-color: $color-primary;
    }
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
