# 云云（Yunyun）开发日志

> 本文件是项目的**完整过程记录**：用了什么、改了什么、本来要用什么、为何换掉、换成什么。  
> **约定**：之后每一次开发、修复、换方案，都必须在文末「变更履历」**顶部追加**一条，不得覆盖旧内容。  
> 日期以对话发生日为准（2026-09-14 起）。仓库：`c:\yunyun`。

---

## 〇、如何读这份日志

1. **第一节**：需求从何而来。  
2. **第二节**：方案选型与被否决的方案（含原因）。  
3. **第三节**：落地时实际写了哪些代码与文件。  
4. **第四节**：构建/部署踩坑与换法。  
5. **第五节**：上线后的功能与文档迭代。  
6. **变更履历**：按时间倒序追加的后续操作（含本文件建立之后的每一次改动）。

使用手册（给使用者看的网址说明）在 `USER_GUIDE.md`，**不是**本日志的替代。

---

## 一、需求来源（2026-09-14）

仓库最初几乎为空，仅有 `ReadMe.md` 一段中文需求。用户要求：

1. 网站名：**云云**。  
2. **注册 / 登录**；注册必须用 **QQ 邮箱**收验证码。  
3. **一个 QQ 邮箱最多注册两个账号**。  
4. 内容题材：散文、短篇小说（类意林/中文网）、诗歌、随笔。  
5. 用户可互相浏览、评论，类似早期论坛。  
6. 先 **本地部署跑通**，再上公开域名。  
7. 后端 **必须用 Python**。  
8. 首轮只要**技术方案**，尚未要求立刻写代码。

随后用户补充担心：

- 网站会不会跑不起来、会不会崩。  
- 数据会不会丢、能不能完整正确存储。  
- 前端**不能太简朴**。

再随后用户确认前端用 **Vue**。

---

## 二、技术方案：采用、备选、放弃

### 2.1 最终采用（当前）

| 层 | 采用 | 用途 |
|---|---|---|
| 后端语言 | Python 3.12（Docker 镜像） | 硬性要求 Python |
| Web 框架 | FastAPI + Uvicorn | API、校验、OpenAPI |
| ORM | SQLAlchemy 2.x | 模型与事务 |
| 校验 | Pydantic v2 | 请求体、邮箱/用户名/密码规则 |
| 认证 | JWT（python-jose）+ passlib/bcrypt | 登录态 |
| 主存储 | PostgreSQL 16 | 用户、栏目、作品、评论 |
| 缓存 | Redis 7 | 验证码、发送冷却 |
| 邮件 | smtplib + QQ SMTP（465） | 注册验证码 |
| 前端 | Vue 3 + Vite + Vue Router + Pinia | 页面与交互 |
| 编排 | Docker Compose | db / redis / backend / frontend |
| 数据卷 | `pgdata`、`redisdata` | 容器删了库文件还在 |

### 2.2 本来考虑、后来不用的方案

| 本来要用 | 后来 | 原因 |
|---|---|---|
| **前端：Jinja2 + HTMX**（服务端渲染） | **Vue 3 SPA** | 初稿为了快、少 CORS。用户明确页面不能太土，并选定 Vue。Jinja 默认观感偏后台/论坛灰框。 |
| **SQLite 本地起步** | 从一开始就用 **PostgreSQL** | 用户最担心数据丢失与正确性；SQLite 上公网并发、备份习惯差，本地和公网两套库会搬家翻车。 |
| **Django** | FastAPI | Django 能做论坛且有 Admin，但偏重；当前要独立好看前端 + 清晰 API，FastAPI 更贴。未落地 Django。 |
| **Flask** | FastAPI | 能做，但邮件、校验、OpenAPI 要自己拼，成本高于 FastAPI。未落地 Flask。 |
| **React** | Vue | 用户回复「Vue吧」。 |
| **把正文存 Redis** | Redis **只存验证码** | Redis 适合过期数据；崩溃或清空不应丢掉文章。账号与正文只进 Postgres。 |
| **邮箱字段 UNIQUE** | 邮箱 **不唯一**，应用层 + 行锁限制 ≤2 | 需求是一邮箱两账号，UNIQUE 会直接禁掉第二个号。用户名才 UNIQUE。 |
| **Alembic 一上来管迁移** | 启动时 `create_all` + 种子栏目 | MVP 赶本地跑通；Alembic 已进 requirements 但尚未写迁移脚本。表结构大变时应改用 Alembic。 |
| **后端 Docker 里 apt 装 gcc、libpq-dev** | 只 pip 装 **psycopg[binary]** | 编译工具让 Debian 源下几十 MB，构建卡很久。binary wheel 不需要 gcc。 |
| **pip 走官方 pypi.org** | 清华镜像 `pypi.tuna.tsinghua.edu.cn` | 构建时报 `sqlalchemy==2.0.36` 无匹配版本（实为索引/网络失败）。 |
| **宿主机 Python 3.14 跑后端** | 容器内 **Python 3.12** | 本机 3.14 装 pydantic-core 等会源码编译，慢且不稳。 |
| **用户名仅 ASCII 字母数字下划线** | 放宽：中文/英文/数字等，全站唯一 | 注册页文案像「必须混用三类字符」；用户要 `TTTTTr` 这类名，规则不必那么苛刻。 |
| **密码只要求 ≥6 位** | 注册要求 **≥8 且同时含大小写** | 用户明确要求密码要有大小写。登录仍接受旧号较短密码，以免旧账号进不去。 |

