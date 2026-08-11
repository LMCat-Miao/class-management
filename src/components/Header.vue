<template>
  <div class="header">
    <h2>AI课程管理平台</h2>
    <div class="header-right">
      <span>{{ userStore.userInfo?.username || '用户' }}</span>
      <el-button type="primary" link @click="logout">退出登录</el-button>
    </div>
  </div>
</template>

<script setup>
import { useUserStore } from '@/stores/user.js'
import { useRouter } from 'vue-router'
import { removeToken } from '@/utils/auth.js'

const userStore = useUserStore()
const router = useRouter()

const logout = () => {
  userStore.clearUserInfo()
  removeToken()
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
