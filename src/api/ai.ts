import request from '@/utils/request'
import { isMockEnabled } from '@/mock'
import {
  mockGenerateIntro,
  mockParsePdf,
  mockGenerateQuiz
} from '@/mock/ai'
import type { AxiosProgressEvent } from 'axios'

export function generateIntro(data: Record<string, unknown>) {
  if (isMockEnabled()) return mockGenerateIntro(data)
  return request({
    url: '/ai/generate-intro',
    method: 'post',
    data
  })
}

export function parsePdf(
  formData: FormData,
  onProgress?: (percent: number) => void
) {
  if (isMockEnabled()) return mockParsePdf(formData, onProgress)
  return request({
    url: '/ai/parse-pdf',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (event: AxiosProgressEvent) => {
      if (!event.total) return
      onProgress?.(Math.round((event.loaded * 100) / event.total))
    }
  })
}

export function generateQuiz(data: Record<string, unknown>) {
  if (isMockEnabled()) return mockGenerateQuiz(data)
  return request({
    url: '/ai/generate-quiz',
    method: 'post',
    data
  })
}
