<template>
  <div class="page-container">
    <div class="page-card">
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="搜索用户名" clearable style="width: 200px" @clear="loadList" @keyup.enter="loadList" />
        <el-select v-model="query.role_id" placeholder="角色" clearable style="width: 140px" @change="loadList">
          <el-option v-for="r in roles" :key="r.id" :label="r.name" :value="r.id" />
        </el-select>
        <el-select v-model="query.status" placeholder="状态" clearable style="width: 120px" @change="loadList">
          <el-option label="启用" value="active" />
          <el-option label="禁用" value="disabled" />
        </el-select>
        <el-button type="primary" @click="loadList">查询</el-button>
        <div class="toolbar-right">
          <el-button type="primary" :icon="Plus" @click="openCreate">新建账号</el-button>
        </div>
      </div>

      <el-table :data="list" v-loading="loading" border stripe style="margin-top: 12px">
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="nickname" label="昵称" min-width="120" />
        <el-table-column prop="role_name" label="角色" min-width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="roleTagType(row.role_code)">{{ row.role_name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'" size="small">
              {{ row.status === 'active' ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login_at" label="最近登录" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.last_login_at) }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <div class="table-ops">
              <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button link type="warning" @click="openResetPwd(row)">重置密码</el-button>
              <el-button v-if="row.status === 'active'" link type="info" @click="toggleStatus(row, 'disabled')">禁用</el-button>
              <el-button v-else link type="success" @click="toggleStatus(row, 'active')">启用</el-button>
              <el-button link type="danger" @click="removeAccount(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.page_size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 12px; justify-content: flex-end"
        @size-change="loadList"
        @current-change="loadList"
      />
    </div>

    <!-- 新建账号 -->
    <el-dialog v-model="createVisible" title="新建账号" width="440px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="createForm.username" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="createForm.password" type="password" show-password />
          <div class="form-tip">至少 8 位，需包含数字和字母</div>
        </el-form-item>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="createForm.nickname" />
        </el-form-item>
        <el-form-item label="角色" prop="role_id">
          <el-select v-model="createForm.role_id" placeholder="选择角色" style="width: 100%">
            <el-option v-for="r in roles" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 编辑账号 -->
    <el-dialog v-model="editVisible" title="编辑账号" width="440px">
      <el-form ref="editFormRef" :model="editForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input :model-value="editForm.username" disabled />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="editForm.nickname" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.role_id" style="width: 100%">
            <el-option v-for="r in roles" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="editForm.status">
            <el-radio value="active">启用</el-radio>
            <el-radio value="disabled">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码 -->
    <el-dialog v-model="resetPwdVisible" title="重置密码" width="420px">
      <el-alert :title="`将重置 ${resetPwdTarget?.username} 的密码，重置后需强制改密`" type="warning" :closable="false" show-icon style="margin-bottom: 12px" />
      <el-form ref="resetPwdFormRef" :model="resetPwdForm" :rules="resetPwdRules" label-width="90px">
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="resetPwdForm.new_password" type="password" show-password />
          <div class="form-tip">至少 8 位，需包含数字和字母</div>
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm">
          <el-input v-model="resetPwdForm.confirm" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPwdVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitResetPwd">重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { accountApi, roleApi } from '@/api/manage'
import { useAuthStore } from '@/store/modules/auth'
import { formatDateTime } from '@/utils/format'
import { useStatusMaps } from '@/composables/useStatusMaps'
import { usePasswordRules } from '@/composables/usePasswordRules'

const route = useRoute()
const { roleTagType } = useStatusMaps()
const { passwordRules, newPasswordRules, confirmRules } = usePasswordRules()

const auth = useAuthStore()
const loading = ref(false)
const submitLoading = ref(false)
const list = ref<any[]>([])
const total = ref(0)
const roles = ref<any[]>([])

const query = reactive({ page: 1, page_size: 20, keyword: '', role_id: undefined as number | undefined, status: '' })

async function loadRoles() {
  try {
    const data: any = await roleApi.list()
    roles.value = data.list || []
  } catch {}
}

async function loadList() {
  loading.value = true
  try {
    const data: any = await accountApi.list({
      page: query.page,
      page_size: query.page_size,
      keyword: query.keyword || undefined,
      role_id: query.role_id,
      status: query.status || undefined,
    })
    list.value = data.list || []
    total.value = data.total || 0
  } catch {
  } finally {
    loading.value = false
  }
}

// ---- 新建 ----
const createVisible = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive({ username: '', password: '', nickname: '', role_id: undefined as number | undefined })
const createRules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }, { min: 2, message: '至少 2 位', trigger: 'blur' }],
  password: passwordRules as any,
  role_id: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

function openCreate() {
  Object.assign(createForm, { username: '', password: '', nickname: '', role_id: undefined })
  createVisible.value = true
}

async function submitCreate() {
  await createFormRef.value?.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      await accountApi.create({
        username: createForm.username,
        password: createForm.password,
        nickname: createForm.nickname || undefined,
        role_id: createForm.role_id!,
      })
      ElMessage.success('账号创建成功')
      createVisible.value = false
      loadList()
    } catch {
    } finally {
      submitLoading.value = false
    }
  })
}

