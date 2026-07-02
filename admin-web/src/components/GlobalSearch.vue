<template>
  <el-dialog
    v-model="visible"
    title="全局搜索"
    width="600px"
    align-center
    :show-close="true"
    append-to-body
    @open="onOpen"
  >
    <el-input
      ref="inputRef"
      v-model="keyword"
      size="large"
      placeholder="搜索词条 / 用户提交 / 管理员 / 操作日志..."
      :prefix-icon="Search"
      clearable
      @input="onInput"
      @keydown.esc="visible = false"
    >
      <template #loading>
        <el-icon v-if="loading" class="is-loading"><Loading /></el-icon>
      </template>
    </el-input>

    <el-scrollbar max-height="420px" class="search-result">
      <!-- 空状态 -->
      <div v-if="!keyword.trim()" class="search-empty">
        <el-icon><Search /></el-icon>
        <p>输入关键词开始搜索</p>
      </div>

      <!-- 无结果 -->
      <div v-else-if="!loading && isEmpty" class="search-empty">
        <el-icon><CircleClose /></el-icon>
        <p>未找到与「{{ keyword }}」相关的结果</p>
      </div>

      <!-- 分组结果 -->
      <template v-else>
        <div v-if="result.words.length" class="search-group">
          <div class="group-title">
            <el-icon><Document /></el-icon>
            词条（{{ result.words.length }}）
          </div>
          <div
            v-for="w in result.words"
            :key="`w-${w.id}`"
            class="search-item"
            @click="goWord(w)"
          >
            <div class="item-content">
              <div class="item-label">
                <span class="hl">{{ w.word }}</span>
                <el-tag v-if="w.pinyin" size="small" type="info" class="ml">{{ w.pinyin }}</el-tag>
                <el-tag size="small" :type="statusTagType(w.status)" class="ml">{{ statusLabel(w.status) }}</el-tag>
              </div>
              <div class="item-desc">{{ w.meaning || '（无释义）' }}</div>
            </div>
            <el-icon class="item-arrow"><ArrowRight /></el-icon>
          </div>
        </div>

        <div v-if="result.submissions.length" class="search-group">
          <div class="group-title">
            <el-icon><EditPen /></el-icon>
            用户提交（{{ result.submissions.length }}）
          </div>
          <div
            v-for="s in result.submissions"
            :key="`s-${s.id}`"
            class="search-item"
            @click="goSubmission(s)"
          >
            <div class="item-content">
              <div class="item-label">
                <span class="hl">{{ s.word }}</span>
                <el-tag size="small" :type="statusTagType(s.status)" class="ml">{{ statusLabel(s.status) }}</el-tag>
              </div>
              <div class="item-desc">{{ s.meaning || '（无释义）' }}</div>
            </div>
            <el-icon class="item-arrow"><ArrowRight /></el-icon>
          </div>
        </div>

        <div v-if="result.admins.length" class="search-group">
          <div class="group-title">
            <el-icon><UserFilled /></el-icon>
            管理员（{{ result.admins.length }}）
          </div>
          <div
            v-for="a in result.admins"
            :key="`a-${a.id}`"
            class="search-item"
            @click="goAdmin(a)"
          >
            <div class="item-content">
              <div class="item-label">
                <span class="hl">{{ a.username }}</span>
                <span v-if="a.nickname" class="ml nickname">（{{ a.nickname }}）</span>
                <el-tag size="small" :type="a.status === 'active' ? 'success' : 'danger'" class="ml">
                  {{ a.status === 'active' ? '启用' : '禁用' }}
                </el-tag>
              </div>
            </div>
            <el-icon class="item-arrow"><ArrowRight /></el-icon>
          </div>
        </div>

        <div v-if="result.logs.length" class="search-group">
          <div class="group-title">
            <el-icon><List /></el-icon>
            操作日志（{{ result.logs.length }}）
          </div>
          <div
            v-for="log in result.logs"
            :key="`l-${log.id}`"
            class="search-item"
            @click="goLog(log)"
          >
            <div class="item-content">
              <div class="item-label">
                <span class="mono">{{ log.method }}</span>
                <span class="ml path">{{ log.path }}</span>
                <el-tag size="small" :type="log.status_code < 400 ? 'success' : 'danger'" class="ml">
                  {{ log.status_code }}
                </el-tag>
              </div>
              <div class="item-desc">
                {{ log.username || '-' }} · {{ log.module }}/{{ log.action }} · {{ formatDateTime(log.created_at) }}
              </div>
            </div>
            <el-icon class="item-arrow"><ArrowRight /></el-icon>
          </div>
        </div>
      </template>
    </el-scrollbar>
    <div class="search-tip">按 Ctrl+K 快速打开 | Esc 关闭 | ↑↓ 选择</div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  Search, Document, UserFilled, List, ArrowRight, EditPen, CircleClose, Loading,
} from '@element-plus/icons-vue'
import { searchApi } from '@/api/manage'
import { formatDateTime } from '@/utils/format'
import { useStatusMaps } from '@/composables/useStatusMaps'

