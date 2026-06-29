<template>
  <view class="page settings-page">
    <!-- 顶部自定义导航栏 -->
    <view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="nav-bar__inner">
        <view class="nav-bar__back" @click="handleBack">‹</view>
        <text class="nav-bar__title">设置</text>
        <view class="nav-bar__placeholder"></view>
      </view>
    </view>
    <view class="nav-placeholder" :style="{ height: (statusBarHeight + 44) + 'px' }"></view>

    <view class="settings-page__body">
      <!-- 默认翻译模式 -->
      <view class="settings-page__group">
        <view class="settings-page__group-title">翻译偏好</view>
        <view class="settings-page__group-body card">
          <view class="settings-page__item">
            <text class="settings-page__item-label">默认翻译模式</text>
            <view class="settings-page__seg">
              <view
                class="settings-page__seg-item"
                :class="{ 'settings-page__seg-item--active': prefs.default_mode === 'translate' }"
                @click="setPref('default_mode', 'translate')"
              >中译中</view>
              <view
                class="settings-page__seg-item"
                :class="{ 'settings-page__seg-item--active': prefs.default_mode === 'dict' }"
                @click="setPref('default_mode', 'dict')"
              >词典</view>
            </view>
          </view>
          <view class="settings-page__divider"></view>
          <view class="settings-page__item">
            <text class="settings-page__item-label">风险提示</text>
            <view
              class="settings-page__switch"
              :class="{ 'settings-page__switch--on': prefs.show_risk_advice }"
              @click="toggleRisk"
            >
              <view class="settings-page__switch-dot"></view>
            </view>
          </view>
        </view>
      </view>

      <!-- 显示设置 -->
      <view class="settings-page__group">
        <view class="settings-page__group-title">显示设置</view>
        <view class="settings-page__group-body card">
          <view class="settings-page__item">
            <text class="settings-page__item-label">深色模式</text>
            <view class="settings-page__seg">
              <view
                class="settings-page__seg-item"
                :class="{ 'settings-page__seg-item--active': prefs.theme === 'light' }"
                @click="setPref('theme', 'light')"
              >浅色</view>
              <view
                class="settings-page__seg-item"
                :class="{ 'settings-page__seg-item--active': prefs.theme === 'dark' }"
                @click="setPref('theme', 'dark')"
              >深色</view>
              <view
                class="settings-page__seg-item"
                :class="{ 'settings-page__seg-item--active': prefs.theme === 'auto' }"
                @click="setPref('theme', 'auto')"
              >跟随系统</view>
            </view>
          </view>
          <view class="settings-page__divider"></view>
          <view class="settings-page__item settings-page__item--col">
            <text class="settings-page__item-label">字体大小</text>
            <view class="settings-page__font-size">
              <view
                v-for="opt in fontOptions"
                :key="opt.value"
                class="settings-page__font-item"
                :class="{
                  'settings-page__font-item--active': prefs.font_size === opt.value,
                  'settings-page__font-item--sm': opt.value === 'small',
                  'settings-page__font-item--lg': opt.value === 'large'
                }"
                @click="setPref('font_size', opt.value)"
              >{{ opt.label }}</view>
            </view>
          </view>
        </view>
      </view>

      <!-- 其他 -->
      <view class="settings-page__group">
        <view class="settings-page__group-title">其他</view>
        <view class="settings-page__group-body card">
          <view class="settings-page__item" @click="resetGuide">
            <text class="settings-page__item-label">重置新手引导</text>
            <text class="settings-page__item-arrow">›</text>
          </view>
          <view class="settings-page__divider"></view>
          <view class="settings-page__item" @click="clearCache">
            <text class="settings-page__item-label">清除缓存</text>
            <text class="settings-page__item-arrow">›</text>
          </view>
          <view class="settings-page__divider"></view>
          <view class="settings-page__item">
            <text class="settings-page__item-label">版本号</text>
            <text class="settings-page__item-value">v{{ version }}</text>
          </view>
        </view>
      </view>

      <!-- 退出登录 -->
      <view v-if="userStore.isLoggedIn" class="settings-page__logout" @click="handleLogout">
        退出登录
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useUserStore } from '@/store/modules/user'
import { useAppStore } from '@/store/modules/app'
import storage from '@/utils/storage'
import { APP_VERSION } from '@/config/env'

const userStore = useUserStore()
const appStore = useAppStore()

const statusBarHeight = ref(0)
const version = ref(APP_VERSION)

// 本地偏好副本（编辑后同步到后端）
const prefs = reactive({
  default_mode: 'translate',
  show_risk_advice: true,
  font_size: 'medium',
  theme: 'auto'
})

const fontOptions = [
  { label: '小', value: 'small' },
  { label: '中', value: 'medium' },
  { label: '大', value: 'large' }
]

onLoad(() => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
  // 从用户偏好初始化
  Object.assign(prefs, userStore.preferences)
})

