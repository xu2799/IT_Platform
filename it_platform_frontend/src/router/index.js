import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

// 视图组件导入
import HomeView from '@/views/HomeView.vue'
import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'
import CourseDetailView from '@/views/CourseDetailView.vue'
import CreateCourseView from '@/views/CreateCourseView.vue'
import CourseListView from '@/views/CourseListView.vue'

// Admin 组件导入 (请确保这些文件都真实存在)
import AdminLayout from '@/views/admin/AdminLayout.vue'
import AdminDashboardView from '@/views/admin/AdminDashboardView.vue'
import AdminCourseManager from '@/views/admin/AdminCourseManager.vue'
import AdminApplicationsView from '@/views/admin/AdminApplicationsView.vue'
import AdminUserManager from '@/views/admin/AdminUserManager.vue'
import AdminCommentManager from '@/views/admin/AdminCommentManager.vue'

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
      path: '/courses/:id/edit',
      name: 'course-edit',
      component: () => import('@/views/CourseEditView.vue'),
      props: true,
      meta: { requiresAuth: true, requiredRole: ['instructor', 'admin'] }
    },
    {
      path: '/create-course',
      name: 'create-course',
      component: CreateCourseView,
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
      path: '/favorites',
      name: 'favorites',
      component: () => import('@/views/FavoritesView.vue'),
      meta: { requiresAuth: true }
    },

    // --- Admin 路由 ---
    {
      path: '/admin',
      component: AdminLayout,
      meta: { requiresAuth: true, requiredRole: ['admin'] },
      children: [
        {
          path: '',
          redirect: { name: 'admin-dashboard' }
        },
        {
          path: 'dashboard',
          name: 'admin-dashboard',
          component: AdminDashboardView,
          meta: { title: '仪表盘' }
        },
        {
          // 【重要】: 这里的 component 必须是 AdminCourseManager
          path: 'courses',
          name: 'admin-courses',
          component: AdminCourseManager,
          meta: { title: '课程管理' }
        },
        {
          // 【重要】: 这里的 component 必须是 AdminUserManager
          path: 'users',
          name: 'admin-users',
          component: AdminUserManager,
          meta: { title: '用户管理' }
        },
        {
          path: 'comments',
          name: 'admin-comments',
          component: AdminCommentManager,
          meta: { title: '评论管理' }
        },
        {
          path: 'applications',
          name: 'admin-applications',
          component: AdminApplicationsView,
          meta: { title: '讲师审核' }
        }
      ]
    },
  ]
})

router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore()
    const requiresAuth = to.meta.requiresAuth
    const requiredRole = to.meta.requiredRole

    if (authStore.token && (!authStore.user || authStore.user.favorited_courses === undefined)) {
        try {
            await authStore.fetchUser()
        } catch (error) {
            authStore.logout()
            return next({ name: 'login' })
        }
    }

    if (requiresAuth && !authStore.isAuthenticated) {
        return next({ name: 'login' })
    }

    if (requiresAuth && requiredRole) {
        const userRole = authStore.user?.role
        if (!userRole || !requiredRole.includes(userRole)) {
            alert('您没有访问此页面的权限。')
            return next({ name: 'home' })
        }
    }

    if ((to.name === 'login' || to.name === 'register') && authStore.isAuthenticated) {
        return next({ name: 'courses' })
    }

    next()
})

export default router
