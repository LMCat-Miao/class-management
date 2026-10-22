<template>
  <div class="header">
    <div class="brand">
      <div class="brand-mark" aria-hidden="true">
        <span class="brand-mark-inner">AI</span>
      </div>
      <div class="brand-text">
        <h2>AI课程管理平台</h2>
        <p>Course Intelligence Console</p>
      </div>
    </div>

    <div class="header-right">
      <div class="user-chip">
        <el-avatar :size="34" class="user-avatar">
          {{ avatarText }}
        </el-avatar>
        <div class="user-meta">
          <span class="user-name">{{ userStore.nickname }}</span>
          <el-tag size="small" effect="light" round class="role-tag">
            {{ roleLabel }}
          </el-tag>
        </div>
      </div>
      <div class="divider" />
      <el-button class="logout-btn" text @click="logout">
        <el-icon><SwitchButton /></el-icon>
        退出登录
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
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 22px;
  background: rgba(255, 255, 255, 0.92);
  border-bottom: 1px solid var(--cm-border);
  backdrop-filter: blur(10px);
  z-index: 20;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-mark {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(145deg, #4c6ef5, #3b5bdb 55%, #364fc7);
  display: grid;
  place-items: center;
  box-shadow: 0 6px 14px rgba(59, 91, 219, 0.28);
}

.brand-mark-inner {
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.brand-text h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--cm-text);
  line-height: 1.2;
}

.brand-text p {
  margin: 2px 0 0;
  font-size: 11px;
  color: var(--cm-text-muted);
  letter-spacing: 0.04em;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-avatar {
  background: var(--cm-primary-soft);
  color: var(--cm-primary);
  font-weight: 700;
  border: 1px solid #dbe4ff;
}

.user-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--cm-text);
  line-height: 1.2;
}

.role-tag {
  width: fit-content;
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
}

.logout-btn:hover {
  color: var(--cm-primary);
}
</style>
