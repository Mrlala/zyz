/**
 * 用户状态模块（setup 风格）
 *
 * State：token, userInfo, preferences, favoriteIds
 * Actions：register / login / logout / fetchProfile / toggleFavorite / restore
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as userApi from '@/api/user'
import * as wordApi from '@/api/word'
import storage from '@/utils/storage'
import { getDeviceId } from '@/api/request'

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

  /**
   * 设备 ID 注册（首次启动调用）
   * 已注册则走登录流程
   */
  async function register() {
    const deviceId = getDeviceId()
    try {
      const data = await userApi.register({ device_id: deviceId })
      token.value = data.token
      await fetchProfile()
      persist()
      return data
    } catch (err) {
      // 设备已注册 → 走登录
      if (err.message && err.message.includes('已注册')) {
        return login()
      }
      throw err
    }
  }

  /**
   * 用户登录（基于设备 ID）
   */
  async function login() {
    const deviceId = getDeviceId()
    const data = await userApi.login({ device_id: deviceId })
    token.value = data.token
    // 拉取 profile 失败不影响登录态生效
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
   * @param {number} wordId 词条 ID
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

  /**
   * 判断是否已收藏
   */
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

  /**
   * 持久化到本地存储
   */
  function persist() {
    if (token.value) storage.set(TOKEN_KEY, token.value)
    if (userInfo.value) storage.set(USER_KEY, userInfo.value)
    storage.set(PREF_KEY, preferences.value)
    storage.set(FAV_KEY, favoriteIds.value)
  }

  /**
   * 从本地存储恢复登录态
   */
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
    // actions
    register,
    login,
    fetchProfile,
    updatePreferences,
    toggleFavorite,
    isFavorited,
    logout,
    persist,
    restore
  }
})
