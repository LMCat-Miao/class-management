# AI 课程管理平台 · 前端校招源码审查报告

> 审查依据：仓库当前真实代码（截至审查日），不以 README / 目录名推测未实现功能。  
> 审查范围：`src/**` 前端、`backend/app/**` FastAPI 后端、根配置与 README。  
> 审查性质：只读分析；本报告为唯一新增产出文件。

---

## 1. 项目整体架构

### 1.1 架构结论

本项目是 **前后端分离的中后台管理系统**：

| 层 | 技术 | 职责 |
|----|------|------|
| 前端 | Vue 3 + TypeScript（核心层）+ Pinia + Vue Router + Axios + Element Plus + ECharts + Vite | 登录鉴权 UI、动态菜单/路由、CRUD 页面、图表看板、AI 助手交互 |
| 后端 | FastAPI + JWT（python-jose）+ Passlib/Bcrypt + 内存列表 | 登录发 Token、业务 CRUD、角色校验、统一 `{ code, data, message }` 响应 |
| 数据 | **无数据库**；`backend/app/data/store.py` 与 `src/mock/data.js` 各持一份内存种子数据 | 进程内可变；**重启后端 / 刷新 Mock 模块后写入丢失** |

通信方式：

- 默认开发配置（`.env.development`）：`VITE_USE_MOCK=false`，`VITE_API_URL=http://127.0.0.1:8000`，Axios 直连 FastAPI。
- `vite.config.ts` 另提供 `/api` → `8000` 的代理（当前 `baseURL` 并未走 `/api`，代理为可选备用）。
- Mock 模式：`VITE_USE_MOCK=true` 时，`src/api/*.ts` 在函数入口分支到 `src/mock/*`，**页面不直接调 Mock**。

### 1.2 前端目录组织

```text
src/
  api/           # 接口门面（Mock / 真后端切换）
  mock/          # 前端 Mock（与后端数据对齐的种子）
  stores/        # user / permission
  router/        # constantRoutes + asyncRoutes
  permission/    # 全局 beforeEach 守卫
  directives/    # v-permission
  constants/     # roles / permissions / ai
  utils/         # request（Axios）、auth（Token）
  types/         # ApiResult、UserInfo、RouteMeta
  layouts/       # Layout
  components/    # Header / Sidebar / BaseTable
  views/         # Dashboard / Course / Teacher / Student / Resource / AiAssistant / Login
```

组织方式接近典型「中后台脚手架」：**按技术分层 + 按业务分 views**，合理。

### 1.3 API / Store / Router / Permission / Mock 关系

```text
Login.vue
  → userStore.login() → api/user.login → (Mock | Axios /login)
  → 写 sessionStorage access/refresh token + userStore.setProfile
  → permissionStore.reset() → router.push('/dashboard')

permission/index.ts beforeEach
  → 有 token 且 !isRoutesAdded
  → userStore.getUser()（必要时）
  → permissionStore.generateRoutes(roles) 过滤 asyncRoutes + addRoute + 生成 menus
  → 再导航目标页

页面
  → api/* → request 拦截器带 Bearer
  → 后端 get_current_user / require_roles
  → 或 Mock 直接返回同形 { code, data, message }

按钮
  → v-permission 读 userStore.permissions 决定是否移除 DOM
```

### 1.4 数据流转（登录后列表示例）

1. 用户持 `sessionStorage.access_token`。
2. 页面调用 `getCourseList(queryParams)`（`src/api/course.ts`）。
3. 非 Mock：`request` 请求拦截器 `Authorization: Bearer …`（`src/utils/request.ts`）。
4. 后端 `list_courses` 按角色过滤教师课程后分页（`backend/app/routers/course.py`）。
5. 响应拦截器校验 `code === 0 | 200`，返回整包 `ApiResult`；页面取 `res.data.list / total`。

### 1.5 模块合理性与耦合

**较合理：**

- API 门面与页面解耦；Mock 切换集中在 api 层。
- 路由表 `meta.roles / meta.menu` 驱动菜单与动态注册。
- 权限常量前后端权限码列表基本对齐（`src/constants/permissions.ts` ↔ `store.py`）。

