<template>
  <view
    class="word-tag"
    :class="`word-tag--${type}`"
    @click="handleClick"
  >
    {{ text }}
  </view>
</template>

<script setup>
const props = defineProps({
  // 标签文字
  text: {
    type: String,
    default: ''
  },
  // 标签类型：category 分类 / risk 风险 / source 来源
  type: {
    type: String,
    default: 'category',
    validator: (v) => ['category', 'risk', 'source'].includes(v)
  }
})

const emit = defineEmits(['click'])

function handleClick() {
  emit('click', props.text)
}
</script>

<style lang="scss" scoped>
.word-tag {
  display: inline-flex;
  align-items: center;
  padding: 4rpx $uni-spacing-row-sm;
  border-radius: 999rpx;
  font-size: $uni-font-size-sm;
  line-height: 1.4;

  // 分类标签：品牌色
  &--category {
    background-color: rgba(79, 70, 229, 0.1);
    color: $uni-color-primary;
  }

  // 风险标签：中性灰，具体颜色由 RiskBadge 承担
  &--risk {
    background-color: rgba(107, 114, 128, 0.1);
    color: $uni-text-color-grey;
  }

  // 来源标签：成功色
  &--source {
    background-color: rgba(16, 185, 129, 0.1);
    color: $uni-color-success;
  }
}
</style>
