import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import NProgress from 'nprogress'
import { useAuthStore } from '@/store/modules/auth'

NProgress.configure({ showSpinner: false, trickleSpeed: 200 })

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { public: true, title: '登录' },
  },
  {
    path: '/',
    component: () => import('@/layouts/AdminLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '工作台', icon: 'Odometer' },
      },
      {
        path: 'system/accounts',
        name: 'Accounts',
        component: () => import('@/views/system/accounts.vue'),
        meta: { title: '账号管理', icon: 'User', permission: 'system:user:manage' },
      },
      {
        path: 'system/roles',
        name: 'Roles',
        component: () => import('@/views/system/roles.vue'),
        meta: { title: '角色权限', icon: 'Lock', permission: 'system:role:manage' },
      },
      {
        path: 'content/words',
        name: 'Words',
        component: () => import('@/views/content/words.vue'),
        meta: { title: '词库管理', icon: 'Document', permission: 'content:word:manage' },
      },
      {
        path: 'content/categories',
        name: 'Categories',
        component: () => import('@/views/content/categories.vue'),
        meta: { title: '分类管理', icon: 'Files', permission: 'content:category:manage' },
      },
      {
        path: 'content/audit',
        name: 'ContentAudit',
        component: () => import('@/views/content/audit.vue'),
        meta: {
          title: '内容审核',
          icon: 'CircleCheck',
          permission: ['content:submission:audit', 'content:correction:audit'],
        },
      },
      {
        path: 'ai/config',
        name: 'AiConfig',
        component: () => import('@/views/ai/config.vue'),
        meta: { title: 'AI 配置', icon: 'MagicStick', permission: 'ai:config:manage' },
      },
      {
        path: 'monitor/api',
        name: 'MonitorApi',
        component: () => import('@/views/monitor/api.vue'),
        meta: { title: 'API 监控', icon: 'DataLine', permission: 'monitor:api:view' },
      },
      {
        path: 'monitor/ai',
        name: 'MonitorAi',
        component: () => import('@/views/monitor/ai.vue'),
        meta: { title: 'AI 监控', icon: 'Cpu', permission: 'monitor:ai:view' },
      },
      {
        path: 'audit/logs',
        name: 'AuditLogs',
        component: () => import('@/views/audit/logs.vue'),
        meta: { title: '操作日志', icon: 'List', permission: 'audit:log:view' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 全局前置守卫：token + 权限校验
router.beforeEach(async (to, _from, next) => {
  NProgress.start()
  const auth = useAuthStore()
  // 恢复 profile（页面刷新后 store 丢失）
  if (auth.token && !auth.profile) {
    auth.restoreProfile()
    if (!auth.profile) {
      try {
        await auth.fetchProfile()
      } catch {
        await auth.logout()
        return next('/login')
      }
    }
  }

  // 公开页面（登录页）
  if (to.meta.public) {
    if (auth.token && to.name === 'Login') {
      return next('/dashboard')
    }
    return next()
  }

  // 未登录跳登录页
  if (!auth.token) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }

  // 权限校验
  const perm = to.meta.permission
  if (perm) {
    const required = Array.isArray(perm) ? perm : [perm]
    const ok = required.some((p) => auth.permissions.includes(p))
    if (!ok) {
      return next('/dashboard')
    }
  }

  next()
})

router.afterEach(() => {
  NProgress.done()
})

export default router