**耦合 / 问题：**

- `permission` Store 直接 `import router` 并 `addRoute`，与路由模块双向依赖。
- 业务列表页（Course / Teacher / Student / Resource）搜索 + 分页 + 表格样板高度重复，未抽 composable。
- 前端按钮权限码与后端 `require_roles` **不是同一套机制**（见第 3、6 节）。
- `pinia-plugin-persistedstate` 已安装并 `pinia.use(persist)`，但 **任何 Store 均未配置 persist**，属无效接入。

---

## 2. 前端模块分析

### 2.1 Vue 3 与 TypeScript

| 检查项 | 结论 | 证据 |
|--------|------|------|
| Composition API | **是**，页面均为 `<script setup>` | 如 `Login.vue`、`Course/index.vue`、`Dashboard/index.vue` |
| ref / reactive / computed / watch | 使用合理，列表多用 `reactive(queryParams)` + `ref(list)` | Course / Student 等 |
| 组件职责过重 | 列表页偏「页面级全能」（搜+表+分页+弹窗），但单文件体量尚可；Dashboard 图表逻辑集中但可接受 | — |
| TS 真正约束 | **核心层有 TS**（stores / router / api / utils / types）；**全部 `.vue` 均无 `lang="ts"`**（全库检索无匹配） | README 所述「渐进」属实 |
| any / 断言 | 未见大量 `any`；API 大量 `Record<string, unknown>` + `as Promise<ApiResult<…>>`，业务实体类型缺失 | `src/api/course.ts` 等 |

**完成程度：** Vue3 Composition 实践完整；TS 对「接口门面与状态」有约束，对「页面与业务模型」约束不足。

### 2.2 Pinia 状态管理

**Store 清单（仅 2 个）：**

| Store | 文件 | 管理内容 |
|-------|------|----------|
| `user` | `src/stores/user.ts` | `userInfo` / `roles` / `permissions`；`login` / `getUser` / `logout` / `setProfile` |
| `permission` | `src/stores/permission.ts` | `menus` / `routes` / `isRoutesAdded`；`generateRoutes` / `reset` |

组织方式：Options Store（`state` + `getters` + `actions`）。

Store 依赖：

- `user` → `api/user`、`utils/auth`
- `permission` → `router`、`asyncRoutes`、`ROLES`
- 守卫与 Header 同时使用两者

登录状态维护：

- Token：`sessionStorage` 的 `access_token` / `refresh_token`（`src/utils/auth.ts`）
- 用户资料：Pinia 内存；**无 persist**
- 刷新恢复：有 token → 守卫调 `getUser()` 拉 `/user/info` → 再动态加路由

注意：`auth.ts` 模块加载时会 **清空 localStorage 中旧 token 键**（迁移防护），正式存储改用 sessionStorage → **关标签即掉登录态**。

`refreshToken`：登录时写入（`userStore.login`），但 **全前端无读取刷新逻辑**（`getRefreshToken` 未被业务调用）。

状态重复：`userInfo.role` 与 `roles[]`、`permissions` 同时存在；`setProfile` 做了归一化，尚可。菜单标题取 `roles[0]`（`buildMenus`），多角色场景会不准（当前演示仅单角色）。

### 2.3 Vue Router

| 项 | 实现 |
|----|------|
| 静态路由 | `constantRoutes`：`/login`、`Root(/ → /login)`（`src/router/routes.ts`） |
| 动态路由 | `asyncRoutes`：Layout 子路由 + 通配 NotFound→dashboard；登录后 `addRoute` |
| 守卫 | `src/permission/index.ts`：`beforeEach` |
| 未登录 | 非白名单 → `/login` |
| 已登录访问 login | → `/dashboard` |
| 用户信息 | 无 userInfo 时 `getUser()` |
| 退出清理 | `Header.vue`：`logout` + `permissionStore.reset` + `resetRouter` + 跳转 login |

风险点：

