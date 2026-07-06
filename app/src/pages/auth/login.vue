<template>
  <view class="auth-page" :style="{ paddingTop: statusBarHeight + 'px' }">
    <!-- Logo + 标题 -->
    <view class="auth-header">
      <view class="auth-header__logo">中译中</view>
      <text class="auth-header__subtitle">看不懂的中文，翻成人话</text>
    </view>

    <!-- 表单卡片 -->
    <view class="auth-card">
      <!-- Tab 切换 -->
      <view class="auth-tab">
        <view
          class="auth-tab__item"
          :class="{ 'auth-tab__item--active': mode === 'login' }"
          @click="switchMode('login')"
        >登录</view>
        <view
          class="auth-tab__item"
          :class="{ 'auth-tab__item--active': mode === 'register' }"
          @click="switchMode('register')"
        >注册</view>
      </view>

      <!-- 用户名 -->
      <view class="auth-field">
        <text class="auth-field__label">用户名</text>
        <input
          class="auth-field__input"
          v-model="form.username"
          :placeholder="mode === 'register' ? '2-20 位字符' : '请输入用户名'"
          maxlength="20"
        />
      </view>

      <!-- 密码 -->
      <view class="auth-field">
        <text class="auth-field__label">密码</text>
        <input
          class="auth-field__input"
          v-model="form.password"
          password
          :placeholder="mode === 'register' ? '至少 8 位，含数字和字母' : '请输入密码'"
          maxlength="64"
        />
      </view>

      <!-- 确认密码（仅注册） -->
      <view v-if="mode === 'register'" class="auth-field">
        <text class="auth-field__label">确认密码</text>
        <input
          class="auth-field__input"
          v-model="form.confirmPassword"
          password
          placeholder="再次输入密码"
          maxlength="64"
        />
      </view>

      <!-- 提交按钮 -->
      <view
        class="auth-submit"
        :class="{ 'auth-submit--disabled': loading }"
        @click="handleSubmit"
      >
        <text class="auth-submit__text">{{ loading ? '处理中...' : (mode === 'login' ? '登录' : '注册') }}</text>
      </view>

      <!-- 提示 -->
      <view class="auth-tip">
        <text v-if="mode === 'login'" class="auth-tip__text">没有账号？点击上方"注册"</text>
        <text v-else class="auth-tip__text">已有账号？点击上方"登录"</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()

const statusBarHeight = ref(0)
const mode = ref('login') // login | register
const loading = ref(false)
const form = ref({
  username: '',
  password: '',
  confirmPassword: ''
})

onLoad(() => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
  // 已登录直接回首页
  if (userStore.isLoggedIn && !userStore.needsProfileSetup) {
    uni.reLaunch({ url: '/pages/index/index' })
  }
})

function switchMode(m) {
  mode.value = m
  form.value.confirmPassword = ''
}

async function handleSubmit() {
  if (loading.value) return

  const { username, password, confirmPassword } = form.value

  // 校验
  if (!username || username.trim().length < 2) {
    uni.showToast({ title: '用户名至少 2 位', icon: 'none' })
    return
  }
  if (!password || password.length < 8) {
    uni.showToast({ title: '密码至少 8 位', icon: 'none' })
    return
  }
  if (!(/\d/.test(password) && /[a-zA-Z]/.test(password))) {
    uni.showToast({ title: '密码需包含数字和字母', icon: 'none' })
    return
  }
  if (mode.value === 'register' && password !== confirmPassword) {
    uni.showToast({ title: '两次密码不一致', icon: 'none' })
    return
  }

  loading.value = true
  try {
    if (mode.value === 'register') {
      await userStore.accountRegister(username.trim(), password)
      uni.showToast({ title: '注册成功', icon: 'success' })
      // 新注册 → 跳转昵称头像设置
      setTimeout(() => {
        uni.reLaunch({ url: '/pages/auth/profile-setup' })
      }, 500)
    } else {
      await userStore.accountLogin(username.trim(), password)
      uni.showToast({ title: '登录成功', icon: 'success' })
      // 登录后判断是否需要设置昵称
      if (userStore.needsProfileSetup) {
        setTimeout(() => {
          uni.reLaunch({ url: '/pages/auth/profile-setup' })
        }, 500)
      } else {
        setTimeout(() => {
          uni.reLaunch({ url: '/pages/index/index' })
        }, 500)
      }
    }
  } catch (err) {
    console.error(err)
    const msg = err.message || '操作失败'
    uni.showToast({ title: msg, icon: 'none' })
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.auth-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #FE2C55 0%, #FE2C55 30%, #F7F8FA 30%);
}

/* ============ 头部 ============ */
.auth-header {
  padding: 40px 24px 60px;
  text-align: center;

  &__logo {
    font-size: 36px;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: 2px;
  }

  &__subtitle {
    display: block;
    margin-top: 8px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.85);
  }
}

/* ============ 表单卡片 ============ */
.auth-card {
  margin: 0 24px;
  padding: 24px 20px;
  background-color: $bg-card;
  border-radius: 20px;
  box-shadow: $shadow-md;
}

.auth-tab {
  display: flex;
  margin-bottom: 24px;
  background-color: $bg-sunken;
  border-radius: 10px;
  padding: 4px;

  &__item {
    flex: 1;
    text-align: center;
    padding: 8px 0;
    font-size: 14px;
    font-weight: 500;
    color: $text-secondary;
    border-radius: 8px;
    transition: all 0.2s;

    &--active {
      background-color: $bg-card;
      color: $color-primary;
      box-shadow: $shadow-xs;
    }
  }
}

.auth-field {
  margin-bottom: 16px;

  &__label {
    display: block;
    font-size: 13px;
    font-weight: 500;
    color: $text-secondary;
    margin-bottom: 6px;
  }

  &__input {
    width: 100%;
    height: 44px;
    padding: 0 14px;
    font-size: 15px;
    color: $text-primary;
    background-color: $bg-sunken;
    border-radius: 10px;
    border: 1px solid transparent;

    &:focus {
      border-color: $color-primary;
    }
  }
}

.auth-submit {
  margin-top: 8px;
  height: 46px;
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
    opacity: 0.6;
  }

  &:active {
    opacity: 0.85;
  }
}

.auth-tip {
  margin-top: 16px;
  text-align: center;

  &__text {
    font-size: 12px;
    color: $text-tertiary;
  }
}
</style>
