<template>
  <view class="submissions-page">
    <!-- 顶部栏 -->
    <view class="top-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="top-bar__inner">
        <view class="top-bar__btn" @click="handleBack">
          <ArrowLeft :size="20" color="#6B7280" />
        </view>
        <text class="top-bar__title">我的提交</text>
        <view class="top-bar__add" @click="openSubmit">
          <Plus :size="16" color="#FFFFFF" />
        </view>
      </view>
    </view>
    <view class="top-bar-placeholder" :style="{ height: (statusBarHeight + 54) + 'px' }"></view>

    <!-- 加载中 -->
    <view v-if="loading && !list.length" class="state-tip">
      <text>加载中...</text>
    </view>

    <template v-else>
      <!-- 提交列表 -->
      <view v-if="list.length" class="submit-list">
        <view
          v-for="item in list"
          :key="item.submission_id || item.id"
          class="submit-card"
        >
          <view class="submit-card__header">
            <text class="submit-card__word">{{ item.word }}</text>
            <text class="submit-card__badge" :class="`submit-card__badge--${item.status}`">{{ statusText(item.status) }}</text>
          </view>
          <text class="submit-card__definition">{{ item.definition }}</text>
          <text v-if="item.example" class="submit-card__example">示例：{{ item.example }}</text>
          <text class="submit-card__time">提交于 {{ formatTime(item.submitted_at) }}</text>

          <!-- 驳回原因（已拒绝） -->
          <view v-if="item.reject_reason" class="submit-card__reason">
            <text class="submit-card__reason-text">驳回原因：{{ item.reject_reason }}</text>
          </view>
        </view>

        <!-- 加载更多 -->
        <view v-if="list.length < total" class="load-more" @click="loadMore">
          <text>{{ loading ? '加载中...' : '加载更多' }}</text>
        </view>
        <view v-else class="load-more load-more--end">
          <text>没有更多了</text>
        </view>
      </view>

      <!-- 空状态 -->
      <view v-else class="empty-state">
        <view class="empty-state__icon">
          <Send :size="32" color="#9CA3AF" />
        </view>
        <text class="empty-state__text">暂无提交记录</text>
        <text class="empty-state__sub">提交新词条，丰富词库</text>
        <view class="empty-state__btn" @click="openSubmit">
          <text class="empty-state__btn-text">提交新词条</text>
        </view>
      </view>
    </template>

    <!-- 提交新词条弹层 -->
    <view v-if="submitVisible" class="submit-modal" @click="closeSubmit">
      <view class="submit-modal__mask"></view>
      <view class="submit-modal__panel" @click.stop>
        <view class="submit-modal__title">提交新词条</view>
        <view class="submit-modal__field">
          <text class="submit-modal__label">词条 <text class="submit-modal__required">*</text></text>
          <input
            class="submit-modal__input"
            v-model="form.word"
            placeholder="如：yyds"
            placeholder-class="submit-modal__placeholder"
            :maxlength="20"
          />
        </view>
        <view class="submit-modal__field">
          <text class="submit-modal__label">释义 <text class="submit-modal__required">*</text></text>
          <textarea
            class="submit-modal__textarea"
            v-model="form.definition"
            placeholder="用一句话解释这个词的意思"
            placeholder-class="submit-modal__placeholder"
            :maxlength="200"
          />
        </view>
        <view class="submit-modal__field">
          <text class="submit-modal__label">示例</text>
          <textarea
            class="submit-modal__textarea submit-modal__textarea--sm"
            v-model="form.example"
            placeholder="造个句子（可选）"
            placeholder-class="submit-modal__placeholder"
            :maxlength="100"
          />
        </view>
        <view class="submit-modal__btns">
          <view class="submit-modal__btn submit-modal__btn--cancel" @click="closeSubmit">取消</view>
          <view
            class="submit-modal__btn submit-modal__btn--submit"
            :class="{ 'submit-modal__btn--disabled': submitting }"
            @click="handleSubmit"
          >{{ submitting ? '提交中...' : '提交' }}</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { onLoad, onReachBottom, onPullDownRefresh } from '@dcloudio/uni-app'