- `generateRoutes` 先 `removeRoute('Root')` 再挂 Layout；靠 `isRoutesAdded` 防重复。逻辑可用，但与 `resetRouter` 白名单（仅 Login/Root）需配合，退出路径正确。
- 通配 `NotFound` 一律 redirect `/dashboard`，无 404 页。
- **路由层按角色过滤菜单**；未再按 `permissions` 细粒度过滤路由。
- 教师仍可注册 `/course/:id`，后端详情接口 **不校验是否本人课程**（见后端节）→ 知道 ID 可越权查看。

### 2.4 Axios 封装（`src/utils/request.ts`）

| 项 | 实现 |
|----|------|
| 实例 | `axios.create` |
| baseURL | `import.meta.env.VITE_API_URL` |
| timeout | 15000 |
| 请求拦截 | 附加 `Bearer ${getToken()}` |
| 响应拦截（2xx） | 有 `code` 字段则要求 `0` 或 `200`，否则 `reject(Error(message))`；否则原样返回 |
| HTTP 错误 | 取 `error.response.data.message`；**仅特殊处理 401**：`clearAuth` + 跳转 login |
| 403 / 500 | **无统一专门分支**，仅通用 reject |
| Token 刷新 | **无**；无请求队列、无防重复刷新 |
| 重复请求取消 | **无** |

### 2.5 权限管理

**设计：RBAC（角色）+ 前端权限码（按钮）双轨。**

角色（`src/constants/roles.ts`）：`admin` / `teacher`。

权限码（`src/constants/permissions.ts`）：

- 管理员：全部 `PERMISSIONS`
- 教师：看板、课程查看、学生查看/编辑、资源查看/上传、AI 三项；**无** 课程增删改发布、教师管理、学生停用、资源删除

菜单 / 路由：

- `meta.roles` 过滤（教师无 Teacher 菜单与路由）
- 教师课程菜单标题「我的课程」（`menuTitle`）

按钮：

- `v-permission` 指令（`src/directives/permission.ts`）在 `mounted` 时无权限则 `removeChild`

前后端一致性：

| 能力 | 前端教师 | 后端 |
|------|----------|------|
| 课程列表仅自己 | UI 依赖接口；**Mock 不过滤** | `list_courses` 按 `teacherId` 过滤 |
| 课程增删改/上下架 | 按钮隐藏 | `require_roles("admin")` |
| 课程详情任意 ID | 可进路由 | **仅登录校验，无归属校验** |
| 教师管理 | 无路由 | 全 admin |
| 学生停用 | 无 `student:status` 按钮 | **任意登录用户可调** `PUT /student/{id}/status` |
| 资源删除 | 按钮隐藏 | admin |
| 资源列表 | 可见全部（前端） | **不过滤教师** |

结论：**不能写「前后端权限完全一致」**；前端隐藏 ≠ 后端强制。教师管理、课程写操作后端较严；学生状态、课程详情、资源列表存在缺口。

### 2.6 API 与 Mock

- 组织：按领域拆分 `user/course/teacher/student/resource/dashboard/ai`。
- 切换：`isMockEnabled()` ← `VITE_USE_MOCK === 'true'`（`src/mock/index.js`）。
- 返回形状：Mock `ok()` 与后端 `ok()` 均为 `{ code: 0, data, message }`，列表均为 `{ list, total, page, pageSize }`，整体对齐。
- 不一致点：
  1. **Mock 登录**：非 `teacher` 的任意用户名会落到管理员权限（`src/mock/auth.js`）；真后端仅 `admin`/`teacher`。
  2. **Mock 课程列表**无教师数据隔离；真后端有。
  3. Dashboard `studentTotal`：Mock 写死 `5200`；后端 `max(5200, len(STUDENTS))`，趋势序列多为硬编码。

### 2.7 页面与组件

| 页面/组件 | 完成度 | 说明 |
|-----------|--------|------|
| Layout / Header / Sidebar | 完整 | 顶栏用户信息+退出；侧栏读 `permissionStore.menus` |
| Login | 完整 | 表单登录、演示账号填充、Mock/后端文案区分；**无表单 rules 组件级校验** |
| Dashboard | 完整（演示数据） | 4 卡片 + 5 图；接口驱动 |
| 课程列表/详情/表单 | 完整 CRUD（管理员） | 教师只读列表+详情；表单内可调 AI 生成简介 |
| 教师管理 | 完整（仅 admin） | 列表/详情/表单 |
| 学生管理 | 完整 CRUD + 状态 | 教师可编辑但前端无停用按钮 |
| 教学资源 | 列表/上传/删除 | 上传只存元数据；原生 `<input type="file">` |
| AI 助手 | 三 Tab 完整交互 | 模板生成，非真实大模型（与 README 一致） |
| BaseTable | 可用 | 列配置 + 具名插槽 + actions 插槽 |

