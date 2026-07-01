<template>
  <view class="ranking-page">
    <!-- 顶部栏 -->
    <view class="top-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="top-bar__inner">
        <view class="top-bar__btn" @click="handleBack">
          <ArrowLeft :size="20" color="#6B7280" />
        </view>
        <text class="top-bar__title">热词排行</text>
        <view class="top-bar__btn" @click="handleFilter">
          <SlidersHorizontal :size="18" color="#6B7280" />
        </view>
      </view>
    </view>
    <view class="top-bar-placeholder" :style="{ height: (statusBarHeight + 54) + 'px' }"></view>

    <!-- 今日热词 -->
    <view class="daily">
      <view class="daily__header">
        <view class="daily__title-wrap">
          <Flame :size="16" color="#FE2C55" />
          <text class="daily__title">今日热词</text>
        </view>
        <text v-if="dailyDateText" class="daily__date">{{ dailyDateText }}</text>
      </view>

      <view v-if="dailyLoading" class="daily__tip">
        <text>加载中...</text>
      </view>
      <view v-else-if="!dailyList.length" class="daily__tip">
        <text>暂无今日热词</text>
      </view>
      <scroll-view v-else scroll-x class="daily__scroll" :show-scrollbar="false">
        <view class="daily__cards">
          <view
            v-for="(item, idx) in dailyList"
            :key="item.id || item.word_id || idx"
            class="daily-card"
            @click="handleItemClick(item)"
          >
            <view class="daily-card__head">
              <text class="daily-card__word">{{ item.word || item.name }}</text>
              <text v-if="item.pinyin" class="daily-card__pinyin">{{ item.pinyin }}</text>
            </view>
            <text class="daily-card__def">{{ item.definition || item.summary || item.desc || '——' }}</text>
            <view class="daily-card__hot">
              <Flame :size="11" color="#FE2C55" />
              <text class="daily-card__hot-text">{{ formatCount(item) }}</text>
            </view>
          </view>
        </view>
      </scroll-view>
    </view>

    <!-- 时段标签 -->
    <view class="period-tabs">
      <view
        v-for="tab in periods"
        :key="tab.value"
        class="period-tabs__tab"
        :class="{ 'period-tabs__tab--active': period === tab.value }"
        @click="switchPeriod(tab.value)"
      >{{ tab.label }}</view>
    </view>

    <!-- 加载中 -->
    <view v-if="loading" class="state-tip">
      <text>加载中...</text>
    </view>

    <template v-else>
      <!-- 空状态 -->
      <view v-if="!list.length" class="state-tip state-tip--empty">
        <text>暂无排行数据</text>
      </view>

      <template v-else>
        <!-- TOP3 领奖台 -->
        <view v-if="top3.length" class="podium">
          <!-- 2nd -->
          <view v-if="top3[1]" class="podium__item podium__item--2nd" @click="handleItemClick(top3[1])">
            <view class="podium__circle podium__circle--2nd">
              <text class="podium__circle-text">2</text>
            </view>
            <text class="podium__word podium__word--2nd">{{ top3[1].word || top3[1].name }}</text>
            <view
              class="podium__vote"
              :class="{ 'podium__vote--active': isVoted(top3[1]) }"
              @click.stop="handleVote(top3[1])"
            >
              <ThumbsUp :size="11" :color="isVoted(top3[1]) ? '#FE2C55' : '#9CA3AF'" />
              <text class="podium__vote-text">{{ formatCount(top3[1]) }}</text>
            </view>
          </view>

          <!-- 1st -->
          <view v-if="top3[0]" class="podium__item podium__item--1st" @click="handleItemClick(top3[0])">
            <view class="podium__circle podium__circle--1st">
              <text class="podium__circle-text">1</text>
            </view>
            <text class="podium__word podium__word--1st">{{ top3[0].word || top3[0].name }}</text>
            <view
              class="podium__vote"
              :class="{ 'podium__vote--active': isVoted(top3[0]) }"
              @click.stop="handleVote(top3[0])"
            >
              <ThumbsUp :size="11" :color="isVoted(top3[0]) ? '#FE2C55' : '#9CA3AF'" />
              <text class="podium__vote-text">{{ formatCount(top3[0]) }}</text>
            </view>
          </view>

          <!-- 3rd -->
          <view v-if="top3[2]" class="podium__item podium__item--3rd" @click="handleItemClick(top3[2])">
            <view class="podium__circle podium__circle--3rd">
              <text class="podium__circle-text">3</text>
            </view>
            <text class="podium__word podium__word--3rd">{{ top3[2].word || top3[2].name }}</text>
            <view
              class="podium__vote"
              :class="{ 'podium__vote--active': isVoted(top3[2]) }"
              @click.stop="handleVote(top3[2])"
            >
              <ThumbsUp :size="11" :color="isVoted(top3[2]) ? '#FE2C55' : '#9CA3AF'" />
              <text class="podium__vote-text">{{ formatCount(top3[2]) }}</text>
            </view>
          </view>
        </view>

        <!-- #4+ 列表 -->
        <view v-if="rest.length" class="rest-list">
          <view
            v-for="(item, idx) in rest"
            :key="item.id || idx"
            class="rest-list__row"
            :class="{ 'rest-list__row--border': idx < rest.length - 1 }"
            @click="handleItemClick(item)"
          >
            <text class="rest-list__rank">{{ idx + 4 }}</text>
            <text class="rest-list__word">{{ item.word || item.name }}</text>
            <view
              class="rest-list__vote"
              :class="{ 'rest-list__vote--active': isVoted(item) }"
              @click.stop="handleVote(item)"
            >
              <ThumbsUp :size="13" :color="isVoted(item) ? '#FE2C55' : '#9CA3AF'" />
              <text class="rest-list__vote-count">{{ formatCount(item) }}</text>
            </view>
          </view>
        </view>
      </template>
    </template>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { ArrowLeft, SlidersHorizontal, ThumbsUp, Flame } from 'lucide-vue-next'
