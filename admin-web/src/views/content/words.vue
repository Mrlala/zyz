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
          <el-button :icon="Upload" @click="openImport">导入词条</el-button>
          <el-button :icon="Download" :loading="exportLoading" @click="exportExcel">导出 Excel</el-button>
          <el-button type="primary" :icon="Plus" @click="openCreate">新建词条</el-button>
        </div>
      </div>

      <div v-if="selectedRows.length > 0" class="batch-bar">
        <span class="batch-info">已选 {{ selectedRows.length }} 项</span>
        <el-button v-if="hasPermission('content:word:audit')" type="success" @click="batchStatus('approved')">批量通过</el-button>
        <el-button v-if="hasPermission('content:word:audit')" type="warning" @click="batchStatus('rejected')">批量驳回</el-button>
        <el-button v-if="hasPermission('content:word:manage')" type="danger" @click="batchDelete">批量删除</el-button>
      </div>

      <el-table :data="list" v-loading="loading" border stripe style="margin-top: 12px" @selection-change="onSelectionChange">
        <el-table-column type="selection" width="50" />
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
        <el-form-item label="出处">
          <el-input v-model="form.origin" type="textarea" :rows="2" placeholder="描述词条来源背景（如源自某事件、某年网络流行）" />
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

    <!-- 批量导入词条 -->
    <el-dialog v-model="importVisible" title="批量导入词条" width="640px">
      <el-steps :active="importStep" finish-status="success" simple>
        <el-step title="上传文件" />
        <el-step title="预览确认" />
        <el-step title="导入结果" />
      </el-steps>

      <!-- 步骤 1：上传 -->
      <div v-if="importStep === 0" class="import-step">
        <el-upload
          drag
          accept=".xlsx,.xls,.csv"
          :auto-upload="false"
          :on-change="onFileChange"
          :show-file-list="false"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">拖拽文件到此处或<em>点击上传</em></div>
          <template #tip>
            <div class="el-upload__tip">
              支持 .xlsx / .csv 格式，单次最多 1000 条。
              必填列：word / meaning / category_name。
              <el-button link type="primary" @click.stop="downloadTemplate">下载模板</el-button>
            </div>
          </template>
        </el-upload>
      </div>

      <!-- 步骤 2：预览 -->
      <div v-if="importStep === 1" class="import-step">
        <el-alert :title="`共解析到 ${importRows.length} 条数据，预览前 5 行`" type="info" :closable="false" />
        <el-table :data="importRows.slice(0, 5)" border size="small" style="margin-top: 8px">
          <el-table-column prop="word" label="词条" />
          <el-table-column prop="meaning" label="释义" show-overflow-tooltip />
          <el-table-column prop="category_name" label="分类" />
          <el-table-column prop="risk_level" label="风险" width="80" />
        </el-table>
      </div>

      <!-- 步骤 3：结果 -->
      <div v-if="importStep === 2" class="import-step">
        <el-result :icon="importResult.failed_count === 0 ? 'success' : 'warning'" title="导入完成">
          <template #sub-title>
            <p>成功 {{ importResult.success_count }} 条 / 跳过 {{ importResult.skipped_count }} 条 / 失败 {{ importResult.failed_count }} 条</p>
          </template>
        </el-result>
        <el-table v-if="importResult.failures.length > 0" :data="importResult.failures" border size="small" max-height="200">
          <el-table-column prop="row" label="行号" width="80" />
          <el-table-column prop="word" label="词条" />
          <el-table-column prop="reason" label="失败原因" />
        </el-table>
      </div>

      <template #footer>
        <el-button @click="importVisible = false">关闭</el-button>
        <el-button v-if="importStep === 0" type="primary" :disabled="!importRows.length" @click="importStep = 1">下一步</el-button>
        <el-button v-if="importStep === 1" type="primary" :loading="importLoading" @click="doImport">确认导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Download, Upload, UploadFilled } from '@element-plus/icons-vue'
import { wordApi, categoryApi } from '@/api/manage'
import { formatDateTime } from '@/utils/format'
import { hasPermission } from '@/utils/permission'
import { exportToExcel, parseImportFile, downloadWordImportTemplate } from '@/utils/excel'
import { useCategoryTree } from '@/composables/useCategoryTree'
import { useStatusMaps } from '@/composables/useStatusMaps'

const route = useRoute()

const { statusLabel, statusTagType, riskLabel, riskTagType } = useStatusMaps()

const loading = ref(false)
const exportLoading = ref(false)
const submitLoading = ref(false)
const list = ref<any[]>([])
const total = ref(0)
const categoryTree = ref<any[]>([])
const selectedRows = ref<any[]>([])

const { flatCategories } = useCategoryTree(categoryTree)

