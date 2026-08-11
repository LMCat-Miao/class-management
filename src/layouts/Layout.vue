<template>
  <el-container class="layout">
    <Header />
    <el-container class="layout-body">
      <Sidebar />
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import Header from '@/components/Header.vue'
import Sidebar from '@/components/Sidebar.vue'
</script>

<style scoped>
.layout {
  height: 100vh;
}

.layout-body {
  height: calc(100vh - 60px);
  overflow: hidden;
}

.layout-main {
  background: #f5f7fa;
  overflow: auto;
}
</style>