重复代码：四套「queryParams + getList + 分页 + BaseTable」几乎同构。

### 2.8 ECharts（`src/views/Dashboard/index.vue`）

| 项 | 结论 |
|----|------|
| 初始化 | `echarts.init` + `setOption`，实例推进 `charts[]` |
| 数据 | `getDashboardData()` → `res.data` |
| 生命周期 | `onMounted` 加载；`onBeforeUnmount` `dispose` + 移除 resize |
| 窗口变化 | `window.resize` → `chart.resize()` |
| 泄漏风险 | 当前只 mount 一次渲染，风险低；若将来多次 `renderCharts` 而不先 dispose，会叠加实例（`charts` 只增不减） |

---

## 3. 后端模块分析

### 3.1 结构

```text
backend/app/
  main.py          # FastAPI、CORS、异常处理、挂载路由
  deps.py          # get_current_user、require_roles
  core/            # config、security、response
  data/store.py    # 内存数据 + 用户哈希
  routers/         # auth、dashboard、course、teacher、student、resource、ai
```

无 SQLAlchemy / Redis / 文件落盘。**数据仅在进程内存。**

### 3.2 认证与 JWT

- 登录：`POST /login`（`auth.py`）校验 `USERS` + `verify_password`，签发：
  - access：`type=access`，默认 120 分钟（`config.py`）
  - refresh：`type=refresh`，默认 7 天
- 鉴权：`HTTPBearer` → `decode_token` → 要求 `type == access` → 查 `USERS`
- **无** `/refresh` 接口；refresh 仅生成与返回，**无法续期**
- 登出：`POST /logout` 需登录，**服务端无 Token 黑名单**（无状态 JWT 惯例）
- 密码：bcrypt 哈希，演示账号 `123456`（启动时 `hash_password`）
- `secret_key` 硬编码在 `config.py`（开发向）

### 3.3 业务接口与权限（摘要）

| 模块 | 鉴权要点 |
|------|----------|
| course list | 登录；教师按 `teacherId` 过滤 |
| course detail | 仅登录，**无归属** |
| course 写/状态 | admin |
| teacher * | admin |
| student * | 任意登录用户（含 status） |
| resource list/upload | 登录；list **无教师过滤**；delete admin |
| dashboard / ai | 登录；AI 为字符串模板 |
| resource upload | `file.read()` 后只记 size/元数据，**不保存文件内容** |

### 3.4 校验与异常

- 入参：Pydantic `BaseModel`（LoginBody、CourseBody 等）
- `RequestValidationError` → 422 + `errors`
- `HTTPException` → `{ code: status, data: null, message }`
- 业务失败多用 `fail()` 返回非 2xx JSONResponse

### 3.5 数据隔离结论

- **不同登录用户共享同一份内存列表**（非多租户）。
- 教师与管理员的差异主要靠：课程列表过滤 + 部分 `require_roles("admin")`。
- **服务重启后所有增删改丢失**，回到种子数据。

---

## 4. 核心业务流程（真实代码）

### 4.1 登录 → 进首页

1. `Login.vue` `handleLogin` → `userStore.login`
2. 存 Token + `setProfile(userInfo)` + `sessionStorage.mock_username`
3. `permissionStore.reset()`（清动态路由标记）
4. `router.push('/dashboard')`
5. 守卫发现 token 且 `!isRoutesAdded` →（已有 userInfo 则跳过 getUser）→ `generateRoutes` → `addRoute` → `return { ...to, replace: true }`

### 4.2 管理员课程 CRUD

列表筛选分页 → 弹窗 `CourseForm` 调教师列表 → create/update → 列表刷新；上下架 `updateCourseStatus`；删除确认框。

### 4.3 教师「我的课程」

