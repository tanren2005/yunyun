# 云云 · 开发者文档

给改代码、启停环境、查路由的人看。使用者手册见 `USER_GUIDE.md`。过程记录见 `PROJECT_LOG.md`。

---

## 1. 技术栈（当前）

| 层 | 实现 |
|---|---|
| 前端 | Vue 3 + Vite + Vue Router + Pinia，开发端口 **5173** |
| 后端 | Python FastAPI + Uvicorn，端口 **8000** |
| 主库 | PostgreSQL 16，端口 **5432**，数据在 Docker 卷 `pgdata` |
| 缓存 | Redis 7，端口 **6379**，卷 `redisdata`（只放验证码） |
| 上传文件 | 容器内 `/data/uploads`，Compose 卷 `uploads` |
| 编排 | 项目根目录 `docker-compose.yml` |

不要把文章、用户、附件元数据只放 Redis。文件本体在 `uploads` 卷，元数据在 Postgres 的 `attachments` 表。

---

## 2. 启动

前置：安装并**打开** Docker Desktop，等到托盘图标就绪。

在 `c:\yunyun`：

```powershell
docker compose up --build
```

第一次会拉镜像、装 Python 依赖。成功后四个容器应是 `Up`：

- `yunyun-frontend-1`
- `yunyun-backend-1`
- `yunyun-db-1`（healthy）
- `yunyun-redis-1`（healthy）

后台跑（不占住终端）：

```powershell
docker compose up --build -d
```

看日志：

```powershell
docker compose logs -f backend
docker compose logs -f frontend
```

未配置 QQ SMTP 时，注册验证码在 **backend 日志**里。

改了 `backend/requirements.txt` 必须 `--build`，仅挂载源码热重载装不上新包。

---

## 3. 安全关闭（不丢数据）

**推荐停止（关进程，保留数据库和上传文件）：**

```powershell
docker compose stop
```

或：

```powershell
docker compose down
```

`down` **不带 `-v`** 只会删容器和默认网络，**命名卷还在**：用户、作品、评论、每日一阅、上传文件都还在。下次 `docker compose up` 数据还在。

**危险，会清空库和附件：**

```powershell
docker compose down -v
```

`-v` 删除 `pgdata`、`redisdata`、`uploads`。没有备份就等于删站。日常关闭**不要**加 `-v`。

暂停电脑前：先 `docker compose stop`，再关 Docker Desktop。不要直接杀 Postgres 容器电源（一般 Compose stop 会先停库）。

备份库：

```powershell
docker compose exec db pg_dump -U yunyun yunyun > backup.sql
```

---

## 4. 本机入口（先记这几个）

| 地址 | 用途 |
|---|---|
| http://localhost:5173 | **给人用的网站** |
| http://localhost:8000/docs | FastAPI Swagger，调试接口 |
| http://localhost:8000/redoc | 备用接口文档 |
| http://localhost:8000/api/health | 后端是否活着 |
| http://localhost:8000/uploads/文件名 | 已上传文件的静态地址 |
| localhost:5432 | Postgres（一般不用手连） |
| localhost:6379 | Redis |

前端 `VITE_API_BASE=http://localhost:8000`，浏览器直接打后端。Vite 也代理了 `/api` 和 `/uploads`。

---

## 5. 前端页面路由（http://localhost:5173 + 路径）

| 路径 | 页面文件 | 作用 | 登录 |
|---|---|---|---|
| `/` | `HomeView.vue` | 首页：栏目、每日一阅摘要、云间/读友会入口、最新作品 | 否 |
| `/c/prose` | `CategoryView.vue` | 散文列表 | 否 |
| `/c/fiction` | 同上 | 小说列表 | 否 |
| `/c/poetry` | 同上 | 诗歌列表 | 否 |
| `/c/essay` | 同上 | 随笔列表 | 否 |
| `/c/:slug` | 同上 | 按栏目 slug 列表 | 否 |
| `/posts/:id` | `PostView.vue` | 作品正文、附件、评论 | 浏览否；评/删要登录 |
| `/write` | `WriteView.vue` | 发四种题材；可上传 Word/文本/PDF/图片/视频 | **是** |
| `/moments` | `MomentsView.vue` | **云间**：公开动态（全员可见，无好友分组） | 浏览否；发/评要登录 |
| `/club` | `ClubView.vue` | **读友会**：分享一本书 | 浏览否；发/评要登录 |
| `/daily` | `DailyView.vue` | **每日一阅**：今日篇 + 出处 + 近日回顾 | 否 |
| `/profile` | `ProfileView.vue` | 资料与改密 | **是** |
| `/notifications` | `NotificationsView.vue` | 消息中心 | **是** |
| `/admin` | `AdminView.vue` | 账号管理 | **是（管理员）** |
| `/login` | `LoginView.vue` | 登录（单设备） | 否 |
| `/login?redirect=/write` | 同上 | 登录后回到 redirect | 否 |
| `/register` | `RegisterView.vue` | 注册 | 否 |

路由定义：`frontend/src/router/index.js`。`meta.auth: true` 的会先跳登录。

