<template>
  <view class="page mine-page">
    <!-- 顶部自定义导航栏 -->
    <view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="nav-bar__inner">
        <text class="nav-bar__title">我的</text>
      </view>
    </view>
    <view class="nav-placeholder" :style="{ height: (statusBarHeight + 44) + 'px' }"></view>

    <view class="mine-page__body">
      <!-- 用户信息卡 -->
      <view class="mine-page__user card">
        <template v-if="userStore.isLoggedIn && profile">
          <view class="mine-page__user-top">
            <view class="mine-page__avatar">{{ avatarText }}</view>
            <view class="mine-page__user-info">
              <view class="mine-page__nickname">{{ userStore.nickname }}</view>
              <view class="mine-page__title-tag" v-if="profile.title">
                <text class="mine-page__title-icon">🏅</text>
                <text>{{ profile.title }}</text>
              </view>
              <view class="mine-page__level">Lv.{{ profile.level || 1 }}</view>
            </view>
          </view>

          <!-- 经验值进度条 -->
          <view class="mine-page__exp">
            <view class="mine-page__exp-header">
              <text class="mine-page__exp-label">经验值</text>
              <text class="mine-page__exp-value">{{ profile.exp || 0 }} / {{ profile.next_level_exp || 100 }}</text>
            </view>
            <view class="mine-page__exp-track">
              <view class="mine-page__exp-fill" :style="{ width: expPercent + '%' }"></view>
            </view>
          </view>

          <!-- 统计 -->
          <view class="mine-page__stats">
            <view class="mine-page__stat">
              <text class="mine-page__stat-value">{{ stats.learn_count || 0 }}</text>
              <text class="mine-page__stat-label">已学</text>
            </view>
            <view class="mine-page__stat">
              <text class="mine-page__stat-value">{{ stats.favorite_count || 0 }}</text>
              <text class="mine-page__stat-label">收藏</text>
            </view>
            <view class="mine-page__stat">
              <text class="mine-page__stat-value">{{ stats.history_count || 0 }}</text>
              <text class="mine-page__stat-label">翻译</text>
            </view>
            <view class="mine-page__stat">
              <text class="mine-page__stat-value">{{ stats.achievement_count || 0 }}</text>
              <text class="mine-page__stat-label">成就</text>
            </view>
          </view>
        </template>

        <!-- 未登录 -->
        <view v-else class="mine-page__login">
          <view class="mine-page__avatar mine-page__avatar--guest">👤</view>
          <view class="mine-page__login-tip">登录后同步学习记录与成就</view>
          <view class="mine-page__login-btn btn btn-primary" @click="handleLogin">登录 / 注册</view>
        </view>
      </view>

      <!-- 成就徽章墙 -->
      <view class="mine-page__section card" v-if="unlockedAchievements.length">
        <view class="mine-page__section-header">
          <text class="mine-page__section-title">成就徽章</text>
          <text class="mine-page__section-count">已解锁 {{ unlockedAchievements.length }} 枚</text>
        </view>
        <view class="mine-page__badges">
          <view
            v-for="(ach, idx) in displayBadges"
            :key="idx"
            class="mine-page__badge"
          >
            <view class="mine-page__badge-icon">{{ ach.icon || '🎖️' }}</view>
            <text class="mine-page__badge-name">{{ ach.name }}</text>
          </view>
          <view v-if="unlockedAchievements.length > 8" class="mine-page__badge mine-page__badge--more" @click="goAchievements">
            <view class="mine-page__badge-icon">＋{{ unlockedAchievements.length - 8 }}</view>
            <text class="mine-page__badge-name">查看全部</text>
          </view>
        </view>
      </view>

      <!-- 功能列表 -->
      <view class="mine-page__menu card">
        <view
          v-for="item in menus"
          :key="item.path"
          class="mine-page__menu-item"
          @click="goMenu(item)"
        >
          <view class="mine-page__menu-left">
            <text class="mine-page__menu-icon">{{ item.icon }}</text>
            <text class="mine-page__menu-name">{{ item.name }}</text>
          </view>
          <view class="mine-page__menu-right">
            <text class="mine-page__menu-extra" v-if="item.extra">{{ item.extra }}</text>
            <text class="mine-page__menu-arrow">›</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/store/modules/user'
