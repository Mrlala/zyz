<template>
  <view class="detail-page">
    <!-- 顶部栏 -->
    <view class="top-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="top-bar__inner">
        <view class="top-bar__btn" @click="handleBack">
          <ArrowLeft :size="20" color="#6B7280" />
        </view>
        <text class="top-bar__title">词条详情</text>
        <view class="top-bar__btn" @click="handleShare">
          <Share2 :size="20" color="#6B7280" />
        </view>
      </view>
    </view>
    <view class="top-bar-placeholder" :style="{ height: (statusBarHeight + 54) + 'px' }"></view>

    <scroll-view scroll-y class="detail-page__body" :style="{ height: 'calc(100vh - ' + (statusBarHeight + 54) + 'px)' }">
      <!-- 加载中 -->
      <view v-if="loading" class="state-tip">
        <text>加载中...</text>
      </view>

      <template v-else-if="word">
        <view class="detail-card">
          <WordDetail :word="word" @relatedClick="handleRelatedClick" />
        </view>

        <!-- 互动数据 -->
        <view class="meta-card">
          <view class="meta-card__item">
            <Flame :size="14" color="#F59E0B" />
            <text>{{ word.hotness || word.hot_score || 0 }} 热度</text>
          </view>
          <view class="meta-card__item">
            <Star :size="14" color="#F59E0B" :fill="'#F59E0B'" />
            <text>{{ word.favorite_count || 0 }} 收藏</text>
          </view>
        </view>
      </template>

      <!-- 空状态 -->
      <view v-else class="empty-state">
        <view class="empty-state__icon">
          <Search :size="32" color="#9CA3AF" />
        </view>
        <text class="empty-state__text">词条不存在或已下架</text>
        <view class="empty-state__btn" @click="handleBack">
          <text class="empty-state__btn-text">返回</text>
        </view>
      </view>

      <view class="detail-page__bottom-space"></view>
    </scroll-view>

    <!-- 底部操作栏 -->
    <view v-if="word" class="detail-page__footer">
      <view
        class="detail-page__footer-btn"
        :class="{ 'detail-page__footer-btn--active': isFavorited }"
        @click="handleFavorite"
      >
        <Heart
          :size="20"
          :color="isFavorited ? '#FE2C55' : '#9CA3AF'"
          :fill="isFavorited ? '#FE2C55' : 'none'"
        />
        <text>{{ isFavorited ? '已收藏' : '收藏' }}</text>
      </view>
      <view class="detail-page__footer-btn" @click="openCorrection">
        <Pencil :size="20" color="#6B7280" />
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
            :class="{ 'correction__btn--disabled': submitting }"
            @click="submitCorrection"
          >{{ submitting ? '提交中...' : '提交' }}</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { ArrowLeft, Share2, Flame, Star, Heart, Pencil, Search } from 'lucide-vue-next'
import WordDetail from '@/components/word/WordDetail.vue'
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
  { label: '例句/出处错误', value: 'example_wrong' },
  { label: '拼音错误', value: 'pinyin_wrong' },
  { label: '分类错误', value: 'category_wrong' },
  { label: '风险标注错误', value: 'risk_wrong' },
  { label: '已过时', value: 'outdated' },
  { label: '其他', value: 'other' }
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

// 复制词条（H5 无原生分享，提供复制功能）
function handleShare() {
  if (!word.value) return
  uni.setClipboardData({
    data: word.value.word || '',
    success: () => {
      uni.showToast({ title: '词条已复制，可粘贴分享', icon: 'none' })
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
}

.top-bar-placeholder {
  width: 100%;
}

/* ============ 主体 ============ */
.detail-page__body {
  box-sizing: border-box;
  padding: 12px 16px;
  padding-bottom: 80px;
}

.detail-card {
  padding: 16px;
  background-color: $bg-card;
  border-radius: 12px;
  box-shadow: $shadow-sm;
  margin-bottom: 8px;
}

.meta-card {
  display: flex;
  justify-content: space-around;
  padding: 14px 16px;
  background-color: $bg-card;
  border-radius: 12px;
  box-shadow: $shadow-xs;

  &__item {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 13px;
    color: $text-secondary;
  }
}

.detail-page__bottom-space {
  height: 20px;
}

/* ============ 状态提示 ============ */
.state-tip {
  padding: 64px 0;
  text-align: center;
  font-size: 14px;
  color: $text-secondary;
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

/* ============ 底部操作栏 ============ */
.detail-page__footer {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  background-color: $bg-card;
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.06);
  padding: 8px 0;
  padding-bottom: calc(8px + env(safe-area-inset-bottom));
  z-index: 50;
}

.detail-page__footer-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: 8px 0;
  font-size: 13px;
  color: $text-secondary;

  &--active {
    color: $color-primary;
  }

  &:active {
    opacity: 0.6;
  }
}

/* ============ 纠错弹层 ============ */
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

  &__sub {
    font-size: 13px;
    color: $text-secondary;
    margin-bottom: 8px;
  }

  &__types {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 16px;
  }

  &__type {
    padding: 8px 16px;
    background-color: $bg-sunken;
    border-radius: 9999px;
    font-size: 13px;
    color: $text-primary;
    border: 1px solid transparent;

    &--active {
      background-color: rgba(254, 44, 85, 0.1);
      color: $color-primary;
      border-color: $color-primary;
    }
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
    margin-bottom: 16px;
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
