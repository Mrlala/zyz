<template>
  <view class="settings-page">
    <!-- 顶部栏 -->
    <view class="top-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="top-bar__inner">
        <view class="top-bar__btn" @click="handleBack">
          <ArrowLeft :size="20" color="#6B7280" />
        </view>
        <text class="top-bar__title">设置</text>
        <view class="top-bar__placeholder"></view>
      </view>
    </view>
    <view class="top-bar-placeholder" :style="{ height: (statusBarHeight + 54) + 'px' }"></view>

    <view class="settings-body">
      <!-- 分组1 账号 -->
      <view class="group-card">
        <!-- 头像 -->
        <view class="group-row" @click="goEditProfile">
          <text class="group-row__label">头像</text>
          <view class="group-row__right">
            <view class="avatar-wrap">
              <view class="avatar-inner" :style="avatarInnerStyle">
                <text class="avatar-text">{{ avatarDisplay }}</text>
              </view>
            </view>
            <ChevronRight :size="16" color="#C0C4CC" />
          </view>
        </view>
        <view class="group-divider"></view>
        <!-- 昵称 -->
        <view class="group-row" @click="goEditProfile">
          <text class="group-row__label">昵称</text>
          <view class="group-row__right">
            <text class="group-row__value">{{ userName }}</text>
            <ChevronRight :size="16" color="#C0C4CC" />
          </view>
        </view>
        <view class="group-divider"></view>
        <!-- 我的成就 -->
        <view class="group-row" @click="goAchievements">
          <text class="group-row__label">我的成就</text>
          <view class="group-row__right">
            <ChevronRight :size="16" color="#C0C4CC" />
          </view>
        </view>
      </view>

      <!-- 分组2 偏好设置 -->
      <text class="group-title">偏好设置</text>
      <view class="group-card">
        <!-- 默认解析模式 -->
        <view class="group-row" @click="selectDefaultMode">
          <text class="group-row__label">默认解析模式</text>
          <view class="group-row__right">
            <text class="group-row__value">{{ defaultModeLabel }}</text>
            <ChevronRight :size="16" color="#C0C4CC" />
          </view>
        </view>
        <view class="group-divider"></view>
        <!-- 深色模式 -->
        <view class="group-row">
          <text class="group-row__label">深色模式</text>
          <view
            class="toggle-switch"
            :class="{ 'toggle-switch--on': darkMode }"
            @click="toggleDarkMode"
          >
            <view class="toggle-knob"></view>
          </view>
        </view>
        <view class="group-divider"></view>
        <!-- 推送通知 -->
        <view class="group-row">
          <text class="group-row__label">推送通知</text>
          <view
            class="toggle-switch"
            :class="{ 'toggle-switch--on': pushNotify }"
            @click="pushNotify = !pushNotify"
          >
            <view class="toggle-knob"></view>
          </view>
        </view>
      </view>

      <!-- 分组3 关于 -->
      <text class="group-title">关于</text>
      <view class="group-card">
        <!-- 版本 -->
        <view class="group-row">
          <text class="group-row__label">版本</text>
          <text class="group-row__value">v{{ version }}</text>
        </view>
        <view class="group-divider"></view>
        <!-- AI 服务状态（D16） -->
        <view class="group-row">
          <text class="group-row__label">AI 服务</text>
          <view class="group-row__right">
            <view
              class="ai-dot"
              :class="aiStatus.available ? 'ai-dot--on' : 'ai-dot--off'"
            ></view>
            <text class="group-row__value">{{ aiStatus.text }}</text>
          </view>
        </view>
        <view class="group-divider"></view>
        <!-- 隐私政策 -->
        <view class="group-row" @click="goAgreement('privacy')">
          <text class="group-row__label">隐私政策</text>
          <ChevronRight :size="16" color="#C0C4CC" />
        </view>
        <view class="group-divider"></view>
        <!-- 用户协议 -->
        <view class="group-row" @click="goAgreement('terms')">
          <text class="group-row__label">用户协议</text>
          <ChevronRight :size="16" color="#C0C4CC" />
        </view>
        <view class="group-divider"></view>
        <!-- 清除缓存 -->
        <view class="group-row" @click="clearCache">
          <text class="group-row__label group-row__label--danger">清除缓存</text>
          <ChevronRight :size="16" color="#C0C4CC" />
        </view>
      </view>

      <!-- 退出登录 -->
      <view v-if="userStore.isLoggedIn" class="logout-btn" @click="handleLogout">
        <text class="logout-btn__text">退出登录</text>
      </view>
      <view v-else class="login-btn" @click="goLogin">
        <text class="login-btn__text">去登录</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { ArrowLeft, ChevronRight } from 'lucide-vue-next'
