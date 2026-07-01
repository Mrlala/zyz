/**
 * 翻译状态模块（setup 风格）— 会话架构
 *
 * 核心概念：一个会话（session）包含多条问答（messages），上限 MAX_MESSAGES_PER_SESSION。
 * - newSession(): 创建新会话
 * - translate(): 在当前会话中追加问答
 * - selectSession(id): 恢复某个会话的全部消息
 *
 * State：mode, sessions, currentSessionId, currentMessages, isLoading
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as translateApi from '@/api/translate'
import storage from '@/utils/storage'

const MODE_KEY = 'zyz_translate_mode'
const SESSIONS_KEY = 'zyz_translate_sessions'
const CURRENT_SESSION_KEY = 'zyz_translate_current_session'
const MAX_SESSIONS = 50 // 最多保留 50 个会话
const MAX_MESSAGES_PER_SESSION = 20 // 每个会话上限 20 条消息（10 轮问答）

export const useTranslateStore = defineStore('translate', () => {
  // 当前翻译模式
  const mode = ref('quick')
  // 全部会话
  const sessions = ref([])
  // 当前会话 ID
  const currentSessionId = ref(null)
  // 翻译中
  const isLoading = ref(false)

  // 当前会话
  const currentSession = computed(() =>
    sessions.value.find((s) => s.id === currentSessionId.value) || null
  )

  // 当前会话的消息列表
  const currentMessages = computed(() =>
    currentSession.value?.messages || []
  )

  // 最近会话（取前 10 个，按更新时间倒序）
  const recentSessions = computed(() =>
    [...sessions.value]
      .sort((a, b) => b.updated_at - a.updated_at)
      .slice(0, 10)
  )

  // 是否有空状态（当前会话无消息且不在加载中）
  const isEmpty = computed(
    () => !isLoading.value && currentMessages.value.length === 0
  )

  /**
   * 切换翻译模式
   */
  function setMode(m) {
    if (m !== 'quick' && m !== 'deep' && m !== 'dict') return
    mode.value = m
    storage.set(MODE_KEY, m)
  }

  /**
   * 创建新会话
   */
  function newSession() {
    const session = {
      id: Date.now(),
      title: '新对话',
      messages: [],
      created_at: Date.now(),
      updated_at: Date.now(),
    }
    sessions.value.unshift(session)
    // 限制会话总数
    if (sessions.value.length > MAX_SESSIONS) {
      sessions.value = sessions.value.slice(0, MAX_SESSIONS)
    }
    currentSessionId.value = session.id
    persist()
    return session
  }

  /**
   * 选择（恢复）某个会话
   */
  function selectSession(id) {
    const session = sessions.value.find((s) => s.id === id)
    if (session) {
      currentSessionId.value = id
      storage.set(CURRENT_SESSION_KEY, id)
    }
  }

  /**
   * 删除某个会话
   */
  function deleteSession(id) {
    const idx = sessions.value.findIndex((s) => s.id === id)
    if (idx >= 0) {
      sessions.value.splice(idx, 1)
      // 如果删除的是当前会话，切换到第一个或新建
      if (currentSessionId.value === id) {
        if (sessions.value.length > 0) {
          currentSessionId.value = sessions.value[0].id
        } else {
          newSession()
        }
      }
      persist()
    }
  }

  /**
   * 执行翻译：在当前会话中追加用户消息 + AI 回复
   */
  async function translate(text, m) {
    const useMode = m || mode.value
    if (!text || !text.trim()) {
      throw new Error('请输入待翻译文本')
    }

    // 确保有当前会话
    if (!currentSession.value) {
      newSession()
    }

    const session = currentSession.value
    const apiMode = useMode === 'dict' ? 'dict' : 'translate'

    isLoading.value = true
    try {
      const result = await translateApi.translate(text, apiMode)

      // 追加用户消息
      session.messages.push({
        role: 'user',
        text,
        created_at: Date.now(),
      })

      // 追加助手消息
      session.messages.push({
        role: 'assistant',
        result: { original_text: text, mode: useMode, ...result },
        translation_id: result.translation_id,
        mode: useMode,
        created_at: Date.now(),
      })

      // 限制每个会话消息数（保留最近 MAX_MESSAGES_PER_SESSION 条）
      if (session.messages.length > MAX_MESSAGES_PER_SESSION) {
        session.messages = session.messages.slice(-MAX_MESSAGES_PER_SESSION)
      }

      // 更新会话标题（首次提问时）
      if (session.title === '新对话') {
        session.title = text.length > 20 ? text.slice(0, 20) + '…' : text
      }

      session.updated_at = Date.now()
      persist()

      return result
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 从本地存储恢复
   */
  function restore() {
    const m = storage.get(MODE_KEY)
    if (m) mode.value = m

    const savedSessions = storage.get(SESSIONS_KEY)
    if (savedSessions && Array.isArray(savedSessions) && savedSessions.length > 0) {
      sessions.value = savedSessions
    }

    const savedCurrentId = storage.get(CURRENT_SESSION_KEY)
    if (savedCurrentId && sessions.value.find((s) => s.id === savedCurrentId)) {
      currentSessionId.value = savedCurrentId
    } else if (sessions.value.length > 0) {
      currentSessionId.value = sessions.value[0].id
    } else {
      // 无会话则创建一个空会话
      newSession()
    }
  }

  /**
   * 清空所有会话
   */
  function clearAllSessions() {
    sessions.value = []
    currentSessionId.value = null
    storage.remove(SESSIONS_KEY)
    storage.remove(CURRENT_SESSION_KEY)
    newSession()
  }

  /**
   * 持久化到本地存储
   */
  function persist() {
    storage.set(SESSIONS_KEY, sessions.value)
    if (currentSessionId.value) {
      storage.set(CURRENT_SESSION_KEY, currentSessionId.value)
    }
  }

  return {
    // state
    mode,
    sessions,
    currentSessionId,
    isLoading,
    // getters
    currentSession,
    currentMessages,
    recentSessions,
    isEmpty,
    // actions
    setMode,
    newSession,
    selectSession,
    deleteSession,
    translate,
    clearAllSessions,
    restore,
    persist,
  }
})
