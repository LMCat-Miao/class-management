"""
角色权限码常量（响应层组装 userInfo.permissions，不入库）。

正式 API 从此模块读取；勿再依赖 app.data.store 中的业务内存列表。
"""

ADMIN_PERMISSIONS = [
    "course:view",
    "course:add",
    "course:edit",
    "course:delete",
    "course:publish",
    "teacher:view",
    "teacher:add",
    "teacher:edit",
    "teacher:delete",
    "student:view",
    "student:edit",
    "student:status",
    "resource:view",
    "resource:upload",
    "resource:delete",
    "dashboard:view",
    "ai:intro",
    "ai:parse",
    "ai:quiz",
]

TEACHER_PERMISSIONS = [
    "dashboard:view",
    "course:view",
    "student:view",
    "student:edit",
    "resource:view",
    "resource:upload",
    "ai:intro",
    "ai:parse",
    "ai:quiz",
]
