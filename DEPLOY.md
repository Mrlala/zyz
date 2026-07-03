# 中译中 · 部署指南

## 一、保底方案：HTML 文件提交（已完成）

`demo-html.zip` 已打包好，内含 `zhongyizhong.html`（单文件，双击即可在浏览器打开，含翻译、热词、词库浏览功能）。

**提交方式**：直接上传 `demo-html.zip` 到 TRAE 社区。

---

## 二、在线部署方案：Docker Compose（推荐）

### 前提条件
- 一台公网可访问的服务器（云主机/VPS）
- 已安装 Docker 和 Docker Compose

### 部署步骤

1. **上传项目到服务器**
   ```bash
   # 在服务器上
   git clone <你的仓库地址> trea_ai
   cd trea_ai
   ```
   或直接上传项目文件夹（需包含 `backend/`、`app/dist/build/h5/`、`docker-compose.yml`、`nginx.conf`）

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env，设置 SECRET_KEY 和 DEEPSEEK_API_KEY（可选）
   nano .env
   ```

3. **确保前端已构建**
   ```bash
   # 如果 app/dist/build/h5 不存在，在本地执行后重新上传
   cd app && npm install && npm run build:h5
   ```

4. **启动服务**
   ```bash
   docker-compose up -d --build
   ```

5. **验证**
   ```bash
   curl http://你的服务器IP/api/config/ai-status
   # 应返回 {"code":0,"message":"success","data":{...}}
   ```

6. **访问**
   - 前端：http://你的服务器IP/
   - API 文档：http://你的服务器IP/api/docs

### 常用命令
```bash
docker-compose logs -f          # 查看日志
docker-compose down             # 停止
docker-compose up -d --build    # 重新构建启动
```

---

## 三、免费平台部署（无服务器时备选）

### 后端部署到 Render（免费）

1. 注册 https://render.com
2. New → Web Service → 连接 GitHub 仓库
3. 配置：
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Root Directory: `backend`
   - 环境变量：添加 `SECRET_KEY`、`DEEPSEEK_API_KEY`（可选）
4. 部署后得到后端地址：`https://xxx.onrender.com`

### 前端部署到 Vercel（免费）

1. 修改 `app/src/config/env.js`，把生产环境的 `/api` 改成后端地址：
   ```js
   const BASE_URL = isDev ? 'http://localhost:8000/api' : 'https://xxx.onrender.com/api'
   ```
2. 重新构建：`cd app && npm run build:h5`
3. 注册 https://vercel.com
4. 上传 `app/dist/build/h5` 目录
5. 部署后得到前端地址：`https://xxx.vercel.app`

**注意**：免费平台有冷启动延迟（Render 15分钟无访问会休眠），评委首次访问可能等 30 秒。

---

## 四、文件清单

| 文件 | 用途 |
|------|------|
| `demo-html.zip` | 保底 HTML 包，上传社区 |
| `app/dist/build/h5/` | 前端构建产物，部署到 nginx/静态托管 |
| `backend/` | 后端源码 |
| `backend/Dockerfile` | 后端容器构建 |
| `docker-compose.yml` | 前后端一体化部署 |
| `nginx.conf` | nginx 配置（前端 + API 代理） |
| `.env.example` | 环境变量模板 |
| `backend/zyz.db` | SQLite 数据库（含初始数据） |