真后端：列表被 `teacherId` 过滤；无新增/编辑/删除/上下架按钮。  
Mock：列表仍为全量（与 README「仅自己的课程」不完全一致）。

### 4.4 AI 简介应用到课程

`IntroGenerator` 写入 `sessionStorage[AI_INTRO_DRAFT_KEY]` → 跳转 `/course?openCreate=1` → `Course/index` 打开表单 → `CourseForm.applyAiDraft` 回填。

---

## 5. 已真实实现的功能清单

- [x] 账号密码登录（Mock / FastAPI 双模式）
- [x] JWT Access 鉴权（真后端）+ 前端 Bearer 注入
- [x] 登录态路由守卫、动态路由、按角色菜单
- [x] 退出登录清理 Store / 路由 / Token
- [x] 按钮级 `v-permission`
- [x] Dashboard 卡片 + ECharts（折线/面积/饼/柱/仪表盘）+ resize/dispose
- [x] 课程列表筛选（名称/分类/教师/状态/日期）分页、详情、管理员 CRUD 与上下架
- [x] 教师列表筛选分页、详情、CRUD（admin）
- [x] 学生列表筛选分页、详情、新增/编辑/状态切换（状态按钮仅 admin 权限码）
- [x] 教学资源列表筛选、上传进度回调、删除（删除按钮仅 admin）
- [x] AI：生成简介、伪 PDF 解析、生成练习题（模板）
- [x] AI 简介跨页应用到「新增课程」
- [x] 统一响应约定与 CORS、健康检查 `/health`
- [x] 密码 bcrypt、角色依赖注入

---

## 6. 未实现或仅部分实现的功能清单

| 项 | 状态 | 说明 |
|----|------|------|
| 真实大模型 / PDF 语义解析 | 未实现 | 模板拼接；README 已声明 |
| 数据库持久化 | 未实现 | 内存；重启丢失 |
| Refresh Token 续期 | **仅半实现** | 有签发与前端存储，无刷新接口与拦截器逻辑 |
| Pinia 持久化 | **未生效** | 插件接入但 Store 未开 persist |
| 页面级 TypeScript | 未完成 | 无 `lang="ts"` 的 vue |
| 业务实体完整类型 | 弱 | API 多用 `Record` |
| 文件真实存储 / 下载 | 未实现 | 只存元数据 |
| Token 刷新队列 / 防重复请求 | 未实现 | — |
| 细粒度后端 permission 码校验 | 未实现 | 仅 role |
| 教师课程详情 / 资源 / 学生数据隔离 | 部分 | 列表有、详情与资源等不足 |
| Mock 与真后端行为完全一致 | 否 | 登录兜底 admin、课程不过滤 |
| 404 页、单元测试、E2E | 未见 | — |
| 生产级密钥与环境配置 | 弱 | 默认 secret |

### README 与代码差异

| README 表述 | 代码实际 |
|-------------|----------|
| JWT Access + Refresh | Access 可用；Refresh **未形成闭环** |
| 教师仅自己的课程 | **真后端列表成立**；Mock 列表不成立；详情两侧均可越权 ID 访问 |
| 核心层已迁 TS，页面可渐进 | 属实：页面仍为 JS script setup |
| AI 为模板非真模型 | 属实 |
| 内存存储重启丢失 | 属实 |
| 技术栈含 pinia-plugin-persistedstate | 依赖存在但 **未真正持久化任何状态** |

---

## 7. 真实技术亮点（建议写进简历的 7 个）

> 下列均有代码支撑；不含「真实 AI / 高并发 / 数据库优化」等不可证实表述。

### 7.1 静态路由 + 动态路由的 RBAC 接入

**1. 业务背景：** 管理员与教师菜单与可访页面不同，刷新后需恢复可访问路由。  
**2. 技术方案：** `constantRoutes` 保登录页；业务路由放 `asyncRoutes`，按 `meta.roles` 过滤后 `addRoute`。  
**3. 具体实现：** `src/router/routes.ts`；`stores/permission.ts` 的 `filterAsyncRoutes` / `generateRoutes` / `buildMenus`；`src/permission/index.ts` 守卫。  
**4. 解决的问题：** 未登录不可进业务页；教师看不到教师管理；刷新可重建路由。  
**5. 技术价值：** 体现中后台权限路由工程能力。  
**6. 面试追问：** 为何不一次注册全部路由只用钩子拦截？`isRoutesAdded` 如何防死循环？退出如何避免残留路由？

