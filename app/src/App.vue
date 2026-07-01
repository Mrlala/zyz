<script>
import { useUserStore } from '@/store/modules/user'
import { useAppStore } from '@/store/modules/app'

export default {
  async onLaunch() {
    console.log('App Launch - 中译中 v1.0.0')

    // 应用初始化：恢复用户登录态、获取设备 ID
    try {
      const appStore = useAppStore()
      appStore.initDeviceId()
      appStore.restorePreferences()

      const userStore = useUserStore()
      userStore.restore()

      // 首次启动无 token 时自动注册（基于设备 ID）
      // 注册失败（设备已注册）会自动 fallback 到 login
      if (!userStore.isLoggedIn) {
        console.log('未检测到登录态，自动注册/登录...')
        try {
          await userStore.register()
          console.log('自动注册成功，userId:', userStore.userId)
        } catch (err) {
          console.error('自动注册/登录失败：', err)
        }
      } else {
        // 已登录：主动拉取最新 profile（避免本地缓存过期）
        try {
          await userStore.fetchProfile()
        } catch (err) {
          // profile 拉取失败（token 过期等）→ 重新登录
          console.warn('profile 拉取失败，尝试重新登录:', err)
          try {
            await userStore.login()
          } catch (e) {
            console.error('重新登录失败：', e)
          }
        }
      }
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
