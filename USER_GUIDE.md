# 云云 · 使用文档

面向本地开发与日常使用。默认前端地址 **http://localhost:5173**，后端地址 **http://localhost:8000**。

---

## 1. 启动

1. 安装并打开 Docker Desktop。
2. 在项目根目录执行：

```bash
docker compose up --build
```

3. 浏览器打开 **http://localhost:5173**。

停止：`docker compose down`（数据仍在 Docker 卷里，不会清库）。  
看后端日志（未配邮箱时验证码在这里）：`docker compose logs backend -f`

---

## 2. 账号规则

| 项目 | 规则 |
|---|---|
| 邮箱 | 必须是 QQ 邮箱（`xxx@qq.com`） |
| 验证码 | 先点「获取验证码」，10 分钟有效；同一邮箱 60 秒内不能连发 |
| 同一邮箱 | 最多注册 **2** 个账号 |
| 用户名 | 2–32 字；中文、英文、数字都可以（如 `TTTTTr`、`小云`）；**全站唯一**；不要空格和 `@ / \ # ?` |
| 显示名 | 作品和评论旁展示的名字，可与用户名不同，不必唯一 |
| 密码（新注册） | 至少 **8** 位，必须**同时有大写和小写字母**（如 `Yunyun123`） |
| 登录 | 用「用户名」或「QQ 邮箱」+ 密码 |

用户名是登录凭证，显示名是给人看的笔名。

未在 `.env` 配置 SMTP 时：点「获取验证码」后，打开后端日志，找到类似：

```text
开发验证码 [你的邮箱] => 123456
```

把数字填进注册页即可。配置了 QQ 邮箱授权码后，验证码会发到邮箱。

---

## 3. 网站页面（前端路由）

这些是你在浏览器地址栏看到的路径。完整例子：`http://localhost:5173/register`。

| 网址路径 | 页面 | 做什么 | 要不要登录 |
|---|---|---|---|
| `/` | 首页 | 品牌介绍、四个栏目入口、全站最新作品列表 | 否 |
| `/c/prose` | 散文栏目 | 只列出「散文」栏目下的作品 | 否 |
| `/c/fiction` | 小说栏目 | 只列出「小说」栏目下的作品 | 否 |
| `/c/poetry` | 诗歌栏目 | 只列出「诗歌」栏目下的作品 | 否 |
| `/c/essay` | 随笔栏目 | 只列出「随笔」栏目下的作品 | 否 |
| `/c/:slug` | 任意栏目 | `:slug` 是栏目英文标识（prose / fiction / poetry / essay） | 否 |
| `/posts/1` | 作品阅读页 | 看正文、阅读量、评论；作者可删除自己的作品 | 浏览否；评论/删除要登录 |
| `/posts/:id` | 任意作品 | `:id` 是作品数字编号，如 `/posts/12` | 同上 |
| `/write` | 写一篇 | 选栏目、正文和/或上传 Word、文本、PDF、图片、视频 | **是** |
| `/moments` | 云间 | 公开动态（全站可见，无好友分组），可发文字和文件 | 浏览否；发布/评论要登录 |
| `/club` | 读友会 | 分享一本书，可附图/文件，读友讨论 | 浏览否；发布/评论要登录 |
| `/daily` | 每日一阅 | 每小时随机一篇散文/诗歌/小说名句及出处 | 否 |
| `/profile` | 我的资料 | 用户名、邮箱、改显示名；邮箱验证改密码 | **是** |
| `/notifications` | 消息 | 别人回复你的通知列表；打开后红点清零 | **是** |
| `/admin` | 管理端 | 搜用户、启用/禁用、设管理员、强制下线 | **是（管理员）** |
| `/login` | 登录 | 用户名或邮箱 + 密码（同账号仅一台有效） | 否 |
| `/login?redirect=/write` | 登录后回跳 | 登录成功后回到 `redirect` 指定的页面 | 否 |
| `/register` | 注册 | 邮箱验证码、用户名、显示名、密码 | 否 |

顶栏按钮对应关系：

- 「云云」→ `/`
- 「散文 / 小说 / 诗歌 / 随笔」→ `/c/...`
- 「云间 / 读友会 / 每日一阅」→ `/moments` `/club` `/daily`
- 「写一篇」→ `/write`
- 「登录」→ `/login`
- 「注册」→ `/register`
- 「退出」→ 清掉本地登录状态，仍停在当前页或回首页

---

## 4. 后端接口（API 路由）

浏览器日常不用直接打开这些地址（前端会代为请求）。完整前缀：`http://localhost:8000`。

交互式接口说明：**http://localhost:8000/docs**（Swagger）。  
备用文档：**http://localhost:8000/redoc**。

### 4.1 系统

| 方法 | 路径 | 作用 |
|---|---|---|
| GET | `/api/health` | 健康检查。返回站点是否正常，例如 `{"status":"ok","name":"云云"}` |

### 4.2 账号 `/api/auth`

| 方法 | 路径 | 作用 | 登录？ |
|---|---|---|---|
| POST | `/api/auth/send-code` | 向 QQ 邮箱发 6 位验证码（或写入后端日志） | 否 |
| POST | `/api/auth/register` | 校验验证码后创建账号；同一邮箱最多 2 个；用户名唯一 | 否 |
| POST | `/api/auth/login` | 用户名或邮箱 + 密码，返回 JWT 和用户信息 | 否 |
| GET | `/api/auth/me` | 根据请求头里的 Token 返回当前用户 | **是** |

