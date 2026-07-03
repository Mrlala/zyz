<template>
  <div class="page-container">
    <!-- 余额 + 弃用预警卡片 -->
    <el-row :gutter="16" style="margin-bottom: 16px">
      <el-col :xs="24" :sm="12" :md="8">
        <div class="stat-card" v-loading="balanceLoading">
          <div class="stat-card-header">
            <span class="stat-label">账户余额</span>
            <el-tag :type="balanceAvailable ? 'success' : 'danger'" size="small" effect="dark">
              {{ balanceAvailable ? '可用' : '不可用' }}
            </el-tag>
          </div>
          <div v-if="balanceCNY" class="balance-body">
            <span class="stat-value" :class="{ 'balance-warn': balanceWarn }">
              ¥{{ balanceCNY.total_balance }}
            </span>
            <div class="balance-detail">
              <span>赠金 ¥{{ balanceCNY.granted_balance }}</span>
              <span>充值 ¥{{ balanceCNY.topped_up_balance }}</span>
            </div>
            <el-button link type="primary" size="small" @click="loadBalance">刷新</el-button>
          </div>
          <div v-else class="balance-empty">
            <span>{{ balanceError || '未获取余额' }}</span>
            <el-button link type="primary" size="small" @click="loadBalance">重试</el-button>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :md="16">
        <div class="stat-card deprecation-card" v-loading="deprecationLoading">
          <div class="stat-card-header">
            <span class="stat-label">当前模型</span>
            <el-tag :type="deprecation.is_deprecated ? 'warning' : 'success'" size="small">
              {{ deprecation.current_model || '-' }}
            </el-tag>
          </div>
          <div v-if="deprecation.is_deprecated" class="deprecation-body">
            <el-alert type="warning" :closable="false" show-icon>
              <template #title>
                ⚠️ 当前模型 <b>{{ deprecation.current_model }}</b> 将于 {{ deprecation.deadline }}（北京时间）弃用
              </template>
              <template #default>
                建议切换到 <b>{{ deprecation.recommended_model }}</b>（兼容旧模型，价格更低）
              </template>
            </el-alert>
            <el-button
              type="warning"
              size="small"
              style="margin-top: 8px"
              :loading="migrateLoading"
              @click="migrateModel"
            >
              一键切换到 {{ deprecation.recommended_model }}
            </el-button>
          </div>
          <div v-else class="deprecation-body">
            <el-alert type="success" :closable="false" show-icon title="当前模型为最新版本，无需切换" />
          </div>
        </div>
      </el-col>
    </el-row>

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
            <!-- 模型字段用下拉选择 -->
            <el-select
              v-if="item.key === 'deepseek_model'"
              v-model="editValues[item.key]"
              placeholder="选择模型"
              filterable
              allow-create
              style="width: 100%"
            >
              <el-option
                v-for="m in modelOptions"
                :key="m.id"
                :label="m.id"
                :value="m.id"
              />
            </el-select>
            <!-- 敏感字段（API Key 等）：密码框 + 显隐切换 -->
            <el-input
              v-else-if="item.is_sensitive"
              v-model="editValues[item.key]"
              type="password"
              placeholder="输入新值以替换（留空不修改）"
              show-password
            />
            <!-- 翻译系统提示词：大文本框 -->
            <el-input
              v-else-if="item.key === 'translate_system_prompt'"
              v-model="editValues[item.key]"
              type="textarea"
              :rows="15"
              placeholder="System Prompt 全文，留空使用默认值"
              style="font-family: monospace; font-size: 13px"
            />
            <!-- 非敏感字段（url/model/temperature 等）：普通文本框 -->
            <el-input
              v-else
              v-model="editValues[item.key]"
              type="text"
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

      <!-- 规则预览卡片 -->
      <el-collapse style="margin-top: 16px">
        <el-collapse-item title="收发规则预览（发送给 AI 的内容 / AI 返回的结构）" name="rules">
          <div v-loading="promptLoading">
            <h4 class="rule-section-title">一、发送规则（User Prompt 模板）</h4>
            <p class="rule-desc">每次翻译时，系统会按以下模板组装 User Prompt 发送给 DeepSeek：</p>
            <pre class="rule-code-block">{{ promptTemplate.user_prompt_template }}</pre>
            <h4 class="rule-section-title" style="margin-top: 12px">占位符说明</h4>
            <el-table :data="promptTemplate.placeholders" border size="small" style="width: 100%">
              <el-table-column prop="name" label="占位符" width="180" />
              <el-table-column prop="desc" label="说明" />
            </el-table>

            <h4 class="rule-section-title" style="margin-top: 16px">二、接收规则（AI 返回 JSON 结构）</h4>
            <p class="rule-desc">AI 必须返回符合以下结构的 JSON，系统解析后展示给用户：</p>
            <el-table :data="promptTemplate.response_fields" border size="small" style="width: 100%">
              <el-table-column prop="field" label="字段" width="160" />
              <el-table-column prop="type" label="类型" width="100" />
              <el-table-column prop="desc" label="说明" />
            </el-table>

            <h4 class="rule-section-title" style="margin-top: 16px">三、当前 System Prompt</h4>
            <el-tag v-if="promptTemplate.is_default" type="info" size="small" style="margin-bottom: 8px">
              当前使用默认 Prompt（未自定义）
            </el-tag>
            <el-tag v-else type="success" size="small" style="margin-bottom: 8px">
              当前使用自定义 Prompt
            </el-tag>
            <pre class="rule-code-block">{{ promptTemplate.system_prompt }}</pre>
          </div>
        </el-collapse-item>
      </el-collapse>

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
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
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

