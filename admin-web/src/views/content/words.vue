<template>
  <div class="page-container">
    <div class="page-card">
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="搜索词条" clearable style="width: 180px" @keyup.enter="loadList" />
        <el-select v-model="query.category_id" placeholder="分类" clearable style="width: 140px" @change="loadList">
          <el-option v-for="c in flatCategories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-select v-model="query.status" placeholder="状态" clearable style="width: 120px" @change="loadList">
          <el-option label="待审核" value="pending" />
          <el-option label="已通过" value="approved" />
          <el-option label="已拒绝" value="rejected" />
          <el-option label="已发布" value="published" />
        </el-select>
        <el-select v-model="query.risk_level" placeholder="风险" clearable style="width: 110px" @change="loadList">
          <el-option label="低" value="low" />
          <el-option label="中" value="medium" />
          <el-option label="高" value="high" />
        </el-select>
        <el-button type="primary" @click="loadList">查询</el-button>
        <div class="toolbar-right">
          <el-button type="primary" :icon="Plus" @click="openCreate">新建词条</el-button>
        </div>
      </div>

      <el-table :data="list" v-loading="loading" border stripe style="margin-top: 12px">
        <el-table-column prop="word" label="词条" min-width="120" />
        <el-table-column prop="pinyin" label="拼音" min-width="120" />
        <el-table-column prop="meaning" label="释义" min-width="200" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="风险" width="80">
          <template #default="{ row }">
            <el-tag :type="riskTagType(row.risk_level)" size="small">{{ riskLabel(row.risk_level) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="view_count" label="浏览" width="80" />
        <el-table-column prop="vote_count" label="投票" width="80" />
        <el-table-column label="创建时间" min-width="150">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <div class="table-ops">
              <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button link type="success" @click="openStatus(row)">审核</el-button>
              <el-button link type="warning" @click="openRisk(row)">风险标记</el-button>
              <el-button link type="danger" @click="removeWord(row)">删除</el-button>
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

    <!-- 新建/编辑词条 -->
    <el-dialog v-model="formVisible" :title="editingId ? '编辑词条' : '新建词条'" width="560px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="80px">
        <el-form-item label="词条" prop="word">
          <el-input v-model="form.word" />
        </el-form-item>
        <el-form-item label="拼音">
          <el-input v-model="form.pinyin" />
        </el-form-item>
        <el-form-item label="释义" prop="meaning">
          <el-input v-model="form.meaning" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="示例">
          <el-input v-model="form.example" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="分类" prop="category_id">
          <el-select v-model="form.category_id" placeholder="选择分类" style="width: 100%">
            <el-option v-for="c in flatCategories" :key="c.id" :label="c.displayName" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="!editingId" label="风险" prop="risk_level">
          <el-radio-group v-model="form.risk_level">
            <el-radio value="low">低</el-radio>
            <el-radio value="medium">中</el-radio>
            <el-radio value="high">高</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>

    <!-- 状态审核 -->
    <el-dialog v-model="statusVisible" title="审核状态变更" width="420px">
      <el-form label-width="80px">
        <el-form-item label="词条">
          <el-input :model-value="statusTarget?.word" disabled />
        </el-form-item>
        <el-form-item label="当前状态">
          <el-tag :type="statusTagType(statusTarget?.status)" size="small">{{ statusLabel(statusTarget?.status) }}</el-tag>
        </el-form-item>
        <el-form-item label="新状态">
          <el-radio-group v-model="newStatus">
            <el-radio value="published">发布</el-radio>
            <el-radio value="approved">通过</el-radio>
            <el-radio value="rejected">拒绝</el-radio>
            <el-radio value="pending">待审核</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="statusVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitStatus">确认</el-button>
      </template>
    </el-dialog>

    <!-- 风险标记 -->
    <el-dialog v-model="riskVisible" title="风险标记" width="480px">
      <el-form label-width="80px">
        <el-form-item label="词条">
          <el-input :model-value="riskTarget?.word" disabled />
        </el-form-item>
        <el-form-item label="风险等级">
          <el-radio-group v-model="riskForm.risk_level">
            <el-radio value="low">低</el-radio>
            <el-radio value="medium">中</el-radio>
            <el-radio value="high">高</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="风险类型">
          <el-select v-model="riskForm.risk_types" multiple filterable allow-create default-first-option style="width: 100%" placeholder="如：法律、舆情、政治">
            <el-option label="法律" value="法律" />
            <el-option label="舆情" value="舆情" />
            <el-option label="政治" value="政治" />
            <el-option label="低俗" value="低俗" />
          </el-select>
        </el-form-item>
        <el-form-item label="使用建议">
          <el-input v-model="riskForm.advice" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="riskVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitRisk">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { wordApi, categoryApi } from '@/api/manage'
import { formatDateTime } from '@/utils/format'

const loading = ref(false)
const submitLoading = ref(false)
const list = ref<any[]>([])
const total = ref(0)
const categoryTree = ref<any[]>([])

const query = reactive({
  page: 1,
  page_size: 20,
  keyword: '',
  category_id: undefined as number | undefined,
  status: '',
  risk_level: '',
})

// 展平分类树（带层级前缀）
const flatCategories = computed(() => {
  const result: any[] = []
  const walk = (nodes: any[], depth = 0) => {
    nodes.forEach((n) => {
      result.push({ id: n.id, name: n.name, displayName: '　'.repeat(depth) + n.name })
      if (n.children?.length) walk(n.children, depth + 1)
    })
  }
  walk(categoryTree.value)
  return result
})

async function loadCategories() {
  try {
    const data: any = await categoryApi.list()
    categoryTree.value = data.tree || []
  } catch {}
}

async function loadList() {
  loading.value = true
  try {
    const data: any = await wordApi.list({
      page: query.page,
      page_size: query.page_size,
      keyword: query.keyword || undefined,
      status: query.status || undefined,
      risk_level: query.risk_level || undefined,
      category_id: query.category_id,
    })
    list.value = data.list || []
    total.value = data.total || 0
  } catch {
  } finally {
    loading.value = false
  }
}

function statusLabel(s?: string) {
  return { pending: '待审核', approved: '已通过', rejected: '已拒绝', published: '已发布' }[s || ''] || s
}
function statusTagType(s?: string): any {
  return { pending: 'warning', approved: 'success', rejected: 'danger', published: 'primary' }[s || ''] || 'info'
}
function riskLabel(s?: string) {
  return { low: '低', medium: '中', high: '高' }[s || ''] || s
}
function riskTagType(s?: string): any {
  return { low: 'success', medium: 'warning', high: 'danger' }[s || ''] || 'info'
}

// ---- 新建/编辑 ----
const formVisible = ref(false)
const formRef = ref<FormInstance>()
const editingId = ref(0)
const form = reactive({ word: '', pinyin: '', meaning: '', example: '', category_id: undefined as number | undefined, risk_level: 'low' })
const formRules: FormRules = {
  word: [{ required: true, message: '请输入词条', trigger: 'blur' }],
  meaning: [{ required: true, message: '请输入释义', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }],
}

function openCreate() {
  editingId.value = 0
  Object.assign(form, { word: '', pinyin: '', meaning: '', example: '', category_id: undefined, risk_level: 'low' })
  formVisible.value = true
}

async function openEdit(row: any) {
  editingId.value = row.id
  try {
    const data: any = await wordApi.get(row.id)
    Object.assign(form, {
      word: data.word,
      pinyin: data.pinyin || '',
      meaning: data.meaning || '',
      example: data.example || '',
      category_id: data.category_id,
      risk_level: data.risk_level || 'low',
    })
    formVisible.value = true
  } catch {}
}

async function submitForm() {
  await formRef.value?.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      if (editingId.value) {
        await wordApi.update(editingId.value, {
          word: form.word,
          pinyin: form.pinyin || undefined,
          meaning: form.meaning,
          example: form.example || undefined,
          category_id: form.category_id,
        })
        ElMessage.success('更新成功')
      } else {
        await wordApi.create({
          word: form.word,
          meaning: form.meaning,
          category_id: form.category_id!,
          pinyin: form.pinyin || undefined,
          example: form.example || undefined,
          risk_level: form.risk_level,
        })
        ElMessage.success('创建成功')
      }
      formVisible.value = false
      loadList()
    } catch {
    } finally {
      submitLoading.value = false
    }
  })
}

