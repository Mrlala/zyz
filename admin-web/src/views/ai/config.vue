<template>
  <div class="page-container">
    <div class="page-card">
      <div class="config-header">
        <h3 style="margin: 0">AI 配置管理</h3>
        <div>
          <el-button :loading="testLoading" @click="testConnection">测试连接</el-button>
          <el-button type="primary" :loading="saveLoading" @click="save">保存配置</el-button>
        </div>
      </div>

      <el-alert type="info" :closable="false" show-icon style="margin: 12px 0">
        敏感字段（API Key）默认隐藏，如需修改请输入新值；非敏感字段可直接编辑。空值不会被保存。
      </el-alert>

      <el-form v-loading="loading" label-width="180px" style="max-width: 720px; margin-top: 16px">
        <el-form-item v-for="item in configs" :key="item.key" :label="item.description || item.key">
          <div class="config-item">
            <el-input
              v-model="editValues[item.key]"
              :type="item.is_sensitive && !revealSecret[item.key] ? 'password' : 'text'"
              :placeholder="item.is_sensitive ? '输入新值以替换（留空不修改）' : ''"
              show-password
            />
            <div class="config-meta">
              <el-tag size="small" :type="item.is_sensitive ? 'danger' : 'info'">
                {{ item.is_sensitive ? '敏感' : '普通' }}
              </el-tag>
              <span class="config-key">{{ item.key }}</span>
              <span class="config-type">({{ item.value_type }})</span>
            </div>
          </div>
        </el-form-item>
      </el-form>

      <!-- 测试结果 -->
      <el-dialog v-model="testResultVisible" title="AI 连接测试结果" width="500px">
        <el-result v-if="testSuccess" icon="success" title="连接成功" :sub-title="`模型: ${testResult.model}`">
          <template #extra>
            <div class="test-detail">
              <p><b>API URL:</b> {{ testResult.api_url }}</p>
              <p><b>回复:</b> {{ testResult.reply }}</p>
              <p><b>Token:</b> 输入 {{ testResult.usage?.prompt_tokens }} / 输出 {{ testResult.usage?.completion_tokens }} / 共 {{ testResult.usage?.total_tokens }}</p>
            </div>
          </template>
        </el-result>
        <el-result v-else icon="error" title="连接失败" :sub-title="testResult?.error">
          <template #extra>
            <div class="test-detail">
              <p v-if="testResult?.api_url"><b>API URL:</b> {{ testResult.api_url }}</p>
              <p v-if="testResult?.model"><b>模型:</b> {{ testResult.model }}</p>
            </div>
          </template>
        </el-result>
        <template #footer>
          <el-button @click="testResultVisible = false">关闭</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { aiConfigApi } from '@/api/manage'

const loading = ref(false)
const saveLoading = ref(false)
const testLoading = ref(false)
const configs = ref<any[]>([])
const editValues = reactive<Record<string, string>>({})
const revealSecret = reactive<Record<string, boolean>>({})

const testResultVisible = ref(false)
const testResult = ref<any>(null)
const testSuccess = ref(false)

async function loadConfig() {
  loading.value = true
  try {
    const data: any = await aiConfigApi.get()
    configs.value = data.list || []
    // 初始化编辑值：非敏感字段显示当前值，敏感字段留空
    configs.value.forEach((c) => {
      editValues[c.key] = c.is_sensitive ? '' : c.value || ''
    })
  } catch {
  } finally {
    loading.value = false
  }
}

async function save() {
  // 只提交有值的项
  const toUpdate = configs.value
    .filter((c) => editValues[c.key] !== '' && editValues[c.key] !== c.value)
    .map((c) => ({ key: c.key, value: editValues[c.key] }))

  if (toUpdate.length === 0) {
    ElMessage.info('没有需要更新的配置')
    return
  }

  saveLoading.value = true
  try {
    const data: any = await aiConfigApi.update(toUpdate)
    ElMessage.success(`已更新 ${data.updated_count} 项配置`)
    loadConfig()
  } catch {
  } finally {
    saveLoading.value = false
  }
}

async function testConnection() {
  testLoading.value = true
  try {
    const data: any = await aiConfigApi.test()
    testResult.value = data
    testSuccess.value = true
    testResultVisible.value = true
  } catch (err: any) {
    // 后端 code=1 时拦截器会 reject，err.response.data 是 BaseResponse
    const resp = err?.response?.data
    if (resp && typeof resp.code === 'number') {
      // BaseResponse 业务失败：提取 data 字段（含 error/api_url/model）
      testResult.value = resp.data || { error: resp.message }
    } else {
      // HTTP 错误（如 400/500）
      testResult.value = { error: resp?.detail || err?.message || '未知错误' }
    }
    testSuccess.value = false
    testResultVisible.value = true
  } finally {
    testLoading.value = false
  }
}

onMounted(loadConfig)
</script>

<style scoped lang="scss">
.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.config-item {
  width: 100%;
}
.config-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}
.config-key {
  font-family: monospace;
}
.config-type {
  color: #c0c4cc;
}
.test-detail {
  text-align: left;
  font-size: 13px;
  line-height: 1.8;
}
</style>
