import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'
import path from 'path'

// Vite 配置
// 集成 uni-app 插件，配置路径别名，全局注入 SCSS 变量
export default defineConfig({
  plugins: [uni()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: '@import "@/styles/variables.scss";'
      }
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    // 生产构建优化：chunk 分割策略
    rollupOptions: {
      output: {
        manualChunks: {
          // Vue 核心
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          // UI 图标库（体积较大，独立打包）
          'icons': ['lucide-vue-next'],
          // uni-app 核心
          'uni-vendor': ['@dcloudio/uni-app', '@dcloudio/uni-components'],
        },
        // chunk 文件名带 hash，便于 CDN 缓存
        chunkFileNames: 'static/js/[name]-[hash].js',
        entryFileNames: 'static/js/[name]-[hash].js',
        assetFileNames: 'static/[ext]/[name]-[hash].[ext]',
      },
    },
    // chunk 大小警告阈值（KB）
    chunkSizeWarningLimit: 500,
    // 启用 CSS 代码分割
    cssCodeSplit: true,
    // 生产环境去除 console
    minify: 'esbuild',
  },
})
