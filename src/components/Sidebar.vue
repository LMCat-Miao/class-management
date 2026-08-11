<template>
  <div class="sidebar">
    <el-menu
      :default-active="activeMenu"
      router
    >
      <el-menu-item
        v-for="item in menus"
        :key="item.path"
        :index="item.path"
      >
        {{ item.name }}
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { usePermissionStore } from '@/stores/permission.js'

const route = useRoute()
const permissionStore = usePermissionStore()
const menus = computed(() => permissionStore.menus)
const activeMenu = computed(() => route.path)
</script>

<style scoped>
.sidebar {
  width: 200px;
  height: 100%;
  border-right: 1px solid #ebeef5;
  background: #fff;
}

.sidebar .el-menu {
  border-right: none;
}
</style>
