import request from '@/utils/request'

/** 为学生创建选课（admin） */
export function createEnrollment(data: { studentId: number; courseId: number }) {
  return request({ url: '/enrollment', method: 'post', data })
}

/** 某学生的选课列表（admin） */
export function getEnrollmentsByStudent(studentId: number | string) {
  return request({ url: `/enrollment/student/${studentId}`, method: 'get' })
}

/** 某课程的选课列表（admin） */
export function getEnrollmentsByCourse(courseId: number | string) {
  return request({ url: `/enrollment/course/${courseId}`, method: 'get' })
}

/** 退选（status→0，admin） */
export function dropEnrollment(enrollmentId: number | string) {
  return request({ url: `/enrollment/${enrollmentId}/drop`, method: 'put' })
}

/** 更新选课状态（admin） */
export function updateEnrollmentStatus(enrollmentId: number | string, status: number) {
  return request({
    url: `/enrollment/${enrollmentId}/status`,
    method: 'put',
    data: { status }
  })
}
