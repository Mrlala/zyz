# 中译中 · 部署指南

## 项目架构

| 服务 | 技术栈 | 构建产物 | 端口 |
|---|---|---|---|
| 后端 API | FastAPI + SQLite | Python 源码 | 8000 |
| App 前端 (H5) | uni-app + Vue3 | `app/dist/build/h5/` | 80 (nginx) |
| 管理后台 | Vue3 + Element Plus | `admin-web/dist/` | 80 (nginx /admin/) |

部署后访问地址：
- App：`http://服务器IP/`
- 管理后台：`http://服务器IP/admin/`
- API 文档：`http://服务器IP/api/docs`

---

## 方案一：Docker Compose 部署（推荐）

### 前提条件
- 服务器已安装 Docker 和 Docker Compose
- 本地已构建前端产物（`app/dist/build/h5/` 和 `admin-web/dist/`）

### 步骤

1. **本地构建前端产物**

```bash
# 构建 App H5
cd app
npm install
npm run build:h5
cd ..

# 构建管理后台
cd admin-web
npm install
npm run build
cd ..
```

2. **上传项目到服务器**

```bash
# 方式一：git clone（需先推送到 GitHub）
git clone https://github.com/Mrlala/zyz.git trea_ai
cd trea_ai

# 方式二：打包上传（排除 node_modules）
# 本地执行：tar --exclude="node_modules" --exclude=".git" -czf trea_ai.tar.gz trea_ai/
# 上传后解压
```

3. **配置环境变量**

```bash
cp .env.example .env
nano .env
```

修改 `.env`：
```ini
SECRET_KEY=生成一个随机字符串
DEEPSEEK_API_KEY=你的真实API Key
DEEPSEEK_MODEL=deepseek-v4-flash
ADMIN_USER_IDS=1
```

4. **确保数据库存在**

```bash
# 如果 backend/zyz.db 不存在，初始化数据库
cd backend
python -c "from core.database import engine, Base; from models import *; Base.metadata.create_all(engine)"
python data/init_data.py
python data/init_admin_data.py
python data/init_word_extras.py
cd ..
```

5. **启动服务**

```bash
docker-compose up -d --build
```

6. **验证**

```bash
# 检查容器状态
docker-compose ps

# 测试 API
curl http://localhost/api/config/ai-status

# 查看日志
docker-compose logs -f backend
```

### 常用命令

```bash
docker-compose up -d --build    # 重新构建并启动
docker-compose down             # 停止所有服务
docker-compose logs -f          # 实时日志
docker-compose restart backend  # 重启后端
```

---

## 方案二：裸机部署（systemd + nginx）

适用于无法使用 Docker 的环境。

### 1. 安装系统依赖

```bash
# Ubuntu/Debian
apt update
apt install -y python3 python3-pip python3-venv nginx

# CentOS/RHEL
yum install -y python3 python3-pip nginx
```

### 2. 安装 Node.js（用于构建前端，可在本地构建后上传）

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs
```

### 3. 部署后端

```bash
# 创建项目目录
mkdir -p /opt/zyz
cd /opt/zyz

# 上传代码或 git clone
git clone https://github.com/Mrlala/zyz.git .

# 创建虚拟环境
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
nano .env
# 修改 SECRET_KEY、DEEPSEEK_API_KEY、DEEPSEEK_MODEL=deepseek-v4-flash

# 初始化数据库
python -c "from core.database import engine, Base; from models import *; Base.metadata.create_all(engine)"
python data/init_data.py
python data/init_admin_data.py
python data/init_word_extras.py

# 测试启动
uvicorn main:app --host 0.0.0.0 --port 8000
# 看到 "Application startup complete" 后 Ctrl+C 退出
```

### 4. 配置 systemd 服务

```bash
cat > /etc/systemd/system/zyz-backend.service << 'EOF'
[Unit]
Description=ZYZ Backend API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/zyz/backend
EnvironmentFile=/opt/zyz/backend/.env
ExecStart=/opt/zyz/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable zyz-backend
systemctl start zyz-backend
systemctl status zyz-backend
```

### 5. 构建并部署前端

```bash
# 构建 App H5
cd /opt/zyz/app
npm install
npm run build:h5