import { useTranslateStore } from '@/store/modules/translate'
import * as achievementApi from '@/api/achievement'

const userStore = useUserStore()
const translateStore = useTranslateStore()

const statusBarHeight = ref(0)
// 用户信息
const profile = ref(null)
// 已解锁成就
const unlockedAchievements = ref([])

// 头像文字（取昵称首字）
const avatarText = computed(() => {
  const name = userStore.nickname || ''
  return name ? name.charAt(0).toUpperCase() : '我'
})

// 统计数据
const stats = computed(() => (profile.value && profile.value.stats) || {})

// 经验百分比
const expPercent = computed(() => {
  const exp = profile.value?.exp || 0
  const next = profile.value?.next_level_exp || 100
  return Math.min(Math.round((exp / next) * 100), 100)
})

// 展示的徽章（最多 8 个）
const displayBadges = computed(() => unlockedAchievements.value.slice(0, 8))

// 功能菜单
const menus = computed(() => [
  { icon: '⭐', name: '我的收藏', path: '/pages/mine/favorites' },
  { icon: '📖', name: '学习历史', path: '/pages/mine/history' },
  { icon: '🔄', name: '翻译历史', path: '/pages/mine/history?type=translate', extra: translateStore.historyCount ? `${translateStore.historyCount}` : '' },
  { icon: '📨', name: '我的提交', path: '/pages/mine/submissions' },
  { icon: '⚙️', name: '设置', path: '/pages/mine/settings' }
])

onLoad(() => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
})

onShow(() => {
  if (userStore.isLoggedIn) {
    fetchProfile()
    fetchAchievements()
  }
})

// 拉取用户信息
async function fetchProfile() {
  try {
    const data = await userStore.fetchProfile()
    profile.value = data
  } catch (err) {
    console.error('获取用户信息失败', err)
  }
}

// 拉取我的成就
async function fetchAchievements() {
  try {
    const data = await achievementApi.getMyAchievements()
    unlockedAchievements.value = (data && data.unlocked) || []
  } catch (err) {
    console.error('获取成就失败', err)
  }
}

// 登录/注册（设备 ID 自动登录）
async function handleLogin() {
  try {
    uni.showLoading({ title: '登录中...' })
    await userStore.register()
    uni.showToast({ title: '登录成功', icon: 'success' })
    fetchProfile()
    fetchAchievements()
  } catch (err) {
    console.error('登录失败', err)
    uni.showToast({ title: '登录失败，请重试', icon: 'none' })
  } finally {
    uni.hideLoading()
  }
}

// 跳转功能页
function goMenu(item) {
  uni.navigateTo({ url: item.path })
}

// 跳转成就页（暂复用提交页结构，可后续扩展）
function goAchievements() {
  uni.showToast({ title: '成就详情即将上线', icon: 'none' })
}
</script>

