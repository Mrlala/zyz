<template>
  <view class="setup-page" :style="{ paddingTop: statusBarHeight + 'px' }">
    <!-- 头部 -->
    <view class="setup-header">
      <text class="setup-header__title">完善资料</text>
      <text class="setup-header__subtitle">设置昵称和头像，让大家认识你</text>
    </view>

    <!-- 头像选择 -->
    <view class="setup-section">
      <text class="setup-section__label">选择头像</text>
      <view class="avatar-grid">
        <view
          v-for="item in presetAvatars"
          :key="item.key"
          class="avatar-grid__item"
          :class="{ 'avatar-grid__item--active': selectedAvatar === item.key }"
          @click="selectedAvatar = item.key"
        >
          <view class="avatar-grid__circle" :style="{ background: item.bg }">
            <text class="avatar-grid__emoji">{{ item.emoji }}</text>
          </view>
          <view v-if="selectedAvatar === item.key" class="avatar-grid__check">
            <Check :size="14" color="#FFFFFF" />
          </view>
        </view>
      </view>
    </view>

    <!-- 昵称输入 -->
    <view class="setup-section">
      <text class="setup-section__label">昵称<text class="setup-section__required">*</text></text>
      <input
        class="setup-nickname"
        v-model="nickname"
        placeholder="请输入昵称（1-20 位）"
        maxlength="20"
      />
      <text class="setup-section__count">{{ nickname.length }}/20</text>
    </view>

    <!-- 预览 -->
    <view class="setup-preview">
      <view class="setup-preview__avatar" :style="{ background: currentAvatar.bg }">
        <text class="setup-preview__emoji">{{ currentAvatar.emoji }}</text>
      </view>
      <text class="setup-preview__name">{{ nickname || '未填写' }}</text>
    </view>

    <!-- 提交按钮 -->
    <view
      class="setup-submit"
      :class="{ 'setup-submit--disabled': loading || !nickname.trim() }"
      @click="handleSubmit"
    >
      <text class="setup-submit__text">{{ loading ? '保存中...' : '完成并进入' }}</text>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { Check } from 'lucide-vue-next'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()

const statusBarHeight = ref(0)
const nickname = ref('')
const selectedAvatar = ref('cat')
const loading = ref(false)

// 预设头像（用 emoji + 背景色，无需图片资源）
const presetAvatars = [
  { key: 'cat',     emoji: '🐱', bg: 'linear-gradient(135deg, #FFE0B2, #FFCC80)' },
  { key: 'dog',     emoji: '🐶', bg: 'linear-gradient(135deg, #FFCDD2, #EF9A9A)' },
  { key: 'panda',   emoji: '🐼', bg: 'linear-gradient(135deg, #ECEFF1, #CFD8DC)' },
  { key: 'fox',     emoji: '🦊', bg: 'linear-gradient(135deg, #FFE0B2, #FFB74D)' },
  { key: 'bear',    emoji: '🐻', bg: 'linear-gradient(135deg, #D7CCC8, #BCAAA4)' },
  { key: 'rabbit',  emoji: '🐰', bg: 'linear-gradient(135deg, #F8BBD0, #F48FB1)' },
  { key: 'lion',    emoji: '🦁', bg: 'linear-gradient(135deg, #FFF9C4, #FFF176)' },
  { key: 'frog',    emoji: '🐸', bg: 'linear-gradient(135deg, #C8E6C9, #A5D6A7)' }
]

const currentAvatar = computed(
  () => presetAvatars.find(a => a.key === selectedAvatar.value) || presetAvatars[0]
)

onLoad(() => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
  // 未登录 → 回登录页
  if (!userStore.isLoggedIn) {
    uni.reLaunch({ url: '/pages/auth/login' })
    return
  }
  // 已有昵称（非首次）→ 回首页
  if (userStore.userInfo?.nickname) {
    nickname.value = userStore.userInfo.nickname
    // 匹配已有头像
    const exist = presetAvatars.find(a => a.key === userStore.userInfo.avatar)
    if (exist) selectedAvatar.value = exist.key
  }
})

async function handleSubmit() {
  if (loading.value) return
  if (!nickname.value.trim()) {
    uni.showToast({ title: '请输入昵称', icon: 'none' })
    return
  }

  loading.value = true
  try {
    await userStore.updateProfile({
      nickname: nickname.value.trim(),
      avatar: selectedAvatar.value
    })
    uni.showToast({ title: '设置成功', icon: 'success' })
    setTimeout(() => {
      uni.reLaunch({ url: '/pages/index/index' })
    }, 500)
  } catch (err) {
    console.error('设置资料失败', err)
    uni.showToast({ title: '设置失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.setup-page {
  min-height: 100vh;
  background-color: $bg-page;
  padding-bottom: 40px;
}

/* ============ 头部 ============ */
.setup-header {
  padding: 32px 24px 24px;
  text-align: center;

  &__title {
    display: block;
    font-size: 22px;
    font-weight: 700;
    color: $text-primary;
  }

  &__subtitle {
    display: block;
    margin-top: 6px;
    font-size: 13px;
    color: $text-tertiary;
  }
}

/* ============ 分区 ============ */
.setup-section {
  margin: 0 24px 24px;
  position: relative;

  &__label {
    display: block;
    font-size: 14px;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: 12px;
  }

  &__required {
    color: $color-primary;
    margin-left: 2px;
  }

  &__count {
    position: absolute;
    right: 14px;
    bottom: 12px;
    font-size: 11px;
    color: $text-tertiary;
  }
}

/* ============ 头像网格 ============ */
.avatar-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;

  &__item {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    aspect-ratio: 1;
    border-radius: 50%;
    background-color: $bg-card;
    border: 2px solid transparent;
    transition: all 0.2s;

    &--active {
      border-color: $color-primary;
    }
  }

  &__circle {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__emoji {
    font-size: 28px;
  }

  &__check {
    position: absolute;
    right: 2px;
    bottom: 2px;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background-color: $color-primary;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid $bg-card;
  }
}

/* ============ 昵称输入 ============ */
.setup-nickname {
  width: 100%;
  height: 48px;
  padding: 0 14px;
  font-size: 15px;
  color: $text-primary;
  background-color: $bg-card;
  border-radius: 12px;
  border: 1px solid $border-color;

  &:focus {
    border-color: $color-primary;
  }
}

/* ============ 预览 ============ */
.setup-preview {
  margin: 0 24px 32px;
  padding: 24px;
  background-color: $bg-card;
  border-radius: 16px;
  box-shadow: $shadow-sm;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;

  &__avatar {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__emoji {
    font-size: 36px;
  }

  &__name {
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
  }
}

/* ============ 提交按钮 ============ */
.setup-submit {
  margin: 0 24px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $gradient-primary;
  border-radius: 12px;

  &__text {
    font-size: 15px;
    font-weight: 600;
    color: #FFFFFF;
  }

  &--disabled {
    opacity: 0.5;
  }

  &:active {
    opacity: 0.85;
  }
}
</style>
