import {
  courses,
  resources,
  nextCourseId,
  teachers
} from './data'
import { ok, fail, paginate } from './index'

function enrichCourse(course) {
  const teacher = teachers.find((t) => t.id === course.teacherId)
  return {
    ...course,
    teacher: teacher?.name || course.teacher || ''
  }
}

export function mockGetCourseList(params = {}) {
  let list = courses.map(enrichCourse)

  if (params.name) {
    list = list.filter((item) => item.name.includes(params.name))
  }
  if (params.category) {
    list = list.filter((item) => item.category === params.category)
  }
  if (params.teacher) {
    list = list.filter((item) => item.teacher.includes(params.teacher))
  }
  if (params.status !== undefined && params.status !== '') {
    list = list.filter((item) => String(item.status) === String(params.status))
  }
  if (params.startDate) {
    list = list.filter((item) => item.createdAt >= params.startDate)
  }
  if (params.endDate) {
    list = list.filter((item) => item.createdAt <= params.endDate)
  }

  return ok(paginate(list, params))
}

export function mockGetCourseDetail(id) {
  const course = courses.find((item) => item.id === Number(id))
  if (!course) return fail('课程不存在')

  const relatedResources = resources.filter((r) => r.courseId === course.id)
  return ok({
    ...enrichCourse(course),
    resources: relatedResources
  })
}

export function mockCreateCourse(data) {
  const teacher = teachers.find((t) => t.id === Number(data.teacherId))
  const item = {
    id: nextCourseId(),
    name: data.name,
    cover: data.cover || 'https://picsum.photos/seed/newcourse/160/90',
    category: data.category,
    teacherId: Number(data.teacherId) || teacher?.id || 1,
    teacher: teacher?.name || data.teacher || '',
    difficulty: data.difficulty || '初级',
    duration: Number(data.duration) || 0,
    studentCount: 0,
    learnCount: 0,
    completionRate: 0,
    status: Number(data.status ?? 1),
    intro: data.intro || '',
    createdAt: new Date().toISOString().slice(0, 10),
    chapters: data.chapters || [{ id: 1, title: '第一章 课程导论' }]
  }
  courses.unshift(item)
  return ok(item)
}

export function mockUpdateCourse(id, data) {
  const index = courses.findIndex((item) => item.id === Number(id))
  if (index < 0) return fail('课程不存在')
  const teacher = teachers.find((t) => t.id === Number(data.teacherId))
  courses[index] = {
    ...courses[index],
    ...data,
    id: courses[index].id,
    teacherId: Number(data.teacherId) || courses[index].teacherId,
    teacher: teacher?.name || data.teacher || courses[index].teacher
  }
  return ok(enrichCourse(courses[index]))
}

export function mockDeleteCourse(id) {
  const index = courses.findIndex((item) => item.id === Number(id))
  if (index < 0) return fail('课程不存在')
  courses.splice(index, 1)
  return ok(true)
}

export function mockUpdateCourseStatus(id, status) {
  const course = courses.find((item) => item.id === Number(id))
  if (!course) return fail('课程不存在')
  course.status = Number(status)
  return ok(enrichCourse(course))
}