import * as hotApi from '@/api/hot'

const statusBarHeight = ref(0)
const period = ref('daily')
const list = ref([])
const loading = ref(true)
// 排序方式：default(后端返回顺序) | hotness(热度降序) | votes(投票数降序)
const sortBy = ref('default')

// 每日热词
const dailyList = ref([])
const dailyDate = ref('')
const dailyLoading = ref(true)

// 投票状态：已投票词条 id 集合（响应式，驱动按钮变色）
const votedIds = ref(new Set())
// 投票请求进行中的 id（非响应式，仅做防重复点击）
const votingIds = new Set()

// 时段标签（文案对齐：daily→今日, weekly→本周, monthly→本月）
const periods = [
  { label: '今日', value: 'daily' },
  { label: '本周', value: 'weekly' },
  { label: '本月', value: 'monthly' }
]

// TOP3 与剩余列表（按当前排序方式重排）
const sortedList = computed(() => {
  const arr = [...list.value]
  if (sortBy.value === 'hotness') {
    arr.sort((a, b) => (b.hotness || b.hot_score || 0) - (a.hotness || a.hot_score || 0))
  } else if (sortBy.value === 'votes') {
    arr.sort((a, b) => (b.vote_count || 0) - (a.vote_count || 0))
  }
  return arr
})
const top3 = computed(() => sortedList.value.slice(0, 3))
const rest = computed(() => sortedList.value.slice(3))

// 今日热词日期文案：2026-07-01 → 7月1日
const dailyDateText = computed(() => {
  if (!dailyDate.value) return ''
  const m = dailyDate.value.match(/(\d{4})-(\d{1,2})-(\d{1,2})/)
  if (m) return `${parseInt(m[2], 10)}月${parseInt(m[3], 10)}日`
  return dailyDate.value
})

onLoad(() => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
  fetchDaily()
  fetchRanking()
})

// 获取每日热词
async function fetchDaily() {
  dailyLoading.value = true
  try {
    const data = await hotApi.getDaily()
    dailyList.value = (data && data.list) || []
    dailyDate.value = (data && data.date) || ''
  } catch (err) {
    console.error('获取每日热词失败', err)
    dailyList.value = []
  } finally {
    dailyLoading.value = false
  }
}

