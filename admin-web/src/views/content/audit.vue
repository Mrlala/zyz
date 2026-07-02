<template>
  <div class="page-container">
    <div class="page-card">
      <el-tabs v-model="activeTab" @tab-change="onTabChange">
        <!-- 用户提交审核 -->
        <el-tab-pane label="用户提交审核" name="submission">
          <div class="toolbar">
            <el-select v-model="subQuery.status" style="width: 120px" @change="loadSubmissions">
              <el-option label="待审核" value="pending" />
              <el-option label="已通过" value="approved" />
              <el-option label="已拒绝" value="rejected" />
            </el-select>
            <el-button type="primary" @click="loadSubmissions">刷新</el-button>
          </div>

          <el-table :data="submissions" v-loading="subLoading" border stripe style="margin-top: 12px">
            <el-table-column prop="word" label="词条" min-width="120" />
            <el-table-column prop="meaning" label="释义" min-width="200" show-overflow-tooltip />
            <el-table-column prop="example" label="示例" min-width="160" show-overflow-tooltip />
            <el-table-column label="提交者" min-width="120">
              <template #default="{ row }">{{ row.submitter?.nickname || '-' }}</template>
            </el-table-column>
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="reviewTagType(row.status)" size="small">{{ reviewLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="提交时间" min-width="150">
              <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <div class="table-ops" v-if="row.status === 'pending'">
                  <el-button link type="success" @click="openReviewSubmission(row, 'approve')">通过</el-button>
                  <el-button link type="danger" @click="openReviewSubmission(row, 'reject')">驳回</el-button>
                </div>
                <span v-else class="done-text">已处理</span>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-model:current-page="subQuery.page"
            v-model:page-size="subQuery.page_size"
            :total="subTotal"
            layout="total, prev, pager, next"
            style="margin-top: 12px; justify-content: flex-end"
            @current-change="loadSubmissions"
          />
        </el-tab-pane>

        <!-- 纠错审核 -->
        <el-tab-pane label="纠错审核" name="correction">
          <div class="toolbar">
            <el-select v-model="corrQuery.status" style="width: 120px" @change="loadCorrections">
              <el-option label="待审核" value="pending" />
              <el-option label="已通过" value="approved" />
              <el-option label="已拒绝" value="rejected" />
            </el-select>
            <el-button type="primary" @click="loadCorrections">刷新</el-button>
          </div>

          <el-table :data="corrections" v-loading="corrLoading" border stripe style="margin-top: 12px">
            <el-table-column prop="word" label="被纠错词条" min-width="120" />
            <el-table-column label="纠错类型" width="120">
              <template #default="{ row }">{{ correctionTypeLabel(row.type) }}</template>
            </el-table-column>
            <el-table-column prop="content" label="纠错内容" min-width="240" show-overflow-tooltip />
            <el-table-column label="提交者" min-width="120">
              <template #default="{ row }">{{ row.submitter?.nickname || '-' }}</template>
            </el-table-column>
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="reviewTagType(row.status)" size="small">{{ reviewLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="提交时间" min-width="150">
              <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <div class="table-ops" v-if="row.status === 'pending'">
                  <el-button link type="success" @click="reviewCorrection(row, 'approve')">通过</el-button>
                  <el-button link type="danger" @click="reviewCorrection(row, 'reject')">驳回</el-button>
                </div>
                <span v-else class="done-text">已处理</span>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-model:current-page="corrQuery.page"
            v-model:page-size="corrQuery.page_size"
            :total="corrTotal"
            layout="total, prev, pager, next"
            style="margin-top: 12px; justify-content: flex-end"
            @current-change="loadCorrections"
          />
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 提交审核弹窗 -->
    <el-dialog v-model="reviewVisible" :title="reviewAction === 'approve' ? '通过提交' : '驳回提交'" width="500px">
      <el-form label-width="90px">
        <el-form-item label="词条">
          <el-input :model-value="reviewTarget?.word" disabled />
        </el-form-item>
        <el-form-item label="原释义">
          <el-input :model-value="reviewTarget?.meaning" type="textarea" :rows="2" disabled />
        </el-form-item>
        <el-form-item v-if="reviewAction === 'approve'" label="覆盖释义">
          <el-input v-model="reviewForm.meaning" type="textarea" :rows="2" placeholder="留空则使用原释义" />
        </el-form-item>
        <el-form-item v-if="reviewAction === 'reject'" label="驳回原因">
          <el-input v-model="reviewForm.comment" type="textarea" :rows="2" placeholder="请填写驳回原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewVisible = false">取消</el-button>
        <el-button :type="reviewAction === 'approve' ? 'success' : 'danger'" :loading="submitLoading" @click="submitReview">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { contentAuditApi } from '@/api/manage'
import { formatDateTime } from '@/utils/format'

const activeTab = ref('submission')

// 提交审核
const subLoading = ref(false)
const submissions = ref<any[]>([])
const subTotal = ref(0)
const subQuery = reactive({ page: 1, page_size: 20, status: 'pending' })

// 纠错审核
const corrLoading = ref(false)
const corrections = ref<any[]>([])
const corrTotal = ref(0)
const corrQuery = reactive({ page: 1, page_size: 20, status: 'pending' })

// 审核弹窗
const reviewVisible = ref(false)
const reviewTarget = ref<any>(null)
const reviewAction = ref('approve')
const reviewForm = reactive({ comment: '', meaning: '' })
const submitLoading = ref(false)

async function loadSubmissions() {
  subLoading.value = true
  try {
    const data: any = await contentAuditApi.listSubmissions({
      page: subQuery.page,
      page_size: subQuery.page_size,
      status: subQuery.status,
    })
    submissions.value = data.list || []
    subTotal.value = data.total || 0
  } catch {
  } finally {
    subLoading.value = false
  }
}

async function loadCorrections() {
  corrLoading.value = true
  try {
    const data: any = await contentAuditApi.listCorrections({
      page: corrQuery.page,
      page_size: corrQuery.page_size,
      status: corrQuery.status,
    })
    corrections.value = data.list || []
    corrTotal.value = data.total || 0
  } catch {
  } finally {
    corrLoading.value = false
  }
}

function onTabChange(tab: string) {
  if (tab === 'submission') loadSubmissions()
  else loadCorrections()
}

function reviewLabel(s: string) {
  return { pending: '待审核', approved: '已通过', rejected: '已拒绝' }[s] || s
}
function reviewTagType(s: string): any {
  return { pending: 'warning', approved: 'success', rejected: 'danger' }[s] || 'info'
}
function correctionTypeLabel(t: string) {
  return {
    meaning_wrong: '释义错误',
    example_wrong: '例句/出处错误',
    pinyin_wrong: '拼音错误',
    category_wrong: '分类错误',
    risk_wrong: '风险标注错误',
    outdated: '已过时',
    other: '其他',
  }[t] || t
}

function openReviewSubmission(row: any, action: string) {
  reviewTarget.value = row
  reviewAction.value = action
  Object.assign(reviewForm, { comment: '', meaning: '' })
  reviewVisible.value = true
}

async function submitReview() {
  submitLoading.value = true
  try {
    await contentAuditApi.reviewSubmission(reviewTarget.value.id, {
      action: reviewAction.value,
      comment: reviewForm.comment || undefined,
      meaning: reviewAction.value === 'approve' ? reviewForm.meaning || undefined : undefined,
    })
    ElMessage.success(reviewAction.value === 'approve' ? '已通过' : '已驳回')
    reviewVisible.value = false
    loadSubmissions()
  } catch {
  } finally {
    submitLoading.value = false
  }
}

async function reviewCorrection(row: any, action: string) {
  const label = action === 'approve' ? '通过' : '驳回'
  try {
    if (action === 'reject') {
      const { value } = await ElMessageBox.prompt('请填写驳回原因', '驳回纠错', {
        confirmButtonText: '确认驳回',
        inputType: 'textarea',
      })
      await contentAuditApi.reviewCorrection(row.id, { action, comment: value || undefined })
    } else {
      await ElMessageBox.confirm(`确认${label}该纠错？`, '提示', { type: 'warning' })
      await contentAuditApi.reviewCorrection(row.id, { action })
    }
    ElMessage.success(`已${label}`)
    loadCorrections()
  } catch {}
}

onMounted(() => {
  loadSubmissions()
  loadCorrections()
})
</script>

<style scoped lang="scss">
.toolbar {
  display: flex;
  gap: 8px;
  align-items: center;
}
.done-text {
  font-size: 12px;
  color: #c0c4cc;
}
</style>