import { useUserStore } from '@/store/modules/user'
import { useTranslateStore } from '@/store/modules/translate'
import storage from '@/utils/storage'
import { APP_VERSION } from '@/config/env'
import * as configApi from '@/api/config'

const userStore = useUserStore()
const translateStore = useTranslateStore()

const statusBarHeight = ref(0)
const version = ref(APP_VERSION)
const pushNotify = ref(true)
// AI 服务状态（D16）
const aiStatus = ref({ available: false, text: '检测中...' })

// 模式映射：前端 quick/deep → 后端 translate；dict → dict
const modeOptions = [
  { key: 'translate', label: '快速解析' },
  { key: 'dict', label: '词典模式' }
]

// 默认解析模式
const defaultModeLabel = computed(() => {
  const m = userStore.preferences?.default_mode || 'translate'
  const found = modeOptions.find(x => x.key === m)
  return found ? found.label : '快速解析'
})

// 深色模式（从 preferences.theme 派生）
const darkMode = computed(() => {
  return userStore.preferences?.theme === 'dark'
})

const userName = computed(() => userStore.userInfo?.nickname || '匿名用户')
// 预设头像 emoji 映射（与 profile-setup.vue 一致）
const AVATAR_MAP = {
  cat: { emoji: '🐱', bg: 'linear-gradient(135deg, #FFE0B2, #FFCC80)' },
  dog: { emoji: '🐶', bg: 'linear-gradient(135deg, #FFCDD2, #EF9A9A)' },
  panda: { emoji: '🐼', bg: 'linear-gradient(135deg, #ECEFF1, #CFD8DC)' },
  fox: { emoji: '🦊', bg: 'linear-gradient(135deg, #FFE0B2, #FFB74D)' },
  bear: { emoji: '🐻', bg: 'linear-gradient(135deg, #D7CCC8, #BCAAA4)' },
  rabbit: { emoji: '🐰', bg: 'linear-gradient(135deg, #F8BBD0, #F48FB1)' },
  lion: { emoji: '🦁', bg: 'linear-gradient(135deg, #FFF9C4, #FFF176)' },
  frog: { emoji: '🐸', bg: 'linear-gradient(135deg, #C8E6C9, #A5D6A7)' }
}
const avatarDisplay = computed(() => {
  const key = userStore.userInfo?.avatar
  if (key && AVATAR_MAP[key]) return AVATAR_MAP[key].emoji
  const name = userName.value
  return name ? name.charAt(0) : '?'
})
const avatarInnerStyle = computed(() => {
  const key = userStore.userInfo?.avatar
  if (key && AVATAR_MAP[key]) {
    return { background: AVATAR_MAP[key].bg }
  }
  return { backgroundColor: '#F3F4F6' }
})

onLoad(() => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
})

// 页面显示时主动拉取最新 profile（D4）与 AI 服务状态（D16）
onShow(() => {
  if (userStore.isLoggedIn) {
    userStore.fetchProfile().catch(() => {})
  }
  fetchAiStatus()
})

// 拉取 AI 服务配置状态
async function fetchAiStatus() {
  try {
    const data = await configApi.getAiStatus()
    aiStatus.value = {
      available: !!data?.available,
      text: data?.mode || (data?.available ? 'AI实时翻译' : '本地词库模式')
    }
  } catch (e) {
    aiStatus.value = { available: false, text: '检测失败' }
  }
}

// 选择默认解析模式
function selectDefaultMode() {
  uni.showActionSheet({
    itemList: modeOptions.map(x => x.label),
    success: (res) => {
      const selected = modeOptions[res.tapIndex]
      userStore.updatePreferences({ default_mode: selected.key })
        .then(() => {
          uni.showToast({ title: '已更新', icon: 'success' })
        })
        .catch(() => {
          uni.showToast({ title: '更新失败', icon: 'none' })
        })
    }
  })
}

