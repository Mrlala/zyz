<template>
  <view class="empty-state">
    <view class="empty-state__icon">{{ displayIcon }}</view>
    <view class="empty-state__text">{{ text }}</view>
    <view
      v-if="btnText"
      class="empty-state__btn"
      @click="handleBtnClick"
    >
      {{ btnText }}
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // 提示文字
  text: {
    type: String,
    default: '暂无内容'
  },
  // 图标，默认空盒子 emoji
  icon: {
    type: String,
    default: '📦'
  },
  // 操作按钮文字，为空则不显示
  btnText: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['btnClick'])

// 默认图标兜底
const displayIcon = computed(() => props.icon || '📦')

function handleBtnClick() {
  emit('btnClick')
}
</script>

<style lang="scss" scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $uni-spacing-col-lg $uni-spacing-row-lg;

  &__icon {
    font-size: 96rpx;
    line-height: 1;
    margin-bottom: $uni-spacing-col-base;
    opacity: 0.7;
  }

  &__text {
    font-size: $uni-font-size-base;
    color: $uni-text-color-grey;
    text-align: center;
    line-height: 1.6;
  }

  &__btn {
    margin-top: $uni-spacing-col-lg;
    padding: 0 $uni-spacing-row-lg;
    height: 72rpx;
    line-height: 72rpx;
    border-radius: $uni-border-radius;
    background-color: $uni-color-primary;
    color: #FFFFFF;
    font-size: $uni-font-size-base;
  }
}
</style>
