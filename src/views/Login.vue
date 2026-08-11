<template>
    <div class="login">
        <h2>AI课程管理平台</h2>
        <el-form :model="form">
            <el-form-item>
                <el-input 
                v-model="form.username" placeholder="用户名"/>
            </el-form-item>
            <el-form-item>
                <el-input 
                v-model="form.password" placeholder="密码" type="password"/>
            </el-form-item>
            <el-form-item>
                <el-button type="primary" @click="handleLogin">登录</el-button>
            </el-form-item>
        </el-form>

    </div>
</template>

<script setup>
import { reactive } from 'vue'
import {login} from '@/api/user.js'
import {setToken} from '@/utils/auth.js'
import {useRouter} from 'vue-router'
import {useUserStore} from '@/stores/user.js'

// 响应式表单数据
const router = useRouter()
// 引入用户状态管理
const userStore = useUserStore()
const form = reactive({
    username: '',
    password: ''
})
// 登录处理函数
const handleLogin = async()=>{
    const res = await login(form)
    console.log(res)
    setToken(res.data.token)
    userStore.setUserInfo(res.data.userInfo)
    router.push('/dashboard')
}

</script>

<style scoped>
.login {
    max-width: 400px;
    margin: 100px auto;
}

</style>