const { statusLabel, statusTagType } = useStatusMaps()

const visible = ref(false)
const keyword = ref('')
const loading = ref(false)
const inputRef = ref()
const router = useRouter()

interface SearchResult {
  words: any[]
  submissions: any[]
  admins: any[]
  logs: any[]
}
const result = ref<SearchResult>({ words: [], submissions: [], admins: [], logs: [] })

const isEmpty = computed(() =>
  !result.value.words.length &&
  !result.value.submissions.length &&
  !result.value.admins.length &&
  !result.value.logs.length,
)

let debounceTimer: ReturnType<typeof setTimeout> | null = null

function onKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    visible.value = !visible.value
    if (!visible.value) {
      keyword.value = ''
      result.value = { words: [], submissions: [], admins: [], logs: [] }
    }
  }
}

function onOpen() {
  nextTick(() => inputRef.value?.focus())
}

function onInput() {
  if (debounceTimer) clearTimeout(debounceTimer)
  const kw = keyword.value.trim()
  if (!kw) {
    result.value = { words: [], submissions: [], admins: [], logs: [] }
    return
  }
  debounceTimer = setTimeout(async () => {
    loading.value = true
    try {
      const data: any = await searchApi.search(kw, 5)
      result.value = {
        words: data.words || [],
        submissions: data.submissions || [],
        admins: data.admins || [],
        logs: data.logs || [],
      }
    } catch {
      result.value = { words: [], submissions: [], admins: [], logs: [] }
    } finally {
      loading.value = false
    }
  }, 300)
}

function goWord(w: any) {
  router.push({ path: '/content/words', query: { keyword: w.word, edit: w.id } })
  closeDialog()
}

function goSubmission(s: any) {
  router.push({ path: '/content/audit', query: { tab: 'submission', word: s.word } })
  closeDialog()
}

function goAdmin(a: any) {
  router.push({ path: '/system/accounts', query: { keyword: a.username } })
  closeDialog()
}

function goLog(log: any) {
  router.push({ path: '/audit/logs', query: { module: log.module } })
  closeDialog()
}

function closeDialog() {
  visible.value = false
  keyword.value = ''
  result.value = { words: [], submissions: [], admins: [], logs: [] }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  if (debounceTimer) clearTimeout(debounceTimer)
})
</script>

<style scoped lang="scss">
.search-result {
  margin-top: 12px;
}
.search-empty {
  text-align: center;
  padding: 40px 0;
  color: #909399;
  .el-icon {
    font-size: 32px;
    margin-bottom: 8px;
  }
  p {
    margin: 4px 0 0;
    font-size: 13px;
  }
}
.search-group {
  padding: 0 4px;
  margin-bottom: 8px;
}
.group-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #909399;
  padding: 8px 4px;
  letter-spacing: 0.3px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  margin-bottom: 4px;
}
.search-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}
.search-item:hover {
  background: var(--el-fill-color-light);
}
.item-content {
  flex: 1;
  min-width: 0;
}
.item-label {
  font-size: 14px;
  color: #303133;
  line-height: 1.5;
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}
.item-desc {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.item-arrow {
  font-size: 14px;
  color: #c0c4cc;
  flex-shrink: 0;
}
.ml {
  margin-left: 4px;
}
.hl {
  font-weight: 500;
}
.nickname {
  color: #606266;
  font-size: 13px;
}
.mono {
  font-family: monospace;
  font-size: 12px;
  padding: 1px 4px;
  background: var(--el-fill-color);
  border-radius: 2px;
}
.path {
  font-family: monospace;
  font-size: 13px;
  color: #409eff;
}
.search-tip {
  margin-top: 12px;
  font-size: 12px;
  color: #909399;
  text-align: center;
}
</style>
