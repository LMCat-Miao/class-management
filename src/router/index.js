import {createRouter,createWebHistory} from "vue-router"
import Login from "@/views/Login.vue"
import Layout from "@/layouts/Layout.vue"
//创建路由
const router = createRouter({
    history: createWebHistory(),
    routes: [
        // 定义路由规则
        {
            path:'/',
            redirect:'/login'
        },
        {
            path: '/login',
            component: () => import('@/views/Login.vue')
        },
        {
            path: '/dashboard',
            component: () => import('@/views/Dashboard.vue')
        },
        {
            path:'/course',
            component: () => import('@/views/Course.vue')
        }
    ]
})
export default router