### 7.2 角色菜单 + 权限码按钮的双层前端权限

**1. 业务背景：** 同页教师只读、管理员可写。  
**2. 技术方案：** 路由/菜单按角色；操作按钮按 `permissions` + 自定义指令。  
**3. 具体实现：** `constants/permissions.ts`；`userStore.hasPermission`；`directives/permission.ts`；Course 页 `v-permission="'course:add'"` 等。  
**4. 解决的问题：** UI 层按能力显隐，减少误操作。  
**5. 技术价值：** 理解「展示权限」与「接口权限」分层（面试需主动讲清后端仍要以 role 兜底）。  
**6. 面试追问：** 只藏按钮能否防越权？指令为何只用 `mounted`？权限变更如何更新 DOM？

### 7.3 API 门面统一 Mock / 真后端切换

**1. 业务背景：** 无后端时也能演示全流程。  
**2. 技术方案：** 环境变量开关；api 层分支，页面无感知。  
**3. 具体实现：** `src/mock/index.js` 的 `isMockEnabled`；各 `src/api/*.ts`；`.env.development`。  
**4. 解决的问题：** 前后端并行、纯前端演示。  
**5. 技术价值：** 接口抽象与环境配置意识。  
**6. 面试追问：** 如何保证 Mock 与后端契约一致？为何不用 MSW / vite-plugin-mock？

### 7.4 Axios 实例与统一业务码处理

**1. 业务背景：** 多接口需统一带 Token、统一错误形态。  
**2. 技术方案：** 单例 Axios + 双拦截器；约定 `code`。  
**3. 具体实现：** `src/utils/request.ts`；`types/api.ts` 的 `ApiResult`。  
**4. 解决的问题：** 调用方少写样板；401 清登录态。  
**5. 技术价值：** 前端网络层基础工程化。  
**6. 面试追问：** 为何成功拦截器返回整个 `body` 而非 `data`？401 与业务 `code!==0` 区别？如何做无感刷新？

### 7.5 Pinia 拆分用户态与权限态并串起登录闭环

**1. 业务背景：** Token、资料、菜单、路由标记职责不同。  
**2. 技术方案：** `user` + `permission` 两 Store，由守卫编排。  
**3. 具体实现：** `stores/user.ts`、`stores/permission.ts`、`permission/index.ts`、`Header.vue` 退出。  
**4. 解决的问题：** 登录/刷新/退出状态一致（在现有设计下可用）。  
**5. 技术价值：** 全局状态边界划分。  
**6. 面试追问：** 为何 userInfo 不 persist？Token 为何放 sessionStorage？与 Cookie HttpOnly 对比？

### 7.6 ECharts 与 Vue 生命周期、resize、销毁

**1. 业务背景：** 看板多图，路由切换易泄漏。  
**2. 技术方案：** 本地 `charts` 数组 + `resize` 监听 + `dispose`。  
**3. 具体实现：** `views/Dashboard/index.vue` 的 `createChart` / `handleResize` / `onBeforeUnmount`。  
**4. 解决的问题：** 基本避免监听与实例残留。  
**5. 技术价值：** 第三方命令式库与声明式框架的衔接。  
**6. 面试追问：** 为何不封装成 Chart 组件？`requestAnimationFrame` 作用？多次拉数如何防重复 init？

### 7.7 AI 结果跨页面回填的轻量业务串联

**1. 业务背景：** 助手页生成简介后要进入课程新建表单。  
**2. 技术方案：** `sessionStorage` 草稿 + 路由 query 打开弹窗。  
**3. 具体实现：** `constants/ai.ts`；`IntroGenerator.applyToCourse`；`Course/index.tryOpenCreateFromAi`；`CourseForm.applyAiDraft`。  
**4. 解决的问题：** 跨路由传递一次性表单草稿。  
**5. 技术价值：** 简单但完整的产品链路思维（非炫技）。  
**6. 面试追问：** 为何不用 Pinia？多标签页冲突？如何做成可测试的服务？

