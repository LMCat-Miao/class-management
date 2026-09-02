export const ROLES = {
  ADMIN: 'admin',
  TEACHER: 'teacher'
} as const

export type Role = (typeof ROLES)[keyof typeof ROLES]

export const ROLE_LABELS: Record<Role, string> = {
  [ROLES.ADMIN]: '管理员',
  [ROLES.TEACHER]: '教师'
}
