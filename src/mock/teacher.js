import { teachers, courses, nextTeacherId } from './data'
import { ok, fail, paginate } from './index'

function enrichTeacher(teacher) {
  const related = courses.filter((c) => c.teacherId === teacher.id)
  return {
    ...teacher,
    courseCount: related.length,
    courses: related.map((c) => ({
      id: c.id,
      name: c.name,
      studentCount: c.studentCount,
      completionRate: c.completionRate
    })),
    studentCount:
      related.reduce((sum, c) => sum + c.studentCount, 0) || teacher.studentCount,
    avgCompletion: related.length
      ? Math.round(
          related.reduce((sum, c) => sum + c.completionRate, 0) / related.length
        )
      : teacher.avgCompletion
  }
}

export function mockGetTeacherList(params = {}) {
  let list = teachers.map(enrichTeacher)
  if (params.name) {
    list = list.filter((item) => item.name.includes(params.name))
  }
  if (params.status !== undefined && params.status !== '') {
    list = list.filter((item) => String(item.status) === String(params.status))
  }
  return ok(paginate(list, params))
}

export function mockGetTeacherDetail(id) {
  const teacher = teachers.find((item) => item.id === Number(id))
  if (!teacher) return fail('教师不存在')
  return ok(enrichTeacher(teacher))
}

export function mockCreateTeacher(data) {
  const item = {
    id: nextTeacherId(),
    name: data.name,
    avatar: data.avatar || '',
    phone: data.phone || '',
    email: data.email || '',
    title: data.title || '讲师',
    courseCount: 0,
    studentCount: 0,
    avgCompletion: 0,
    status: Number(data.status ?? 1),
    courseIds: []
  }
  teachers.unshift(item)
  return ok(item)
}

export function mockUpdateTeacher(id, data) {
  const index = teachers.findIndex((item) => item.id === Number(id))
  if (index < 0) return fail('教师不存在')
  teachers[index] = { ...teachers[index], ...data, id: teachers[index].id }
  return ok(enrichTeacher(teachers[index]))
}

export function mockDeleteTeacher(id) {
  const index = teachers.findIndex((item) => item.id === Number(id))
  if (index < 0) return fail('教师不存在')
  teachers.splice(index, 1)
  return ok(true)
}
