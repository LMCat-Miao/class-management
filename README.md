# AI 课程管理平台

面向课程与教学管理场景的前后端分离系统，提供课程、教师、学生、选课关系、教学资源与数据看板等能力。后端业务数据持久化到 MySQL；前端可切换 Mock 或真实 API。

> AI 相关接口当前为模板生成，**不是**真实大模型调用。

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Vue 3、TypeScript、Pinia、Vue Router、Axios、Element Plus、ECharts、Vite |
| 后端 | FastAPI、SQLAlchemy 2.0、MySQL、Alembic、JWT（HS256）、bcrypt、Uvicorn |
| 数据 | MySQL（Alembic 管理表结构）；正式业务接口读写数据库，不以内存 store 为数据源 |

## 核心功能

- JWT 登录认证（仅 accessToken；登出为客户端会话清理，服务端不撤销 JWT；teacher 停用后旧 Token 访问受保护接口返回 403）
- admin / teacher 角色权限与课程资源归属控制
- 课程 CRUD、上下架、分页与筛选
- 教师管理（CRUD，有课程关联时禁止删除）
- 学生管理（CRUD；教师仅能查看本人课程下已选课学生）
- 选课关系（`/enrollment`，仅 admin；管理端学生详情可分配/退选/恢复）
- 资源上传、下载、删除（文件落盘至 `backend/uploads`；扩展名白名单 + 内容校验；单文件默认 ≤50MB）
- Dashboard 统计（课程/教师/学生总量等为 MySQL 聚合；趋势图仍为演示硬编码）
- Alembic 迁移与幂等 Seed
- 前端 `VITE_USE_MOCK` 切换 Mock / 真实后端

## 项目架构

```text
class_management/
├── src/                      # Vue 前端
│   ├── api/                  # 接口门面（可切 Mock）
│   ├── mock/                 # 前端 Mock（VITE_USE_MOCK=true）
│   ├── stores/               # Pinia
│   ├── router/               # 路由
│   ├── views/                # 页面
│   ├── components/           # 组件
│   └── utils/                # 请求封装等
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── routers/          # HTTP 路由
│   │   ├── services/         # 业务逻辑
│   │   ├── models/           # SQLAlchemy ORM
│   │   ├── core/             # 配置、JWT、统一响应
│   │   ├── db/               # Engine / Session
│   │   ├── core/permissions.py  # 角色权限码常量
│   │   └── data/store.py        # 历史演示常量（仅 migrate_*；非运行时业务源）
│   ├── scripts/              # Seed、迁移脚本、统一测试入口 run_tests.py
│   ├── alembic/              # 数据库迁移
│   ├── uploads/              # 上传文件目录（默认，已 gitignore 内容）
│   ├── .env.example
│   └── requirements.txt
├── package.json
└── README.md
```

更细的后端说明见 [backend/README.md](backend/README.md)。

## 数据库设计

业务表（MySQL + Alembic）：

| 表 | 说明 |
|----|------|
| `users` | 登录账号（role：admin / teacher） |
| `teachers` | 教师档案；`user_id` → `users.id`（可空） |
| `course_categories` | 课程分类 |
| `courses` | 课程；`teacher_id` → `teachers.id`，`category_id` → `course_categories.id` |
| `students` | 学生 |
| `enrollments` | 选课；关联 `students` 与 `courses`（课程删除受选课 RESTRICT 约束） |
| `resources` | 资源元数据；关联 `courses`；文件二进制不入库 |

## 本地开发（Windows CMD）

### 1. 前端依赖

在项目根目录：

```cmd
npm install
```

### 2. 后端虚拟环境

```cmd
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 数据库准备

1. 安装并启动 MySQL（本项目使用端口 **3306**，库名 `class_management`；与其他占用 3307 的项目无关）。
2. 创建数据库（示例，按本机账号调整）：

```sql
CREATE DATABASE class_management
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

3. 配置环境变量：

```cmd
cd backend
copy .env.example .env
```

编辑 `.env`：至少填写 `DB_PASSWORD`。本地开发可保持 `APP_ENV=development`。**不要把 `.env` 提交到 Git。**

4. 执行迁移（在 `backend` 目录、已激活 venv）：

```cmd
python -m alembic upgrade head
```

5. 初始化演示数据（幂等，可重复执行；不会 DROP 表）：

```cmd
python scripts\seed_data.py
```

### 4. 环境变量说明

以 `backend/.env.example` 与 `app/core/config.py` 为准：

