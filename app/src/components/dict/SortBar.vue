<template>
  <view class="sort-bar">
    <view class="sort-bar__tabs">
      <view
        v-for="item in options"
        :key="item.value"
        class="sort-bar__tab"
        :class="{ 'sort-bar__tab--active': modelValue === item.value }"
        @click="handleClick(item.value)"
      >{{ item.label }}</view>
    </view>
    <view v-if="$slots.extra" class="sort-bar__extra">
      <slot name="extra" />
    </view>
  </view>
</template>

<script setup>
const props = defineProps({
  // 排序选项 [{label, value}]
  options: {
    type: Array,
    default: () => []
  },
  // 当前选中值
  modelValue: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue'])

function handleClick(value) {
  if (value === props.modelValue) return
  emit('update:modelValue', value)
}
</script>

<style lang="scss" scoped>
.sort-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  border-bottom: 1px solid $border-color-light;

  &__tabs {
    display: flex;
    gap: 16px;
  }

  &__tab {
    font-size: 13px;
    color: $text-secondary;
    padding-bottom: 2px;
    border-bottom: 2px solid transparent;

    &--active {
      color: $text-primary;
      font-weight: 600;
      border-bottom-color: $color-primary;
    }
  }

  &__extra {
    display: flex;
    align-items: center;
  }
}
</style>
