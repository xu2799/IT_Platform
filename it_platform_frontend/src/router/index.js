// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

// 视图组件导入
import HomeView from '@/views/HomeView.vue'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import CourseDetailView from '@/views/CourseDetailView.vue'
import CreateCourseView from '@/views/CreateCourseView.vue'
import CourseListView from '@/views/CourseListView.vue' 

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/courses',
      name: 'courses',
      component: CourseListView, 
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('@/views/AboutView.vue')
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { simpleHeader: true } 
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { simpleHeader: true } 
    },
    {
      path: '/courses/:id',
      name: 'course-detail',
      component: CourseDetailView,
      props: true
    },
    {
      path: '/courses/:courseId/lessons/:lessonId',
      name: 'lesson-watch',
      component: () => import('@/views/LessonWatchView.vue'),
      props: true,
    },
    {
      path: '/create-course',
      name: 'create-course',
      component: CreateCourseView,
      meta: { requiresAuth: true, requiredRole: ['instructor', 'admin'] }
    },
    {
      path: '/courses/:id/edit',
      name: 'course-edit',
      component: () => import('@/views/CourseEditView.vue'), 
      props: true,
      meta: { requiresAuth: true, requiredRole: ['instructor', 'admin'] }
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'), 
      meta: { requiresAuth: true }
    },
    {
      path: '/instructor-dashboard',
      name: 'instructor-dashboard',
      component: () => import('@/views/InstructorDashboardView.vue'), 
      meta: { requiresAuth: true, requiredRole: ['instructor', 'admin'] }
    },
    {
      path: '/become-instructor',
      name: 'become-instructor',
      component: () => import('@/views/BecomeInstructorView.vue'), 
      meta: { requiresAuth: true, requiredRole: ['student'] } 
    },
    {
      path: '/admin/applications',
      name: 'admin-applications',
      component: () => import('@/views/AdminApplicationsView.vue'), 
      meta: { requiresAuth: true, requiredRole: ['admin'] } 
    },
    {
      path: '/favorites',
      name: 'favorites',
      component: () => import('@/views/FavoritesView.vue'),
      meta: { requiresAuth: true }
    },
  ]
})

// 全局路由守卫
router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore()
    const requiresAuth = to.meta.requiresAuth
    const requiredRole = to.meta.requiredRole
    
    // 1. 检查是否需要恢复用户状态 (有 Token 但 Store 为空)
    if (authStore.token && (!authStore.user || authStore.user.favorited_courses === undefined)) {
        try {
            await authStore.fetchUser()
        } catch (error) {
            authStore.logout()
            return next({ name: 'login' })
        }
    }

    // 2. 检查登录要求
    if (requiresAuth && !authStore.isAuthenticated) {
        return next({ name: 'login' })
    }

    // 3. 检查角色权限要求
    if (requiresAuth && requiredRole) {
        const userRole = authStore.user?.role
        if (!userRole || !requiredRole.includes(userRole)) {
            alert('您没有访问此页面的权限。')
            return next({ name: 'home' })
        }
    }

    // 4. 已登录用户重定向 (防止重复登录)
    if ((to.name === 'login' || to.name === 'register') && authStore.isAuthenticated) {
        return next({ name: 'courses' })
    }

    next()
})

export default router