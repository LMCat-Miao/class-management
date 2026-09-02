import type { RouteRecordRaw } from 'vue-router'
import Layout from '@/layouts/Layout.vue'
import { ROLES } from '@/constants/roles'

/**
 * 业务路由（动态注册）
 * meta.roles: 可访问角色
 * meta.title / meta.menu: 侧边栏展示
 */
export const asyncRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Layout',
    component: Layout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard/index.vue'),
        meta: {
          title: '首页',
          menu: true,
          roles: [ROLES.ADMIN, ROLES.TEACHER]
        }
      },
      {
        path: 'course',
        name: 'Course',
        component: () => import('@/views/Course/index.vue'),
        meta: {
          title: '课程管理',
          menu: true,
          menuTitle: {
            [ROLES.TEACHER]: '我的课程'
          },
          roles: [ROLES.ADMIN, ROLES.TEACHER]
        }
      },
      {
        path: 'course/:id',
        name: 'CourseDetail',
        component: () => import('@/views/Course/Detail.vue'),
        meta: {
          title: '课程详情',
          menu: false,
          roles: [ROLES.ADMIN, ROLES.TEACHER]
        }
      },
      {
        path: 'teacher',
        name: 'Teacher',
        component: () => import('@/views/Teacher/index.vue'),
        meta: {
          title: '教师管理',
          menu: true,
          roles: [ROLES.ADMIN]
        }
      },
      {
        path: 'teacher/:id',
        name: 'TeacherDetail',
        component: () => import('@/views/Teacher/Detail.vue'),
        meta: {
          title: '教师详情',
          menu: false,
          roles: [ROLES.ADMIN]
        }
      },
      {
        path: 'student',
        name: 'Student',
        component: () => import('@/views/Student/index.vue'),
        meta: {
          title: '学生管理',
          menu: true,
          roles: [ROLES.ADMIN, ROLES.TEACHER]
        }
      },
      {
        path: 'student/:id',
        name: 'StudentDetail',
        component: () => import('@/views/Student/Detail.vue'),
        meta: {
          title: '学生详情',
          menu: false,
          roles: [ROLES.ADMIN, ROLES.TEACHER]
        }
      },
      {
        path: 'resource',
        name: 'Resource',
        component: () => import('@/views/Resource/index.vue'),
        meta: {
          title: '教学资源',
          menu: true,
          roles: [ROLES.ADMIN, ROLES.TEACHER]
        }
      },
      {
        path: 'ai-assistant',
        name: 'AiAssistant',
        component: () => import('@/views/AiAssistant/index.vue'),
        meta: {
          title: 'AI课程助手',
          menu: true,
          roles: [ROLES.ADMIN, ROLES.TEACHER]
        }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/dashboard'
  }
]

export const constantRoutes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    name: 'Root',
    redirect: '/login'
  }
]
