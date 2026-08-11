import request from '@/utils/request'
import { isMockEnabled, mockGetCourseList } from '@/mock'

export function getCourseList(params) {
  if (isMockEnabled()) {
    return mockGetCourseList(params)
  }
  return request({
    url: '/course/list',
    method: 'GET',
    params
  })
}

export function getCourseDetail(id) {
  return request({
    url: `/course/${id}`,
    method: 'GET'
  })
}

export function createCourse(data) {
  return request({
    url: '/course',
    method: 'POST',
    data
  })
}

export function updateCourse(id, data) {
  return request({
    url: `/course/${id}`,
    method: 'PUT',
    data
  })
}

export function deleteCourse(id) {
  return request({
    url: `/course/${id}`,
    method: 'DELETE'
  })
}
