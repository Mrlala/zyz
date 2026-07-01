import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import 'vue3-json-viewer/dist/vue3-json-viewer.css'
import 'nprogress/nprogress.css'
import JsonViewer from 'vue3-json-viewer'
import App from './App.vue'
import router from './router'
import pinia from './store'
import './styles/index.scss'

const app = createApp(App)

// 注册所有 Element Plus 图标为全局组件
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component as any)
}

app.use(pinia)
app.use(router)
app.use(ElementPlus)
app.use(JsonViewer)

app.mount('#app')
