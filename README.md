# AI 课程管理平台

Vue 3 + TypeScript 前端管理端，搭配 FastAPI + JWT 后端。

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Vue 3、TypeScript、Pinia、Vue Router、Axios、Element Plus、ECharts、Vite |
| 后端 | FastAPI、JWT（python-jose）、Passlib/Bcrypt、Uvicorn |
| 数据 | 开发期内存数据（与原 Mock 对齐），响应约定 `{ code, data, message }` |

## 目录

```text
├── src/                 # Vue 前端
│   ├── api/             # 接口门面（可切 Mock / 真后端）
│   ├── mock/            # 前端 Mock（VITE_USE_MOCK=true）
│   ├── stores/          # Pinia
│   ├── router/          # 静态 + 动态路由
│   └── ...
└── backend/             # FastAPI
    ├── app/main.py
    ├── app/routers/     # auth / course / teacher / ...
    └── requirements.txt
```

## 快速开始

### 1. 安装前端依赖

```bash
npm install
```

### 2. 安装并启动后端

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API 文档：http://127.0.0.1:8000/docs

### 3. 启动前端

保持根目录 `.env.development`：

```env
VITE_API_URL=http://127.0.0.1:8000
VITE_USE_MOCK=false
```

```bash
npm run dev
```

浏览器打开 Vite 提示的本地地址（默认 http://localhost:5173）。

### 演示账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | 123456 | 管理员 |
| teacher | 123456 | 教师（仅自己的课程） |

## 仅前端 Mock 模式

不启后端时：

```env
VITE_USE_MOCK=true
```

然后 `npm run dev`，任意流程走 `src/mock/*`。

## 常用脚本

```bash
npm run dev         # 前端开发
npm run typecheck   # TypeScript 检查
npm run build       # 类型检查 + 生产构建
npm run preview     # 预览构建产物
```

## 接口约定

- 成功：`{ "code": 0, "data": ..., "message": "ok" }`
- 登录：`POST /login` → `accessToken` + `refreshToken` + `userInfo`
- 鉴权头：`Authorization: Bearer <accessToken>`
- 用户信息：`GET /user/info`

## 说明

- 前端核心层（constants / utils / api / stores / router / permission）已迁到 TypeScript；页面 `.vue` 仍可渐进改为 `lang="ts"`。
- 后端当前为内存存储，重启后写入数据会丢失，适合联调与演示；后续可换 SQLAlchemy / 数据库。
- AI 接口目前为模板生成，非真实大模型。
