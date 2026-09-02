import request from '@/utils/request'
import { isMockEnabled } from '@/mock'
import {
  mockGetResourceList,
  mockUploadResource,
  mockDeleteResource
} from '@/mock/resource'
import type { AxiosProgressEvent } from 'axios'

export function getResourceList(params?: Record<string, unknown>) {
  if (isMockEnabled()) return mockGetResourceList(params)
  return request({ url: '/resource/list', method: 'get', params })
}

export function uploadResource(
  formData: FormData,
  onProgress?: (percent: number) => void
) {
  if (isMockEnabled()) return mockUploadResource(formData, onProgress)
  return request({
    url: '/resource/upload',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (event: AxiosProgressEvent) => {
      if (!event.total) return
      const percent = Math.round((event.loaded * 100) / event.total)
      onProgress?.(percent)
    }
  })
}

export function deleteResource(id: number | string) {
  if (isMockEnabled()) return mockDeleteResource(id)
  return request({ url: `/resource/${id}`, method: 'delete' })
}
