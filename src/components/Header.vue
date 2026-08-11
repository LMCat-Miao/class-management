<template>
    <!-- 这里是仪表盘页面的内容 -->
     <div class="header">
        <h2>AI课程管理平台</h2>
         <div>
        <span>
            {{ userStore.userInfo.username }}
        </span>
        <el-button @click="logout">退出登录</el-button>
    </div>
    </div>
</template>

<script setup>
import { useUserStore } from '@/stores/user.js';
import { useRouter } from 'vue-router';
const userStore = useUserStore();
const router = useRouter();
const logout = () => {
    userStore.clearUser();
    router.push('/login')
};
</script>

<style></style>