<template>
  <view class="page detail-page">
    <!-- 顶部自定义导航栏（含返回按钮） -->
    <view class="nav-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="nav-bar__inner">
        <view class="nav-bar__back" @click="handleBack">‹</view>
        <text class="nav-bar__title">词条详情</text>
        <view class="nav-bar__share" @click="handleShare">↗</view>
      </view>
    </view>
    <view class="nav-placeholder" :style="{ height: (statusBarHeight + 44) + 'px' }"></view>

    <scroll-view scroll-y class="detail-page__body" :style="{ height: 'calc(100vh - ' + (statusBarHeight + 44) + 'px)' }">
      <!-- 加载中 -->
      <view v-if="loading" class="detail-page__loading">
        <view class="detail-page__loading-icon">⏳</view>
        <text class="detail-page__loading-text">加载中...</text>
      </view>

      <template v-else-if="word">
        <view class="detail-page__content card">
          <WordDetail :word="word" @relatedClick="handleRelatedClick" />
        </view>

        <!-- 互动数据 -->
        <view class="detail-page__meta card">
          <view class="detail-page__meta-item">
            <text class="detail-page__meta-icon">🔥</text>
            <text>{{ word.hotness || word.hot_score || 0 }} 热度</text>
          </view>
          <view class="detail-page__meta-item">
            <text class="detail-page__meta-icon">⭐</text>
            <text>{{ word.favorite_count || 0 }} 收藏</text>
          </view>
        </view>
      </template>

      <!-- 空状态 -->
      <EmptyState v-else icon="🔍" text="词条不存在或已下架" btn-text="返回" @btnClick="handleBack" />

      <view class="detail-page__bottom-space"></view>
    </scroll-view>

    <!-- 底部操作栏 -->
    <view v-if="word" class="detail-page__footer">
      <view
        class="detail-page__footer-btn"
        :class="{ 'detail-page__footer-btn--active': isFavorited }"
        @click="handleFavorite"
      >
        <text class="detail-page__footer-icon">{{ isFavorited ? '★' : '☆' }}</text>
        <text>{{ isFavorited ? '已收藏' : '收藏' }}</text>
      </view>
      <view class="detail-page__footer-btn" @click="openCorrection">
        <text class="detail-page__footer-icon">✏️</text>
        <text>纠错</text>
      </view>
    </view>

    <!-- 纠错弹层 -->
    <view v-if="correctionVisible" class="correction" @click="closeCorrection">
      <view class="correction__mask"></view>
      <view class="correction__panel" @click.stop>
        <view class="correction__title">提交纠错</view>
        <view class="correction__sub">选择纠错类型</view>
        <view class="correction__types">
          <view
            v-for="t in correctionTypes"
            :key="t.value"
            class="correction__type"
            :class="{ 'correction__type--active': correctionType === t.value }"
            @click="correctionType = t.value"
          >{{ t.label }}</view>
        </view>
        <view class="correction__sub">补充说明</view>
        <textarea
          class="correction__textarea"
          v-model="correctionContent"
          placeholder="请描述具体问题（可选）"
          placeholder-class="correction__placeholder"
          :maxlength="200"
        />
        <view class="correction__btns">
          <view class="correction__btn correction__btn--cancel" @click="closeCorrection">取消</view>
          <view
            class="correction__btn correction__btn--submit"
            :class="{ 'btn-disabled': submitting }"
            @click="submitCorrection"
          >{{ submitting ? '提交中...' : '提交' }}</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import WordDetail from '@/components/word/WordDetail.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import * as wordApi from '@/api/word'
import * as correctionApi from '@/api/correction'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()

const statusBarHeight = ref(0)
// 词条 ID
const wordId = ref(null)
// 词条详情
const word = ref(null)
// 加载中
const loading = ref(true)
// 是否已收藏
const isFavorited = ref(false)

// 纠错弹层
const correctionVisible = ref(false)
const correctionType = ref('meaning_wrong')
const correctionContent = ref('')
const submitting = ref(false)

// 纠错类型选项
const correctionTypes = [
  { label: '释义错误', value: 'meaning_wrong' },
  { label: '示例不当', value: 'example_wrong' },
  { label: '词条过时', value: 'outdated' },
  { label: '其他问题', value: 'other' }
]

onLoad((options) => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
  wordId.value = Number(options && options.id)
  if (wordId.value) {
    fetchDetail()
  } else {
    loading.value = false
  }
})

