<template>
  <div class="sidebar">
    <el-menu
      :default-active="activeMenu"
      router
      class="sidebar-menu"
      :collapse="collapsed"
    >
      <el-menu-item
        v-for="item in menus"
        :key="item.path"
        :index="item.path"
      >
        <el-icon class="menu-icon">
          <component :is="resolveIcon(item.path)" />
        </el-icon>
        <template #title>
          <span>{{ item.name }}</span>
        </template>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  Odometer,
  Reading,
  User,
  FolderOpened,
  MagicStick,
  Avatar
} from '@element-plus/icons-vue'
import { usePermissionStore } from '@/stores/permission'

const route = useRoute()
const permissionStore = usePermissionStore()
const menus = computed(() => permissionStore.menus)
const collapsed = ref(false)

const iconMap = {
  '/dashboard': Odometer,
  '/course': Reading,
  '/teacher': Avatar,
  '/student': User,
  '/resource': FolderOpened,
  '/ai-assistant': MagicStick
}

const activeMenu = computed(() => {
  if (route.path.startsWith('/course/')) return '/course'
  if (route.path.startsWith('/teacher/')) return '/teacher'
  if (route.path.startsWith('/student/')) return '/student'
  return route.path
})

function resolveIcon(path) {
  return iconMap[path] || Reading
}

function syncCollapse() {
  collapsed.value = window.innerWidth <= 1024
}

onMounted(() => {
  syncCollapse()
  window.addEventListener('resize', syncCollapse)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', syncCollapse)
})
</script>

<style scoped>
.sidebar {
  width: 100%;
  height: 100%;
  background: var(--cm-sidebar-bg);
  padding: 18px 12px;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-menu {
  border-right: none;
  background: transparent;
  --el-menu-bg-color: transparent;
  --el-menu-text-color: #c7d2e5;
  --el-menu-hover-bg-color: rgba(148, 163, 184, 0.12);
  --el-menu-active-color: #ffffff;
  --el-menu-item-height: 46px;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 100%;
}

.sidebar-menu :deep(.el-menu-item) {
  height: 46px;
  margin-bottom: 6px;
  border-radius: 10px;
  padding: 0 14px !important;
  transition: background 0.18s ease, color 0.18s ease;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  color: #fff;
  background: rgba(148, 163, 184, 0.14);
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background: #3b5bdb;
  color: #fff;
  font-weight: 600;
  box-shadow: 0 8px 18px rgba(59, 91, 219, 0.32);
}

.sidebar-menu :deep(.el-menu-item .el-icon) {
  font-size: 18px;
  margin-right: 10px;
  color: inherit;
}

.sidebar-menu.el-menu--collapse {
  width: 100%;
}

.sidebar-menu.el-menu--collapse :deep(.el-menu-item) {
  padding: 0 !important;
  justify-content: center;
}

.sidebar-menu.el-menu--collapse :deep(.el-menu-item .el-icon) {
  margin-right: 0;
}
</style>
