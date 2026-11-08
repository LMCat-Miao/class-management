<template>
  <div class="header">
    <div class="brand">
      <div class="brand-mark" aria-hidden="true">
        <span class="brand-mark-inner">AI</span>
      </div>
      <div class="brand-text">
        <h1>AI课程管理平台</h1>
        <p>Course Intelligence Console</p>
      </div>
    </div>

    <div class="header-right">
      <div class="user-chip" :title="userStore.nickname">
        <el-avatar :size="36" class="user-avatar">
          {{ avatarText }}
        </el-avatar>
        <div class="user-meta">
          <span class="user-name">{{ userStore.nickname }}</span>
          <el-tag size="small" effect="light" class="role-tag">
            {{ roleLabel }}
          </el-tag>
        </div>
      </div>
      <div class="divider" aria-hidden="true" />
      <el-button class="logout-btn" text @click="logout">
        <el-icon><SwitchButton /></el-icon>
        <span class="logout-text">退出登录</span>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { SwitchButton } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { usePermissionStore } from '@/stores/permission'
import { useRouter } from 'vue-router'
import { resetRouter } from '@/router'
import { ROLE_LABELS } from '@/constants/roles'

const userStore = useUserStore()
const permissionStore = usePermissionStore()
const router = useRouter()

const roleLabel = computed(() => {
  const role = userStore.roles[0]
  return ROLE_LABELS[role] || role || '用户'
})

const avatarText = computed(() => {
  const name = userStore.nickname || '用'
  return String(name).slice(0, 1)
})

const logout = async () => {
  await userStore.logout()
  permissionStore.reset()
  resetRouter()
  router.push('/login')
}
</script>

<style scoped>
.header {
  height: var(--cm-header-h);
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #ffffff;
  border-bottom: 1px solid var(--cm-border);
  box-shadow: 0 1px 0 rgba(15, 23, 42, 0.02);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.brand-mark {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(145deg, #4c6ef5, #3b5bdb 55%, #364fc7);
  display: grid;
  place-items: center;
  flex-shrink: 0;
  box-shadow: 0 6px 14px rgba(59, 91, 219, 0.25);
}

.brand-mark-inner {
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.brand-text h1 {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--cm-text);
  line-height: 1.25;
  white-space: nowrap;
}

.brand-text p {
  margin: 2px 0 0;
  font-size: 11px;
  color: var(--cm-text-muted);
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-shrink: 0;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  max-width: 220px;
  min-width: 0;
}

.user-avatar {
  background: var(--cm-primary-soft);
  color: var(--cm-primary);
  font-weight: 700;
  border: 1px solid #dbe4ff;
  flex-shrink: 0;
}

.user-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--cm-text);
  line-height: 1.2;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-tag {
  width: fit-content;
  border-radius: 6px;
  --el-tag-bg-color: var(--cm-primary-soft);
  --el-tag-border-color: transparent;
  --el-tag-text-color: var(--cm-primary);
}

.divider {
  width: 1px;
  height: 28px;
  background: var(--cm-border);
}

.logout-btn {
  color: var(--cm-text-secondary);
  font-weight: 500;
}

.logout-btn:hover {
  color: var(--cm-primary);
}

@media (max-width: 1024px) {
  .header {
    padding: 0 14px;
  }

  .brand-text p {
    display: none;
  }

  .logout-text {
    display: none;
  }

  .user-name {
    max-width: 88px;
  }
}
</style>
