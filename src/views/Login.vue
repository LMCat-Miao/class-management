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

    <div class="mock-tip">
      <p>{{ isMock ? '演示 Mock 账号：' : '后端演示账号：' }}</p>
      <p>
        管理员：
        <el-button link type="primary" @click="fillAccount('admin')">admin / 123456</el-button>
      </p>
      <p>
        教师：
        <el-button link type="primary" @click="fillAccount('teacher')">teacher / 123456</el-button>
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { usePermissionStore } from '@/stores/permission'
import { isMockEnabled } from '@/mock'

const router = useRouter()
const userStore = useUserStore()
const permissionStore = usePermissionStore()
const loading = ref(false)
const isMock = isMockEnabled()

const form = reactive({
  username: isMock ? 'admin' : '',
  password: isMock ? '123456' : ''
})

function fillAccount(type) {
  form.username = type
  form.password = '123456'
}

const handleLogin = async () => {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }

  loading.value = true
  try {
    await userStore.login(form)
    permissionStore.reset()
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
  max-width: 420px;
  margin: 100px auto;
  padding: 36px 32px;
  background: var(--cm-surface);
  border-radius: var(--cm-radius);
  border: 1px solid var(--cm-border);
  box-shadow: var(--cm-shadow);
}

.login h2 {
  margin: 0 0 28px;
  text-align: center;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--cm-text);
}

.mock-tip {
  margin-top: 8px;
  text-align: center;
  font-size: 13px;
  color: var(--cm-text-secondary);
  line-height: 1.8;
}

.mock-tip p {
  margin: 0;
}
</style>
