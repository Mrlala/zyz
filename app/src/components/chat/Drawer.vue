<template>
  <view v-if="open" class="drawer-mask" @click="handleClose"></view>
  <view class="drawer" :class="{ 'drawer--open': open }">
    <!-- 头部 -->
    <view class="drawer__header">
      <view class="drawer__brand">
        <text class="drawer__brand-name">中译中</text>
        <text class="drawer__brand-sub">中文语境理解 Skill</text>
      </view>
      <view class="drawer__close" @click="handleClose">
        <X :size="20" color="#9CA3AF" />
      </view>
    </view>

    <!-- 搜索框 -->
    <view class="drawer__search">
      <Search :size="16" color="#9CA3AF" />
      <input
        class="drawer__search-input"
        placeholder="搜索对话内容"
        placeholder-class="drawer__search-placeholder"
        v-model="searchText"
      />
    </view>

    <!-- 新对话按钮 -->
    <view class="drawer__new-chat" @click="handleNewChat">
      <Plus :size="16" color="#6B7280" />
      <text class="drawer__new-chat-text">新对话</text>
    </view>

    <!-- 滚动内容区 -->
    <scroll-view scroll-y class="drawer__content">
      <!-- 知识库组 -->
      <view class="drawer__group-title">知识库</view>
      <view class="drawer__menu">
        <view class="drawer__menu-item" v-for="item in knowledgeMenu" :key="item.key" @click="handleNavigate(item.url)">
          <component :is="item.icon" :size="20" color="#6B7280" />
          <text class="drawer__menu-text">{{ item.label }}</text>
          <ChevronRight :size="16" color="#D1D5DB" />
        </view>
      </view>

      <!-- 我的内容组 -->
      <view class="drawer__group-title">我的内容</view>
      <view class="drawer__menu">
        <view class="drawer__menu-item" v-for="item in myMenu" :key="item.key" @click="handleNavigate(item.url)">
          <component :is="item.icon" :size="20" color="#6B7280" />
          <text class="drawer__menu-text">{{ item.label }}</text>
          <ChevronRight :size="16" color="#D1D5DB" />
        </view>
      </view>

      <!-- 最近对话组 -->
      <view class="drawer__group-title">最近对话</view>
      <view class="drawer__menu">
        <view
          v-for="(item, idx) in recentHistory"
          :key="idx"
          class="drawer__menu-item drawer__menu-item--history"
          @click="handleSelectHistory(item)"
        >
          <text class="drawer__menu-text drawer__menu-text--history">{{ item.text }}</text>
          <text class="drawer__menu-time">{{ formatTime(item.created_at) }}</text>
        </view>
        <view v-if="!recentHistory.length" class="drawer__empty">暂无历史对话</view>
      </view>
    </scroll-view>

    <!-- 底部用户栏 -->
    <view class="drawer__footer">
      <view class="drawer__user" @click="handleNavigate('/pages/mine/settings')">
        <view class="drawer__avatar-wrap">
          <view class="drawer__avatar">
            <text class="drawer__avatar-text">{{ avatarText }}</text>
          </view>
        </view>
        <view class="drawer__user-info">
          <text class="drawer__user-name">{{ userName }}</text>
          <text class="drawer__user-sub">{{ userSub }}</text>
        </view>
        <view class="drawer__settings-btn" @click.stop="handleNavigate('/pages/mine/settings')">
          <Settings :size="18" color="#9CA3AF" />
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  X, Search, Plus, BookOpen, ShieldCheck, Trophy,
  Star, Send, ChevronRight, Settings, History
} from 'lucide-vue-next'
import { useTranslateStore } from '@/store/modules/translate'
import { useUserStore } from '@/store/modules/user'

const props = defineProps({
  open: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'navigate', 'selectHistory', 'newChat'])

const translateStore = useTranslateStore()
const userStore = useUserStore()

const searchText = ref('')

// 知识库菜单
const knowledgeMenu = [
  { key: 'dict', label: '词库', url: '/pages/dict/index', icon: BookOpen },
  { key: 'review', label: '审核', url: '/pages/review/index', icon: ShieldCheck },
  { key: 'ranking', label: '热词排行', url: '/pages/hot/ranking', icon: Trophy }
]

// 我的内容菜单
const myMenu = [
  { key: 'history', label: '浏览历史', url: '/pages/mine/history', icon: History },
  { key: 'favorites', label: '收藏', url: '/pages/mine/favorites', icon: Star },
  { key: 'submissions', label: '我的提交', url: '/pages/mine/submissions', icon: Send }
]

