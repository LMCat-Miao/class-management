export const PERMISSIONS = {
  COURSE_VIEW: 'course:view',
  COURSE_ADD: 'course:add',
  COURSE_EDIT: 'course:edit',
  COURSE_DELETE: 'course:delete',
  COURSE_PUBLISH: 'course:publish',
  TEACHER_VIEW: 'teacher:view',
  TEACHER_ADD: 'teacher:add',
  TEACHER_EDIT: 'teacher:edit',
  TEACHER_DELETE: 'teacher:delete',
  STUDENT_VIEW: 'student:view',
  STUDENT_EDIT: 'student:edit',
  STUDENT_STATUS: 'student:status',
  RESOURCE_VIEW: 'resource:view',
  RESOURCE_UPLOAD: 'resource:upload',
  RESOURCE_DELETE: 'resource:delete',
  DASHBOARD_VIEW: 'dashboard:view',
  AI_INTRO: 'ai:intro',
  AI_PARSE: 'ai:parse',
  AI_QUIZ: 'ai:quiz'
} as const

export type Permission = (typeof PERMISSIONS)[keyof typeof PERMISSIONS]

export const ADMIN_PERMISSIONS: Permission[] = Object.values(PERMISSIONS)

export const TEACHER_PERMISSIONS: Permission[] = [
  PERMISSIONS.DASHBOARD_VIEW,
  PERMISSIONS.COURSE_VIEW,
  PERMISSIONS.STUDENT_VIEW,
  PERMISSIONS.STUDENT_EDIT,
  PERMISSIONS.RESOURCE_VIEW,
  PERMISSIONS.RESOURCE_UPLOAD,
  PERMISSIONS.AI_INTRO,
  PERMISSIONS.AI_PARSE,
  PERMISSIONS.AI_QUIZ
]