### 2.3 讨论过、尚未做的

- 公网：Nginx 反代 + 域名 + Let’s Encrypt。  
- 管理后台、搜索、点赞、私信、富文本增强。  
- 楼中楼：库有 `parent_id`，前端暂按平铺列表。

---

## 三、从零落地时写了什么（2026-09-14 下午）

### 3.1 仓库与编排

新建：

- `docker-compose.yml`：postgres:16-alpine、redis:7-alpine、backend、frontend；健康检查；`restart: unless-stopped`。  
- `.env`、`.env.example`：JWT 密钥、SMTP、CORS。  
- `.gitignore`：`.env`、`node_modules`、venv、`dist` 等。

本机当时环境：Windows、PowerShell、Node v24.14.1、Python 3.14.7、Docker 29.3.0、npm 11.11.0。

**PowerShell**：不支持 `cmd` 的 `&&`，脚手架命令必须拆开执行。

### 3.2 后端文件与职责

| 路径 | 写了什么 |
|---|---|
| `backend/Dockerfile` | 见第四节，改过两次 |
| `backend/requirements.txt` | fastapi、uvicorn、sqlalchemy、psycopg、alembic、pydantic、jose、passlib、bcrypt、redis、email-validator 等 |
| `app/config.py` | 配置；一邮箱最多 2 账号；验证码 TTL 600s、重发间隔 60s |
| `app/database.py` | Engine（`pool_pre_ping`）、Session、Base |
| `app/models/__init__.py` | User、Category、Post、Comment |
| `app/schemas.py` | 请求/响应；QQ 邮箱校验 |
| `app/core/security.py` | bcrypt、JWT |
| `app/core/redis_client.py` | Redis 连接 |
| `app/services/mail.py` | SMTP_SSL 发信；未配置返回 False |
| `app/services/code.py` | 验证码写入 Redis；失败则打日志方便本地注册 |
| `app/api/auth.py` | send-code / register / login / me |
| `app/api/content.py` | 栏目、帖子、评论 |
| `app/api/deps.py` | Bearer Token 取当前用户 |
| `app/seed.py` | 空库写入散文/小说/诗歌/随笔 |
| `app/main.py` | CORS、挂路由、启动建表+种子、`/api/health` |

注册时曾用 `func.count().with_for_update()`，后改为 **查出该邮箱用户并 `FOR UPDATE` 再 `len`**，锁行语义更清楚，并去掉多余的 `func` 导入。

### 3.3 前端文件与职责

脚手架：`npm create vite@latest frontend -- --template vue`，再装 `vue-router@4`、`pinia`。

自写：`src/api.js`、`stores/auth.js`、`router/index.js`、`styles/main.css`、`App.vue`、页头页脚、PostCard、Home/Category/Post/Write/Login/Register。

视觉：墨青绿 + 雾纸底 + 字趣小魏 / Noto 宋，避免通用紫渐变模板。

删除 Vite 默认 `HelloWorld.vue`、`style.css`。误写到 `frontend/frontend/` 的目录已删。

`vite.config.js` 配了 `/api` 代理到 `localhost:8000`；Compose 里前端环境变量 `VITE_API_BASE=http://localhost:5173` 实际为 `http://localhost:8000`，浏览器直连后端。

### 3.4 种子栏目

| slug | 中文名 |
|---|---|
| prose | 散文 |
| fiction | 小说 |
| poetry | 诗歌 |
| essay | 随笔 |