// 切换深色模式
function toggleDarkMode() {
  const next = darkMode.value ? 'light' : 'dark'
  userStore.updatePreferences({ theme: next })
    .then(() => {
      uni.showToast({ title: darkMode.value ? '已关闭' : '已开启', icon: 'none' })
    })
    .catch(() => {
      uni.showToast({ title: '更新失败', icon: 'none' })
    })
}

// 清除缓存
function clearCache() {
  uni.showModal({
    title: '提示',
    content: '确定清除本地缓存？登录状态将保留',
    success: (res) => {
      if (res.confirm) {
        storage.remove('zyz_search_history')
        storage.remove('zyz_translate_sessions')
        storage.remove('zyz_translate_current_session')
        translateStore.clearAllSessions()
        uni.showToast({ title: '已清除', icon: 'success' })
      }
    }
  })
}

// 退出登录
function handleLogout() {
  uni.showModal({
    title: '提示',
    content: '确定退出登录？',
    success: (res) => {
      if (res.confirm) {
        userStore.logout()
        uni.showToast({ title: '已退出', icon: 'success' })
        // 退出后跳转登录页
        setTimeout(() => {
          uni.reLaunch({ url: '/pages/auth/login' })
        }, 500)
      }
    }
  })
}

// 跳转登录页
function goLogin() {
  uni.reLaunch({ url: '/pages/auth/login' })
}

function handleBack() {
  uni.navigateBack({ delta: 1 })
}

// 跳转成就页
function goAchievements() {
  uni.navigateTo({ url: '/pages/mine/achievements' })
}

// 跳转资料编辑页（复用 profile-setup，编辑模式）
function goEditProfile() {
  uni.navigateTo({ url: '/pages/auth/profile-setup?mode=edit' })
}

// 跳转协议页（隐私政策 / 用户协议）
function goAgreement(type) {
  uni.navigateTo({ url: `/pages/mine/agreement?type=${type}` })
}
</script>

<style lang="scss" scoped>
.settings-page {
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
.settings-body {
  padding: 12px 16px 32px;
}

/* ============ 分组卡片 ============ */
.group-card {
  margin-top: 12px;
  background-color: $bg-card;
  border-radius: 12px;
  box-shadow: $shadow-xs;
  overflow: hidden;
}

.group-title {
  display: block;
  margin-top: 24px;
  margin-bottom: 8px;
  padding-left: 4px;
  font-size: 11px;
  color: $text-tertiary;
}

.group-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  padding: 0 16px;

  &__label {
    font-size: 14px;
    color: $text-primary;

    &--danger {
      color: $color-danger;
    }
  }

  &__right {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  &__value {
    font-size: 14px;
    color: $text-tertiary;
  }
}

.group-divider {
  height: 1px;
  background-color: $border-color-light;
  margin-left: 16px;
}

/* ============ 头像 ============ */
.avatar-wrap {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  padding: 2px;
  background: $gradient-primary;
}

.avatar-inner {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background-color: $bg-sunken;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-text {
  font-size: 15px;
  font-weight: 500;
  color: $text-secondary;
}

/* ============ Toggle 开关 ============ */
.toggle-switch {
  position: relative;
  width: 44px;
  height: 24px;
  border-radius: 12px;
  background-color: $border-color;
  transition: background-color 0.2s ease;
  flex-shrink: 0;

  &--on {
    background-color: $color-primary;
  }
}

.toggle-knob {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: #FFFFFF;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease;
}

.toggle-switch--on .toggle-knob {
  transform: translateX(20px);
}

/* ============ AI 服务状态圆点 ============ */
.ai-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;

  &--on {
    background-color: $color-success;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
  }

  &--off {
    background-color: $border-color;
  }
}

/* ============ 退出登录 ============ */
.logout-btn {
  margin-top: 24px;
  padding: 14px 0;
  text-align: center;

  &__text {
    font-size: 14px;
    font-weight: 500;
    color: $color-danger;
  }

  &:active {
    opacity: 0.6;
  }
}

.login-btn {
  margin-top: 24px;
  padding: 14px 0;
  text-align: center;
  background-color: $color-primary;
  border-radius: 12px;

  &__text {
    font-size: 14px;
    font-weight: 500;
    color: #FFFFFF;
  }

  &:active {
    opacity: 0.8;
  }
}
</style>
