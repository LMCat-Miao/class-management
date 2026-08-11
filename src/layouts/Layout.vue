<template>
    <el-container>
        <Header />
        <el-container>
            <Sidebar />
            <el-main>
                <router-view />
            </el-main>
        </el-container>
    </el-container>
</template>

<script setup>
import Header from '../components/Header.vue';
import Sidebar from '../components/Sidebar.vue';
import router from '../router';

</script>

<style></style>