// 最近对话（取前5条）
const recentHistory = computed(() => {
  return (translateStore.history || []).slice(0, 5)
})

// 用户信息
const userName = computed(() => userStore.userInfo?.nickname || '匿名用户')
const userSub = computed(() => userStore.userInfo?.username || '')
const avatarText = computed(() => {
  const name = userName.value
  return name ? name.charAt(0) : '?'
})

function handleClose() {
  emit('close')
}

function handleNewChat() {
  emit('newChat')
}

function handleNavigate(url) {
  emit('navigate', url)
}

function handleSelectHistory(item) {
  emit('selectHistory', item)
}

function formatTime(ts) {
  if (!ts) return ''
  const now = Date.now()
  const diff = now - ts
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return Math.floor(diff / 86400000) + '天前'
}
</script>

<style lang="scss" scoped>
.drawer-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: $bg-mask;
  z-index: 40;
}

.drawer {
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  width: 85%;
  max-width: 320px;
  background-color: #FFFFFF;
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.1);
  border-radius: 0 20px 20px 0;
  z-index: 41;
  display: flex;
  flex-direction: column;
  transform: translateX(-100%);
  transition: transform 0.25s cubic-bezier(0.3, 0, 0, 1);

  &--open {
    transform: translateX(0);
  }

  &__header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    padding: 20px 20px 12px;
  }

  &__brand {
    flex: 1;
  }

  &__brand-name {
    display: block;
    font-size: 20px;
    font-weight: 700;
    color: $text-primary;
  }

  &__brand-sub {
    display: block;
    font-size: 13px;
    color: $text-tertiary;
    margin-top: 2px;
  }

  &__close {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__search {
    display: flex;
    align-items: center;
    height: 40px;
    background-color: $bg-sunken;
    border-radius: 10px;
    padding: 0 12px;
    margin: 0 20px 12px;
    gap: 8px;
  }

  &__search-input {
    flex: 1;
    font-size: 14px;
    color: $text-primary;
    background: transparent;
  }

  &__search-placeholder {
    color: $text-tertiary;
    font-size: 14px;
  }

  &__new-chat {
    display: flex;
    align-items: center;
    gap: 12px;
    height: 40px;
    margin: 0 20px 16px;
    border-radius: 10px;
    background-color: #FFFFFF;
    border: 1px solid $border-color;
    padding: 0 16px;
  }

  &__new-chat-text {
    font-size: 14px;
    color: $text-secondary;
  }

  &__content {
    flex: 1;
    overflow-y: auto;
  }

  &__group-title {
    font-size: 11px;
    font-weight: 600;
    color: $text-tertiary;
    letter-spacing: 0.05em;
    padding: 16px 20px 8px;
  }

  &__menu {
    border-top: 1px solid $border-color-light;
  }

  &__menu-item {
    display: flex;
    align-items: center;
    gap: 12px;
    height: 48px;
    padding: 0 20px;
    border-bottom: 1px solid $border-color-light;

    &--history {
      padding: 0 20px;
    }
  }

  &__menu-text {
    flex: 1;
    font-size: 14px;
    color: $text-primary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;

    &--history {
      color: $text-primary;
    }
  }

  &__menu-time {
    flex-shrink: 0;
    font-size: 12px;
    color: $text-tertiary;
  }

  &__empty {
    padding: 16px 20px;
    font-size: 13px;
    color: $text-tertiary;
    text-align: center;
  }

  &__footer {
    flex-shrink: 0;
    border-top: 1px solid $border-color;
  }

  &__user {
    display: flex;
    align-items: center;
    gap: 12px;
    height: 56px;
    padding: 0 20px;
  }

  &__avatar-wrap {
    flex-shrink: 0;
    padding: 2px;
    border-radius: 50%;
    background: linear-gradient(135deg, #FE2C55, #25F4EE);
  }

  &__avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background-color: $bg-sunken;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__avatar-text {
    font-size: 14px;
    font-weight: 500;
    color: $text-secondary;
  }

  &__user-info {
    flex: 1;
    overflow: hidden;
  }

  &__user-name {
    display: block;
    font-size: 14px;
    font-weight: 500;
    color: $text-primary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__user-sub {
    display: block;
    font-size: 12px;
    color: $text-tertiary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__settings-btn {
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}
</style>
