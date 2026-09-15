# 云云

文学向社区小站：散文、小说、诗歌、随笔。支持 QQ 邮箱验证码注册（同一邮箱最多 2 个账号）、发帖与评论。

**完整使用说明（页面路由、接口、账号规则）：见 [USER_GUIDE.md](./USER_GUIDE.md)。**  
**开发启停、安全关闭、全部网址：见 [DEV_GUIDE.md](./DEV_GUIDE.md)。**  
**开发过程与每次改动记录：见 [PROJECT_LOG.md](./PROJECT_LOG.md)（只追加，不覆盖）。**

## 技术栈

- **后端**：Python FastAPI + SQLAlchemy + PostgreSQL + Redis
- **前端**：Vue 3 + Vite + Vue Router + Pinia
- **部署**：Docker Compose（数据落在命名卷，容器重启不丢）

## 本地启动（推荐 Docker）

1. 确保已安装 Docker Desktop
2. 在项目根目录：

```bash
copy .env.example .env
docker compose up --build
```

3. 打开浏览器：
   - 前端：http://localhost:5173
   - 后端 API 文档：http://localhost:8000/docs
   - 健康检查：http://localhost:8000/api/health

### 验证码说明

在 `.env` 中配置 QQ 邮箱 SMTP（`SMTP_USER` / `SMTP_PASS` 为授权码）后，验证码会发到邮箱。

未配置时，验证码会打印在 **backend 容器日志**里，本地照样能完成注册。

## 数据安全

- 用户、作品、评论存在 **PostgreSQL**（Docker 卷 `pgdata`）
- Redis 只存验证码等短期数据
- 备份示例：

```bash
docker compose exec db pg_dump -U yunyun yunyun > backup.sql
```

恢复：

```bash
Get-Content backup.sql | docker compose exec -T db psql -U yunyun yunyun
```

## 不配 Docker 时（开发）

需本机已有 PostgreSQL、Redis，并改 `.env` / 环境变量中的连接串。

```bash
# 终端 1
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 终端 2
cd frontend
npm install
npm run dev
```

## 公网方向（本地跑通后）

同一套 Compose 部署到云主机 → Nginx 反代前端与 `/api` → 域名 + HTTPS；务必更换 `SECRET_KEY` 并配置 SMTP 与定期 `pg_dump`。
