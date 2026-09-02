import request from '@/utils/request'
import { isMockEnabled } from '@/mock'
import { mockGetDashboardData } from '@/mock/dashboard'

export function getDashboardData() {
  if (isMockEnabled()) return mockGetDashboardData()
  return request({
    url: '/dashboard',
    method: 'get'
  })
}
