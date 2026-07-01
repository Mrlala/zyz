/**
 * 用户状态模块（setup 风格）
 *
 * State：token, userInfo, preferences, favoriteIds
 * Actions：accountLogin / accountRegister / logout / fetchProfile / updateProfile / toggleFavorite / restore
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as userApi from '@/api/user'
import * as wordApi from '@/api/word'
import storage from '@/utils/storage'

const TOKEN_KEY = 'zyz_token'
const USER_KEY = 'zyz_user_info'
const PREF_KEY = 'zyz_preferences'
const FAV_KEY = 'zyz_favorite_ids'

export const useUserStore = defineStore('user', () => {
  // State
  const token = ref('')
  const userInfo = ref(null)
  const preferences = ref({
    default_mode: 'translate',
    show_risk_advice: true,
    font_size: 'medium',
    theme: 'auto'
  })
  const favoriteIds = ref([])

  // Getters
  const isLoggedIn = computed(() => !!token.value)
  const userId = computed(() => userInfo.value?.user_id || null)
  const nickname = computed(() => userInfo.value?.nickname || '匿名用户')
  const avatar = computed(() => userInfo.value?.avatar || '')
  // 新注册用户需设置昵称头像
  const needsProfileSetup = computed(
    () => !!token.value && !userInfo.value?.nickname
  )
  // 是否管理员
  const isAdmin = computed(() => !!userInfo.value?.is_admin)

  /**
   * 账号密码注册
   */
  async function accountRegister(username, password) {
    const data = await userApi.registerAccount({ username, password })
    token.value = data.token
    // 注册后 userInfo 为空，触发 needsProfileSetup
    userInfo.value = { user_id: data.user_id }
    persist()
    return data
  }

  /**
   * 账号密码登录
   */
  async function accountLogin(username, password) {
    const data = await userApi.loginAccount({ username, password })
    token.value = data.token
    userInfo.value = { user_id: data.user_id }
    try {
      await fetchProfile()
    } catch (e) {
      console.warn('登录后拉取 profile 失败，稍后重试', e)
    }
    persist()
    return data
  }

  /**
   * 拉取用户信息
   */
  async function fetchProfile() {
    const profile = await userApi.getProfile()
    userInfo.value = profile
    if (profile.preferences) {
      preferences.value = { ...preferences.value, ...profile.preferences }
    }
    return profile
  }

  /**
   * 更新用户资料（昵称、头像）
   */
  async function updateProfile(patch) {
    const data = await userApi.updateProfile(patch)
    // 同步到 userInfo
    if (userInfo.value) {
      userInfo.value = {
        ...userInfo.value,
        nickname: data.nickname,
        avatar: data.avatar
      }
    }
    persist()
    return data
  }

  /**
   * 更新用户偏好
   */
  async function updatePreferences(patch) {
    const updated = await userApi.updatePreferences(patch)
    preferences.value = { ...preferences.value, ...updated }
    persist()
    return updated
  }

  /**
   * 切换收藏状态
   */
  async function toggleFavorite(wordId) {
    const idx = favoriteIds.value.indexOf(wordId)
    const isFavorited = idx >= 0
    if (isFavorited) {
      await wordApi.unfavorite(wordId)
      favoriteIds.value.splice(idx, 1)
    } else {
      await wordApi.favorite(wordId)
      favoriteIds.value.push(wordId)
    }
    storage.set(FAV_KEY, favoriteIds.value)
    return !isFavorited
  }

  function isFavorited(wordId) {
    return favoriteIds.value.includes(wordId)
  }

  /**
   * 退出登录
   */
  function logout() {
    token.value = ''
    userInfo.value = null
    favoriteIds.value = []
    storage.remove(TOKEN_KEY)
    storage.remove(USER_KEY)
    storage.remove(FAV_KEY)
  }

  function persist() {
    if (token.value) storage.set(TOKEN_KEY, token.value)
    if (userInfo.value) storage.set(USER_KEY, userInfo.value)
    storage.set(PREF_KEY, preferences.value)
    storage.set(FAV_KEY, favoriteIds.value)
  }

  function restore() {
    token.value = storage.get(TOKEN_KEY) || ''
    userInfo.value = storage.get(USER_KEY) || null
    const savedPref = storage.get(PREF_KEY)
    if (savedPref) preferences.value = { ...preferences.value, ...savedPref }
    favoriteIds.value = storage.get(FAV_KEY) || []
  }

  return {
    // state
    token,
    userInfo,
    preferences,
    favoriteIds,
    // getters
    isLoggedIn,
    userId,
    nickname,
    avatar,
    needsProfileSetup,
    isAdmin,
    // actions
    accountRegister,
    accountLogin,
    fetchProfile,
    updateProfile,
    updatePreferences,
    toggleFavorite,
    isFavorited,
    logout,
    persist,
    restore
  }
})