---

## 四、构建与运行：失败与换法

1. **Docker 未开**  
   报错连不上 `dockerDesktopLinuxEngine`。  
   **处理**：启动 Docker Desktop，等 `docker ps` 可用。

2. **宿主机 pip 装依赖**  
   Python 3.14 + pydantic-core 走编译，耗时长。  
   **换法**：以后端容器 3.12 为准；根目录 `.venv` 不是正式运行环境。

3. **Dockerfile 装 gcc**  
   apt 拉 56MB+ 编译链，构建十几分钟仍未完。  
   **换法**：去掉 apt；用 psycopg binary wheel。

4. **官方 PyPI**  
   `No matching distribution found for sqlalchemy==2.0.36`。  
   **换法**：清华 PyPI 镜像。之后安装成功。

5. **Compose 起来后的验证**  
   `/api/health` 正常；栏目 4 条；未配 SMTP 时日志打印验证码；用接口完成注册 `demo_user` 并发帖，库中有数据。  
   前端 `http://localhost:5173` HTTP 200。

容器名：`yunyun-db-1`、`yunyun-redis-1`、`yunyun-backend-1`、`yunyun-frontend-1`。

---

## 五、功能与文档迭代（同日稍后）

### 5.1 Vite 报错：`Failed to resolve import "./api"`

- **现象**：`src/stores/auth.js` 写 `import { api } from './api'`。  
- **原因**：`api.js` 在 `src/`，不在 `src/stores/`。`./` 会找 `stores/api.js`。views 里的 `../api` 是对的。  
- **修改**：改为 `import { api } from '../api'`。  
- **当时**写过一版 `PROJECT_LOG.md`，后来该文件被清空成 1 行空文件；**本文件为 2026-09-14 晚重建的完整版**。

### 5.2 用户名与密码规则

用户反馈注册页「必须字母数字下划线」太苛刻，举例 `TTTTTr` 应可用；用户名仍须唯一；密码要有大小写。

| 项 | 改前 | 改后 |
|---|---|---|
| 用户名 | 仅 ASCII 字母数字下划线，最短 3 | 2–32 字；中文/英文/数字等；禁空格与 `@/\ # ?`；**UNIQUE 不变** |
| 密码（注册） | ≥6 | ≥8 且必须同时有大写、小写 |
| 注册页文案 | placeholder「字母数字下划线」 | 说明可 `TTTTTr`、中文，并提示密码规则 |
| 登录页密码最短 | 曾误改成 8 | **改回 6**，避免旧测试号登不进去 |

改动文件：`backend/app/schemas.py`、`frontend/src/views/RegisterView.vue`、`frontend/src/views/LoginView.vue`。

### 5.3 使用文档

新建 `USER_GUIDE.md`：启动方法、账号规则、**每一个前端路径**、**每一个 API 路径**、推荐流程、FAQ。  
`ReadMe.md` 增加指向该文件的链接。

### 5.4 本回合（写详细开发日志）

- 重建本 `PROJECT_LOG.md`（完整史 + 履历）。  
- 新增 `.cursor/rules/project-log.mdc`：之后每次改代码/方案，必须往本日志「变更履历」追加，禁止覆盖。

---

## 六、当前功能清单

已实现：QQ 邮箱验证码（SMTP 或日志回退）、注册（邮箱≤2、用户名唯一）、登录退出、JWT、四栏目、发帖/列表/详情/阅读量、作者删帖、评论、Vue 文学站页面、Compose 本地全栈。

未实现：公网域名与 HTTPS、管理后台、搜索、点赞、私信、Alembic 正式迁移流、前端楼中楼展示。

---

## 七、关键路径对照（给后来改代码的人）

```text
yunyun/
├── PROJECT_LOG.md          ← 本日志（只追加）
├── USER_GUIDE.md           ← 使用者手册（路由说明）
├── ReadMe.md               ← 启动摘要
├── docker-compose.yml
├── .env / .env.example
├── .cursor/rules/project-log.mdc
├── backend/app/            ← Python API
└── frontend/src/           ← Vue 页面
```

前端路由：`/`、`/c/:slug`、`/posts/:id`、`/write`、`/login`、`/register`。  
API 前缀：`/api`（详见 USER_GUIDE）。

---

### 2026-09-15 — 每日一阅全文累积；修复登录；换微信码

