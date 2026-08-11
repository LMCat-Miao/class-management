import request from '@/utils/request'
import { isMockEnabled } from '@/mock'
import {
  mockGetTeacherList,
  mockGetTeacherDetail,
  mockCreateTeacher,
  mockUpdateTeacher,
  mockDeleteTeacher
} from '@/mock/teacher'

export function getTeacherList(params) {
  if (isMockEnabled()) return mockGetTeacherList(params)
  return request({ url: '/teacher/list', method: 'get', params })
}

export function getTeacherDetail(id) {
  if (isMockEnabled()) return mockGetTeacherDetail(id)
  return request({ url: `/teacher/${id}`, method: 'get' })
}

export function createTeacher(data) {
  if (isMockEnabled()) return mockCreateTeacher(data)
  return request({ url: '/teacher', method: 'post', data })
}

export function updateTeacher(id, data) {
  if (isMockEnabled()) return mockUpdateTeacher(id, data)
  return request({ url: `/teacher/${id}`, method: 'put', data })
}

export function deleteTeacher(id) {
  if (isMockEnabled()) return mockDeleteTeacher(id)
  return request({ url: `/teacher/${id}`, method: 'delete' })
}
