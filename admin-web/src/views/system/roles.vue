<template>
  <div class="page-container roles-page">
    <div class="roles-layout">
      <!-- 左侧角色列表 -->
      <div class="page-card role-list-panel">
        <h3 style="margin: 0 0 12px">角色列表</h3>
        <el-radio-group v-model="selectedRoleId" class="role-radio-group" @change="onRoleChange">
          <el-radio v-for="r in roles" :key="r.id" :value="r.id" class="role-radio-item">
            <div class="role-info">
              <span class="role-name">{{ r.name }}</span>
              <el-tag size="small" :type="roleTagType(r.code)">{{ r.code }}</el-tag>
              <el-tag v-if="r.is_builtin" size="small" type="info">内置</el-tag>
            </div>
            <div class="role-desc">{{ r.description }}</div>
          </el-radio>
        </el-radio-group>
      </div>

      <!-- 右侧权限矩阵 -->
      <div class="page-card permission-panel">
        <div class="permission-header">
          <h3 style="margin: 0">
            权限配置
            <span v-if="currentRole" class="current-role-name">— {{ currentRole.name }}</span>
          </h3>
          <el-button type="primary" :loading="saveLoading" :disabled="!currentRole" @click="savePermissions">保存配置</el-button>
        </div>

        <el-alert v-if="currentRole?.is_builtin" type="info" :closable="false" show-icon style="margin: 12px 0">
          内置角色的权限可调整，但建议保留核心权限以确保系统正常运行。
        </el-alert>

        <div v-loading="loading" class="permission-groups">
          <div v-for="(perms, module) in permissionGroups" :key="module" class="perm-group">
            <div class="perm-group-title">
              <el-checkbox
                :model-value="isModuleAllChecked(module as string)"
                :indeterminate="isModuleIndeterminate(module as string)"
                @change="toggleModule(module as string, $event as boolean)"
              >
                {{ moduleLabel(module as string) }}
              </el-checkbox>
            </div>
            <el-checkbox-group v-model="selectedPermIds" class="perm-items">
              <el-checkbox v-for="p in perms" :key="p.id" :value="p.id" :label="p.id">
                <span class="perm-name">{{ p.name }}</span>
                <span class="perm-code">{{ p.code }}</span>
              </el-checkbox>
            </el-checkbox-group>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { roleApi } from '@/api/manage'
import { useStatusMaps } from '@/composables/useStatusMaps'

const { roleTagType, moduleLabel } = useStatusMaps()

const loading = ref(false)
const saveLoading = ref(false)
const roles = ref<any[]>([])
const permissionGroups = ref<Record<string, any[]>>({})
const selectedRoleId = ref<number | undefined>(undefined)
const selectedPermIds = ref<number[]>([])

const currentRole = computed(() => roles.value.find((r) => r.id === selectedRoleId.value))

function isModuleAllChecked(module: string) {
  const perms = permissionGroups.value[module] || []
  return perms.length > 0 && perms.every((p) => selectedPermIds.value.includes(p.id))
}

function isModuleIndeterminate(module: string) {
  const perms = permissionGroups.value[module] || []
  const checked = perms.filter((p) => selectedPermIds.value.includes(p.id))
  return checked.length > 0 && checked.length < perms.length
}

function toggleModule(module: string, checked: boolean) {
  const perms = permissionGroups.value[module] || []
  const ids = perms.map((p) => p.id)
  if (checked) {
    const set = new Set(selectedPermIds.value)
    ids.forEach((id) => set.add(id))
    selectedPermIds.value = Array.from(set)
  } else {
    selectedPermIds.value = selectedPermIds.value.filter((id) => !ids.includes(id))
  }
}

async function loadRoles() {
  loading.value = true
  try {
    const [roleData, permData]: any[] = await Promise.all([roleApi.list(), roleApi.listAllPermissions()])
    roles.value = roleData.list || []
    permissionGroups.value = permData.groups || {}
    if (roles.value.length > 0) {
      selectedRoleId.value = roles.value[0].id
      onRoleChange(roles.value[0].id)
    }
  } catch {
  } finally {
    loading.value = false
  }
}

function onRoleChange(roleId: number) {
  const role = roles.value.find((r) => r.id === roleId)
  if (!role) return
  // role.permissions 是 code 列表，需反查 id
  const allPerms: any[] = []
  Object.values(permissionGroups.value).forEach((g) => allPerms.push(...g))
  const codeToId = new Map(allPerms.map((p) => [p.code, p.id]))
  selectedPermIds.value = (role.permissions || []).map((code: string) => codeToId.get(code)).filter(Boolean) as number[]
}

async function savePermissions() {
  if (!currentRole.value) return
  saveLoading.value = true
  try {
    await roleApi.updateRolePermissions(currentRole.value.id, selectedPermIds.value)
    ElMessage.success('权限配置已保存')
    // 刷新角色列表（权限码已变更）
    const data: any = await roleApi.list()
    roles.value = data.list || []
  } catch {
  } finally {
    saveLoading.value = false
  }
}

onMounted(loadRoles)
</script>

<style scoped lang="scss">
.roles-page {
  .roles-layout {
    display: flex;
    gap: 16px;
    height: calc(100vh - var(--admin-header-height) - 48px);
  }
  .role-list-panel {
    width: 280px;
    flex-shrink: 0;
  }
  .role-radio-group {
    display: flex;
    flex-direction: column;
    width: 100%;
  }
  .role-radio-item {
    display: flex;
    align-items: flex-start;
    padding: 10px 8px;
    border-radius: 4px;
    margin-right: 0;
    height: auto;
    line-height: 1.5;
    &:hover {
      background: #f5f7fa;
    }
  }
  .role-info {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
  }
  .role-name {
    font-weight: 500;
  }
  .role-desc {
    font-size: 12px;
    color: #909399;
    margin-top: 4px;
    margin-left: 24px;
  }
  .permission-panel {
    flex: 1;
    overflow-y: auto;
  }
  .permission-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .current-role-name {
    font-size: 14px;
    color: var(--admin-primary);
    font-weight: normal;
  }
  .permission-groups {
    margin-top: 12px;
  }
  .perm-group {
    border: 1px solid #ebeef5;
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 12px;
  }
  .perm-group-title {
    font-weight: 600;
    margin-bottom: 8px;
    padding-bottom: 8px;
    border-bottom: 1px solid #f0f0f0;
  }
  .perm-items {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 24px;
  }
  .perm-name {
    margin-right: 6px;
  }
  .perm-code {
    font-size: 12px;
    color: #909399;
    font-family: monospace;
  }
}
</style>
