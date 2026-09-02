import request from '@/utils/request'
import { isMockEnabled } from '@/mock'
import {
  mockGetStudentList,
  mockGetStudentDetail,
  mockUpdateStudent,
  mockUpdateStudentStatus,
  mockCreateStudent
} from '@/mock/student'

export function getStudentList(params?: Record<string, unknown>) {
  if (isMockEnabled()) return mockGetStudentList(params)
  return request({ url: '/student/list', method: 'get', params })
}

export function getStudentDetail(id: number | string) {
  if (isMockEnabled()) return mockGetStudentDetail(id)
  return request({ url: `/student/${id}`, method: 'get' })
}

export function createStudent(data: Record<string, unknown>) {
  if (isMockEnabled()) return mockCreateStudent(data)
  return request({ url: '/student', method: 'post', data })
}

export function updateStudent(id: number | string, data: Record<string, unknown>) {
  if (isMockEnabled()) return mockUpdateStudent(id, data)
  return request({ url: `/student/${id}`, method: 'put', data })
}

export function updateStudentStatus(id: number | string, status: number) {
  if (isMockEnabled()) return mockUpdateStudentStatus(id, status)
  return request({
    url: `/student/${id}/status`,
    method: 'put',
    data: { status }
  })
}