# 构建管理后台
cd /opt/zyz/admin-web
npm install
npm run build
```

### 6. 配置 Nginx

```bash
cat > /etc/nginx/conf.d/zyz.conf << 'EOF'
server {
    listen 80;
    server_name _;

    # App 前端（H5）
    root /opt/zyz/app/dist/build/h5;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # 管理后台
    location /admin/ {
        alias /opt/zyz/admin-web/dist/;
        try_files $uri $uri/ /admin/index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    gzip_min_length 1024;
}
EOF

nginx -t          # 测试配置
systemctl reload nginx
```

### 7. 验证

```bash
curl http://localhost/api/config/ai-status
# 应返回 {"code":0,"message":"success","data":{...}}
```

---

## 方案三：HTTPS 配置（有域名时）

### 使用 Let's Encrypt 免费证书

```bash
# 安装 certbot
apt install -y certbot python3-certbot-nginx

# 申请证书（替换 your-domain.com 为真实域名）
certbot --nginx -d your-domain.com

# 自动续期（certbot 默认已配置）
certbot renew --dry-run
```

### 手动 HTTPS 配置

修改 nginx 配置：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # ... 其余配置同上 ...
}
```

---

## 更新部署

当代码有更新时：

```bash
cd /opt/zyz
git pull origin master

# 如果后端有改动
systemctl restart zyz-backend

# 如果前端有改动
cd app && npm run build:h5 && cd ..
cd admin-web && npm run build && cd ..

# 如果 nginx 配置有改动
nginx -t && systemctl reload nginx
```

---

## 环境变量说明

| 变量 | 说明 | 默认值 |
|---|---|---|
| `SECRET_KEY` | JWT 签名密钥（生产必须修改） | `change-this-in-production` |
| `DEEPSEEK_API_KEY` | DeepSeek API Key（留空则降级为本地词库） | 空 |
| `DEEPSEEK_API_URL` | DeepSeek API 地址 | `https://api.deepseek.com/v1/chat/completions` |
| `DEEPSEEK_MODEL` | AI 模型名（`deepseek-chat` 已弃用） | `deepseek-v4-flash` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间（分钟） | `10080`（7天） |
| `ADMIN_USER_IDS` | 管理员用户 ID（逗号分隔） | `1` |
| `DATABASE_URL` | 数据库连接串 | `sqlite:///./zyz.db` |

---

## 常见问题

### 1. `docker-compose up` 报 `zyz.db` 挂载为目录

**原因**：Docker 在文件不存在时会将挂载路径创建为目录。

**解决**：先在 `backend/` 下创建空的 `zyz.db` 文件，或先初始化数据库：
```bash
cd backend && python -c "from core.database import engine, Base; from models import *; Base.metadata.create_all(engine)" && cd ..
```

### 2. 管理后台刷新 404

**原因**：admin-web 已改为 hash 模式，地址栏带 `#`，不会 404。如果仍 404，检查 nginx `/admin/` 的 `alias` 路径是否正确。

### 3. AI 翻译不工作

**检查**：
```bash
curl http://localhost/api/config/ai-status
# data.enabled 应为 true
```
若 `enabled: false`，检查 `DEEPSEEK_API_KEY` 是否配置正确。

### 4. 前端访问 API 报 CORS 错误

后端已默认允许所有来源。若仍有问题，检查 `backend/config.py` 的 `CORS_ORIGINS` 配置。

### 5. 数据库迁移

本项目使用 SQLAlchemy 自动建表 + 轻量迁移（`ALTER TABLE ADD COLUMN`）。后端启动时会自动执行迁移，无需手动操作。

---

## 文件清单

| 文件 | 用途 |
|---|---|
| `backend/` | 后端源码 |
| `backend/Dockerfile` | 后端容器构建 |
| `backend/requirements.txt` | Python 依赖 |
| `backend/.env.example` | 后端环境变量模板 |
| `app/dist/build/h5/` | App 前端构建产物 |
| `admin-web/dist/` | 管理后台构建产物 |
| `docker-compose.yml` | Docker 一体化部署 |
| `nginx.conf` | Nginx 配置（Docker 用） |
| `.env.example` | Docker 部署环境变量模板 |
| `start.ps1` | Windows 本地开发启动脚本 |