import { ArrowLeft, Plus, Send } from 'lucide-vue-next'
import * as submissionApi from '@/api/submission'

const statusBarHeight = ref(0)
const list = ref([])
const page = ref(1)
const pageSize = 20
const total = ref(0)
const loading = ref(false)

// 提交弹层
const submitVisible = ref(false)
const submitting = ref(false)
const form = reactive({
  word: '',
  definition: '',
  example: ''
})

onLoad(() => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
  fetchList(true)
})

onPullDownRefresh(() => {
  fetchList(true).finally(() => {
    uni.stopPullDownRefresh()
  })
})

onReachBottom(() => {
  loadMore()
})

// 获取提交列表
async function fetchList(reset = false) {
  if (loading.value) return
  loading.value = true
  if (reset) {
    page.value = 1
    list.value = []
  }
  try {
    const params = { page: page.value, page_size: pageSize }
    const data = await submissionApi.getMySubmissions(params)
    const arr = (data && data.list) || []
    total.value = (data && data.total) || 0
    list.value = reset ? arr : list.value.concat(arr)
  } catch (err) {
    console.error('获取提交列表失败', err)
  } finally {
    loading.value = false
  }
}

function loadMore() {
  if (loading.value || list.value.length >= total.value) return
  page.value++
  fetchList(false)
}

// 状态文案（文案对齐：已驳回→已拒绝）
function statusText(s) {
  const map = { pending: '审核中', approved: '已通过', rejected: '已拒绝' }
  return map[s] || s || ''
}

// 打开提交弹层
function openSubmit() {
  form.word = ''
  form.definition = ''
  form.example = ''
  submitVisible.value = true
}

function closeSubmit() {
  submitVisible.value = false
}

// 提交新词条
async function handleSubmit() {
  if (submitting.value) return
  if (!form.word.trim()) {
    uni.showToast({ title: '请输入词条', icon: 'none' })
    return
  }
  if (!form.definition.trim()) {
    uni.showToast({ title: '请输入释义', icon: 'none' })
    return
  }
  submitting.value = true
  try {
    await submissionApi.submitWord({
      word: form.word.trim(),
      definition: form.definition.trim(),
      example: form.example.trim()
    })
    uni.showToast({ title: '提交成功，等待审核', icon: 'success' })
    closeSubmit()
    fetchList(true)
  } catch (err) {
    console.error('提交失败', err)
  } finally {
    submitting.value = false
  }
}

function handleBack() {
  uni.navigateBack({ delta: 1 })
}

