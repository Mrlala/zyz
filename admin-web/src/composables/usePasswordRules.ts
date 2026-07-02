import type { FormRules } from 'element-plus'

/** 密码强度校验：至少 8 位，需包含数字和字母 */
function passwordValidator(_r: any, value: string, cb: (err?: Error) => void) {
  if (value && !(/\d/.test(value) && /[a-zA-Z]/.test(value))) {
    cb(new Error('需包含数字和字母'))
  } else {
    cb()
  }
}

/**
 * 密码规则 composable
 * 提供密码字段规则和确认密码规则（消除多处重复）
 */
export function usePasswordRules() {
  /** 密码字段规则（required + min8 + 数字字母） */
  const passwordRules = [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '至少 8 位', trigger: 'blur' },
    { validator: passwordValidator, trigger: 'blur' },
  ]

  /** 新密码字段规则（用于改密场景，message 为"请输入新密码"） */
  const newPasswordRules = [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '至少 8 位', trigger: 'blur' },
    { validator: passwordValidator, trigger: 'blur' },
  ]

  /**
   * 确认密码规则
   * @param getNewPassword 获取新密码的函数（用于动态比较）
   */
  function confirmRules(getNewPassword: () => string) {
    return [
      { required: true, message: '请确认密码', trigger: 'blur' },
      {
        validator: (_r: any, value: string, cb: (err?: Error) => void) => {
          if (value !== getNewPassword()) cb(new Error('两次密码不一致'))
          else cb()
        },
        trigger: 'blur',
      },
    ]
  }

  return { passwordRules, newPasswordRules, confirmRules, passwordValidator }
}
