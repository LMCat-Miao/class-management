import { courses, teachers, students } from './data'
import { ok } from './index'

export function mockGetDashboardData() {
  const months = [
    '1月', '2月', '3月', '4月', '5月', '6月',
    '7月', '8月', '9月', '10月', '11月', '12月'
  ]

  const categoryMap = {}
  courses.forEach((c) => {
    categoryMap[c.category] = (categoryMap[c.category] || 0) + 1
  })

  const hotCourses = [...courses]
    .sort((a, b) => b.learnCount - a.learnCount)
    .slice(0, 5)
    .map((c) => ({ name: c.name, value: c.learnCount }))

  const avgCompletion = Math.round(
    courses.reduce((sum, c) => sum + c.completionRate, 0) / courses.length
  )

  return ok({
    cards: {
      courseTotal: courses.length,
      teacherTotal: teachers.length,
      studentTotal: 5200,
      learnTotal: courses.reduce((sum, c) => sum + c.learnCount, 0)
    },
    courseTrend: {
      months,
      values: [8, 12, 18, 25, 32, 40, 52, 66, 78, 90, 108, courses.length + 120]
    },
    studentTrend: {
      months,
      values: [120, 160, 210, 280, 350, 420, 510, 600, 720, 830, 950, 1100]
    },
    categoryPie: Object.entries(categoryMap).map(([name, value]) => ({
      name,
      value
    })),
    hotCourses,
    completionRate: avgCompletion
  })
}
