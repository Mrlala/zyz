/**
 * 配置查询接口
 * 对应后端：backend/api/v1/config.py
 * - GET /config/ai-status 检测 AI 服务状态
 */
import { get } from './request'

/**
 * 检测 AI 服务配置状态
 * @returns {Promise<{available: boolean, model: string, mode: string}>}
 */
export function getAiStatus() {
  return get('/config/ai-status', {}, { silent: true })
}

export default {
  getAiStatus
}