- **做了什么**：
  - 每日一阅改为全文（背影/荷塘月色/孔乙己/故乡/社戏等），页面按时间倒序一篇接一篇展示全文；清空旧「节选」记录并回填近几小时样例。
  - 管理员 `Tan` 密码重置为可登录状态（因调试曾改坏）；登录页已有「忘记密码」，资料页可改密，均走 QQ 邮箱验证码。
  - 联系页去掉「扫码添加好友（TTTTTr）」文案，更换新微信二维码。
- **原方案 → 新方案**：节选 + 只显一篇/标题列表 → 中学阅读篇幅全文 + 累积堆叠；登录密码异常 → 重置并可邮箱找回。
- **原因**：用户本轮明确要求。

### 2026-09-15 — 每日一阅词库改为公版全文

- **做了什么**：重写 `backend/app/data/daily_pool.py`，共 34 条（诗歌 12 / 云散 11 / 云说 3 / 名句 8）。收录朱自清《背影》《荷塘月色》《春》《匆匆》、许地山《落花生》、鲁迅《孔乙己》《故乡》《一件小事》等完整正文；另含陋室铭、爱莲说、桃花源记、醉翁亭记、岳阳楼记及古典/现代公版诗与名句；每条含 `note` 典故说明。
- **原方案 → 新方案**：偏摘录、短条堆量 → 中学阅读体量的全文精选（约 25–40 篇质量优先）。
- **原因**：用户要求全文、禁「节选」、指定经典必须完整。

### 2026-09-14 — 空文件上传提示更清晰

- **做了什么**：附件列表显示文件大小；选中 0 字节文件时立刻提示；发布前拦截空附件；后端错误文案说明「请先保存再上传」。
- **原因**：用户选了 `落花解读.txt` 但被拒「空文件」——后端读到大小为 0，多半是磁盘上未保存内容的空文件；原先提示太简略。

### 2026-09-14 — 删除用户、评论回复、联系页、题材更名、扩充每日一阅

- **做了什么**：
  - 管理端「删除」永久移除用户及其作品/评论/动态/读书分享（已有 API，UI 确认后调用）。
  - 作品评论、云间、云友会支持楼中楼回复；`parent_id` 入库，回复人收到通知。
  - 新增 `/contact`：手机 17872364043、QQ 389176505、微信二维码 `public/wechat-qr.png`；顶栏「联系」、页脚入口。
  - 题材展示名：散文→云散、小说→云说、随笔→云笔、读友会→云友会（种子栏目 + 全站文案）。
  - 每日一阅词库扩至诗歌/云散/云说/名句约 60+ 条，含朱自清、沈从文、冰心、汪曾祺、梁实秋等现代文；页面展示「典故与背景」`note`；旧记录缺 note 时按标题回填。
- **原方案 → 新方案**：评论仅平铺 → 可回复并通知；每日一阅偏文言短库且无背景 → 题材均衡 + 典故说明；联系信息散落 → 独立联系页。
- **原因**：用户本轮明确要求。

### 2026-09-14 — 修复 api.js 括号导致 Vite 解析失败

- **做了什么**：`frontend/src/api.js` 中 `upload` 一行误写 `token})` 改为 `token)`。
- **原因**：Vite import-analysis 报 invalid JS syntax，页面红屏。

### 2026-09-14 — 管理端默认账号 Tan；顶栏露出资料/管理

- **做了什么**：创建管理员 `Tan`（密码已写入库，不记入日志明文用途外说明）；顶栏按钮顺序改为写一篇→资料→管理→名字→退出并允许换行；重建 frontend/backend；`ADMIN_USERNAME=Tan`。
- **原因**：用户看不到资料/管理入口；要求管理端默认账号为 Tan。


- **做了什么**：JWT `session_version` 单设备登录；评论回复写通知 + 顶栏红点；`/profile` 改资料与邮箱验证改密；每日一阅每小时随机并扩充词库；`/admin` 管理账号；`translate=no` 减轻浏览器「译/?」。
- **原方案 → 新方案**：每日一篇 → 每小时随机；可多端同登 → 新登录踢旧会话；无管理端 → 有管理端。
- **原因**：用户本轮明确要求。

### 2026-09-14 — 登录改为当前窗口有效

- **做了什么**：登录态从 `localStorage` 改为 `sessionStorage`，并清掉旧的本地记住登录。
- **原方案 → 新方案**：整个浏览器共用登录 → 每个窗口/标签页各自登录；同一标签刷新仍保持。
- **原因**：用户新开一个网页访问首页时，不想未登录就进入已登录状态。


