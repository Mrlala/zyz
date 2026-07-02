<template>
  <div class="login-bg">
    <div class="login-box">
      <h1 class="login-title">中译中 · 后台管理</h1>
      <p class="login-subtitle">三员分立管理系统</p>
      <el-form ref="formRef" :model="form" :rules="rules" @keyup.enter="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="管理员账号" :prefix-icon="User" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            :prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" style="width: 100%" :loading="loading" @click="handleLogin">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-tip">默认账号 admin / admin123（首次登录需改密）</div>
    </div>

    <!-- 首次登录强制改密弹窗 -->
    <el-dialog v-model="forcePwdVisible" title="首次登录请修改密码" width="420px" :close-on-click-modal="false" :show-close="false">
      <el-alert title="为了账号安全，请先修改初始密码" type="warning" :closable="false" show-icon style="margin-bottom: 16px" />
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="90px">
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" show-password />
          <div class="form-tip">至少 8 位，需包含数字和字母</div>
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="pwdForm.confirm_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" :loading="pwdLoading" @click="submitForcePwd">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/modules/auth'
import { authApi } from '@/api/manage'
import { usePasswordRules } from '@/composables/usePasswordRules'

const { newPasswordRules, confirmRules } = usePasswordRules()

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const formRef = ref<FormInstance>()
const form = ref({ username: 'admin', password: '' })
const loading = ref(false)

const rules: FormRules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const data: any = await auth.login(form.value.username, form.value.password)
      // 拉取个人资料 + 权限
      await auth.fetchProfile()
      if (data.must_change_password) {
        forcePwdVisible.value = true
      } else {
        redirectAfterLogin()
      }
    } catch {
      // 拦截器已提示
    } finally {
      loading.value = false
    }
  })
}

function redirectAfterLogin() {
  const redirect = (route.query.redirect as string) || '/dashboard'
  router.push(redirect)
}

// 首次登录强制改密
const forcePwdVisible = ref(false)
const pwdLoading = ref(false)
const pwdFormRef = ref<FormInstance>()
const pwdForm = ref({ new_password: '', confirm_password: '' })

const pwdRules: FormRules = {
  new_password: newPasswordRules as any,
  confirm_password: confirmRules(() => pwdForm.value.new_password) as any,
}

async function submitForcePwd() {
  if (!pwdFormRef.value) return
  await pwdFormRef.value.validate(async (valid) => {
    if (!valid) return
    pwdLoading.value = true
    try {
      // 强制改密：旧密码用登录时的密码
      await authApi.changePassword(form.value.password, pwdForm.value.new_password)
      ElMessage.success('密码修改成功')
      forcePwdVisible.value = false
      // 刷新 profile 清除 must_change_password
      await auth.fetchProfile()
      redirectAfterLogin()
    } catch {
      // 拦截器已提示
    } finally {
      pwdLoading.value = false
    }
  })
}
</script>

<style scoped lang="scss">
.login-tip {
  text-align: center;
  font-size: 12px;
  color: #c0c4cc;
  margin-top: 12px;
}
.form-tip {
  font-size: 12px;
  color: #909399;
}
</style>
