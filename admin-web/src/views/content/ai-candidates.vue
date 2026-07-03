<template>
  <div class="page-container">
    <div class="page-card">
      <div class="toolbar">
        <el-input
          v-model="query.keyword"
          placeholder="搜索候选词"
          clearable
          style="width: 180px"
          @keyup.enter="loadList"
        />
        <el-select v-model="query.status" placeholder="状态" clearable style="width: 140px" @change="loadList">
          <el-option label="累积中" value="collecting" />
          <el-option label="已转提交" value="promoted" />
          <el-option label="已丢弃" value="discarded" />
        </el-select>
        <el-input-number v-model="query.min_count" :min="1" placeholder="最小频次" controls-position="right" style="width: 130px" @change="loadList" />
        <el-button type="primary" @click="loadList">查询</el-button>
        <el-button @click="resetFilter">重置</el-button>
      </div>

      <el-table :data="list" v-loading="loading" border stripe style="margin-top: 12px">
        <el-table-column prop="word" label="候选词" min-width="120" />
        <el-table-column label="AI 释义" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.meaning">{{ row.meaning }}</span>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="occurrence_count" label="出现频次" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.occurrence_count >= 3 ? 'success' : 'info'" size="small">
              {{ row.occurrence_count }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="原文片段" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.context_sample" style="color: #606266">{{ row.context_sample }}</span>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="first_seen_at" label="首次出现" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.first_seen_at) }}</template>
        </el-table-column>
        <el-table-column prop="last_seen_at" label="最近出现" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.last_seen_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <div class="table-ops">
              <el-button
                v-if="row.status === 'collecting'"
                link
                type="primary"
                @click="promote(row)"
              >转提交</el-button>
              <el-button
                v-if="row.status === 'collecting'"
                link
                type="warning"
                @click="discard(row)"
              >丢弃</el-button>
              <span v-if="row.status === 'promoted'" style="color: #909399; font-size: 12px">
                Submission #{{ row.promoted_submission_id }}
              </span>
              <span v-if="row.status === 'discarded'" style="color: #c0c4cc; font-size: 12px">已丢弃</span>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.page_size"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 12px; justify-content: flex-end"
        @size-change="loadList"
        @current-change="loadList"
      />
      <el-empty v-if="!loading && list.length === 0" description="暂无 AI 候选词，用户翻译后系统会自动收集新词" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { aiCandidateApi } from '@/api/manage'
import { formatDateTime } from '@/utils/format'

const loading = ref(false)
const list = ref<any[]>([])
const total = ref(0)
const query = reactive({
  page: 1,
  page_size: 20,
  keyword: '',
  status: '',
  min_count: undefined as number | undefined,
})

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    collecting: '累积中',
    promoted: '已转提交',
    discarded: '已丢弃',
  }
  return map[s] || s
}

function statusTagType(s: string): string {
  const map: Record<string, string> = {
    collecting: 'warning',
    promoted: 'success',
    discarded: 'info',
  }
  return map[s] || 'info'
}

async function loadList() {
  loading.value = true
  try {
    const data: any = await aiCandidateApi.list({
      page: query.page,
      page_size: query.page_size,
      status: query.status || undefined,
      min_count: query.min_count,
      keyword: query.keyword || undefined,
    })
    list.value = data.list || []
    total.value = data.total || 0
  } catch {
  } finally {
    loading.value = false
  }
}

function resetFilter() {
  query.keyword = ''
  query.status = ''
  query.min_count = undefined
  query.page = 1
  loadList()
}

async function promote(row: any) {
  try {
    await ElMessageBox.confirm(`确认将候选词「${row.word}」转为 Submission 进入人工审核？`, '提示', { type: 'warning' })
    await aiCandidateApi.promote(row.id)
    ElMessage.success('已转为 Submission')
    loadList()
  } catch {}
}

async function discard(row: any) {
  try {
    await ElMessageBox.confirm(`确认丢弃候选词「${row.word}」？丢弃后不再累积频次。`, '提示', { type: 'warning' })
    await aiCandidateApi.discard(row.id)
    ElMessage.success('已丢弃')
    loadList()
  } catch {}
}

onMounted(() => {
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
.table-ops {
  display: flex;
  gap: 4px;
  align-items: center;
}
</style>
