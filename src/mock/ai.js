import { ok, fail } from './index'

function randomDelay(min = 800, max = 1500) {
  return min + Math.floor(Math.random() * (max - min + 1))
}

export function mockGenerateIntro(data = {}) {
  const name = data.name?.trim()
  if (!name) return fail('请输入课程名称')

  const keywords = (data.keywords || []).filter(Boolean)
  const keywordText = keywords.length
    ? keywords.join('、')
    : '核心知识点与项目实践'
  const category = data.category || '专业'

  const intro = `本课程《${name}》面向${category}方向学习者，系统讲解${keywordText}等相关内容。课程强调理论与实践结合，通过案例演练帮助学员掌握关键技术要点，提升解决实际问题的能力，适合希望快速建立完整知识体系并落地应用的同学。`

  return ok({ intro }, 'ok').then((res) => {
    return new Promise((resolve) => {
      setTimeout(() => resolve(res), randomDelay())
    })
  })
}

export function mockParsePdf(formData, onProgress) {
  const file = formData.get('file')
  const courseName = formData.get('courseName') || ''

  if (!file) return fail('请上传 PDF 文件')

  const fileName = file.name || '课程资料.pdf'
  if (!/\.pdf$/i.test(fileName)) {
    return fail('仅支持 PDF 文件')
  }

  const topic = courseName || fileName.replace(/\.pdf$/i, '')

  return new Promise((resolve) => {
    let progress = 0
    const timer = setInterval(() => {
      progress += 25
      onProgress?.(Math.min(progress, 100))
      if (progress >= 100) {
        clearInterval(timer)
        setTimeout(() => {
          resolve({
            code: 0,
            message: 'ok',
            data: {
              fileName,
              summary: `已解析《${topic}》相关教学资料。文档围绕课程核心概念展开，涵盖基础理论、关键技术与实践案例，适合作为课堂教学与课后复习材料。`,
              knowledgePoints: [
                `${topic} 基础概念与发展背景`,
                '核心 API / 关键技术点',
                '常见业务场景与最佳实践',
                '项目实战与问题排查思路'
              ],
              chapters: [
                `第一章 ${topic} 导论`,
                '第二章 核心原理与基础用法',
                '第三章 进阶特性与工程化实践',
                '第四章 综合案例与总结'
              ],
              focus: [
                '掌握核心概念与基本用法',
                '理解常见业务场景下的选型思路',
                '能够独立完成中小型实践项目'
              ],
              difficulties: [
                '抽象概念理解与知识迁移',
                '工程化细节与性能优化',
                '复杂场景下的问题定位'
              ]
            }
          })
        }, randomDelay(600, 1000))
      }
    }, 180)
  })
}

export function mockGenerateQuiz(data = {}) {
  const courseName = data.courseName?.trim() || data.topic?.trim()
  if (!courseName) return fail('请选择课程或输入主题')

  const count = Math.min(Math.max(Number(data.count) || 3, 1), 5)
  const topic = data.topic?.trim() || courseName

  const choice = Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    type: 'choice',
    question: `关于「${topic}」，下列说法正确的是？（第 ${i + 1} 题）`,
    options: [
      'A. 只适用于理论学习，无法落地实践',
      'B. 需要结合具体业务场景理解与应用',
      'C. 与工程化无关，无需关注性能',
      'D. 以上都不对'
    ],
    answer: 'B'
  }))

  const judge = Array.from({ length: Math.max(2, count - 1) }, (_, i) => ({
    id: i + 1,
    type: 'judge',
    question: `「${topic}」相关知识点可以直接照搬到所有项目中，无需结合业务调整。（第 ${i + 1} 题）`,
    answer: false
  }))

  const short = Array.from({ length: Math.max(1, count - 2) }, (_, i) => ({
    id: i + 1,
    type: 'short',
    question: `请简述「${topic}」中的一个核心概念，并说明其在实际项目中的应用场景。（第 ${i + 1} 题）`,
    answer: `建议从概念定义、适用场景、注意事项三方面作答，并结合《${courseName}》课程内容举例说明。`
  }))

  return ok({ choice, judge, short }).then((res) => {
    return new Promise((resolve) => {
      setTimeout(() => resolve(res), randomDelay())
    })
  })
}