// 设置偏好并同步
async function setPref(key, value) {
  prefs[key] = value
  // 同步本地 app store
  if (key === 'theme') {
    appStore.setTheme(value === 'dark' ? 'dark' : 'light')
  } else if (key === 'font_size') {
    appStore.setFontSize(value)
  }
  // 同步后端
  try {
    await userStore.updatePreferences({ [key]: value })
    uni.showToast({ title: '已保存', icon: 'success' })
  } catch (err) {
    console.error('保存偏好失败', err)
  }
}

// 切换风险提示开关
async function toggleRisk() {
  const next = !prefs.show_risk_advice
  prefs.show_risk_advice = next
  // 同步 app store（仅在当前值与新值不一致时切换，避免重复翻转）
  if (appStore.showRiskWarning !== next) {
    appStore.toggleRiskWarning()
  }
  try {
    await userStore.updatePreferences({ show_risk_advice: next })
    uni.showToast({ title: '已保存', icon: 'success' })
  } catch (err) {
    console.error('保存失败', err)
  }
}

// 重置新手引导
function resetGuide() {
  uni.showModal({
    title: '提示',
    content: '下次打开翻译页将重新展示新手引导',
    success: (res) => {
      if (res.confirm) {
        storage.remove('zyz_guide_shown')
        uni.showToast({ title: '已重置', icon: 'success' })
      }
    }
  })
}

// 清除缓存
function clearCache() {
  uni.showModal({
    title: '提示',
    content: '确定清除本地缓存？登录状态将保留',
    success: (res) => {
      if (res.confirm) {
        // 清理非关键缓存（保留 token、user、设备 ID）
        storage.remove('zyz_search_history')
        storage.remove('zyz_translate_history')
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
        setTimeout(() => {
          uni.switchTab({ url: '/pages/mine/index' })
        }, 800)
      }
    }
  })
}

function handleBack() {
  uni.navigateBack({ delta: 1 })
}
</script>

<style lang="scss" scoped>
.settings-page {
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

  // 分组
  &__group {
    margin-bottom: $uni-spacing-col-base;
  }

  &__group-title {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
    margin-bottom: $uni-spacing-row-sm;
    padding-left: $uni-spacing-row-sm;
  }

  &__group-body {
    padding: 0;
    overflow: hidden;
  }

  &__item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: $uni-spacing-col-base $uni-spacing-row-base;
    min-height: 96rpx;

    &--col {
      flex-direction: column;
      align-items: stretch;
    }

    &:active {
      background-color: $uni-bg-color;
    }
  }

  &__item-label {
    font-size: $uni-font-size-base;
    color: $uni-text-color;
  }

  &__item-value {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
  }

  &__item-arrow {
    font-size: $uni-font-size-lg;
    color: $uni-text-color-placeholder;
  }

  &__divider {
    height: 2rpx;
    background-color: $uni-border-color;
    margin-left: $uni-spacing-row-base;
  }

  // 分段选择器
  &__seg {
    display: flex;
    background-color: $uni-bg-color;
    border-radius: 999rpx;
    padding: 4rpx;
  }

  &__seg-item {
    padding: 8rpx $uni-spacing-row-base;
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
    border-radius: 999rpx;

    &--active {
      background-color: $uni-color-primary;
      color: #FFFFFF;
      font-weight: 600;
    }
  }

  // 开关
  &__switch {
    width: 88rpx;
    height: 48rpx;
    border-radius: 999rpx;
    background-color: $uni-border-color;
    position: relative;
    transition: background-color 0.2s;

    &--on {
      background-color: $uni-color-primary;
    }
  }

  &__switch-dot {
    position: absolute;
    top: 4rpx;
    left: 4rpx;
    width: 40rpx;
    height: 40rpx;
    border-radius: 50%;
    background-color: #FFFFFF;
    transition: transform 0.2s;
    box-shadow: 0 2rpx 4rpx rgba(0, 0, 0, 0.2);
  }

  &__switch--on &__switch-dot {
    transform: translateX(40rpx);
  }

  // 字体大小
  &__font-size {
    display: flex;
    gap: $uni-spacing-row-sm;
    margin-top: $uni-spacing-row-sm;
  }

  &__font-item {
    flex: 1;
    text-align: center;
    padding: 16rpx 0;
    background-color: $uni-bg-color;
    border-radius: $uni-border-radius;
    font-size: $uni-font-size-sm;
    color: $uni-text-color;
    border: 2rpx solid transparent;

    &--sm {
      font-size: $uni-font-size-xs;
    }

    &--lg {
      font-size: $uni-font-size-lg;
    }

    &--active {
      background-color: rgba(79, 70, 229, 0.1);
      color: $uni-color-primary;
      border-color: $uni-color-primary;
      font-weight: 600;
    }
  }

  // 退出登录
  &__logout {
    margin-top: $uni-spacing-col-lg;
    height: 96rpx;
    line-height: 96rpx;
    text-align: center;
    background-color: #FFFFFF;
    border-radius: $uni-border-radius;
    box-shadow: $uni-box-shadow;
    font-size: $uni-font-size-base;
    color: $uni-color-error;

    &:active {
      opacity: 0.7;
    }
  }
}
</style>