---

## 8. P0 / P1 / P2 问题清单

### P0（安全或核心语义风险）

1. **Refresh Token 名存实亡**  
   后端签发、前端存储，但无刷新 API、拦截器也不使用 → 简历若写「双 Token 无感续期」属不实。  
   位置：`security.py` `create_refresh_token`；`user.ts` `setRefreshToken`；全库无 refresh 消费。

2. **教师可越权读任意课程详情**  
   `GET /course/{id}` 仅 `get_current_user`，无 `teacherId` 校验（`course.py` `course_detail`）。前端路由也对教师开放。

3. **学生状态接口后端未按角色收紧**  
   前端隐藏停用按钮，但教师 Token 可直接调 `PUT /student/{id}/status`（`student.py`）。

4. **Mock 登录权限兜底为管理员**  
   `mock/auth.js`：非 teacher 用户名复制 admin 权限 → 演示环境可「任意账号变管理员」。

5. **JWT `secret_key` 硬编码**（若对外演示需知情）  
   `backend/app/core/config.py`。

### P1（质量 / 完整性 / 可靠性）

1. Mock 与真后端教师课程列表行为不一致（`mock/course.js` vs `course.py`）。  
2. 资源列表无教师范围过滤；上传不落盘文件。  
3. Dashboard 趋势与 `studentTotal` 含硬编码演示数，非真实统计。  
4. `pinia-plugin-persistedstate` 未使用，易造成「做了持久化」的误解。  
5. Vue 页面无 TS；API 缺少 Course/Teacher 等实体类型。  
6. 401 外错误处理粗糙；无 403 友好提示分流。  
7. `v-permission` 仅 `mounted`，权限异步变更不更新。  
8. AI / PDF 能力若简历夸大易被追问穿帮（代码为模板）。

### P2（工程优化）

1. 列表页搜索分页逻辑重复，可抽 `usePagedList`。  
2. 上传交互可用 `el-upload` 统一。  
3. Dashboard 多次 `renderCharts` 需先清空实例。  
4. NotFound 应独立 404 而非回首页。  
5. `getRefreshToken` 等死代码应删除或补齐刷新链路。  
6. `permission` Store 与 router 循环依赖可改为纯函数 + 守卫编排。  
7. 前端 `fail` 业务码与 HTTP status 混用时的调用方体验可再统一。

---

## 9. 优化建议及优先级

| 优先级 | 建议 | 预期收益 |
|--------|------|----------|
| 高 | 补齐或删除 Refresh：要么实现 `/refresh` + 队列刷新，要么简历与 README 去掉「双 Token 续期」表述 | 避免面试翻车 |
| 高 | 后端：课程详情 / 资源列表按教师归属过滤；学生写/状态 `require_roles` 与前端权限对齐 | 权限故事自洽 |
| 高 | Mock 登录去掉「任意用户→admin」；课程列表按 `mock_username`/`teacherId` 过滤 | 双模式行为一致 |
| 中 | 为 Course/Teacher/Student/Resource 补类型；关键页面加 `lang="ts"` | 体现 TS 深度 |
| 中 | 抽列表 composable；Chart 封装组件 | 降重复、好讲重构 |
| 中 | 去掉未用 persist 插件，或真正 persist 非敏感 UI 偏好 | 依赖诚实 |
| 低 | 文件存储、真 AI、数据库 | 加分项，非校招前端必需 |

**当前最值得优先改进的三个方向：**

1. **把权限故事讲圆**：前后端角色/数据隔离一致，不夸大 Token 刷新。  
2. **补齐 TypeScript 与业务模型类型**，让「Vue3 + TS」经得起看代码。  
3. **收敛 Mock/真后端差异**，并诚实包装 AI（业务串联亮点保留，不说大模型）。

---

## 10. 前端校招面试高频追问清单

### 项目与架构

1. 画一下从登录到看到「我的课程」的完整时序。  
2. Mock 和真后端怎么切？页面为什么不能直接 import mock？  
3. 动态路由怎么加？刷新为什么不会丢？会不会重复 `addRoute`？  
4. 管理员和教师权限差在哪？前端藏按钮后端拦了吗？（结合具体接口回答）

