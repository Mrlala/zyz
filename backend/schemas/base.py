"""统一响应格式

所有接口响应均采用 BaseResponse 包装，对应 SDD 4.5.1 统一响应格式。
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class BaseResponse(BaseModel):
    """统一响应结构。

    :param code: 业务状态码，200 表示成功
    :param message: 状态描述信息
    :param data: 业务数据，错误时为 None
    """

    code: int = 200
    message: str = "success"
    data: Any = None
