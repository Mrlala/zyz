<template>
  <view class="ach-page">
    <!-- 顶部栏 -->
    <view class="top-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="top-bar__inner">
        <view class="top-bar__btn" @click="handleBack">
          <ArrowLeft :size="20" color="#6B7280" />
        </view>
        <text class="top-bar__title">成就</text>
        <view class="top-bar__placeholder"></view>
      </view>
    </view>
    <view class="top-bar-placeholder" :style="{ height: (statusBarHeight + 54) + 'px' }"></view>

    <view class="ach-body">
      <!-- 用户成就概览卡片 -->
      <view class="overview-card">
        <view class="overview-card__top">
          <!-- 等级 -->
          <view class="overview-card__level">
            <view class="overview-card__level-circle">
              <Crown :size="22" color="#FFFFFF" />
            </view>
            <view class="overview-card__level-info">
              <text class="overview-card__level-label">Lv.{{ level }}</text>
              <text class="overview-card__level-sub">{{ levelTitle }}</text>
            </view>
          </view>
          <!-- 已解锁计数 -->
          <view class="overview-card__count">
            <view class="overview-card__count-numRow">
              <text class="overview-card__count-num">{{ unlockedCount }}</text>
              <text class="overview-card__count-split">/{{ totalCount }}</text>
            </view>
            <text class="overview-card__count-label">已解锁成就</text>
          </view>
        </view>

        <!-- 经验进度条 -->
        <view class="overview-card__exp">
          <view class="overview-card__exp-bar">
            <view class="overview-card__exp-fill" :style="{ width: expPercent + '%' }"></view>
          </view>
          <view class="overview-card__exp-meta">
            <text class="overview-card__exp-cur">{{ currentLevelExp }}/{{ levelThreshold }} EXP</text>
            <text class="overview-card__exp-next">距下一级 {{ needNextLevel }} EXP</text>
          </view>
        </view>
      </view>

      <!-- Tab 切换 -->
      <view class="tab-filters">
        <view
          v-for="tab in tabs"
          :key="tab.value"
          class="tab-filters__tab"
          :class="{ 'tab-filters__tab--active': activeTab === tab.value }"
          @click="activeTab = tab.value"
        >{{ tab.label }}</view>
      </view>

      <!-- 加载中 -->
      <view v-if="loading" class="state-tip">
        <text>加载中...</text>
      </view>

      <template v-else>
        <!-- 成就卡片列表 -->
        <view v-if="displayList.length" class="ach-list">
          <view
            v-for="item in displayList"
            :key="item.id"
            class="ach-card"
            :class="{ 'ach-card--locked': item._locked }"
          >
            <!-- 左侧图标 -->
            <view class="ach-card__icon" :style="{ backgroundColor: item._iconBg }">
              <component :is="item._comp" :size="22" :color="item._iconColor" />
            </view>
            <!-- 右侧信息 -->
            <view class="ach-card__info">
              <view class="ach-card__head">
                <text class="ach-card__name">{{ item.name }}</text>
                <!-- 状态标签 -->
                <view
                  v-if="item._state === 'unlocked'"
                  class="ach-card__tag ach-card__tag--done"
                >
                  <text>已解锁</text>
                </view>
                <view
                  v-else-if="item._state === 'in_progress'"
                  class="ach-card__tag ach-card__tag--progress"
                >
                  <text>进行中</text>
                </view>
                <view v-else class="ach-card__tag ach-card__tag--locked">
                  <text>未解锁</text>
                </view>
              </view>

              <text v-if="item.description" class="ach-card__desc">{{ item.description }}</text>

              <!-- 已解锁：经验奖励 -->
              <text
                v-if="item._state === 'unlocked' && item.exp_reward"
                class="ach-card__reward"
              >+{{ item.exp_reward }} EXP</text>

              <!-- 进行中：进度条 -->
              <view
                v-if="item._state === 'in_progress' && item.target"
                class="ach-card__progress"
              >
                <view class="ach-card__progress-bar">
                  <view
                    class="ach-card__progress-fill"
                    :style="{ width: item._progressPercent + '%' }"
                  ></view>
                </view>
                <text class="ach-card__progress-text">{{ item.current || 0 }}/{{ item.target }}</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 空状态 -->
        <view v-else class="empty-state">
          <view class="empty-state__icon">
            <Trophy :size="32" color="#9CA3AF" />
          </view>
          <text class="empty-state__text">{{ emptyText }}</text>
        </view>
      </template>

      <!-- 成就排行榜（Top5） -->
      <view v-if="ranking.length" class="ranking-card">
        <view class="ranking-card__head">
          <Trophy :size="16" color="#FE2C55" />
          <text class="ranking-card__title">成就排行榜</text>
        </view>
        <view
          v-for="(r, idx) in ranking"
          :key="r.user_id || idx"
          class="ranking-card__row"
          :class="{ 'ranking-card__row--border': idx < ranking.length - 1 }"
        >
          <text
            class="ranking-card__rank"
            :class="{
              'ranking-card__rank--1': idx === 0,
              'ranking-card__rank--2': idx === 1,
              'ranking-card__rank--3': idx === 2
            }"
          >{{ idx + 1 }}</text>
          <text class="ranking-card__name">{{ r.nickname || '匿名用户' }}</text>
          <view class="ranking-card__right">
            <text class="ranking-card__count">{{ r.achievement_count || 0 }}成就</text>
            <text class="ranking-card__exp">{{ r.exp || 0 }} EXP</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import {
  ArrowLeft,
  Trophy,
  Award,
  Star,
  Zap,
  Target,
  Flame,
  Crown,
  Medal
} from 'lucide-vue-next'
import { getAchievements, getMyAchievements, getRanking } from '@/api/achievement'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()

