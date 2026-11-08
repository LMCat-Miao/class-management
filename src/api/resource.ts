import axios from 'axios'
import request from '@/utils/request'
import { isMockEnabled } from '@/mock'
import {
  mockGetResourceList,
  mockUploadResource,
  mockDeleteResource
} from '@/mock/resource'
import { getToken, clearAuth } from '@/utils/auth'
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

function parseContentDisposition(header?: string): string {
  if (!header) return ''
  const star = /filename\*\s*=\s*UTF-8''([^;]+)/i.exec(header)
  if (star?.[1]) {
    try {
      return decodeURIComponent(star[1].trim().replace(/"/g, ''))
    } catch {
      return star[1].trim().replace(/"/g, '')
    }
  }
  const quoted = /filename\s*=\s*"([^"]+)"/i.exec(header)
  if (quoted?.[1]) return quoted[1]
  const plain = /filename\s*=\s*([^;]+)/i.exec(header)
  return plain?.[1]?.trim().replace(/"/g, '') || ''
}

function triggerBlobDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename || 'download'
  a.style.display = 'none'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/**
 * 资源下载：二进制 Blob，不走 JSON 响应拦截器。
 * 文件名优先取 Content-Disposition（含 filename* UTF-8）。
 */
export async function downloadResource(id: number | string): Promise<void> {
  if (isMockEnabled()) {
    throw new Error('Mock 模式不支持真实文件下载')
  }

  const token = getToken()
  const baseURL = import.meta.env.VITE_API_URL

  try {
    const res = await axios.get(`${baseURL}/resource/${id}/download`, {
      responseType: 'blob',
      timeout: 60000,
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })

    const ctype = String(res.headers['content-type'] || '')
    // 少数网关可能用 200 + JSON 错误体
    if (ctype.includes('application/json')) {
      const text = await (res.data as Blob).text()
      let message = '下载失败'
      try {
        const body = JSON.parse(text) as { message?: string }
        message = body.message || message
      } catch {
        /* ignore */
      }
      throw new Error(message)
    }

    const filename =
      parseContentDisposition(res.headers['content-disposition']) || `resource-${id}`
    triggerBlobDownload(res.data as Blob, filename)
  } catch (err: unknown) {
    if (axios.isAxiosError(err) && err.response?.data instanceof Blob) {
      const status = err.response.status
      let message = '下载失败'
      let errorCode = ''
      try {
        const body = JSON.parse(await err.response.data.text()) as {
          message?: string
          error?: string
        }
        message = body.message || message
        errorCode = body.error || ''
      } catch {
        /* ignore */
      }
      if (status === 401 || (status === 403 && errorCode === 'ACCOUNT_DISABLED')) {
        clearAuth()
        Promise.all([
          import('@/stores/user'),
          import('@/stores/permission'),
          import('@/router')
        ]).then(([{ useUserStore }, { usePermissionStore }, routerMod]) => {
          useUserStore().reset()
          usePermissionStore().reset()
          const router = routerMod.default
          if (router.currentRoute.value.path !== '/login') {
            router.push('/login')
          }
        })
      }
      throw new Error(message)
    }
    if (err instanceof Error) throw err
    throw new Error('下载失败')
  }
}
