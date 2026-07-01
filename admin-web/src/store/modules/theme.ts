import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export type ThemeMode = 'light' | 'dark'

export const useThemeStore = defineStore('theme', () => {
  const theme = ref<ThemeMode>((localStorage.getItem('admin_theme') as ThemeMode) || 'light')

  function applyTheme(mode: ThemeMode) {
    const html = document.documentElement
    if (mode === 'dark') {
      html.classList.add('dark')
      html.setAttribute('data-theme', 'dark')
    } else {
      html.classList.remove('dark')
      html.setAttribute('data-theme', 'light')
    }
  }

  function toggle() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  // 监听变化，持久化 + 应用
  watch(
    theme,
    (newTheme) => {
      localStorage.setItem('admin_theme', newTheme)
      applyTheme(newTheme)
    },
    { immediate: true },
  )

  return { theme, toggle }
})
