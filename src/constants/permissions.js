export const PERMISSIONS = {
  // course
  COURSE_VIEW: 'course:view',
  COURSE_ADD: 'course:add',
  COURSE_EDIT: 'course:edit',
  COURSE_DELETE: 'course:delete',
  COURSE_PUBLISH: 'course:publish',
  // teacher
  TEACHER_VIEW: 'teacher:view',
  TEACHER_ADD: 'teacher:add',
  TEACHER_EDIT: 'teacher:edit',
  TEACHER_DELETE: 'teacher:delete',
  // student
  STUDENT_VIEW: 'student:view',
  STUDENT_EDIT: 'student:edit',
  STUDENT_STATUS: 'student:status',
  // resource
  RESOURCE_VIEW: 'resource:view',
  RESOURCE_UPLOAD: 'resource:upload',
  RESOURCE_DELETE: 'resource:delete',
  // dashboard
  DASHBOARD_VIEW: 'dashboard:view'
}

export const ADMIN_PERMISSIONS = Object.values(PERMISSIONS)

export const TEACHER_PERMISSIONS = [
  PERMISSIONS.DASHBOARD_VIEW,
  PERMISSIONS.COURSE_VIEW,
  PERMISSIONS.STUDENT_VIEW,
  PERMISSIONS.STUDENT_EDIT,
  PERMISSIONS.RESOURCE_VIEW,
  PERMISSIONS.RESOURCE_UPLOAD
]
