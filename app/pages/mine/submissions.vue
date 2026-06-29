<template>
  <view class="page submissions-page">
    <!-- 顶部自定义导航栏 -->
    <view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="nav-bar__inner">
        <view class="nav-bar__back" @click="handleBack">‹</view>
        <text class="nav-bar__title">我的提交</text>
        <view class="nav-bar__add" @click="openSubmit">＋</view>
      </view>
    </view>
    <view class="nav-placeholder" :style="{ height: (statusBarHeight + 44) + 'px' }"></view>

    <view class="submissions-page__body">
      <!-- 状态筛选 -->
      <view class="submissions-page__tabs">
        <view
          v-for="tab in statusTabs"
          :key="tab.value"
          class="submissions-page__tab"
          :class="{ 'submissions-page__tab--active': status === tab.value }"
          @click="switchStatus(tab.value)"
        >{{ tab.label }}</view>
      </view>

      <!-- 列表 -->
      <view class="submissions-page__list">
        <view v-if="loading" class="submissions-page__loading">
          <view class="submissions-page__loading-icon">⏳</view>
          <text class="submissions-page__loading-text">加载中...</text>
        </view>

        <template v-else>
          <view
            v-for="item in list"
            :key="item.submission_id || item.id"
            class="submissions-page__item card"
          >
            <view class="submissions-page__item-header">
              <text class="submissions-page__item-word">{{ item.word }}</text>
              <text
                class="submissions-page__item-status"
                :class="`submissions-page__item-status--${item.status}`"
              >{{ statusText(item.status) }}</text>
            </view>
            <view class="submissions-page__item-definition">{{ item.definition }}</view>
            <view v-if="item.example" class="submissions-page__item-example">
              示例：{{ item.example }}
            </view>
            <view class="submissions-page__item-time">
              提交于 {{ formatTime(item.submitted_at) }}
            </view>
            <view v-if="item.reject_reason" class="submissions-page__item-reason">
              驳回原因：{{ item.reject_reason }}
            </view>
          </view>

          <EmptyState
            v-if="!list.length"
            icon="📨"
            text="还没有提交记录"
            btn-text="提交新词条"
            @btnClick="openSubmit"
          />

          <LoadMore
            v-if="list.length > 0"
            :status="loadMoreStatus"
            @loadMore="loadMore"
          />
        </template>
      </view>
    </view>

    <!-- 提交新词条弹层 -->
    <view v-if="submitVisible" class="submit" @click="closeSubmit">
      <view class="submit__mask"></view>
      <view class="submit__panel" @click.stop>
        <view class="submit__title">提交新词条</view>
        <view class="submit__field">
          <text class="submit__label">词条 <text class="submit__required">*</text></text>
          <input
            class="submit__input"
            v-model="form.word"
            placeholder="如：yyds"
            placeholder-class="submit__placeholder"
            :maxlength="20"
          />
        </view>
        <view class="submit__field">
          <text class="submit__label">释义 <text class="submit__required">*</text></text>
          <textarea
            class="submit__textarea"
            v-model="form.definition"
            placeholder="用一句话解释这个词的意思"
            placeholder-class="submit__placeholder"
            :maxlength="200"
          />
        </view>
        <view class="submit__field">
          <text class="submit__label">示例</text>
          <textarea
            class="submit__textarea submit__textarea--sm"
            v-model="form.example"
            placeholder="造个句子（可选）"
            placeholder-class="submit__placeholder"
            :maxlength="100"
          />
        </view>
        <view class="submit__btns">
          <view class="submit__btn submit__btn--cancel" @click="closeSubmit">取消</view>
          <view
            class="submit__btn submit__btn--submit"
            :class="{ 'btn-disabled': submitting }"
            @click="handleSubmit"
          >{{ submitting ? '提交中...' : '提交' }}</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { onLoad, onReachBottom, onPullDownRefresh } from '@dcloudio/uni-app'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadMore from '@/components/common/LoadMore.vue'
import * as submissionApi from '@/api/submission'

const statusBarHeight = ref(0)
const status = ref('')
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

// 状态筛选标签
const statusTabs = [
  { label: '全部', value: '' },
  { label: '待审核', value: 'pending' },
  { label: '已通过', value: 'approved' },
  { label: '已驳回', value: 'rejected' }
]