### Vue / Pinia / Router

5. 为什么用两个 Store 而不是一个？  
6. `isRoutesAdded` 解决什么问题？和导航死循环的关系？  
7. `resetRouter` 白名单为什么只留 Login/Root？  
8. Composition API 在列表页怎么组织状态？有没有过重组件？

### 网络与鉴权

9. 请求/响应拦截器分别做了什么？  
10. Access / Refresh 在你项目里各自走到哪一步？过期了会发生什么？  
11. Token 放 sessionStorage 的优劣 vs localStorage vs HttpOnly Cookie？  
12. 401 时为什么动态 `import('@/router')`？

### 权限

13. `v-permission` 实现原理？和 `v-if="hasPermission"` 对比？  
14. 路由 `meta.roles` 和 `permissions` 码如何分工？  
15. 如果老师直接请求 `DELETE /course/1` 结果是什么？

### ECharts / 工程

16. 图表如何避免内存泄漏？  
17. 为什么 `vue-tsc` 进 build 脚本？页面没写 TS 时检查覆盖哪些？  
18. AI 简介是怎么「应用到课程」的？有哪些边界情况？

### 后端联动（常被问到）

19. 数据存在哪？重启会怎样？  
20. 密码怎么存？JWT payload 有什么？为什么校验 `type==access`？  
21. AI 接口是不是调了 OpenAI？如果不是，你如何在简历里写？

---

## 11. 客观水平评价（校招视角）

### 总体判断

这是一个 **完成度较好的 Vue3 中后台练手项目**：具备登录鉴权、动态路由、角色菜单、按钮权限、CRUD 模块、图表看板、前后端联调与 Mock 切换，代码结构清晰，**足以支撑前端实习 / 校招项目深挖**，前提是表述诚实、能讲清边界。

它 **不是** 生产级系统：无数据库、无真实 AI、Refresh 未闭环、权限后端未完全对齐、TS 未贯彻到页面。

### 水平档位（主观但基于代码）

| 维度 | 档位 |
|------|------|
| 作为校招「主项目」叙事完整度 | 中上 |
| 工程化（分层、约定、双端） | 中上 |
| 业务复杂度 / 创新深度 | 中 |
| 安全与权限严谨度 | 中偏下（有明显可追问漏洞） |
| TypeScript 深度 | 中偏下（核心有、页面无） |

### 面试策略建议

- **主打：** 动态路由 + RBAC、API 门面 Mock 切换、Axios 封装、Pinia 登录闭环、ECharts 生命周期、AI 草稿跨页串联。  
- **主动披露：** AI 是模板；数据内存；Refresh 只做到签发；部分接口教师仍可越权 → 反而显得可复盘。  
- **不要写：** 微服务、真实大模型落地、高并发、双 Token 无感刷新、Pinia 持久化已完成、复杂性能优化指标。

### 结论一句话

**可以拿去打前端校招，但竞争力取决于你是否把「权限与鉴权链路」讲透，以及是否在面试前修掉最容易被拆穿的不一致（Refresh、Mock/后端差异、越权接口）。优先改进方向见第 9 节三条。**

---

## 附录：关键文件索引

| 主题 | 路径 |
|------|------|
| 入口 | `src/main.ts` |
| Axios | `src/utils/request.ts` |
| Token | `src/utils/auth.ts` |
| 用户 Store | `src/stores/user.ts` |
| 权限 Store | `src/stores/permission.ts` |
| 路由表 | `src/router/routes.ts` |
| 守卫 | `src/permission/index.ts` |
| 权限指令 | `src/directives/permission.ts` |
| 权限常量 | `src/constants/permissions.ts` |
| Dashboard / ECharts | `src/views/Dashboard/index.vue` |
| 后端入口 | `backend/app/main.py` |
| JWT | `backend/app/core/security.py` |
| 依赖注入 | `backend/app/deps.py` |
| 内存数据 | `backend/app/data/store.py` |
| 课程权限 | `backend/app/routers/course.py` |

---

*报告结束。*