// 获取词条详情
async function fetchDetail() {
  loading.value = true
  try {
    const data = await wordApi.getWordDetail(wordId.value)
    word.value = data
    isFavorited.value = !!(data && (data.is_favorited || data.favorited))
  } catch (err) {
    console.error('获取词条详情失败', err)
    word.value = null
  } finally {
    loading.value = false
  }
}

// 返回
function handleBack() {
  uni.navigateBack({ delta: 1 })
}

// 分享
function handleShare() {
  if (!word.value) return
  uni.setClipboardData({
    data: word.value.word || '',
    success: () => {
      uni.showToast({ title: '词条已复制', icon: 'success' })
    }
  })
}

// 收藏/取消收藏
async function handleFavorite() {
  if (!wordId.value) return
  try {
    await userStore.toggleFavorite(wordId.value)
    isFavorited.value = userStore.isFavorited(wordId.value)
    // 更新收藏数
    if (word.value) {
      word.value.favorite_count = (word.value.favorite_count || 0) + (isFavorited.value ? 1 : -1)
    }
    uni.showToast({
      title: isFavorited.value ? '已收藏' : '已取消收藏',
      icon: 'none'
    })
  } catch (err) {
    console.error('收藏操作失败', err)
  }
}

// 点击相关词条，跳转其详情
function handleRelatedClick(item) {
  const id = item.id || item.word_id
  if (id) {
    uni.redirectTo({ url: `/pages/word-detail/index?id=${id}` })
  }
}

// 打开纠错弹层
function openCorrection() {
  correctionType.value = 'meaning_wrong'
  correctionContent.value = ''
  correctionVisible.value = true
}

// 关闭纠错弹层
function closeCorrection() {
  correctionVisible.value = false
}

// 提交纠错
async function submitCorrection() {
  if (submitting.value) return
  submitting.value = true
  try {
    await correctionApi.submitCorrection({
      word_id: wordId.value,
      type: correctionType.value,
      content: correctionContent.value
    })
    uni.showToast({ title: '纠错已提交，感谢反馈', icon: 'success' })
    closeCorrection()
  } catch (err) {
    console.error('提交纠错失败', err)
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
.detail-page {
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

    &__share {
      width: 56rpx;
      height: 56rpx;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: $uni-font-size-lg;
      color: $uni-text-color;
    }
  }

  &__body {
    box-sizing: border-box;
    padding: $uni-spacing-col-base $uni-spacing-row-base;
    padding-bottom: 160rpx;
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

  &__content {
    margin-bottom: $uni-spacing-col-base;
  }

  &__meta {
    display: flex;
    justify-content: space-around;
  }

  &__meta-item {
    display: flex;
    align-items: center;
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
  }

  &__meta-icon {
    margin-right: $uni-spacing-row-sm;
  }

  &__bottom-space {
    height: 40rpx;
  }

  // 底部操作栏
  &__footer {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    background-color: #FFFFFF;
    box-shadow: 0 -2rpx 12rpx rgba(0, 0, 0, 0.06);
    padding: $uni-spacing-col-sm 0;
    padding-bottom: calc(#{$uni-spacing-col-sm} + env(safe-area-inset-bottom));
    z-index: 50;
  }

  &__footer-btn {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: $uni-spacing-row-sm 0;
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;

    &--active {
      color: $uni-color-warning;
    }

    &:active {
      opacity: 0.6;
    }
  }

  &__footer-icon {
    font-size: 44rpx;
    margin-bottom: 4rpx;
  }
}

// 纠错弹层
.correction {
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

  &__sub {
    font-size: $uni-font-size-sm;
    color: $uni-text-color-grey;
    margin-bottom: $uni-spacing-row-sm;
  }

  &__types {
    display: flex;
    flex-wrap: wrap;
    gap: $uni-spacing-row-sm;
    margin-bottom: $uni-spacing-col-base;
  }

  &__type {
    padding: 12rpx $uni-spacing-row-base;
    background-color: $uni-bg-color;
    border-radius: 999rpx;
    font-size: $uni-font-size-sm;
    color: $uni-text-color;
    border: 2rpx solid transparent;

    &--active {
      background-color: rgba(79, 70, 229, 0.1);
      color: $uni-color-primary;
      border-color: $uni-color-primary;
    }
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
    margin-bottom: $uni-spacing-col-base;
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
