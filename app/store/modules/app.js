/**
 * 应用配置模块（setup 风格）
 *
 * State：theme, fontSize, showRiskWarning, version, deviceId
 * Actions：setTheme / setFontSize / toggleRiskWarning / initDeviceId / restorePreferences
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import storage from '@/utils/storage'
import { APP_VERSION } from '@/config/env'

const THEME_KEY = 'zyz_theme'
const FONT_KEY = 'zyz_font_size'
const RISK_KEY = 'zyz_show_risk'
const DEVICE_ID_KEY = 'zyz_device_id'

export const useAppStore = defineStore('app', () => {
  // 主题：light / dark
  const theme = ref('light')
  // 字体大小：small / medium / large
  const fontSize = ref('medium')
  // 是否显示风险提示
  const showRiskWarning = ref(true)
  // 应用版本号
  const version = ref(APP_VERSION)
  // 设备 ID
  const deviceId = ref('')

  /**
   * 切换主题
   * @param {string} t light / dark
   */
  function setTheme(t) {
    if (t !== 'light' && t !== 'dark') return
    theme.value = t
    storage.set(THEME_KEY, t)
  }

  /**
   * 切换字体大小
   * @param {string} s small / medium / large
   */
  function setFontSize(s) {
    if (!['small', 'medium', 'large'].includes(s)) return
    fontSize.value = s
    storage.set(FONT_KEY, s)
  }

  /**
   * 切换风险提示开关
   */
  function toggleRiskWarning() {
    showRiskWarning.value = !showRiskWarning.value
    storage.set(RISK_KEY, showRiskWarning.value)
  }

  /**
   * 初始化设备 ID（首次启动调用）
   * 优先从存储读取，不存在则生成并持久化
   */
  function initDeviceId() {
    let id = storage.get(DEVICE_ID_KEY)
    if (!id) {
      id = `web_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
      storage.set(DEVICE_ID_KEY, id)
    }
    deviceId.value = id
    return id
  }

  /**
   * 从本地存储恢复偏好设置
   */
  function restorePreferences() {
    const t = storage.get(THEME_KEY)
    if (t) theme.value = t

    const f = storage.get(FONT_KEY)
    if (f) fontSize.value = f

    const r = storage.get(RISK_KEY)
    if (r !== null && r !== undefined && r !== '') {
      showRiskWarning.value = !!r
    }
  }

  return {
    // state
    theme,
    fontSize,
    showRiskWarning,
    version,
    deviceId,
    // actions
    setTheme,
    setFontSize,
    toggleRiskWarning,
    initDeviceId,
    restorePreferences
  }
})