const loadMoreStatus = computed(() => {
  if (loading.value) return 'loading'
  if (list.value.length >= total.value && list.value.length > 0) return 'noMore'
  return 'more'
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
    if (status.value) params.status = status.value
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

// 切换状态筛选
function switchStatus(value) {
  if (status.value === value) return
  status.value = value
  fetchList(true)
}

// 状态文案
function statusText(s) {
  const map = { pending: '待审核', approved: '已通过', rejected: '已驳回' }
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
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${m}-${day}`
}
</script>

<style lang="scss" scoped>
.submissions-page {
  min-height: 100vh;
  background-color: $uni-bg-color;

  .nav-bar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
    background-color: #FFFFFF;
    box-shadow: $uni-box-shadow;

    &__inner {
      height: 88rpx;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 $uni-spacing-row-base;
    }

    &__back {
      width: 56rpx;
      height: 56rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 56rpx;
      color: $uni-text-color;
      line-height: 1;
    }

    &__title {
      font-size: $uni-font-size-lg;
      font-weight: 600;
      color: $uni-text-color;
    }

    &__add {
      width: 56rpx;
      height: 56rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: $uni-font-size-title;
      color: $uni-color-primary;
    }
  }

  &__body {
    padding: $uni-spacing-col-base $uni-spacing-row-base;
    padding-bottom: 60rpx;
  }

  // 状态筛选
  &__tabs {
    display: flex;
    background-color: #FFFFFF;
    border-radius: $uni-border-radius;
    padding: 6rpx;
    margin-bottom: $uni-spacing-col-base;
  }

  &__tab {
    flex: 1;
    text-align: center;
    padding: 14rpx 0;
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
    border-radius: $uni-border-radius;

    &--active {
      background-color: $uni-color-primary;
      color: #FFFFFF;
      font-weight: 600;
    }
  }

  &__list {
    padding-top: $uni-spacing-row-sm;
  }

  &__loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: $uni-spacing-col-xl 0;
  }

  &__loading-icon {
    font-size: 96rpx;
    margin-bottom: $uni-spacing-col-base;
  }

  &__loading-text {
    font-size: $uni-font-size-base;
    color: $uni-text-color-grey;
  }

  // 提交项
  &__item {
    margin-bottom: $uni-spacing-col-sm;
  }

  &__item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $uni-spacing-row-sm;
  }

  &__item-word {
    font-size: $uni-font-size-lg;
    font-weight: 600;
    color: $uni-text-color;
  }

  &__item-status {
    font-size: $uni-font-size-xs;
    padding: 4rpx $uni-spacing-row-sm;
    border-radius: 999rpx;

    &--pending {
      background-color: rgba(245, 158, 11, 0.12);
      color: $uni-color-warning;
    }

    &--approved {
      background-color: rgba(16, 185, 129, 0.12);
      color: $uni-color-success;
    }

    &--rejected {
      background-color: rgba(239, 68, 68, 0.12);
      color: $uni-color-error;
    }
  }

  &__item-definition {
    font-size: $uni-font-size-base;
    color: $uni-text-color;
    line-height: 1.6;
    margin-bottom: $uni-spacing-row-sm;
  }

  &__item-example {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
    line-height: 1.6;
    padding: $uni-spacing-row-sm $uni-spacing-row-base;
    background-color: $uni-bg-color;
    border-radius: $uni-border-radius;
    margin-bottom: $uni-spacing-row-sm;
  }

  &__item-time {
    font-size: $uni-font-size-xs;
    color: $uni-text-color-placeholder;
  }

  &__item-reason {
    margin-top: $uni-spacing-row-sm;
    padding: $uni-spacing-row-sm $uni-spacing-row-base;
    background-color: rgba(239, 68, 68, 0.06);
    border-radius: $uni-border-radius;
    font-size: $uni-font-size-sm;
    color: $uni-color-error;
    line-height: 1.6;
  }
}

// 提交弹层
.submit {
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
    border-radius: $uni-border-radius-lg $uni-border-radius-lg 0 0;
    padding: $uni-spacing-col-lg $uni-spacing-row-lg;
    padding-bottom: calc(#{$uni-spacing-col-lg} + env(safe-area-inset-bottom));
  }

  &__title {
    font-size: $uni-font-size-lg;
    font-weight: 600;
    color: $uni-text-color;
    text-align: center;
    margin-bottom: $uni-spacing-col-base;
  }

  &__field {
    margin-bottom: $uni-spacing-col-base;
  }

  &__label {
    display: block;
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
    margin-bottom: $uni-spacing-row-sm;
  }

  &__required {
    color: $uni-color-error;
  }

  &__input {
    width: 100%;
    height: 80rpx;
    padding: 0 $uni-spacing-row-base;
    background-color: $uni-bg-color;
    border-radius: $uni-border-radius;
    font-size: $uni-font-size-base;
    color: $uni-text-color;
    box-sizing: border-box;
  }

  &__textarea {
    width: 100%;
    min-height: 160rpx;
    padding: $uni-spacing-row-base;
    background-color: $uni-bg-color;
    border-radius: $uni-border-radius;
    font-size: $uni-font-size-base;
    color: $uni-text-color;
    box-sizing: border-box;

    &--sm {
      min-height: 100rpx;
    }
  }

  &__placeholder {
    color: $uni-text-color-placeholder;
  }

  &__btns {
    display: flex;
    gap: $uni-spacing-row-base;
  }

  &__btn {
    flex: 1;
    height: 80rpx;
    line-height: 80rpx;
    text-align: center;
    border-radius: $uni-border-radius;
    font-size: $uni-font-size-base;

    &--cancel {
      background-color: $uni-bg-color;
      color: $uni-text-color-grey;
    }

    &--submit {
      background-color: $uni-color-primary;
      color: #FFFFFF;
      font-weight: 600;
    }
  }
}
</style>