// ---- 状态审核 ----
const statusVisible = ref(false)
const statusTarget = ref<any>(null)
const newStatus = ref('published')

function openStatus(row: any) {
  statusTarget.value = row
  newStatus.value = 'published'
  statusVisible.value = true
}

async function submitStatus() {
  submitLoading.value = true
  try {
    await wordApi.updateStatus(statusTarget.value.id, newStatus.value)
    ElMessage.success('状态已更新')
    statusVisible.value = false
    loadList()
  } catch {
  } finally {
    submitLoading.value = false
  }
}

// ---- 风险标记 ----
const riskVisible = ref(false)
const riskTarget = ref<any>(null)
const riskForm = reactive({ risk_level: 'low', risk_types: [] as string[], advice: '' })

async function openRisk(row: any) {
  riskTarget.value = row
  try {
    const data: any = await wordApi.get(row.id)
    Object.assign(riskForm, {
      risk_level: data.risk_level || 'low',
      risk_types: data.risk_types || [],
      advice: data.risk_advice || '',
    })
  } catch {
    Object.assign(riskForm, { risk_level: row.risk_level || 'low', risk_types: [], advice: '' })
  }
  riskVisible.value = true
}

async function submitRisk() {
  submitLoading.value = true
  try {
    await wordApi.updateRisk(riskTarget.value.id, {
      risk_level: riskForm.risk_level,
      risk_types: riskForm.risk_types,
      advice: riskForm.advice,
    })
    ElMessage.success('风险标记已保存')
    riskVisible.value = false
    loadList()
  } catch {
  } finally {
    submitLoading.value = false
  }
}

// ---- 删除 ----
async function removeWord(row: any) {
  try {
    await ElMessageBox.confirm(`确认删除词条「${row.word}」？`, '提示', { type: 'warning' })
    await wordApi.remove(row.id)
    ElMessage.success('删除成功')
    loadList()
  } catch {}
}

onMounted(() => {
  loadCategories()
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
</style>