// ---- 编辑 ----
const editVisible = ref(false)
const editFormRef = ref<FormInstance>()
const editForm = reactive({ id: 0, username: '', nickname: '', role_id: undefined as number | undefined, status: '' })

function openEdit(row: any) {
  Object.assign(editForm, { id: row.id, username: row.username, nickname: row.nickname || '', role_id: row.role_id, status: row.status })
  editVisible.value = true
}

async function submitEdit() {
  submitLoading.value = true
  try {
    await accountApi.update(editForm.id, {
      nickname: editForm.nickname,
      role_id: editForm.role_id,
      status: editForm.status,
    })
    ElMessage.success('保存成功')
    editVisible.value = false
    loadList()
  } catch {
  } finally {
    submitLoading.value = false
  }
}

// ---- 启停 ----
async function toggleStatus(row: any, status: string) {
  const action = status === 'active' ? '启用' : '禁用'
  try {
    await ElMessageBox.confirm(`确认${action}账号 ${row.username}？`, '提示', { type: 'warning' })
    await accountApi.update(row.id, { status })
    ElMessage.success(`${action}成功`)
    loadList()
  } catch {}
}

// ---- 删除 ----
async function removeAccount(row: any) {
  try {
    await ElMessageBox.confirm(`确认删除账号 ${row.username}？此操作不可恢复`, '危险操作', { type: 'error', confirmButtonText: '删除', confirmButtonClass: 'el-button--danger' })
    await accountApi.remove(row.id)
    ElMessage.success('删除成功')
    loadList()
  } catch {}
}

// ---- 重置密码 ----
const resetPwdVisible = ref(false)
const resetPwdFormRef = ref<FormInstance>()
const resetPwdTarget = ref<any>(null)
const resetPwdForm = reactive({ new_password: '', confirm: '' })
const resetPwdRules: FormRules = {
  new_password: newPasswordRules as any,
  confirm: confirmRules(() => resetPwdForm.new_password) as any,
}

function openResetPwd(row: any) {
  resetPwdTarget.value = row
  Object.assign(resetPwdForm, { new_password: '', confirm: '' })
  resetPwdVisible.value = true
}

async function submitResetPwd() {
  await resetPwdFormRef.value?.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      await accountApi.resetPassword(resetPwdTarget.value.id, resetPwdForm.new_password)
      ElMessage.success('密码重置成功')
      resetPwdVisible.value = false
    } catch {
    } finally {
      submitLoading.value = false
    }
  })
}

onMounted(() => {
  loadRoles()
  // 消费 GlobalSearch 跳转携带的 query.keyword 自动填充并搜索
  const kw = route.query.keyword as string | undefined
  if (kw) query.keyword = kw
  loadList()
})
</script>

<style scoped lang="scss">
.toolbar {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.toolbar-right {
  margin-left: auto;
}
.form-tip {
  font-size: 12px;
  color: #909399;
}
</style>
