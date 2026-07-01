<script>
import { useUserStore } from '@/store/modules/user'
import { useAppStore } from '@/store/modules/app'

export default {
  async onLaunch() {
    console.log('App Launch - 中译中 v1.0.0')

    // 应用初始化：恢复用户登录态
    try {
      const appStore = useAppStore()
      appStore.initDeviceId()
      appStore.restorePreferences()

      const userStore = useUserStore()
      userStore.restore()

      if (!userStore.isLoggedIn) {
        // 未登录 → 跳转登录页
        console.log('未登录，跳转登录页')
        uni.reLaunch({ url: '/pages/auth/login' })
      } else if (userStore.needsProfileSetup) {
        // 已登录但未设置昵称头像 → 跳转资料设置页
        console.log('需要设置昵称头像')
        uni.reLaunch({ url: '/pages/auth/profile-setup' })
      } else {
        // 已登录：主动拉取最新 profile
        try {
          await userStore.fetchProfile()
        } catch (err) {
          // token 过期 → 清除登录态，跳登录页
          console.warn('profile 拉取失败，token 可能已过期:', err)
          userStore.logout()
          uni.reLaunch({ url: '/pages/auth/login' })
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
