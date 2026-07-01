<template>
  <view class="empty-state">
    <view class="empty-state__icon">
      <component :is="icon" :size="32" color="#9CA3AF" />
    </view>
    <text class="empty-state__text">{{ text }}</text>
    <text v-if="sub" class="empty-state__sub">{{ sub }}</text>
    <view v-if="actionText" class="empty-state__btn" @click="handleAction">
      <text class="empty-state__btn-text">{{ actionText }}</text>
    </view>
  </view>
</template>

<script setup>
const props = defineProps({
  // lucide 图标组件
  icon: {
    type: [Object, Function],
    default: null
  },
  // 主文案
  text: {
    type: String,
    default: ''
  },
  // 副文案
  sub: {
    type: String,
    default: ''
  },
  // 操作按钮文案
  actionText: {
    type: String,
    default: ''
  },
  // 操作跳转路径
  actionUrl: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['action'])

function handleAction() {
  emit('action')
  if (props.actionUrl) {
    uni.navigateTo({ url: props.actionUrl })
  }
}
</script>

<style lang="scss" scoped>
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

    &:active {
      opacity: 0.85;
    }
  }

  &__btn-text {
    font-size: 13px;
    font-weight: 500;
    color: #FFFFFF;
  }
}
</style>
