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
  background: var(--cm-bg);
}

.layout-body {
  height: calc(100vh - var(--cm-header-h));
  overflow: hidden;
}

.layout-main {
  background:
    radial-gradient(1200px 400px at 0% 0%, rgba(59, 91, 219, 0.06), transparent 55%),
    radial-gradient(900px 360px at 100% 0%, rgba(21, 170, 191, 0.05), transparent 50%),
    var(--cm-bg);
  overflow: auto;
  padding: 20px;
}
</style>