const query = reactive({
  page: 1,
  page_size: 20,
  keyword: '',
  category_id: undefined as number | undefined,
  status: '',
  risk_level: '',
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

async function exportExcel() {
  exportLoading.value = true
  try {
    // 分页拉取当前筛选条件下的全部数据
    const allRows: any[] = []
    let page = 1
    const pageSize = 100
    while (true) {
      const data: any = await wordApi.list({
        page,
        page_size: pageSize,
        keyword: query.keyword || undefined,
        status: query.status || undefined,
        risk_level: query.risk_level || undefined,
        category_id: query.category_id,
      })
      const rows = data.list || []
      allRows.push(...rows)
      if (allRows.length >= (data.total || 0) || rows.length < pageSize) break
      page++
    }
    if (allRows.length === 0) {
      ElMessage.info('当前筛选条件下无词条可导出')
      return
    }
    const exportRows = allRows.map((r) => ({
      '词条': r.word || '',
      '拼音': r.pinyin || '',
      '释义': r.meaning || '',
      '示例': r.example || '',
      '状态': statusLabel(r.status),
      '风险等级': riskLabel(r.risk_level),
      '浏览数': r.view_count || 0,
      '投票数': r.vote_count || 0,
      '创建时间': formatDateTime(r.created_at),
    }))
    exportToExcel(exportRows, 'words', '词条列表')
    ElMessage.success(`已导出 ${allRows.length} 条词条`)
  } catch {
  } finally {
    exportLoading.value = false
  }
}

// ---- 新建/编辑 ----
const formVisible = ref(false)
const formRef = ref<FormInstance>()
const editingId = ref(0)
const form = reactive({ word: '', pinyin: '', meaning: '', example: '', origin: '', category_id: undefined as number | undefined, risk_level: 'low' })
const formRules: FormRules = {
  word: [{ required: true, message: '请输入词条', trigger: 'blur' }],
  meaning: [{ required: true, message: '请输入释义', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }],
}

function openCreate() {
  editingId.value = 0
  Object.assign(form, { word: '', pinyin: '', meaning: '', example: '', origin: '', category_id: undefined, risk_level: 'low' })
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
      origin: data.origin || '',
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
          origin: form.origin || undefined,
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
          origin: form.origin || undefined,
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

// ---- 批量操作 ----
function onSelectionChange(rows: any[]) {
  selectedRows.value = rows
}

async function batchStatus(newStatus: string) {
  const ids = selectedRows.value.map((r) => r.id)
  if (!ids.length) return
  const label = statusLabel(newStatus)
  try {
    await ElMessageBox.confirm(`确认将选中的 ${ids.length} 个词条批量设为「${label}」？`, '批量审核', { type: 'warning' })
    await wordApi.batchUpdateStatus(ids, newStatus)
    ElMessage.success('批量审核成功')
    selectedRows.value = []
    loadList()
  } catch {}
}

async function batchDelete() {
  const ids = selectedRows.value.map((r) => r.id)
  if (!ids.length) return
  try {
    await ElMessageBox.confirm(`确认删除选中的 ${ids.length} 个词条？删除后不可恢复。`, '批量删除', { type: 'warning' })
    await wordApi.batchDelete(ids)
    ElMessage.success('批量删除成功')
    selectedRows.value = []
    loadList()
  } catch {}
}

// ---- 批量导入 ----
const importVisible = ref(false)
const importStep = ref(0)
const importRows = ref<any[]>([])
const importLoading = ref(false)
const importResult = reactive({
  success_count: 0,
  skipped_count: 0,
  failed_count: 0,
  failures: [] as Array<{ row: number; word: string; reason: string }>,
})

function openImport() {
  importStep.value = 0
  importRows.value = []
  Object.assign(importResult, { success_count: 0, skipped_count: 0, failed_count: 0, failures: [] })
  importVisible.value = true
}

async function onFileChange(file: any) {
  try {
    const rows = await parseImportFile(file.raw)
    if (!rows.length) {
      ElMessage.warning('文件无数据')
      return
    }
    importRows.value = rows
      .map((r: Record<string, any>) => ({
        word: (r.word || '').toString().trim(),
        meaning: (r.meaning || '').toString().trim(),
        category_name: (r.category_name || '').toString().trim(),
        pinyin: r.pinyin ? r.pinyin.toString().trim() : undefined,
        risk_level: r.risk_level ? r.risk_level.toString().trim() : 'low',
        example: r.example ? r.example.toString().trim() : undefined,
      }))
      .filter((r: any) => r.word && r.meaning && r.category_name)
    if (!importRows.value.length) {
      ElMessage.warning('有效数据为 0，请检查必填列：word / meaning / category_name')
      return
    }
    importStep.value = 1
  } catch (e: any) {
    ElMessage.error(e.message || '文件解析失败')
  }
}

async function doImport() {
  importLoading.value = true
  try {
    const data: any = await wordApi.batchCreate(importRows.value)
    Object.assign(importResult, data)
    importStep.value = 2
    if (data.success_count > 0) {
      ElMessage.success(`成功导入 ${data.success_count} 条词条`)
      loadList()
    }
  } catch (e: any) {
    ElMessage.error(e.message || '导入失败')
  } finally {
    importLoading.value = false
  }
}

function downloadTemplate() {
  downloadWordImportTemplate()
}

onMounted(() => {
  loadCategories()
  // 消费 GlobalSearch 跳转携带的 query.keyword 自动填充并搜索
  const kw = route.query.keyword as string | undefined
  if (kw) {
    query.keyword = kw
  }
  loadList()
  // 若带 edit 参数，可后续触发编辑弹窗（暂仅搜索定位）
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
.batch-bar {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 12px;
  padding: 8px 12px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
  .batch-info {
    margin-right: 8px;
    color: var(--el-text-color-regular);
    font-size: 14px;
  }
}
</style>
