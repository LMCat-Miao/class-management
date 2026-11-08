# Backend · FastAPI + SQLAlchemy + MySQL

总览与前后端联调步骤见仓库根目录 [README.md](../README.md)。本文仅说明后端。

**当前状态**：登录、课程、教师、学生、选课、资源、Dashboard 等业务 API 均读写 **MySQL**。角色权限常量在 `app/core/permissions.py`。`app/data/store.py` 中的列表仅作历史演示常量 / `migrate_*` 数据源，**不是**运行时业务数据源；导入该模块不做密码哈希副作用。

## 架构

```text
app/
  main.py           # 应用入口、CORS、异常处理、路由注册；导入时校验生产 SECRET_KEY
  deps.py           # JWT 当前用户、角色依赖
  core/             # config（含 APP_ENV / SECRET_KEY 校验）、security、response
  db/               # Engine、Session、Base
  models/           # ORM：users, teachers, course_categories, courses,
                    #       students, enrollments, resources
  routers/          # HTTP 层
  services/         # 业务与查询
scripts/            # Seed、一次性迁移、冒烟测试
alembic/            # 结构迁移
uploads/            # 默认上传根目录（文件内容 gitignore）
```

## 配置

1. 复制环境变量模板：

```cmd
cd backend
copy .env.example .env
```

2. 编辑 `.env`（勿提交 Git）。字段以 `.env.example` 与 `app/core/config.py` 为准：

| 变量 | 说明 |
|------|------|
| `APP_ENV` | `development`（默认）或 `production` / `prod` |
| `DB_*` | MySQL 连接（`DB_HOST`/`DB_PORT`/`DB_USER`/`DB_PASSWORD`/`DB_NAME`） |
| `SECRET_KEY` | JWT 密钥；**生产必填且不能为开发默认值** |
| `UPLOAD_DIR` | 上传目录，默认 `uploads` |
| `UPLOAD_MAX_BYTES` | 资源上传单文件上限，默认 52428800（50MB） |
| `AI_PDF_MAX_BYTES` | AI PDF 解析内存上限，默认 10485760（10MB） |

### JWT / 生产安全

- 开发：可不设 `SECRET_KEY`，使用代码内开发默认值（仅限本地）。
- 生产：必须 `APP_ENV=production`（或 `prod`）且配置强随机 `SECRET_KEY`；缺失或仍为开发默认值时，**应用启动失败**。
- 不改变算法（HS256）与 Token 过期时间配置项含义。

生成示例（本地自行执行，勿把结果提交仓库）：

```cmd
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## 数据库

### 建库示例

```sql
CREATE DATABASE class_management
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

### 迁移（在 backend 目录、已激活 venv）

```cmd
python -m alembic upgrade head
```

回滚上一版（慎用）：

```cmd
python -m alembic downgrade -1
```

连接 URL 由 `alembic/env.py` 从 Settings / `.env` 注入，不要把真实密码写进 `alembic.ini`。

### Seed（幂等）

```cmd
python scripts\seed_data.py
```

- 已存在用户不覆盖密码；分类/教师按名跳过；课程仅在 `courses` 为空时插入。
- 不会 DROP 表或清空已有业务行。

可选：将历史内存演示学生/资源元数据导入（默认 dry-run，加 `--apply` 才写入）：

```cmd
python scripts\migrate_students_from_store.py
python scripts\migrate_students_from_store.py --apply
python scripts\migrate_resources_from_store.py
python scripts\migrate_resources_from_store.py --apply
```

## 启动（本地演示）

```cmd
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

也可执行：`scripts\start_backend.cmd`

- 健康检查：`GET /health` → http://127.0.0.1:8000/health
- OpenAPI：http://127.0.0.1:8000/docs
- 前端在仓库**根目录** `npm run dev`（默认 http://localhost:5173），需 `VITE_USE_MOCK=false`
- MySQL：**3306 / class_management**（勿连 3307 其他项目）
- 本仓库面向本地面试演示，**未包含公网部署**

## 上传目录与校验

- 默认：`backend/uploads`（相对启动时的工作目录，请在 `backend` 下启动）。
- 按课程 ID 分子目录；磁盘文件名使用 UUID；元数据在 `resources` 表。
- 扩展名白名单见 `app/services/resource_write.py` 中 `ALLOWED_EXT_MAP`。
- 上传还会校验文件实际内容（魔术字节 / OOXML / OLE），见 `app/services/file_content.py`；不信任客户端 Content-Type。
- 上传顺序：权限 → 临时文件 → 内容校验 → 原子落盘 → DB commit；DB 失败会删除刚落盘文件。
- 删除资源/课程：先提交 DB，再尽力清理磁盘；清理失败只记日志，**无后台重试**。

## 认证说明

- 仅签发 JWT `accessToken`（HS256），**不签发 refreshToken**，无自动刷新接口。
- teacher 必须关联启用中的教师档案（`teachers.status=1`）；停用后旧 Token 访问受保护接口返回 **403**，body 可含 `error=ACCOUNT_DISABLED`。
- `POST /logout`：客户端会话清理语义，服务端不撤销 JWT / 无黑名单。

## 主要路由（OpenAPI tags）

Swagger 分组：`auth` / `course` / `teacher` / `student` / `enrollment` / `resource` / `dashboard` / `ai`。

- `POST /login` · `GET /user/info` · `POST /logout`
- `GET /dashboard`
- `GET|POST|PUT|DELETE /course...` · `PUT /course/{id}/status`
- `GET|POST|PUT|DELETE /teacher...`
- `GET|POST|PUT /student...`
- `POST|GET|PUT /enrollment...`（仅 admin）
- `GET|POST|DELETE /resource...` · `GET /resource/{id}/download`
- `POST /ai/generate-intro` · `/ai/parse-pdf` · `/ai/generate-quiz`（模板生成；PDF 有大小与内容校验）

## 统一测试入口

```cmd
cd backend
.venv\Scripts\activate
python scripts\run_tests.py --list
python scripts\run_tests.py --safe
python scripts\run_tests.py --category security --include-db-write
python scripts\run_tests.py --category database --include-db-write
python scripts\run_tests.py --category file --include-db-write --include-restart
```

- 默认只跑非写库（配置 + 连接探测）。
- 写库测试须 `--include-db-write`；入口会校验目标为 `127.0.0.1:3306/class_management`。
- 不含 Seed / Alembic / `migrate_*`。

## 演示账号

- `admin` / `123456`
- `teacher` / `123456`

仅本地演示；生产必须改密。日常开发**不必**反复 Seed；仅空库初始化时执行一次即可。

## 生产注意

1. `APP_ENV=production` + 强随机 `SECRET_KEY`。
2. 使用强数据库密码；勿提交 `.env`。
3. 配置合适的 CORS / 反向代理 / HTTPS（本仓库未内置完整生产部署）。
4. 定期备份数据库；上传目录需纳入备份策略。
5. 文件删除失败目前仅记日志，无自动重试队列。
