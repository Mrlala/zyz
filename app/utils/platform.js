/**
 * 平台判断工具
 * 基于 uni.getSystemInfoSync 提供平台信息缓存
 */

let systemInfo = null
let platformInfo = null

/**
 * 获取系统信息（带缓存）
 * @returns {object}
 */
export function getSystemInfo() {
  if (!systemInfo) {
    try {
      systemInfo = uni.getSystemInfoSync()
    } catch (err) {
      console.error('[platform] 获取系统信息失败:', err)
      systemInfo = {}
    }
  }
  return systemInfo
}

/**
 * 获取运行平台标识
 * h5 / mp-weixin / app-plus / app-plus-nvue
 * @returns {string}
 */
export function getPlatform() {
  // #ifdef H5
  return 'h5'
  // #endif
  // #ifdef MP-WEIXIN
  return 'mp-weixin'
  // #endif
  // #ifdef APP-PLUS
  return 'app-plus'
  // #endif
  // eslint-disable-next-line no-unreachable
  return 'unknown'
}

/**
 * 是否为 H5
 */
export function isH5() {
  return getPlatform() === 'h5'
}

/**
 * 是否为微信小程序
 */
export function isMpWeixin() {
  return getPlatform() === 'mp-weixin'
}

/**
 * 是否为 App
 */
export function isApp() {
  return getPlatform() === 'app-plus'
}

/**
 * 获取状态栏高度（px）
 */
export function getStatusBarHeight() {
  const info = getSystemInfo()
  return info.statusBarHeight || 0
}

/**
 * 获取导航栏高度（含状态栏，px）
 * H5 自定义导航通常为 44px
 */
export function getNavBarHeight() {
  const statusBar = getStatusBarHeight()
  // #ifdef H5
  return 44
  // #endif
  // #ifndef H5
  // eslint-disable-next-line no-unreachable
  return statusBar + 44
  // #endif
}

/**
 * 获取窗口宽度（px）
 */
export function getWindowWidth() {
  const info = getSystemInfo()
  return info.windowWidth || 375
}

/**
 * 获取窗口高度（px）
 */
export function getWindowHeight() {
  const info = getSystemInfo()
  return info.windowHeight || 667
}

export default {
  getSystemInfo,
  getPlatform,
  isH5,
  isMpWeixin,
  isApp,
  getStatusBarHeight,
  getNavBarHeight,
  getWindowWidth,
  getWindowHeight
}
