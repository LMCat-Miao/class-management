import { students, nextStudentId } from './data'
import { ok, fail, paginate } from './index'

export function mockGetStudentList(params = {}) {
  let list = [...students]
  if (params.name) {
    list = list.filter((item) => item.name.includes(params.name))
  }
  if (params.studentNo) {
    list = list.filter((item) => item.studentNo.includes(params.studentNo))
  }
  if (params.className) {
    list = list.filter((item) => item.className.includes(params.className))
  }
  if (params.status !== undefined && params.status !== '') {
    list = list.filter((item) => String(item.status) === String(params.status))
  }
  return ok(paginate(list, params))
}

export function mockGetStudentDetail(id) {
  const student = students.find((item) => item.id === Number(id))
  if (!student) return fail('学生不存在')
  return ok({ ...student })
}

export function mockUpdateStudent(id, data) {
  const index = students.findIndex((item) => item.id === Number(id))
  if (index < 0) return fail('学生不存在')
  students[index] = { ...students[index], ...data, id: students[index].id }
  return ok(students[index])
}

export function mockUpdateStudentStatus(id, status) {
  const student = students.find((item) => item.id === Number(id))
  if (!student) return fail('学生不存在')
  student.status = Number(status)
  return ok(student)
}

export function mockCreateStudent(data) {
  const item = {
    id: nextStudentId(),
    name: data.name,
    avatar: data.avatar || '',
    studentNo: data.studentNo,
    className: data.className || '',
    phone: data.phone || '',
    learnCourseCount: 0,
    finishCourseCount: 0,
    progress: 0,
    status: Number(data.status ?? 1),
    registeredAt: new Date().toISOString().slice(0, 10),
    recentCourses: [],
    avgCompletion: 0
  }
  students.unshift(item)
  return ok(item)
}
