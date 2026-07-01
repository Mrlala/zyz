/**
 * 翻译状态模块（setup 风格）
 *
 * State：mode, currentResult, history, isLoading
 * Actions：setMode / translate / clearResult / addHistory / clearHistory / restore
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as translateApi from '@/api/translate'
import storage from '@/utils/storage'

const MODE_KEY = 'zyz_translate_mode'
const HISTORY_KEY = 'zyz_translate_history'
const MAX_HISTORY = 20

export const useTranslateStore = defineStore('translate', () => {
  // 当前翻译模式：quick(快速解析) / deep(深度解析) / dict(词典)
  const mode = ref('quick')
  // 当前翻译结果
  const currentResult = ref(null)
  // 翻译历史（最多 20 条）
  const history = ref([])
  // 翻译中
  const isLoading = ref(false)

  // 历史记录数量
  const historyCount = computed(() => history.value.length)

  /**
   * 切换翻译模式
   * @param {string} m quick / deep / dict
   */
  function setMode(m) {
    if (m !== 'quick' && m !== 'deep' && m !== 'dict') return
    mode.value = m
    storage.set(MODE_KEY, m)
  }

  /**
   * 执行翻译
   * @param {string} text 待翻译文本
   * @param {string} [m] 可选模式覆盖
   */
  async function translate(text, m) {
    const useMode = m || mode.value
    if (!text || !text.trim()) {
      throw new Error('请输入待翻译文本')
    }
    // 前端三态映射到后端两态：quick/deep → translate，dict → dict
    const apiMode = useMode === 'dict' ? 'dict' : 'translate'
    isLoading.value = true
    try {
      const result = await translateApi.translate(text, apiMode)
      currentResult.value = {
        original_text: text,
        mode: useMode,
        ...result
      }
      addHistory({
        text,
        mode: useMode,
        translation_id: result.translation_id,
        created_at: Date.now()
      })
      return currentResult.value
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 清空当前翻译结果
   */
  function clearResult() {
    currentResult.value = null
  }

  /**
   * 添加到历史记录（保持最新在前，最多 MAX_HISTORY 条）
   */
  function addHistory(item) {
    history.value.unshift(item)
    if (history.value.length > MAX_HISTORY) {
      history.value = history.value.slice(0, MAX_HISTORY)
    }
    storage.set(HISTORY_KEY, history.value)
  }

  /**
   * 清空历史记录
   */
  function clearHistory() {
    history.value = []
    storage.remove(HISTORY_KEY)
  }

  /**
   * 从本地存储恢复
   */
  function restore() {
    const m = storage.get(MODE_KEY)
    if (m) mode.value = m
    history.value = storage.get(HISTORY_KEY) || []
  }

  return {
    // state
    mode,
    currentResult,
    history,
    isLoading,
    // getters
    historyCount,
    // actions
    setMode,
    translate,
    clearResult,
    addHistory,
    clearHistory,
    restore
  }
})
