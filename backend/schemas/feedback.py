"""反馈相关请求/响应模型

对应 SDD 4.5.9 反馈接口。
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    """质量反馈请求。

    :param translation_id: 关联的翻译记录 ID
    :param type: 反馈类型 accurate/inaccurate/outdated
    :param comment: 补充说明，最长 500 字
    """

    translation_id: int = Field(..., description="关联的翻译记录 ID")
    type: str = Field(..., description="反馈类型：accurate/inaccurate/outdated")
    comment: str | None = Field(None, max_length=500, description="补充说明")


class FeedbackResponse(BaseModel):
    """反馈响应数据。"""

    success: bool = True
    message: str = "反馈成功"
    feedback_id: int = 0