// 余额卡片
const balanceLoading = ref(false)
const balanceData = ref<any>(null)
const balanceError = ref('')
const balanceAvailable = computed(() => !!balanceData.value?.is_available)
const balanceCNY = computed(() => {
  const infos = balanceData.value?.balance_infos || []
  return infos.find((b: any) => b.currency === 'CNY') || infos[0] || null
})
const balanceWarn = computed(() => {
  if (!balanceCNY.value) return false
  return parseFloat(balanceCNY.value.total_balance || '0') < 10
})

// 弃用预警
const deprecationLoading = ref(false)
const deprecation = ref<any>({ current_model: '', is_deprecated: false, deadline: '', recommended_model: '' })
const migrateLoading = ref(false)

// 模型下拉选项
const modelOptions = ref<any[]>([])

// 规则预览
const promptLoading = ref(false)
const promptTemplate = ref<any>({
  system_prompt: '',
  is_default: true,
  user_prompt_template: '',
  placeholders: [],
  response_fields: [],
})

async function loadPromptTemplate() {
  promptLoading.value = true
  try {
    promptTemplate.value = await aiConfigApi.getPromptTemplate()
  } catch {
  } finally {
    promptLoading.value = false
  }
}

async function loadConfig() {
  loading.value = true
  try {
    const data: any = await aiConfigApi.get()
    configs.value = data.list || []
    configs.value.forEach((c) => {
      editValues[c.key] = c.is_sensitive ? '' : c.value || ''
    })
  } catch {
  } finally {
    loading.value = false
  }
}

async function loadBalance() {
  balanceLoading.value = true
  balanceError.value = ''
  try {
    balanceData.value = await aiConfigApi.getBalance()
  } catch (err: any) {
    const resp = err?.response?.data
    balanceError.value = resp?.message || '余额查询失败'
    balanceData.value = null
  } finally {
    balanceLoading.value = false
  }
}

async function loadDeprecation() {
  deprecationLoading.value = true
  try {
    deprecation.value = await aiConfigApi.getDeprecation()
  } catch {
  } finally {
    deprecationLoading.value = false
  }
}

async function loadModels() {
  try {
    const data: any = await aiConfigApi.getModels()
    modelOptions.value = data.list || []
  } catch {
    // 余额未配置或网络错误时，回退到预设列表
    modelOptions.value = [
      { id: 'deepseek-v4-flash' },
      { id: 'deepseek-v4-pro' },
    ]
  }
}

async function migrateModel() {
  const target = deprecation.value.recommended_model
  try {
    await ElMessageBox.confirm(
      `确认将模型从 ${deprecation.value.current_model} 切换到 ${target}？切换后立即生效。`,
      '模型切换确认',
      { type: 'warning' },
    )
    migrateLoading.value = true
    const data: any = await aiConfigApi.migrateModel(target)
    ElMessage.success(`已切换：${data.old_model} → ${data.new_model}`)
    await loadConfig()
    await loadDeprecation()
  } catch {
  } finally {
    migrateLoading.value = false
  }
}

async function save() {
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
    loadDeprecation()
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
    const resp = err?.response?.data
    if (resp && typeof resp.code === 'number') {
      testResult.value = resp.data || { error: resp.message }
    } else {
      testResult.value = { error: resp?.detail || err?.message || '未知错误' }
    }
    testSuccess.value = false
    testResultVisible.value = true
  } finally {
    testLoading.value = false
  }
}

onMounted(() => {
  loadConfig()
  loadBalance()
  loadDeprecation()
  loadModels()
  loadPromptTemplate()
})
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

/* 余额卡片 */
.stat-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 16px;
  height: 100%;
  min-height: 140px;
}
.stat-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.stat-label {
  font-size: 14px;
  color: #909399;
}
.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}
.balance-warn {
  color: #f56c6c;
}
.balance-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.balance-detail {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #909399;
}
.balance-empty {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #c0c4cc;
  font-size: 13px;
}
.deprecation-card {
  display: flex;
  flex-direction: column;
}
.deprecation-body {
  margin-top: 8px;
}
.rule-section-title {
  margin: 0 0 6px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
.rule-desc {
  margin: 0 0 8px;
  font-size: 13px;
  color: #606266;
}
.rule-code-block {
  margin: 0;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 6px;
  font-family: monospace;
  font-size: 12px;
  line-height: 1.6;
  color: #303133;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
}
</style>
