import request from '@/utils/request'
import { isMockEnabled } from '@/mock'
import {
  mockGetCourseList,
  mockGetCourseDetail,
  mockCreateCourse,
  mockUpdateCourse,
  mockDeleteCourse,
  mockUpdateCourseStatus
} from '@/mock/course'

export function getCourseList(params?: Record<string, unknown>) {
  if (isMockEnabled()) return mockGetCourseList(params)
  return request({ url: '/course/list', method: 'get', params })
}

export function getCourseDetail(id: number | string) {
  if (isMockEnabled()) return mockGetCourseDetail(id)
  return request({ url: `/course/${id}`, method: 'get' })
}

export function createCourse(data: Record<string, unknown>) {
  if (isMockEnabled()) return mockCreateCourse(data)
  return request({ url: '/course', method: 'post', data })
}

export function updateCourse(id: number | string, data: Record<string, unknown>) {
  if (isMockEnabled()) return mockUpdateCourse(id, data)
  return request({ url: `/course/${id}`, method: 'put', data })
}

export function deleteCourse(id: number | string) {
  if (isMockEnabled()) return mockDeleteCourse(id)
  return request({ url: `/course/${id}`, method: 'delete' })
}

export function updateCourseStatus(id: number | string, status: number) {
  if (isMockEnabled()) return mockUpdateCourseStatus(id, status)
  return request({
    url: `/course/${id}/status`,
    method: 'put',
    data: { status }
  })
}
