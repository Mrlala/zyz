<template>
  <el-container class="admin-layout">
    <el-aside :width="collapsed ? 'var(--admin-sidebar-collapsed-width)' : 'var(--admin-sidebar-width)'" class="sidebar">
      <div class="logo">
        <span v-if="!collapsed">中译中后台</span>
        <span v-else>中</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="collapsed"
        :collapse-transition="false"
        background-color="#001529"
        text-color="#b7c0cd"
        active-text-color="#fff"
        router
      >
        <template v-for="item in visibleMenus" :key="item.path">
          <el-menu-item :index="item.path">
            <el-icon><component :is="item.icon" /></el-icon>
            <template #title>{{ item.title }}</template>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="collapsed = !collapsed">
            <Fold v-if="!collapsed" />
            <Expand v-else />
          </el-icon>
          <span class="page-title">{{ currentTitle }}</span>
        </div>
        <div class="header-right">
          <el-tooltip :content="theme.theme === 'light' ? '暗色模式' : '亮色模式'" placement="bottom">
            <el-icon class="header-icon" @click="theme.toggle()">
              <Moon v-if="theme.theme === 'light'" />
              <Sunny v-else />
            </el-icon>
          </el-tooltip>
          <el-tooltip content="全屏切换" placement="bottom">
            <el-icon class="header-icon" @click="toggleFullscreen">
              <FullScreen />
            </el-icon>
          </el-tooltip>
          <el-dropdown @command="onCommand">
            <span class="user-info">
              <el-avatar :size="28" class="user-avatar">{{ avatarText }}</el-avatar>
              <span class="user-name">{{ auth.profile?.nickname || auth.profile?.username }}</span>
              <el-tag size="small" type="info" class="role-tag">{{ auth.profile?.role_name }}</el-tag>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="changePassword">
                  <el-icon><Key /></el-icon>修改密码
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main">
        <router-view v-slot="{ Component }">
          <keep-alive>
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </el-main>
    </el-container>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="pwdDialogVisible" title="修改密码" width="420px" :close-on-click-modal="false">
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="90px">
        <el-form-item label="原密码" prop="old_password">
          <el-input v-model="pwdForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" show-password />
          <div class="form-tip">至少 8 位，需包含数字和字母</div>
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="pwdForm.confirm_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="pwdLoading" @click="submitChangePwd">确认</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Fold,
  Expand,
  ArrowDown,
  Key,
  SwitchButton,
  Odometer,
  User,
  Lock,
  Document,
  Files,
  CircleCheck,
  MagicStick,
  DataLine,
  Cpu,
  List,
  Moon,
  Sunny,
  FullScreen,
} from '@element-plus/icons-vue'
import screenfull from 'screenfull'
import { useAuthStore } from '@/store/modules/auth'
import { useThemeStore } from '@/store/modules/theme'
import { authApi } from '@/api/manage'

const auth = useAuthStore()
const theme = useThemeStore()
const route = useRoute()
const router = useRouter()

function toggleFullscreen() {
  if (screenfull.isEnabled) screenfull.toggle()
}

const collapsed = ref(false)

// 菜单配置（与路由表一致，便于按权限过滤）
const allMenus = [
  { path: '/dashboard', title: '工作台', icon: Odometer, permission: '' },
  { path: '/system/accounts', title: '账号管理', icon: User, permission: 'system:user:manage' },
  { path: '/system/roles', title: '角色权限', icon: Lock, permission: 'system:role:manage' },
  { path: '/content/words', title: '词库管理', icon: Document, permission: 'content:word:manage' },
  { path: '/content/categories', title: '分类管理', icon: Files, permission: 'content:category:manage' },
  {
    path: '/content/audit',
    title: '内容审核',
    icon: CircleCheck,
    permission: 'content:submission:audit',
    altPermission: 'content:correction:audit',
  },
  { path: '/ai/config', title: 'AI 配置', icon: MagicStick, permission: 'ai:config:manage' },
  { path: '/monitor/api', title: 'API 监控', icon: DataLine, permission: 'monitor:api:view' },
  { path: '/monitor/ai', title: 'AI 监控', icon: Cpu, permission: 'monitor:ai:view' },
  { path: '/audit/logs', title: '操作日志', icon: List, permission: 'audit:log:view' },
]

const visibleMenus = computed(() =>
  allMenus.filter((m) => {
    if (!m.permission) return true
    const ok1 = m.permission ? auth.permissions.includes(m.permission) : true
    const ok2 = m.altPermission ? auth.permissions.includes(m.altPermission) : false
    return ok1 || ok2
  }),
)

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => (route.meta.title as string) || '后台管理')

const avatarText = computed(() => {
  const name = auth.profile?.nickname || auth.profile?.username || ''
  return name.charAt(0).toUpperCase()
})

async function onCommand(cmd: string) {
  if (cmd === 'changePassword') {
    pwdDialogVisible.value = true
  } else if (cmd === 'logout') {
    try {
      await ElMessageBox.confirm('确认退出登录？', '提示', { type: 'warning' })
      await auth.logout()
      router.push('/login')
    } catch {
      // 取消
    }
  }
}

// 修改密码
const pwdDialogVisible = ref(false)
const pwdLoading = ref(false)
const pwdFormRef = ref<FormInstance>()
const pwdForm = ref({ old_password: '', new_password: '', confirm_password: '' })

const pwdRules: FormRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '至少 8 位', trigger: 'blur' },
    {
      validator: (_r, value, cb) => {
        if (value && !(/\d/.test(value) && /[a-zA-Z]/.test(value))) {
          cb(new Error('需包含数字和字母'))
        } else {
          cb()
        }
      },
      trigger: 'blur',
    },
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (_r, value, cb) => {
        if (value !== pwdForm.value.new_password) cb(new Error('两次密码不一致'))
        else cb()
      },
      trigger: 'blur',
    },
  ],
}

async function submitChangePwd() {
  if (!pwdFormRef.value) return
  await pwdFormRef.value.validate(async (valid) => {
    if (!valid) return
    pwdLoading.value = true
    try {
      await authApi.changePassword(pwdForm.value.old_password, pwdForm.value.new_password)
      ElMessage.success('密码修改成功')
      pwdDialogVisible.value = false
      pwdForm.value = { old_password: '', new_password: '', confirm_password: '' }
      // 改密后刷新 profile（清除 must_change_password 标记）
      await auth.fetchProfile()
    } catch {
      // 拦截器已提示
    } finally {
      pwdLoading.value = false
    }
  })
}
</script>

<style scoped lang="scss">
.admin-layout {
  height: 100vh;
}
.sidebar {
  background: #001529;
  transition: width 0.2s;
  overflow: hidden;
}
.logo {
  height: var(--admin-header-height);
  line-height: var(--admin-header-height);
  text-align: center;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
}
.sidebar :deep(.el-menu) {
  border-right: none;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  height: var(--admin-header-height);
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  color: #606266;
}
.page-title {
  font-size: 16px;
  font-weight: 500;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 4px;
}
.header-icon {
  font-size: 18px;
  cursor: pointer;
  color: #606266;
  margin-right: 12px;
}
.header-icon:hover {
  color: var(--admin-primary);
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 0 8px;
}
.user-avatar {
  background: var(--admin-primary);
  color: #fff;
}
.user-name {
  font-size: 14px;
}
.role-tag {
  margin-right: 4px;
}
.main {
  background: var(--admin-bg);
  padding: 16px;
  overflow-y: auto;
}
.form-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}
</style>
