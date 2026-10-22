<template>
  <div class="sidebar">
    <div class="sidebar-label">导航菜单</div>
    <el-menu
      :default-active="activeMenu"
      router
      class="sidebar-menu"
    >
      <el-menu-item
        v-for="item in menus"
        :key="item.path"
        :index="item.path"
      >
        <el-icon class="menu-icon">
          <component :is="resolveIcon(item.path)" />
        </el-icon>
        <span>{{ item.name }}</span>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup>
import { computed } from 'vue'
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
</script>

<style scoped>
.sidebar {
  width: var(--cm-sidebar-w);
  height: 100%;
  background: #0f172a;
  border-right: none;
  padding: 16px 12px;
  flex-shrink: 0;
}

.sidebar-label {
  padding: 0 12px 12px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #64748b;
}

.sidebar-menu {
  border-right: none;
  background: transparent;
  --el-menu-bg-color: transparent;
  --el-menu-text-color: #cbd5e1;
  --el-menu-hover-bg-color: rgba(148, 163, 184, 0.12);
  --el-menu-active-color: #ffffff;
}

.sidebar-menu :deep(.el-menu-item) {
  height: 44px;
  margin-bottom: 4px;
  border-radius: 10px;
  transition: background 0.18s ease, color 0.18s ease, transform 0.18s ease;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  color: #fff;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, #3b5bdb, #4c6ef5);
  color: #fff;
  box-shadow: 0 8px 18px rgba(59, 91, 219, 0.35);
  font-weight: 600;
}

.menu-icon {
  margin-right: 8px;
  font-size: 18px;
}
</style>