---

## 6. 后端 API 路由（http://localhost:8000）

### 账号 `app/api/auth.py`

| 方法 | 路径 | 作用 |
|---|---|---|
| POST | `/api/auth/send-code` | 发 QQ 验证码 |
| POST | `/api/auth/register` | 注册（邮箱≤2、用户名唯一、密码大小写） |
| POST | `/api/auth/login` | 登录，返回 JWT |
| GET | `/api/auth/me` | 当前用户（要 Token） |

### 作品 `app/api/content.py`

| 方法 | 路径 | 作用 |
|---|---|---|
| GET | `/api/categories` | 四栏目 |
| GET | `/api/posts` | 作品列表，`?category=fiction&skip=0&limit=20` |
| GET | `/api/posts/{id}` | 详情，阅读量 +1，含 attachments |
| POST | `/api/posts` | 发帖，正文可空（准备只传文件） |
| PATCH | `/api/posts/{id}` | 作者改稿 |
| DELETE | `/api/posts/{id}` | 作者删除 |
| GET/POST | `/api/posts/{id}/comments` | 评论 |

### 云间 / 读友会 / 每日一阅 `app/api/community.py`

| 方法 | 路径 | 作用 |
|---|---|---|
| GET | `/api/daily` | 当天篇；没有则按日期从词库生成并写入库 |
| GET | `/api/daily/history` | 近日列表 |
| GET | `/api/moments` | 公开动态时间线 |
| POST | `/api/moments` | 发动态 |
| DELETE | `/api/moments/{id}` | 作者删除 |
| GET/POST | `/api/moments/{id}/comments` | 动态评论 |
| GET | `/api/books` | 读书分享列表 |
| GET | `/api/books/{id}` | 单篇分享 |
| POST | `/api/books` | 发布分享 |
| DELETE | `/api/books/{id}` | 作者删除 |
| GET/POST | `/api/books/{id}/comments` | 读友讨论 |

### 上传 `app/api/uploads.py`

| 方法 | 路径 | 作用 |
|---|---|---|
| POST | `/api/posts/{id}/files` | 给作品挂附件（仅作者） |
| POST | `/api/moments/{id}/files` | 给动态挂附件 |
| POST | `/api/books/{id}/files` | 给读书分享挂附件 |
| GET | `/uploads/{stored_name}` | 下载/播放文件（静态） |

`multipart/form-data` 字段名必须是 **`files`**（可多个）。单文件上限默认 80MB，每条最多 8 个。

允许：`.txt .md .pdf .doc .docx`、图片、`.mp4 .webm .mov`、`.mp3 .wav .m4a`。

`.txt` / `.md` / `.docx` 上传到**作品**且正文为空时，会尝试抽文本填进 `posts.content`。

需登录的接口：`Authorization: Bearer <token>`。

---

## 7. 新模块怎么工作（实现要点）

**云间（`/moments`）**  
不是微信好友圈，也没有 QQ 空间权限：没有「仅好友」。任何登录用户发的动态，游客也能看。表：`moments`、`moment_comments`。

**每日一阅**  
不用外接大模型。词库在 `backend/app/data/daily_pool.py`（古典诗文，带来源）。按 **Asia/Shanghai 的公历日期**对词库取模，写入 `daily_readings`，同一天全站相同。启动时 `ensure_today()`，访问 `/api/daily` 也会补当天。要换篇：改词库，并删掉当天那行再请求接口。

**读友会**  
表 `book_shares`：书名、作者、分享正文 + 附件。

**四种题材上传**  
先 `POST /api/posts` 再 `POST /api/posts/{id}/files`。前端 `WriteView.vue` 已串起来。

---

## 8. 目录（改功能时看这里）

```text
backend/app/models/__init__.py   表结构
backend/app/schemas.py           请求响应
backend/app/api/content.py       作品
backend/app/api/community.py     云间/读友会/每日
backend/app/api/uploads.py       上传
backend/app/services/files.py    存盘、抽 Word 文本
backend/app/services/daily.py    每日篇
backend/app/data/daily_pool.py   每日词库
frontend/src/views/               页面
frontend/src/router/index.js      前端路由
docker-compose.yml                启停与卷
```

---

## 9. 环境变量（根目录 `.env`）

| 变量 | 含义 |
|---|---|
| `SECRET_KEY` | JWT 密钥，上线必换 |
| `SMTP_*` | QQ 邮箱；空则验证码打日志 |
| `CORS_ORIGINS` | 允许的前端源 |
| Compose 覆盖 `DATABASE_URL` / `REDIS_URL` / `UPLOAD_DIR` | 指向容器内服务 |

---

## 10. 常见开发操作

改 Python 后：backend 开了 `--reload`，保存即重启。  
改 Vue 后：Vite 热更新。  
加了 pip 包：`docker compose up --build -d backend`。  
表结构新增：当前用 `create_all`，**新表会自动建，已有表不会改列**。要改旧列需手写 SQL 或上 Alembic。

Windows PowerShell **不要**用 `&&` 串命令，请分行执行。