const statusBarHeight = ref(0)
const loading = ref(true)
const activeTab = ref('unlocked')

// 全部成就（含描述、分类、经验奖励）
const allAchievements = ref([])
// 我的已解锁成就
const unlocked = ref([])
// 我的进行中成就
const inProgress = ref([])
// 成就排行榜
const ranking = ref([])

// Tab 配置
const tabs = [
  { label: '已解锁', value: 'unlocked' },
  { label: '进行中', value: 'in_progress' },
  { label: '全部', value: 'all' }
]

// 每级所需经验
const levelThreshold = 500

/* ============ 图标与颜色映射 ============ */
// 按成就类型分配不同图标与配色，已解锁用彩色，进行中/未解锁用灰色
const ICON_MAP = {
  zap:    { comp: Zap,    bg: 'rgba(16,185,129,0.12)',  color: '#10B981' }, // 学习 → 成功绿
  flame:  { comp: Flame,  bg: 'rgba(239,68,68,0.12)',   color: '#EF4444' }, // 连续 → 危险红
  star:   { comp: Star,   bg: 'rgba(245,158,11,0.12)',  color: '#F59E0B' }, // 收藏 → 警告金
  target: { comp: Target, bg: 'rgba(254,44,85,0.10)',   color: '#FE2C55' }, // 审核 → 主色红
  award:  { comp: Award,  bg: 'rgba(37,244,238,0.14)',  color: '#0EA5B7' }, // 贡献 → 青色
  crown:  { comp: Crown,  bg: 'rgba(245,158,11,0.12)',  color: '#F59E0B' }, // 等级 → 金色
  medal:  { comp: Medal,  bg: 'rgba(37,244,238,0.14)',  color: '#0EA5B7' }, // 徽章 → 青色
  trophy: { comp: Trophy, bg: 'rgba(254,44,85,0.10)',   color: '#FE2C55' }  // 默认 → 主色红
}

// 灰色样式（进行中 / 未解锁）
const LOCKED_STYLE = { bg: 'rgba(156,163,175,0.12)', color: '#9CA3AF' }

// 根据成就名称/分类/icon 选择图标 key
function pickIconKey(ach) {
  const key = `${ach.name || ''} ${ach.category || ''} ${ach.icon || ''}`.toLowerCase()
  if (/学习|learn|课程/.test(key)) return 'zap'
  if (/连续|streak|打卡|签到/.test(key)) return 'flame'
  if (/收藏|favorite|collect/.test(key)) return 'star'
  if (/审核|review/.test(key)) return 'target'
  if (/贡献|contribute|提交|submit/.test(key)) return 'award'
  if (/等级|level|王者|大师|crown/.test(key)) return 'crown'
  if (/徽章|badge|medal/.test(key)) return 'medal'
  return 'trophy'
}

// 装饰单个成就项：补充图标组件、配色、进度百分比、状态
function decorate(item, state) {
  const key = pickIconKey(item)
  const base = ICON_MAP[key]
  const locked = state !== 'unlocked'
  const style = locked ? LOCKED_STYLE : { bg: base.bg, color: base.color }
  return {
    ...item,
    _state: state,
    _locked: locked,
    _comp: base.comp,
    _iconBg: style.bg,
    _iconColor: style.color,
    _progressPercent: item.target
      ? Math.min(100, Math.round(((item.current || 0) / item.target) * 100))
      : 0
  }
}

