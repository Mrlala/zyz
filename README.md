# 中译中

> 一款 AI 驱动的网络流行语翻译词典，让「黑话」不再难懂。

中译中是一个面向中文网络流行语的实时翻译工具，支持词条释义、多语境解析、风险提示、词条纠错、AI 实时生成释义等功能。用户可浏览词库、提交新词、收藏与纠错，管理员可通过后台管理词条、审核提交、监控 AI 状态。

## 功能亮点

### 用户端（App H5）
- **智能翻译**：输入网络流行语，AI 实时生成「人话翻译」+ 多语境释义
- **词库命中**：词库已有的词条直接返回，无需调用 AI，响应更快
- **词条详情**：右侧抽屉展示释义、出处、示例、演化历程、相关场景、使用频率
- **AI 词条提交**：AI 临时生成的词条可一键提交到词库审核队列
- **section 级纠错**：释义/出处/示例/拼音/分类/风险均可独立纠错
- **收藏与历史**：收藏喜欢的词条，支持会话历史记录
- **热词榜单**：TOP3 领奖台 + 趋势箭头，掌握流行风向
- **个人中心**：登录注册、昵称头像设置、我的提交、成就系统

### 管理后台（Admin Web）
- **工作台**：核心数据看板（用户数、词条数、翻译量、AI 调用统计）
- **词库管理**：词条 CRUD、批量导入导出、Excel 模板、风险标记
- **内容审核**：用户提交审核 + 纠错审核双 Tab
- **AI 候选词**：AI 临时生成的高频词自动进入候选队列
- **账号与权限**：RBAC 角色权限管理
- **AI 配置**：Prompt 模板管理、模型切换、监控面板

### 后端 API
- **FastAPI + SQLAlchemy**：高性能异步框架，自动建表 + 轻量迁移
- **DeepSeek AI 集成**：OpenAI 兼容格式，支持模型切换与降级
- **JWT 认证**：Bearer Token + RBAC 权限校验
- **安全加固**：登录锁定、速率限制、敏感词过滤、CORS 控制

## 技术栈

| 层 | 技术 |
|---|---|
| App 前端 | uni-app + Vue 3 + Pinia + Tailwind CSS + lucide-vue-next |
| 管理后台 | Vue 3 + Element Plus + Vue Router + ECharts |
| 后端 API | FastAPI + SQLAlchemy + Pydantic + JWT |
| 数据库 | SQLite（开发）/ PostgreSQL（可选） |
| AI 服务 | DeepSeek（deepseek-v4-flash） |
| 部署 | Docker Compose / Nginx + systemd |

## 项目结构

```
trea_ai/
├── app/                    # App 前端（uni-app H5）
│   ├── src/
│   │   ├── pages/          # 页面（index/dict/word-detail/mine/auth...）
│   │   ├── components/     # 组件（chat/word/common...）
│   │   ├── api/            # 接口封装
│   │   ├── store/          # Pinia 状态管理
│   │   └── styles/         # 全局样式 + SCSS 变量
│   └── package.json
├── admin-web/              # 管理后台（Vue3 + Element Plus）
│   ├── src/
│   │   ├── views/          # 页面（dashboard/content/system/ai...）
│   │   ├── layouts/        # 布局
│   │   ├── router/         # 路由（hash 模式）
│   │   └── store/          # 状态管理
│   └── package.json
├── backend/                # 后端 API（FastAPI）
│   ├── api/v1/             # 路由（含 manage/ 子模块）
│   ├── core/               # 核心（database/security/middleware/rbac...）
│   ├── models/             # 数据模型
│   ├── schemas/            # Pydantic schema
│   ├── services/           # 业务服务（ai/translator/word...）
│   ├── data/               # 初始化脚本
│   ├── config.py
│   ├── main.py
│   └── requirements.txt
├── docker-compose.yml      # Docker 一体化部署
├── nginx.conf              # Nginx 配置
├── DEPLOY.md               # 部署指南
└── start.ps1               # Windows 本地开发启动脚本
```

## 快速开始

### 环境要求
- Node.js 18+
- Python 3.10+
- npm / pnpm

### 1. 后端启动

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# 编辑 .env，配置 DEEPSEEK_API_KEY（可选，无则降级为本地词库）

# 初始化数据库
python -c "from core.database import engine, Base; from models import *; Base.metadata.create_all(engine)"
python data/init_data.py
python data/init_admin_data.py
python data/init_word_extras.py

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/api/docs 查看 API 文档。

### 2. App 前端启动

```bash
cd app
npm install
npm run dev:h5
```

访问 http://localhost:5173

### 3. 管理后台启动

```bash
cd admin-web
npm install
npm run dev
```

访问 http://localhost:5176

### 一键启动（Windows）

```powershell
.\start.ps1
```

## 部署

详见 [DEPLOY.md](./DEPLOY.md)，支持：

- **Docker Compose**：一键部署前后端 + Nginx
- **裸机部署**：systemd + Nginx
- **HTTPS**：Let's Encrypt 免费证书

```bash
# Docker 部署
docker-compose up -d --build
```

## 默认账号

初始化后默认管理员账号：
- 用户名：`admin`
- 密码：`admin123`（首次登录强制修改）

## 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `SECRET_KEY` | JWT 签名密钥 | 必须修改 |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | 空（降级本地词库） |
| `DEEPSEEK_MODEL` | AI 模型 | `deepseek-v4-flash` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间 | `10080`（7天） |
| `ADMIN_USER_IDS` | 管理员用户 ID | `1` |

## License

MIT
