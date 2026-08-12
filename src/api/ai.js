import request from '@/utils/request'
import { isMockEnabled } from '@/mock'
import {
  mockGenerateIntro,
  mockParsePdf,
  mockGenerateQuiz
} from '@/mock/ai'

export function generateIntro(data) {
  if (isMockEnabled()) return mockGenerateIntro(data)
  return request({
    url: '/ai/generate-intro',
    method: 'post',
    data
  })
}

export function parsePdf(formData, onProgress) {
  if (isMockEnabled()) return mockParsePdf(formData, onProgress)
  return request({
    url: '/ai/parse-pdf',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (event) => {
      if (!event.total) return
      onProgress?.(Math.round((event.loaded * 100) / event.total))
    }
  })
}

export function generateQuiz(data) {
  if (isMockEnabled()) return mockGenerateQuiz(data)
  return request({
    url: '/ai/generate-quiz',
    method: 'post',
    data
  })
}
