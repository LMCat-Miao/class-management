<template>
  <div class="login">
    <h2>AI课程管理平台</h2>
    <el-form :model="form" @keyup.enter="handleLogin">
      <el-form-item>
        <el-input v-model="form.username" placeholder="用户名" />
      </el-form-item>
      <el-form-item>
        <el-input
          v-model="form.password"
          placeholder="密码"
          type="password"
          show-password
        />
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          :loading="loading"
          style="width: 100%"
          @click="handleLogin"
        >
          登录
        </el-button>
      </el-form-item>
    </el-form>
    <p v-if="isMock" class="mock-tip">
      当前为演示模式，输入任意账号密码即可进入<br />
      推荐：admin / 123456
    </p>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { login } from '@/api/user.js'
import { setToken } from '@/utils/auth.js'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user.js'
import { isMockEnabled } from '@/mock'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const isMock = isMockEnabled()

const form = reactive({
  username: isMock ? 'admin' : '',
  password: isMock ? '123456' : ''
})

const handleLogin = async () => {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }

  loading.value = true
  try {
    const res = await login(form)
    setToken(res.data.token)
    userStore.setUserInfo(res.data.userInfo)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (error) {
    ElMessage.error(error.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login {
  max-width: 400px;
  margin: 120px auto;
  padding: 32px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.login h2 {
  margin: 0 0 24px;
  text-align: center;
  font-size: 22px;
}

.mock-tip {
  margin: 8px 0 0;
  text-align: center;
  font-size: 13px;
  line-height: 1.6;
  color: #909399;
}
</style>
