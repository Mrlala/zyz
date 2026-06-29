import { createSSRApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import uView from 'uview-ui'

// 主入口：创建应用实例，注册 Pinia 与 uView
export function createApp() {
  const app = createSSRApp(App)

  // Pinia 状态管理
  app.use(createPinia())

  // uView UI 组件库
  app.use(uView)

  return {
    app
  }
}