/* ============ 数据合并 ============ */
// 全部成就详情映射（id → item），用于补全已解锁/进行中缺失的描述等字段
const detailMap = computed(() => {
  const m = new Map()
  allAchievements.value.forEach((a) => m.set(String(a.id), a))
  return m
})

// 已解锁 id 集合
const unlockedIds = computed(() => new Set(unlocked.value.map((a) => String(a.id))))

// 进行中映射（id → item）
const progressMap = computed(() => {
  const m = new Map()
  inProgress.value.forEach((a) => m.set(String(a.id), a))
  return m
})

// 已解锁列表（合并描述/分类）
const unlockedList = computed(() =>
  unlocked.value.map((a) => {
    const detail = detailMap.value.get(String(a.id)) || {}
    return decorate({ ...detail, ...a }, 'unlocked')
  })
)

// 进行中列表（合并描述/分类）
const inProgressList = computed(() =>
  inProgress.value.map((a) => {
    const detail = detailMap.value.get(String(a.id)) || {}
    return decorate({ ...detail, ...a }, 'in_progress')
  })
)

// 全部列表：按全部成就顺序，标注每个成就的状态
const allList = computed(() =>
  allAchievements.value.map((a) => {
    const id = String(a.id)
    if (unlockedIds.value.has(id)) {
      const u = unlocked.value.find((x) => String(x.id) === id) || {}
      return decorate({ ...a, ...u }, 'unlocked')
    }
    const p = progressMap.value.get(id)
    if (p) return decorate({ ...a, ...p }, 'in_progress')
    // 未开始
    return decorate({ ...a }, 'locked')
  })
)

// 当前 Tab 展示列表
const displayList = computed(() => {
  if (activeTab.value === 'unlocked') return unlockedList.value
  if (activeTab.value === 'in_progress') return inProgressList.value
  return allList.value
})

const emptyText = computed(() => {
  if (activeTab.value === 'unlocked') return '还没有解锁任何成就'
  if (activeTab.value === 'in_progress') return '暂无进行中的成就'
  return '暂无成就数据'
})

/* ============ 概览统计 ============ */
const unlockedCount = computed(() => unlocked.value.length)
const totalCount = computed(() => allAchievements.value.length)

// 总经验：累加已解锁成就的奖励经验
const totalExp = computed(() =>
  unlocked.value.reduce((sum, a) => sum + (a.exp_reward || 0), 0)
)

const level = computed(() => Math.floor(totalExp.value / levelThreshold) + 1)
const currentLevelExp = computed(() => totalExp.value % levelThreshold)
const expPercent = computed(() =>
  Math.round((currentLevelExp.value / levelThreshold) * 100)
)
const needNextLevel = computed(() => levelThreshold - currentLevelExp.value)

// 等级称号
const levelTitle = computed(() => {
  const lv = level.value
  if (lv >= 10) return '成就大师'
  if (lv >= 6) return '成就达人'
  if (lv >= 3) return '成就先锋'
  return '成就新秀'
})

/* ============ 生命周期 ============ */
onLoad(() => {
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
  fetchData()
})

// 拉取成就数据：全部成就始终拉取；登录用户额外拉取我的成就与排行榜
async function fetchData() {
  loading.value = true
  try {
    const tasks = [getAchievements()]
    // /achievements/mine 需登录，未登录跳过避免 401 弹窗
    if (userStore.isLoggedIn) {
      tasks.push(getMyAchievements())
    }
    // 排行榜无需登录
    tasks.push(getRanking({ limit: 5 }).catch(() => []))

    const results = await Promise.all(tasks)
    allAchievements.value = results[0] || []

    if (results.length >= 2 && userStore.isLoggedIn) {
      const mine = results[1] || {}
      unlocked.value = mine.unlocked || []
      inProgress.value = mine.in_progress || []
      // 排行榜在最后一位
      ranking.value = Array.isArray(results[2]) ? results[2] : []
    } else {
      // 未登录：排行榜在第二位
      ranking.value = Array.isArray(results[1]) ? results[1] : []
    }
  } catch (err) {
    console.error('获取成就数据失败', err)
  } finally {
    loading.value = false
  }
}

function handleBack() {
  uni.navigateBack({ delta: 1 })
}
</script>

<style lang="scss" scoped>
.ach-page {
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

  &__placeholder {
    width: 32px;
  }
}

.top-bar-placeholder {
  width: 100%;
}

/* ============ 主体 ============ */
.ach-body {
  padding: 12px 16px 32px;
}

