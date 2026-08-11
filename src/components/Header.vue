<template>
  <div class="header">
    <h2>AI课程管理平台</h2>
    <div class="header-right">
      <span>{{ userStore.nickname }}</span>
      <el-tag size="small" type="info">{{ roleLabel }}</el-tag>
      <el-button type="primary" link @click="logout">退出登录</el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'
import { usePermissionStore } from '@/stores/permission'
import { useRouter } from 'vue-router'
import { resetRouter } from '@/router'
import { ROLE_LABELS } from '@/constants/roles'

const userStore = useUserStore()
const permissionStore = usePermissionStore()
const router = useRouter()

const roleLabel = computed(() => {
  const role = userStore.roles[0]
  return ROLE_LABELS[role] || role || '用户'
})

const logout = async () => {
  await userStore.logout()
  permissionStore.reset()
  resetRouter()
  router.push('/login')
}
</script>

<style scoped>
.header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid #ebeef5;
  background: #fff;
}

.header h2 {
  margin: 0;
  font-size: 18px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
