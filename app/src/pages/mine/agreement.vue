<template>
  <view class="agreement-page">
    <!-- 顶部栏 -->
    <view class="top-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="top-bar__inner">
        <view class="top-bar__btn" @click="handleBack">
          <ArrowLeft :size="20" color="#6B7280" />
        </view>
        <text class="top-bar__title">{{ pageTitle }}</text>
        <view class="top-bar__placeholder"></view>
      </view>
    </view>
    <view class="top-bar-placeholder" :style="{ height: (statusBarHeight + 54) + 'px' }"></view>

    <!-- 协议正文 -->
    <scroll-view scroll-y class="agreement-body">
      <view class="agreement-meta">
        <text class="agreement-meta__text">更新日期：{{ updateDate }}</text>
      </view>
      <view v-for="(sec, idx) in sections" :key="idx" class="agreement-section">
        <text class="agreement-section__title">{{ idx + 1 }}. {{ sec.title }}</text>
        <text class="agreement-section__content">{{ sec.content }}</text>
      </view>
      <view class="agreement-footer">
        <text class="agreement-footer__text">— 中译中团队 —</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { ArrowLeft } from 'lucide-vue-next'

const statusBarHeight = ref(0)
const type = ref('privacy') // privacy | terms

const pageTitle = computed(() => type.value === 'terms' ? '用户协议' : '隐私政策')
const updateDate = '2026-07-01'

// 隐私政策内容
const privacySections = [
  {
    title: '信息收集',
    content: '我们在您使用「中译中」时可能收集以下信息：账号信息（用户名、加密密码）、用户资料（昵称、头像）、翻译与查询记录、收藏与提交内容、设备标识与使用日志。我们不收集您的真实姓名、手机号、身份证等敏感身份信息。'
  },
  {
    title: '信息使用',
    content: '收集的信息仅用于：提供翻译与词典服务、改善产品体验、生成个性化内容推荐、统计热门词条与排行、保障账号与系统安全。我们不会将您的个人信息出售或交易给任何第三方。'
  },
  {
    title: '信息存储与保护',
    content: '您的数据存储于国内服务器，采用加密传输与密码哈希存储。我们采取合理的技术与管理措施保护您的信息安全，但请注意，互联网传输不存在绝对安全的方式。'
  },
  {
    title: 'AI 翻译服务',
    content: '当词条未命中本地词库时，我们将调用 DeepSeek 等大模型进行实时翻译。您输入的文本会作为 prompt 发送至模型服务方以生成翻译结果，请勿输入涉及个人隐私或商业机密的内容。'
  },
  {
    title: '用户内容',
    content: '您提交的释义、纠错、反馈等内容，您享有所有权并授权我们在服务范围内使用、展示、修改。我们有权对违规内容进行下架处理。'
  },
  {
    title: '信息删除',
    content: '您可在「设置-清除缓存」中清除本地缓存。如需注销账号或删除服务器数据，请通过反馈渠道联系管理员，我们将在 7 个工作日内处理。'
  },
  {
    title: '未成年人保护',
    content: '本应用面向一般大众，若您是未成年人，请在监护人指导下使用，并避免提交任何个人隐私信息。'
  },
  {
    title: '政策更新',
    content: '本政策可能随产品迭代更新，更新后将在应用内提示。继续使用即视为您同意更新后的政策。'
  }
]

// 用户协议内容
const termsSections = [
  {
    title: '服务说明',
    content: '「中译中」是一款面向中文语境的语义翻译工具，提供词条翻译、词库浏览、热词排行、内容提交等功能。我们尽力保证服务可用性，但不对服务的连续性、准确性作绝对保证。'
  },
  {
    title: '账号注册与使用',
    content: '您需使用账号密码注册登录。请妥善保管账号密码，因账号泄露造成的损失由您自行承担。禁止注册多个账号进行刷榜、恶意投票等行为。'
  },
  {
    title: '用户行为规范',
    content: '您承诺不利用本服务从事以下行为：发布违法、色情、暴力、骚扰、侵权内容；提交虚假、误导性释义；恶意刷票、刷热度；攻击、破坏系统；未经授权爬取数据。违反者我们将下架内容、封禁账号，必要时追究法律责任。'
  },
  {
    title: '内容审核',
    content: '用户提交的释义、纠错等内容需经审核后方可发布。我们有权根据社区准则决定是否发布，且无需另行通知。'
  },
  {
    title: '知识产权',
    content: '本应用的界面、代码、词条库、设计等知识产权归本团队所有。未经授权禁止复制、改编、商用。用户提交的内容版权归原作者所有，但授权本应用在服务范围内使用。'
  },
  {
    title: '免责声明',
    content: 'AI 翻译结果由大模型生成，可能存在不准确或不当之处，仅供参考，不构成专业建议。因使用本服务产生的任何直接或间接损失，本团队不承担责任。'
  },
  {
    title: '服务变更与终止',
    content: '我们保留随时变更、暂停、终止部分或全部服务的权利。您可随时停止使用并注销账号。账号长期未登录，我们有权予以回收。'
  },
  {
    title: '争议解决',
    content: '本协议适用中华人民共和国法律。因本协议或使用本服务产生的争议，双方应友好协商解决；协商不成的，提交本团队所在地有管辖权的人民法院诉讼解决。'
  }
]

const sections = computed(() => type.value === 'terms' ? termsSections : privacySections)

onLoad((options) => {
  if (options && options.type === 'terms') {
    type.value = 'terms'
  } else {
    type.value = 'privacy'
  }
  try {
    const sysInfo = uni.getSystemInfoSync()
    statusBarHeight.value = sysInfo.statusBarHeight || 0
  } catch (e) {
    statusBarHeight.value = 0
  }
})

function handleBack() {
  uni.navigateBack({ delta: 1 })
}
</script>

<style lang="scss" scoped>
.agreement-page {
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

/* ============ 正文 ============ */
.agreement-body {
  height: calc(100vh - 54px);
  padding: 0 20px 32px;
  box-sizing: border-box;
}

.agreement-meta {
  padding: 16px 0 8px;

  &__text {
    font-size: 12px;
    color: $text-tertiary;
  }
}

.agreement-section {
  margin-top: 20px;

  &__title {
    display: block;
    font-size: 15px;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: 8px;
  }

  &__content {
    display: block;
    font-size: 13px;
    line-height: 1.7;
    color: $text-regular;
  }
}

.agreement-footer {
  margin-top: 32px;
  text-align: center;

  &__text {
    font-size: 12px;
    color: $text-tertiary;
  }
}
</style>