`send-code` 请求体：`{"email":"xxx@qq.com"}`  
`register` 请求体：`email`、`code`、`username`、`password`、`display_name`  
`login` 请求体：`account`、`password`  
需登录的接口：请求头 `Authorization: Bearer <access_token>`

### 4.3 栏目与作品 `/api`

| 方法 | 路径 | 作用 | 登录？ |
|---|---|---|---|
| GET | `/api/categories` | 四个栏目列表（散文/小说/诗歌/随笔） | 否 |
| GET | `/api/posts` | 作品列表（最新在前） | 否 |
| GET | `/api/posts?category=fiction` | 只列某一栏目。`category` 为 slug | 否 |
| GET | `/api/posts?skip=0&limit=20` | 分页：`skip` 跳过条数，`limit` 每页条数（1–50） | 否 |
| GET | `/api/posts/{id}` | 作品详情；每次访问阅读量 +1 | 否 |
| POST | `/api/posts` | 发布作品 | **是** |
| PATCH | `/api/posts/{id}` | 修改自己的作品（标题/正文/栏目/摘要） | **是**（仅作者） |
| DELETE | `/api/posts/{id}` | 删除自己的作品 | **是**（仅作者） |
| GET | `/api/posts/{id}/comments` | 某篇作品的评论列表 | 否 |
| POST | `/api/posts/{id}/comments` | 发表评论；可选 `parent_id` 回复某条评论 | **是** |

发布作品请求体：`title`、`content`、`category_id`、可选 `summary`。  
`category_id` 对应栏目数字 id（一般散文=1、小说=2、诗歌=3、随笔=4，以 `/api/categories` 为准）。

### 4.4 云间、读友会、每日一阅、上传

| 方法 | 路径 | 作用 | 登录？ |
|---|---|---|---|
| GET | `/api/daily` | 当前小时篇（散文/诗歌/小说等）及出处 | 否 |
| GET | `/api/daily/history` | 近几小时每日一阅 | 否 |
| GET | `/api/moments` | 公开动态 | 否 |
| POST | `/api/moments` | 发动态 | **是** |
| DELETE | `/api/moments/{id}` | 删自己的动态 | **是** |
| GET/POST | `/api/moments/{id}/comments` | 动态评论 | GET 否；POST 是 |
| GET | `/api/books` | 读友会列表 | 否 |
| POST | `/api/books` | 分享一本书 | **是** |
| GET/POST | `/api/books/{id}/comments` | 读书讨论 | GET 否；POST 是 |
| POST | `/api/posts/{id}/files` 等 | 上传附件（posts/moments/books） | **是** |

更完整的启停与路由表见 **[DEV_GUIDE.md](./DEV_GUIDE.md)**（面向开发）。

---

## 5. 推荐使用流程

1. 打开 http://localhost:5173/register  
2. 填 QQ 邮箱 → 获取验证码（查邮箱或后端日志）  
3. 设用户名（如 `TTTTTr`，全站不能重复）和符合大小写要求的密码  
4. 注册成功会自动登录并回到首页  
5. 点「写一篇」发布；在阅读页底部评论  
6. 下次用 http://localhost:5173/login 登录  

游客可以浏览首页、栏目和作品，但不能发帖或评论。

---

## 6. 常见问题

**验证码收不到**  
未配 SMTP 是正常的，去看 `docker compose logs backend`。若已配 SMTP，确认用的是 QQ 邮箱「授权码」而不是 QQ 密码。

**提示用户名已被占用**  
用户名全站唯一，换一个即可。同一 QQ 邮箱还可以再注册一个不同用户名的号（最多两个）。

**提示该 QQ 邮箱最多只能注册 2 个账号**  
这个邮箱已经有两个号了，换邮箱或登录已有账号。

**密码不符合要求**  
新注册必须同时有大写和小写，且不少于 8 位。例如 `abcABC12` 可以，`12345678` 或全小写不行。

**打开 /write 却跳到登录页**  
写文章必须登录。登录后会按地址栏里的 `redirect` 回到写作页。

**数据会不会丢**  
用户、作品、评论在 PostgreSQL 的 Docker 卷 `pgdata` 里。`docker compose down` 不会删卷；只有 `docker compose down -v` 才会清空数据。备份：`docker compose exec db pg_dump -U yunyun yunyun > backup.sql`

---

## 7. 环境与端口

| 地址 | 用途 |
|---|---|
| http://localhost:5173 | 网站（给人用） |
| http://localhost:8000 | 后端 API |
| http://localhost:8000/docs | 接口调试页 |
| http://localhost:8000/api/health | 后端是否存活 |
| localhost:5432 | PostgreSQL（容器映射） |
| localhost:6379 | Redis（验证码） |

SMTP、密钥等写在项目根目录 `.env`。模板见 `.env.example`。

### 配置 QQ 邮箱真正发信

1. QQ 邮箱网页 → **设置 → 账号与安全**（你现在这页）。
2. 确认「POP3/IMAP/SMTP」为已开启。
3. 点 **生成授权码**，按提示用手机短信验证，复制得到的 **16 位授权码**。
4. 打开项目根目录 `.env`，填：

```
SMTP_USER=你的QQ号@qq.com
SMTP_PASS=刚才复制的授权码
SMTP_FROM=你的QQ号@qq.com
```

`SMTP_PASS` 不能填 QQ 密码。  
5. 在项目根目录执行（必须 recreate 才会读新的 `.env`）：

```powershell
docker compose up -d --force-recreate backend
```

6. 等约 1 分钟冷却过后，再点「获取验证码」，到 QQ 邮箱收件箱和垃圾箱查看「【云云】注册验证码」。