| 变量 | 必填 | 说明 |
|------|------|------|
| `APP_ENV` | 否（默认 `development`） | `development` 本地；`production` / `prod` 生产 |
| `DB_HOST` | 否（默认 `127.0.0.1`） | MySQL 主机 |
| `DB_PORT` | 否（默认 `3306`） | MySQL 端口 |
| `DB_USER` | 否（默认 `root`） | 数据库用户 |
| `DB_PASSWORD` | **本地建议必填** | 数据库密码（勿写入文档或 Git） |
| `DB_NAME` | 否（默认 `class_management`） | 库名 |
| `SECRET_KEY` | 生产 **必填** | JWT 签名密钥；生产禁止使用开发默认值 |
| `UPLOAD_DIR` | 否（默认 `uploads`） | 上传根目录（相对 backend 工作目录） |
| `UPLOAD_MAX_BYTES` | 否（默认 50MB） | 资源上传单文件上限（字节） |
| `AI_PDF_MAX_BYTES` | 否（默认 10MB） | AI PDF 解析读入内存上限 |

前端（根目录 `.env.development` / `.env.example`）：

| 变量 | 说明 |
|------|------|
| `VITE_API_URL` | 后端地址，如 `http://127.0.0.1:8000` |
| `VITE_USE_MOCK` | `true` 仅前端 Mock；`false` 走真实 API |

生产环境必须设置 `APP_ENV=production` 与强随机 `SECRET_KEY`，否则应用**拒绝启动**。

### 5. 启动（Windows 本地演示）

> **当前交付形态为本地演示**，未做公网 / Docker / CI/CD 部署。前端位于**仓库根目录**（没有单独的 `frontend/` 子目录）。

**终端 1 · 后端**（`backend` 目录，已激活 `.venv`）：

```cmd
cd /d D:\project\class_management\class_management\backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

或双击 / 执行：`backend\scripts\start_backend.cmd`

- 健康检查：http://127.0.0.1:8000/health
- Swagger：http://127.0.0.1:8000/docs

**终端 2 · 前端**（仓库根目录）：

```cmd
cd /d D:\project\class_management\class_management
npm run dev
```

或执行：`scripts\start_frontend.cmd`

浏览器打开 http://localhost:5173 。确认根目录 `.env.development` 中：

- `VITE_API_URL=http://127.0.0.1:8000`
- `VITE_USE_MOCK=false`（走真实后端）

数据库须为 **127.0.0.1:3306 / class_management**（勿连其他项目的 3307）。

## 演示账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | 123456 | 管理员 |
| teacher | 123456 | 教师（张老师档案） |

**仅用于本地演示。** 公开或生产部署前必须修改密码，不要把弱口令当作生产账号。启动脚本中不写入密码。

### 建议演示路径（面试）

1. admin 登录 → Dashboard 卡片与课程列表（MySQL 聚合）。
2. 课程 CRUD / 上下架；教师管理（有课不可删）。
3. 学生详情 → **选课管理**（分配 / 退选 / 恢复；仅 admin）。
4. 资源上传 / 下载 / 删除；教师仅能操作本人课程资源。
5. 教师账号登录 → 验证只能看到本人课程与学生。
6. AI 助手：说明为**模板生成**；PDF 解析侧重上传校验，**不是完整 RAG**。

## 测试说明

在 `backend` 目录、激活 venv 后使用统一入口：

```cmd
python scripts\run_tests.py --list
python scripts\run_tests.py --safe
python scripts\run_tests.py --category database --include-db-write
python scripts\run_tests.py --category api --include-db-write
python scripts\run_tests.py --category file --include-db-write
python scripts\run_tests.py --category file --include-db-write --include-restart
```

- 默认 / `--safe`：仅配置校验与只读连接探测（不写库）。
- 写库冒烟须显式 `--include-db-write`（独立测试数据 + cleanup，仍勿对生产库执行）。
- 临时拉起 **8765** 端口 uvicorn 的重启测试另需 `--include-restart`（不占用 8000）。
- **不要**把 `seed_data.py`、Alembic、`migrate_* --apply` 当作日常测试；空库初始化才需要 Seed。

前端（仓库根目录）：

```cmd
npm run typecheck
npm run build
```

## 当前限制（如实边界）

- **未完成公网部署**；本仓库面向本机面试演示。
- Dashboard 的 `studentTrend` / 部分趋势仍为演示硬编码，非真实按月统计。
- AI 接口为模板生成，不是真实大模型；`/ai/parse-pdf` 主要完成大小与 PDF 内容校验，**不能描述为已实现 RAG / 向量检索**。
- 资源/课程删除后若磁盘清理失败，依赖日志排查，**无后台重试队列**。
- 无 Docker / CI/CD / 生产监控内置方案。
- `POST /logout` 为客户端会话清理语义，不使 JWT 在服务端即时失效；无 refresh 换发接口。

## 接口约定

- 成功：`{ "code": 0, "data": ..., "message": "ok" }`
- 失败：HTTP status 表达协议语义；`body.code` 与 status 对齐；可选 `error`（如 `ACCOUNT_DISABLED`）
- 登录：`POST /login` → `accessToken` + `userInfo`（不返回 refreshToken）
- 鉴权头：`Authorization: Bearer <accessToken>`
