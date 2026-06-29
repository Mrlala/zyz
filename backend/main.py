"""FastAPI 应用入口

创建 app，配置 CORS 中间件，注册路由。
包含健康检查接口与全部业务 API（挂载于 /api 前缀下）。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1 import api_router

app = FastAPI(
    title="黑话翻译 API",
    description="黑话翻译系统后端服务",
    version="1.0.0",
)

# CORS 中间件：允许跨域访问（开发阶段全放开，生产环境应限制来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册业务路由（SDD 4.5 全部 33 个接口）
app.include_router(api_router, prefix="/api")


@app.get("/", tags=["系统"])
def root():
    """根路径，返回服务简介与文档地址。"""
    return {"message": "黑话翻译 API 服务", "docs": "/docs"}


@app.get("/health", tags=["系统"])
def health_check():
    """健康检查接口。"""
    return {"status": "ok", "service": "黑话翻译 API"}