<style lang="scss" scoped>
.mine-page {
  min-height: 100vh;
  background-color: $uni-bg-color;

  .nav-bar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
    background-color: $uni-color-primary;

    &__inner {
      height: 88rpx;
      display: flex;
      align-items: center;
      padding: 0 $uni-spacing-row-base;
    }

    &__title {
      font-size: $uni-font-size-title;
      font-weight: 700;
      color: #FFFFFF;
    }
  }

  &__body {
    padding: $uni-spacing-col-base $uni-spacing-row-base;
    padding-bottom: 60rpx;
  }

  // 用户信息卡
  &__user {
    margin-bottom: $uni-spacing-col-base;
  }

  &__user-top {
    display: flex;
    align-items: center;
    margin-bottom: $uni-spacing-col-base;
  }

  &__avatar {
    width: 112rpx;
    height: 112rpx;
    border-radius: 50%;
    background-color: $uni-color-primary;
    color: #FFFFFF;
    font-size: $uni-font-size-title;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: $uni-spacing-row-base;

    &--guest {
      background-color: $uni-bg-color;
      color: $uni-text-color-grey;
      font-size: 64rpx;
    }
  }

  &__user-info {
    flex: 1;
  }

  &__nickname {
    font-size: $uni-font-size-lg;
    font-weight: 600;
    color: $uni-text-color;
    margin-bottom: 8rpx;
  }

  &__title-tag {
    display: inline-flex;
    align-items: center;
    padding: 4rpx $uni-spacing-row-sm;
    background-color: rgba(245, 158, 11, 0.12);
    color: $uni-color-warning;
    font-size: $uni-font-size-sm;
    border-radius: 999rpx;
    margin-bottom: 8rpx;
  }

  &__title-icon {
    margin-right: 4rpx;
  }

  &__level {
    font-size: $uni-font-size-sm;
    color: $uni-color-primary;
    font-weight: 600;
  }

  &__exp {
    margin-bottom: $uni-spacing-col-base;
  }

  &__exp-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: $uni-spacing-row-sm;
  }

  &__exp-label {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
  }

  &__exp-value {
    font-size: $uni-font-size-sm;
    color: $uni-color-primary;
    font-weight: 600;
  }

  &__exp-track {
    height: 16rpx;
    background-color: $uni-border-color;
    border-radius: 999rpx;
    overflow: hidden;
  }

  &__exp-fill {
    height: 100%;
    background: linear-gradient(90deg, $uni-color-primary, $uni-color-primary-light);
    border-radius: 999rpx;
    transition: width 0.3s ease-out;
  }

  &__stats {
    display: flex;
    justify-content: space-around;
    padding-top: $uni-spacing-col-base;
    border-top: 2rpx solid $uni-border-color;
  }

  &__stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
  }

  &__stat-value {
    font-size: $uni-font-size-lg;
    font-weight: 700;
    color: $uni-text-color;
  }

  &__stat-label {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
    margin-top: 4rpx;
  }

  // 未登录
  &__login {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: $uni-spacing-col-base 0;
  }

  &__login-tip {
    font-size: $uni-font-size-base;
    color: $uni-text-color-grey;
    margin: $uni-spacing-col-sm 0 $uni-spacing-col-base;
  }

  &__login-btn {
    padding: 0 $uni-spacing-row-xl;
  }

  // 通用区块
  &__section {
    margin-bottom: $uni-spacing-col-base;
  }

  &__section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $uni-spacing-col-sm;
  }

  &__section-title {
    font-size: $uni-font-size-base;
    font-weight: 600;
    color: $uni-text-color;
  }

  &__section-count {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
  }

  &__badges {
    display: flex;
    flex-wrap: wrap;
    gap: $uni-spacing-row-sm;
  }

  &__badge {
    width: calc((100% - 56rpx) / 4);
    display: flex;
    flex-direction: column;
    align-items: center;

    &--more {
      .mine-page__badge-icon {
        background-color: $uni-bg-color;
        color: $uni-color-primary;
      }
    }
  }

  &__badge-icon {
    width: 88rpx;
    height: 88rpx;
    border-radius: 50%;
    background-color: rgba(79, 70, 229, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 48rpx;
    margin-bottom: 8rpx;
  }

  &__badge-name {
    font-size: $uni-font-size-xs;
    color: $uni-text-color-grey;
    text-align: center;
    line-height: 1.3;
  }

  // 功能菜单
  &__menu {
    padding: 0;
    overflow: hidden;
  }

  &__menu-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: $uni-spacing-col-base $uni-spacing-row-base;
    border-bottom: 2rpx solid $uni-border-color;

    &:last-child {
      border-bottom: none;
    }

    &:active {
      background-color: $uni-bg-color;
    }
  }

  &__menu-left {
    display: flex;
    align-items: center;
  }

  &__menu-icon {
    font-size: $uni-font-size-lg;
    margin-right: $uni-spacing-row-base;
  }

  &__menu-name {
    font-size: $uni-font-size-base;
    color: $uni-text-color;
  }

  &__menu-right {
    display: flex;
    align-items: center;
  }

  &__menu-extra {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
    margin-right: $uni-spacing-row-sm;
  }

  &__menu-arrow {
    font-size: $uni-font-size-lg;
    color: $uni-text-color-placeholder;
  }
}
</style>
