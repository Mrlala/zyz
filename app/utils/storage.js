/**
 * 本地存储封装
 * 基于 uni.getStorageSync / uni.setStorageSync / uni.removeStorageSync
 * 自动 JSON 序列化/反序列化，统一异常处理
 */

/**
 * 读取存储值
 * @param {string} key 键名
 * @returns {*} 反序列化后的值，不存在时返回 null
 */
export function get(key) {
  try {
    const value = uni.getStorageSync(key)
    if (value === '' || value === null || value === undefined) return null
    // 已序列化的 JSON 字符串自动解析
    if (typeof value === 'string' && (value.startsWith('{') || value.startsWith('['))) {
      try {
        return JSON.parse(value)
      } catch (e) {
        return value
      }
    }
    return value
  } catch (err) {
    console.error('[storage.get] 读取失败:', key, err)
    return null
  }
}

/**
 * 写入存储值
 * @param {string} key 键名
 * @param {*} value 任意可序列化值
 */
export function set(key, value) {
  try {
    const v = typeof value === 'object' ? JSON.stringify(value) : value
    uni.setStorageSync(key, v)
  } catch (err) {
    console.error('[storage.set] 写入失败:', key, err)
  }
}

/**
 * 移除存储值
 * @param {string} key 键名
 */
export function remove(key) {
  try {
    uni.removeStorageSync(key)
  } catch (err) {
    console.error('[storage.remove] 移除失败:', key, err)
  }
}

/**
 * 清空所有本地存储（谨慎使用）
 */
export function clear() {
  try {
    uni.clearStorageSync()
  } catch (err) {
    console.error('[storage.clear] 清空失败:', err)
  }
}

export default { get, set, remove, clear }
