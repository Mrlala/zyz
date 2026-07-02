<template>
  <div class="page-container">
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin: 0">分类管理</h3>
        <div class="toolbar-right">
          <el-button type="primary" :icon="Plus" @click="openCreate(null)">新建一级分类</el-button>
        </div>
      </div>

      <el-input v-model="filterText" placeholder="过滤分类" clearable style="margin: 12px 0" />

      <el-tree
        ref="treeRef"
        :data="treeData"
        :props="{ label: 'name', children: 'children' }"
        node-key="id"
        :filter-node-method="filterNode"
        :expand-on-click-node="false"
        default-expand-all
      >
        <template #default="{ node, data }">
          <div class="tree-node">
            <span class="node-label">
              <el-tag size="small" :type="levelTagType(data.level)">L{{ data.level }}</el-tag>
              {{ data.name }}
              <span class="node-meta">排序: {{ data.sort_order }}</span>
            </span>
            <span class="node-ops">
              <el-button link type="primary" @click.stop="openCreate(data)">添加子分类</el-button>
              <el-button link type="warning" @click.stop="openEdit(data)">编辑</el-button>
              <el-button link type="danger" @click.stop="removeCategory(data)">删除</el-button>
            </span>
          </div>
        </template>
      </el-tree>
    </div>

    <!-- 新建/编辑 -->
    <el-dialog v-model="formVisible" :title="editingId ? '编辑分类' : '新建分类'" width="440px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item v-if="!editingId" label="父分类">
          <el-select v-model="form.parent_id" clearable placeholder="无（一级分类）" style="width: 100%">
            <el-option v-for="c in flatCategories" :key="c.id" :label="c.displayName" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="999" />
        </el-form-item>
        <el-form-item label="图标">
          <el-input v-model="form.icon" placeholder="图标 URL 或标识（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { categoryApi } from '@/api/manage'
import { useCategoryTree } from '@/composables/useCategoryTree'
import { useStatusMaps } from '@/composables/useStatusMaps'

const { levelTagType } = useStatusMaps()

const treeRef = ref()
const treeData = ref<any[]>([])
const loading = ref(false)
const submitLoading = ref(false)
const filterText = ref('')

const { flatCategories } = useCategoryTree(treeData, { maxLevel: 3 })

watch(filterText, (val) => treeRef.value?.filter(val))

function filterNode(value: string, data: any) {
  if (!value) return true
  return data.name.includes(value)
}

async function loadTree() {
  loading.value = true
  try {
    const data: any = await categoryApi.list()
    treeData.value = data.tree || []
  } catch {
  } finally {
    loading.value = false
  }
}

// ---- 新建/编辑 ----
const formVisible = ref(false)
const formRef = ref<FormInstance>()
const editingId = ref(0)
const form = reactive({ name: '', parent_id: undefined as number | undefined, sort_order: 0, icon: '' })
const formRules: FormRules = {
  name: [{ required: true, message: '请输入分类名称', trigger: 'blur' }],
}

function openCreate(parent: any) {
  editingId.value = 0
  Object.assign(form, { name: '', parent_id: parent?.id, sort_order: 0, icon: '' })
  formVisible.value = true
}

function openEdit(data: any) {
  editingId.value = data.id
  Object.assign(form, { name: data.name, parent_id: undefined, sort_order: data.sort_order ?? 0, icon: data.icon || '' })
  formVisible.value = true
}

async function submitForm() {
  await formRef.value?.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      if (editingId.value) {
        await categoryApi.update(editingId.value, {
          name: form.name,
          sort_order: form.sort_order,
          icon: form.icon || undefined,
        })
        ElMessage.success('更新成功')
      } else {
        await categoryApi.create({
          name: form.name,
          parent_id: form.parent_id,
          sort_order: form.sort_order,
          icon: form.icon || undefined,
        })
        ElMessage.success('创建成功')
      }
      formVisible.value = false
      loadTree()
    } catch {
    } finally {
      submitLoading.value = false
    }
  })
}

async function removeCategory(data: any) {
  try {
    await ElMessageBox.confirm(`确认删除分类「${data.name}」？`, '提示', { type: 'warning' })
    await categoryApi.remove(data.id)
    ElMessage.success('删除成功')
    loadTree()
  } catch {}
}

onMounted(loadTree)
</script>

<style scoped lang="scss">
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.toolbar-right {
  margin-left: auto;
}
.tree-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding-right: 8px;
}
.node-label {
  display: flex;
  align-items: center;
  gap: 6px;
}
.node-meta {
  font-size: 12px;
  color: #c0c4cc;
  margin-left: 8px;
}
.node-ops {
  display: none;
}
:deep(.el-tree-node__content:hover) .node-ops {
  display: inline-flex;
}
</style>