- **做了什么**：在 `.env` 填入 QQ 邮箱与授权码（不记录授权码本身）；`docker compose up -d --force-recreate backend`。
- **原因**：用户要验证码真正发到邮箱。


- **做了什么**：在 `.env.example`、`USER_GUIDE.md` 写明授权码填法与 recreate backend。
- **原因**：用户已开启 SMTP，需要把授权码写入 `.env` 才能真正收到验证码。

### 2026-09-14 — 本地未配 SMTP 时在注册页显示验证码

- **做了什么**：`send-code` 在未配置 QQ 发信时返回 `dev_code`，注册页自动填入；已配 SMTP 则只发邮件、不回传验证码。
- **原方案 → 新方案**：只写后端日志 → 本地开发直接显示在页面。
- **原因**：用户点了获取验证码但邮箱收不到（`.env` 的 `SMTP_USER`/`SMTP_PASS` 为空，系统本来就不会发信）。

### 2026-09-14 — 再次修复 auth.js 的 api 导入路径

- **做了什么**：`frontend/src/stores/auth.js` 中 `import { api } from './api'` 改回 `'../api'`。
- **原方案 → 新方案**：同目录导入 → 上一级 `src/api.js`。
- **原因**：该文件又变回错误路径，Vite 红屏；`api.js` 不在 `stores/` 下。

### 2026-09-14 — 云间、每日一阅、读友会、附件上传

- **做了什么**：新增公开动态「云间」、按日轮换的「每日一阅」、读书分享「读友会」；散文/小说/诗歌/随笔及动态/读书会支持上传 Word、文本、PDF、图片、音视频；Docker 增加 `uploads` 卷；写面向开发的 `DEV_GUIDE.md`；更新 `USER_GUIDE.md`、`ReadMe.md`。
- **原方案 → 新方案**：
  - 站点只有四栏目发帖 → 增加广场型模块，避免只像投稿站。
  - 每日一阅本来可接大模型实时生成 → **改用古典诗文词库按日期取模写入数据库**。原因：本地无稳定 LLM 密钥，且要求「出处」必须准确，词库可核对来源；同一天全站同一篇。
  - 文件若只塞进 Postgres 字节 → **磁盘卷 + attachments 表**。原因：视频大会撑爆数据库。
  - 朋友圈若做好友关系/可见范围 → **不做分组，全站公开**。原因：用户明确要「所有人都是好友」、区别于微信朋友圈和 QQ 空间隐私。
- **原因**：用户要求扩充内容形态，并要开发者文档（启动、安全关闭、每个网址）。

### 2026-09-14 — 建立强制更新的开发日志

- **做了什么**：重写完整 `PROJECT_LOG.md`（此前文件被清空）；新增 Cursor 规则 `.cursor/rules/project-log.mdc`，要求后续改动必须追加履历；`ReadMe.md` 增加指向本日志的链接。  
- **原方案 → 新方案**：原先只打算写一份静态日志；因文件曾丢失且用户要求「后续操作都要写入」，改为「完整史 + 倒序履历 + 编辑器规则」。  
- **原因**：用户要非常详细的开发日志，并要求之后每次操作都记进去。

### 2026-09-14 — 用户名放宽与密码大小写；使用手册

- **做了什么**：放宽用户名校验；注册密码须大小写且≥8；写 `USER_GUIDE.md`；ReadMe 加链接。  
- **原方案 → 新方案**：用户名仅 `[A-Za-z0-9_]` → 允许中文与普通字母数字（如 TTTTTr）；密码仅长度 → 必须大小写混合。  
- **原因**：用户觉得用户名规则苛刻，并要求密码含大小写、要带全部网址说明的文档。

### 2026-09-14 — 修复 auth store 错误导入

- **做了什么**：`stores/auth.js` 的 `./api` 改为 `../api`。  
- **原方案 → 新方案**：相对同目录导入 → 指向上一级 `src/api.js`。  
- **原因**：Vite `import-analysis` 找不到模块，页面红屏。

### 2026-09-14 — MVP 从零搭建并本地跑通

- **做了什么**：Compose + FastAPI + Vue 文学站 MVP；验证码、帖子、评论。  
- **原方案 → 新方案**：方案阶段的 Jinja → Vue；Dockerfile 的 gcc/官方 PyPI → binary wheel + 清华镜像。  
- **原因**：用户选定 Vue；构建失败与过慢。
