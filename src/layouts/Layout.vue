<template>
  <el-container class="layout" direction="vertical">
    <el-header class="layout-header" height="68px">
      <Header />
    </el-header>
    <el-container class="layout-body">
      <el-aside class="layout-aside" width="232px">
        <Sidebar />
      </el-aside>
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

.layout-header {
  padding: 0;
  height: var(--cm-header-h) !important;
  flex-shrink: 0;
  z-index: 30;
}

.layout-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.layout-aside {
  height: 100%;
  overflow: hidden;
  background: var(--cm-sidebar-bg);
  flex-shrink: 0;
}

.layout-main {
  background: var(--cm-bg);
  overflow: auto;
  padding: 24px;
  min-width: 0;
}

@media (max-width: 1024px) {
  .layout-aside {
    width: 72px !important;
  }

  .layout-main {
    padding: 16px;
  }
}
</style>
