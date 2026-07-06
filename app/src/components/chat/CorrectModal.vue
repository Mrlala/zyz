<template>
  <view v-if="showMask" class="correct-modal" @click="handleClose">
    <view class="correct-modal__mask"></view>
    <view class="correct-modal__dialog" @click.stop>
      <!-- 标题 -->
      <view class="correct-modal__header">
        <view class="correct-modal__title-wrap">
          <AlertCircle :size="16" color="#FE2C55" />
          <text class="correct-modal__title">{{ title }}</text>
        </view>
        <view class="correct-modal__close" @click="handleClose">
          <X :size="16" color="#9CA3AF" />
        </view>
      </view>

      <!-- 副标题（可选） -->
      <view v-if="subtitle" class="correct-modal__subtitle">{{ subtitle }}</view>

      <!-- 类型选择（可选） -->
      <view v-if="options && options.length" class="correct-modal__options">
        <view
          v-for="opt in options"
          :key="opt.value"
          class="correct-modal__option"
          :class="{ 'correct-modal__option--active': selectedType === opt.value }"
          @click="selectedType = opt.value"
        >
          <text>{{ opt.label }}</text>
        </view>
      </view>

      <!-- 原始内容预览（可选） -->
      <view v-if="originalContent" class="correct-modal__original">
        <text class="correct-modal__original-label">原始内容</text>
        <text class="correct-modal__original-body">{{ originalContent }}</text>
      </view>

      <!-- 文本输入 -->
      <view class="correct-modal__input-wrap">
        <textarea
          class="correct-modal__textarea"
          v-model="inputContent"
          :placeholder="placeholder"
          placeholder-class="correct-modal__placeholder"
          :maxlength="500"
          :auto-height="true"
          :adjust-position="false"
        />
        <text class="correct-modal__counter">{{ inputContent.length }}/500</text>
      </view>

      <!-- 操作按钮 -->
      <view class="correct-modal__actions">
        <view class="correct-modal__btn correct-modal__btn--ghost" @click="handleClose">
          <text>取消</text>
        </view>
        <view
          class="correct-modal__btn correct-modal__btn--primary"
          :class="{ 'correct-modal__btn--disabled': !canConfirm }"
          @click="handleConfirm"
        >
          <text>提交纠错</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { AlertCircle, X } from 'lucide-vue-next'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '纠错' },
  subtitle: { type: String, default: '' },
  placeholder: { type: String, default: '请描述问题或给出正确内容' },
  options: { type: Array, default: () => [] }, // [{label, value}]
  originalContent: { type: String, default: '' }
})

const emit = defineEmits(['update:open', 'confirm'])

const showMask = ref(false)
const inputContent = ref('')
const selectedType = ref('')

const canConfirm = computed(() => {
  if (!inputContent.value.trim()) return false
  if (props.options && props.options.length && !selectedType.value) return false
  return true
})

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      showMask.value = true
      inputContent.value = ''
      selectedType.value = props.options && props.options.length ? props.options[0].value : ''
    } else {
      setTimeout(() => {
        showMask.value = false
      }, 200)
    }
  }
)

function handleClose() {
  emit('update:open', false)
}

function handleConfirm() {
  if (!canConfirm.value) return
  emit('confirm', {
    content: inputContent.value.trim(),
    type: selectedType.value || ''
  })
  emit('update:open', false)
}
</script>

<style lang="scss" scoped>
.correct-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 32px;

  &__mask {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
  }

  &__dialog {
    position: relative;
    width: 100%;
    max-width: 340px;
    background-color: $bg-card;
    border-radius: 16px;
    padding: 18px 16px 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
    animation: correctModalIn 0.2s ease;
  }

  @keyframes correctModalIn {
    from {
      opacity: 0;
      transform: scale(0.92) translateY(-8px);
    }
    to {
      opacity: 1;
      transform: scale(1) translateY(0);
    }
  }

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 6px;
  }

  &__title-wrap {
    display: flex;
    align-items: center;
    gap: 6px;
    flex: 1;
    min-width: 0;
  }

  &__title {
    font-size: 15px;
    font-weight: 600;
    color: $text-primary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__close {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;

    &:active {
      background-color: $bg-sunken;
    }
  }

  &__subtitle {
    font-size: 12px;
    color: $text-tertiary;
    margin-bottom: 12px;
    line-height: 1.5;
  }

  &__options {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 14px;
  }

  &__option {
    padding: 6px 12px;
    border-radius: 16px;
    background-color: $bg-sunken;
    font-size: 12px;
    color: $text-secondary;
    border: 1px solid transparent;
    transition: all 0.15s ease;

    &--active {
      background-color: rgba(254, 44, 85, 0.08);
      color: $color-primary;
      border-color: rgba(254, 44, 85, 0.3);
    }
  }

  &__original {
    background-color: $bg-sunken;
    border-radius: 10px;
    padding: 10px 12px;
    margin-bottom: 12px;
  }

  &__original-label {
    display: block;
    font-size: 11px;
    color: $text-tertiary;
    margin-bottom: 4px;
  }

  &__original-body {
    display: block;
    font-size: 13px;
    color: $text-secondary;
    line-height: 1.5;
  }

  &__input-wrap {
    position: relative;
    background-color: $bg-sunken;
    border-radius: 10px;
    padding: 10px 12px 24px;
    margin-bottom: 14px;
  }

  &__textarea {
    width: 100%;
    min-height: 80px;
    font-size: 14px;
    color: $text-primary;
    line-height: 1.6;
    background-color: transparent;
  }

  &__placeholder {
    color: $text-tertiary;
    font-size: 14px;
  }

  &__counter {
    position: absolute;
    right: 12px;
    bottom: 6px;
    font-size: 11px;
    color: $text-tertiary;
  }

  &__actions {
    display: flex;
    gap: 10px;
  }

  &__btn {
    flex: 1;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 500;
    transition: opacity 0.15s ease;

    &:active {
      opacity: 0.7;
    }

    &--ghost {
      background-color: $bg-sunken;
      color: $text-secondary;
    }

    &--primary {
      background-color: $color-primary;
      color: #FFFFFF;
    }

    &--disabled {
      opacity: 0.4;
      pointer-events: none;
    }
  }
}
</style>