/* ============ 概览卡片 ============ */
.overview-card {
  padding: 16px;
  border-radius: 12px;
  background-color: $bg-card;
  box-shadow: $shadow-xs;

  &__top {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  &__level {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  &__level-circle {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: $gradient-primary;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  &__level-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  &__level-label {
    font-size: 16px;
    font-weight: 700;
    color: $text-primary;
    line-height: 1.2;
  }

  &__level-sub {
    font-size: 11px;
    color: $text-tertiary;
  }

  &__count {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 2px;
  }

  &__count-numRow {
    display: flex;
    align-items: baseline;
  }

  &__count-num {
    font-size: 22px;
    font-weight: 700;
    color: $color-primary;
    line-height: 1.1;
  }

  &__count-split {
    margin-left: 2px;
    font-size: 13px;
    color: $text-tertiary;
  }

  &__count-label {
    font-size: 11px;
    color: $text-tertiary;
  }

  /* 经验进度条 */
  &__exp {
    margin-top: 14px;
  }

  &__exp-bar {
    height: 6px;
    border-radius: 3px;
    background-color: $bg-sunken;
    overflow: hidden;
  }

  &__exp-fill {
    height: 100%;
    border-radius: 3px;
    background: $gradient-primary;
    transition: width 0.3s ease;
  }

  &__exp-meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 6px;
  }

  &__exp-cur {
    font-size: 11px;
    font-weight: 500;
    color: $text-secondary;
  }

  &__exp-next {
    font-size: 11px;
    color: $text-tertiary;
  }
}

/* ============ Tab 切换 ============ */
.tab-filters {
  display: flex;
  gap: 24px;
  margin-top: 20px;
  border-bottom: 1px solid $border-color-light;

  &__tab {
    padding-bottom: 12px;
    font-size: 14px;
    color: $text-tertiary;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;

    &--active {
      color: $text-primary;
      font-weight: 600;
      border-bottom-color: $color-primary;
    }
  }
}

/* ============ 成就卡片列表 ============ */
.ach-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ach-card {
  display: flex;
  align-items: flex-start;
  padding: 14px;
  border-radius: 12px;
  background-color: $bg-card;
  box-shadow: $shadow-xs;

  &--locked {
    opacity: 0.92;
  }

  &__icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  &__info {
    flex: 1;
    min-width: 0;
    padding-left: 12px;
  }

  &__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  &__name {
    flex: 1;
    min-width: 0;
    font-size: 15px;
    font-weight: 600;
    color: $text-primary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* 状态标签 */
  &__tag {
    flex-shrink: 0;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 11px;

    &--done {
      background-color: rgba(16, 185, 129, 0.12);
      color: $color-success;
    }

    &--progress {
      background-color: rgba(254, 44, 85, 0.10);
      color: $color-primary;
    }

    &--locked {
      background-color: $bg-sunken;
      color: $text-tertiary;
    }
  }

  &__desc {
    display: block;
    margin-top: 4px;
    font-size: 13px;
    color: $text-secondary;
    line-height: 1.5;
  }

  &__reward {
    display: block;
    margin-top: 6px;
    font-size: 11px;
    font-weight: 500;
    color: $color-success;
  }

  /* 进行中进度条 */
  &__progress {
    margin-top: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  &__progress-bar {
    flex: 1;
    height: 5px;
    border-radius: 3px;
    background-color: $bg-sunken;
    overflow: hidden;
  }

  &__progress-fill {
    height: 100%;
    border-radius: 3px;
    background-color: $color-primary;
    transition: width 0.3s ease;
  }

  &__progress-text {
    flex-shrink: 0;
    font-size: 11px;
    color: $text-tertiary;
  }
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
  padding: 64px 0 40px;

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
  }
}

/* ============ 成就排行榜 ============ */
.ranking-card {
  margin-top: 20px;
  padding: 14px 16px;
  border-radius: 12px;
  background-color: $bg-card;
  box-shadow: $shadow-xs;

  &__head {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 8px;
  }

  &__title {
    font-size: 14px;
    font-weight: 600;
    color: $text-primary;
  }

  &__row {
    display: flex;
    align-items: center;
    height: 44px;

    &--border {
      border-bottom: 1px solid $border-color-light;
    }
  }

  &__rank {
    width: 24px;
    flex-shrink: 0;
    font-size: 14px;
    font-weight: 600;
    color: $text-tertiary;
    text-align: center;

    &--1 {
      color: $color-warning;
    }

    &--2 {
      color: $text-secondary;
    }

    &--3 {
      color: $color-warning;
    }
  }

  &__name {
    flex: 1;
    min-width: 0;
    margin-left: 8px;
    font-size: 14px;
    color: $text-primary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__right {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  &__count {
    font-size: 12px;
    color: $text-tertiary;
  }

  &__exp {
    font-size: 12px;
    font-weight: 600;
    color: $color-primary;
  }
}
</style>
