import { resources, courses, nextResourceId } from './data'
import { ok, fail, paginate, delay } from './index'

function extType(name = '') {
  const ext = name.split('.').pop()?.toLowerCase()
  const map = {
    pdf: 'PDF',
    ppt: 'PPT',
    pptx: 'PPT',
    doc: 'Word',
    docx: 'Word',
    xls: 'Excel',
    xlsx: 'Excel',
    png: '图片',
    jpg: '图片',
    jpeg: '图片',
    mp4: '视频',
    mov: '视频'
  }
  return map[ext] || '其他'
}

function formatSize(size) {
  if (!size) return '0KB'
  if (size < 1024) return `${size}B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)}KB`
  return `${(size / 1024 / 1024).toFixed(1)}MB`
}

export function mockGetResourceList(params = {}) {
  let list = [...resources]
  if (params.name) {
    list = list.filter((item) => item.name.includes(params.name))
  }
  if (params.type) {
    list = list.filter((item) => item.type === params.type)
  }
  if (params.courseId) {
    list = list.filter((item) => String(item.courseId) === String(params.courseId))
  }
  return ok(paginate(list, params))
}

export function mockUploadResource(formData, onProgress) {
  const file = formData.get('file')
  const courseId = Number(formData.get('courseId'))
  const course = courses.find((c) => c.id === courseId)

  return new Promise((resolve) => {
    let progress = 0
    const timer = setInterval(() => {
      progress += 20
      onProgress?.(progress)
      if (progress >= 100) {
        clearInterval(timer)
        const item = {
          id: nextResourceId(),
          name: file?.name || `resource-${Date.now()}`,
          type: extType(file?.name),
          courseId: courseId || 0,
          courseName: course?.name || '未分配课程',
          size: formatSize(file?.size || 0),
          uploader: '当前用户',
          uploadedAt: new Date().toISOString().replace('T', ' ').slice(0, 16),
          status: 1
        }
        resources.unshift(item)
        resolve({ code: 0, data: item, message: 'ok' })
      }
    }, 200)
  })
}

export function mockDeleteResource(id) {
  const index = resources.findIndex((item) => item.id === Number(id))
  if (index < 0) return fail('资源不存在')
  resources.splice(index, 1)
  return ok(true)
}

export function mockUploadDelay() {
  return delay(null, 0)
}
