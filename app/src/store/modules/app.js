/**
 * 应用配置模块（setup 风格）
 *
 * State：version, deviceId
 * Actions：initDeviceId / restorePreferences
 *
 * 说明：theme/fontSize/showRiskWarning 的偏好已由 userStore.updatePreferences
 * 持久化到服务端，本地不再维护，相关 action 已移除。
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import storage from '@/utils/storage'
import { APP_VERSION } from '@/config/env'

const DEVICE_ID_KEY = 'zyz_device_id'

export const useAppStore = defineStore('app', () => {
  // 应用版本号
  const version = ref(APP_VERSION)
  // 设备 ID
  const deviceId = ref('')

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
   * 恢复本地偏好（仅设备 ID，主题/字号由 userStore 管理）
   */
  function restorePreferences() {
    // 兼容旧版本遗留的本地存储键，清除迁移残留
    storage.remove('zyz_theme')
    storage.remove('zyz_font_size')
    storage.remove('zyz_show_risk')
  }

  return {
    // state
    version,
    deviceId,
    // actions
    initDeviceId,
    restorePreferences
  }
})