// 获取排行榜
async function fetchRanking() {
  loading.value = true
  try {
    const data = await hotApi.getRanking({ period: period.value, limit: 50 })
    list.value = (data && data.list) || []
  } catch (err) {
    console.error('获取排行榜失败', err)
    list.value = []
  } finally {
    loading.value = false
  }
}

function switchPeriod(value) {
  if (period.value === value) return
  period.value = value
  fetchRanking()
}

// 格式化热度次数
function formatCount(item) {
  const count = item.hotness || item.hot_score || item.vote_count || 0
  if (count >= 10000) {
    return (count / 10000).toFixed(1) + '万次'
  }
  return count.toLocaleString() + '次'
}

// 点击词条进入详情
function handleItemClick(word) {
  const id = word.id || word.word_id
  if (id) {
    uni.navigateTo({ url: `/pages/word-detail/index?id=${id}` })
  }
}

// 是否已投票（本地标记或后端返回的 has_voted）
function isVoted(item) {
  const id = item.id || item.word_id
  if (!id) return false
  return votedIds.value.has(id) || !!item.has_voted
}

// 投票
async function handleVote(item) {
  const id = item.id || item.word_id
  if (!id) return
  // 防止重复点击
  if (votingIds.has(id)) return
  votingIds.add(id)
  try {
    // 静默调用，错误提示由本函数统一控制
    await hotApi.vote(id, 'upvote', { silent: true })
    votedIds.value.add(id)
    incrementHotness(item)
    uni.showToast({ title: '投票成功', icon: 'success' })
  } catch (err) {
    const status = err && err.statusCode
    if (status === 401) {
      uni.showToast({ title: '请先登录', icon: 'none' })
    } else if (status === 409) {
      // 重复投票：标记为已投，避免再次请求
      votedIds.value.add(id)
      uni.showToast({ title: '已投过票', icon: 'none' })
    } else {
      uni.showToast({ title: (err && err.message) || '投票失败', icon: 'none' })
    }
  } finally {
    votingIds.delete(id)
  }
}

// 投票成功后热度 +1（兼容多种字段命名）
function incrementHotness(item) {
  if (typeof item.hotness === 'number') {
    item.hotness += 1
  } else if (typeof item.hot_score === 'number') {
    item.hot_score += 1
  } else if (typeof item.vote_count === 'number') {
    item.vote_count += 1
  } else {
    item.hotness = (item.hotness || 0) + 1
  }
}

// 筛选：选择排序方式（前端重排，无需后端请求）
const sortOptions = [
  { key: 'default', label: '默认排序' },
  { key: 'hotness', label: '按热度排序' },
  { key: 'votes', label: '按投票数排序' }
]

function handleFilter() {
  uni.showActionSheet({
    itemList: sortOptions.map(o => o.label),
    success: (res) => {
      const selected = sortOptions[res.tapIndex]
      if (selected && sortBy.value !== selected.key) {
        sortBy.value = selected.key
        uni.showToast({ title: '已切换：' + selected.label, icon: 'none' })
      }
    }
  })
}

function handleBack() {
  uni.navigateBack({ delta: 1 })
}
</script>

