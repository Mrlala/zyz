<script>
import { useUserStore } from '@/store/modules/user'
import { useAppStore } from '@/store/modules/app'

export default {
  onLaunch() {
    console.log('App Launch - 中译中 v1.0.0')

    // 应用初始化：恢复用户登录态、获取设备 ID
    try {
      const appStore = useAppStore()
      appStore.initDeviceId()
      appStore.restorePreferences()

      const userStore = useUserStore()
      userStore.restore()
    } catch (err) {
      console.error('应用初始化失败：', err)
    }
  },
  onShow() {
    console.log('App Show')
  },
  onHide() {
    console.log('App Hide')
  }
}
</script>

<style lang="scss">
/* 每个页面公共样式入口 */
@import '@/styles/index.scss';
</style>
