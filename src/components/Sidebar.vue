
<script setup>
import { computed } from 'vue'
import {usePermissionStore} from '@/stores/permission.js'

const permissionStore = usePermissionStore()
const menus = computed(() => permissionStore.menus)
</script>

<template>
    <div class="sidebar">
        <el-menu>
            <el-menu-item v-for="item in menus" :key="item.path" :index="item.path">
                <router-link :to="item.path">{{ item.name }}</router-link>
            </el-menu-item>
        </el-menu>
    </div>
</template>

<style scoped>
</style>