<style lang="scss" scoped>
.ranking-page {
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

/* ============ 今日热词 ============ */
.daily {
  margin: 8px 0 4px;

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 16px;
    margin-bottom: 10px;
  }

  &__title-wrap {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  &__title {
    font-size: 16px;
    font-weight: 700;
    color: $text-primary;
  }

  &__date {
    font-size: 12px;
    color: $text-tertiary;
  }

  &__tip {
    padding: 24px 0;
    text-align: center;
    font-size: 13px;
    color: $text-tertiary;
  }

  &__scroll {
    width: 100%;
    white-space: nowrap;
  }

  &__cards {
    display: inline-flex;
    gap: 10px;
    padding: 0 16px 6px;
  }
}

.daily-card {
  flex-shrink: 0;
  width: 140px;
  padding: 12px;
  border-radius: 12px;
  background-color: $bg-card;
  box-shadow: $shadow-sm;
  box-sizing: border-box;

  &__head {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  &__word {
    font-size: 16px;
    font-weight: 700;
    color: $text-primary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__pinyin {
    font-size: 11px;
    color: $text-tertiary;
  }

  &__def {
    margin-top: 8px;
    font-size: 12px;
    line-height: 1.5;
    color: $text-secondary;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    height: 36px;
  }

  &__hot {
    margin-top: 10px;
    display: flex;
    align-items: center;
    gap: 3px;
  }

  &__hot-text {
    font-size: 11px;
    font-weight: 600;
    color: $color-primary;
  }
}

/* ============ 时段标签 ============ */
.period-tabs {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  padding: 4px 0 16px;

  &__tab {
    padding-bottom: 8px;
    font-size: 14px;
    font-weight: 500;
    color: $text-tertiary;
    border-bottom: 2px solid transparent;

    &--active {
      color: $text-primary;
      border-bottom-color: $color-primary;
    }
  }
}

/* ============ 状态提示 ============ */
.state-tip {
  padding: 64px 0;
  text-align: center;
  font-size: 14px;
  color: $text-secondary;

  &--empty {
    color: $text-tertiary;
  }
}

/* ============ TOP3 领奖台 ============ */
.podium {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 12px;
  margin: 0 16px;
  padding: 20px;
  border-radius: 16px;
  background-color: $bg-card;
  box-shadow: $shadow-sm;

  &__item {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 80px;

    &--2nd { padding-top: 16px; }
    &--1st { padding-top: 0; }
    &--3rd { padding-top: 24px; }
  }

  &__circle {
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    color: #FFFFFF;

    &--1st {
      width: 48px;
      height: 48px;
      background-color: $color-primary;
    }
    &--2nd {
      width: 40px;
      height: 40px;
      background-color: $text-secondary;
    }
    &--3rd {
      width: 40px;
      height: 40px;
      background-color: $text-tertiary;
    }
  }

  &__circle-text {
    font-size: 16px;
    font-weight: 700;
  }

  &__word {
    margin-top: 8px;
    text-align: center;
    width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;

    &--1st {
      font-size: 16px;
      font-weight: 700;
      color: $text-primary;
    }
    &--2nd {
      font-size: 14px;
      font-weight: 500;
      color: $text-primary;
    }
    &--3rd {
      font-size: 13px;
      font-weight: 500;
      color: $text-primary;
    }
  }

  &__vote {
    margin-top: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 3px;
    padding: 3px 8px;
    border-radius: 10px;
    background-color: $bg-sunken;

    &-text {
      font-size: 11px;
      font-weight: 600;
      color: $text-tertiary;
    }

    &--active {
      background-color: rgba(254, 44, 85, 0.1);

      .podium__vote-text {
        color: $color-primary;
      }
    }
  }
}

/* ============ #4+ 列表 ============ */
.rest-list {
  margin: 12px 16px 32px;
  border-radius: 12px;
  overflow: hidden;
  background-color: $bg-card;
  box-shadow: $shadow-sm;

  &__row {
    display: flex;
    align-items: center;
    height: 52px;
    padding: 0 16px;

    &--border {
      border-bottom: 1px solid $border-color-light;
    }
  }

  &__rank {
    width: 28px;
    flex-shrink: 0;
    font-size: 14px;
    font-weight: 600;
    color: $text-tertiary;
  }

  &__word {
    flex: 1;
    min-width: 0;
    margin-left: 4px;
    font-size: 14px;
    font-weight: 500;
    color: $text-primary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__vote {
    flex-shrink: 0;
    margin-left: 8px;
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border-radius: 12px;
    background-color: $bg-sunken;

    &-count {
      font-size: 12px;
      font-weight: 600;
      color: $text-tertiary;
    }

    &--active {
      background-color: rgba(254, 44, 85, 0.1);

      .rest-list__vote-count {
        color: $color-primary;
      }
    }
  }
}
</style>