// 格式化时间
function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(typeof ts === 'number' ? ts : Date.parse(ts))
  if (isNaN(d.getTime())) return ''
  const now = Date.now()
  const diff = now - d.getTime()
  if (diff < 86400000) return '今天'
  if (diff < 86400000 * 2) return '昨天'
  if (diff < 86400000 * 7) return Math.floor(diff / 86400000) + '天前'
  if (diff < 86400000 * 14) return '1周前'
  if (diff < 86400000 * 30) return Math.floor(diff / (86400000 * 7)) + '周前'
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${m}-${day}`
}
</script>

<style lang="scss" scoped>
.submissions-page {
  min-height: 100vh;
  background-color: $bg-page;
}

/* ============ 顶部栏 ============ */
.top-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 30;
  background-color: $bg-page;

  &__inner {
    height: 54px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 16px;
  }

  &__btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__title {
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
  }

  &__add {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background-color: $color-primary;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.top-bar-placeholder {
  width: 100%;
}

/* ============ 状态提示 ============ */
.state-tip {
  padding: 64px 0;
  text-align: center;
  font-size: 14px;
  color: $text-secondary;
}

/* ============ 提交列表 ============ */
.submit-list {
  padding: 8px 16px 32px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.submit-card {
  padding: 14px 16px;
  border-radius: 10px;
  background-color: $bg-card;
  box-shadow: $shadow-sm;

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  &__word {
    flex: 1;
    min-width: 0;
    font-size: 15px;
    font-weight: 600;
    color: $text-primary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__badge {
    flex-shrink: 0;
    padding: 2px 10px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 500;
    white-space: nowrap;

    &--pending {
      background-color: rgba(254, 44, 85, 0.1);
      color: $color-primary;
    }
    &--approved {
      background-color: rgba(16, 185, 129, 0.1);
      color: $color-success;
    }
    &--rejected {
      background-color: rgba(239, 68, 68, 0.1);
      color: $color-danger;
    }
  }

  &__definition {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    overflow: hidden;
    margin-top: 8px;
    font-size: 13px;
    line-height: 1.5;
    color: $text-secondary;
  }

  &__example {
    display: block;
    margin-top: 4px;
    font-size: 12px;
    color: $text-tertiary;
    line-height: 1.5;
  }

  &__time {
    display: block;
    margin-top: 8px;
    font-size: 11px;
    color: $text-tertiary;
  }

  &__reason {
    margin-top: 8px;
    padding: 8px 12px;
    border-radius: 8px;
    background-color: rgba(239, 68, 68, 0.06);
  }

  &__reason-text {
    font-size: 12px;
    color: $color-danger;
    line-height: 1.6;
  }
}

/* ============ 加载更多 ============ */
.load-more {
  text-align: center;
  padding: 16px 0;
  font-size: 12px;
  color: $text-tertiary;

  &--end {
    color: $text-tertiary;
  }
}

/* ============ 空状态 ============ */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80px 0 40px;

  &__icon {
    width: 56px;
    height: 56px;
    border-radius: 16px;
    background-color: $bg-sunken;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 12px;
  }

  &__text {
    font-size: 14px;
    color: $text-secondary;
    margin-bottom: 4px;
  }

  &__sub {
    font-size: 12px;
    color: $text-tertiary;
  }

  &__btn {
    margin-top: 16px;
    padding: 8px 20px;
    border-radius: 9999px;
    background-color: $color-primary;
  }

  &__btn-text {
    font-size: 13px;
    font-weight: 500;
    color: #FFFFFF;
  }
}

/* ============ 提交弹层 ============ */
.submit-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;

  &__mask {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
  }

  &__panel {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    max-height: 80vh;
    overflow-y: auto;
    background-color: #FFFFFF;
    border-radius: 20px 20px 0 0;
    padding: 20px 16px;
    padding-bottom: calc(20px + env(safe-area-inset-bottom));
  }

  &__title {
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
    text-align: center;
    margin-bottom: 16px;
  }

  &__field {
    margin-bottom: 16px;
  }

  &__label {
    display: block;
    font-size: 13px;
    color: $text-secondary;
    margin-bottom: 8px;
  }

  &__required {
    color: $color-danger;
  }

  &__input {
    width: 100%;
    height: 40px;
    padding: 0 16px;
    background-color: $bg-sunken;
    border-radius: 10px;
    font-size: 14px;
    color: $text-primary;
    box-sizing: border-box;
  }

  &__textarea {
    width: 100%;
    min-height: 80px;
    padding: 12px 16px;
    background-color: $bg-sunken;
    border-radius: 10px;
    font-size: 14px;
    color: $text-primary;
    box-sizing: border-box;

    &--sm {
      min-height: 60px;
    }
  }

  &__placeholder {
    color: $text-tertiary;
  }

  &__btns {
    display: flex;
    gap: 12px;
  }

  &__btn {
    flex: 1;
    height: 44px;
    line-height: 44px;
    text-align: center;
    border-radius: 10px;
    font-size: 14px;

    &--cancel {
      background-color: $bg-sunken;
      color: $text-secondary;
    }

    &--submit {
      background-color: $color-primary;
      color: #FFFFFF;
      font-weight: 600;
    }

    &--disabled {
      opacity: 0.6;
    }
  }
}
</style>
