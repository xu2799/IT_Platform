<script setup>
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

// 简单的路径匹配高亮
const isActive = (path) => route.path.includes(path)
</script>

<template>
  <div class="admin-layout">
    <aside class="admin-sidebar">
      <div class="sidebar-header">
        <h2>后台管理系统</h2>
        <p>IT Platform Admin</p>
      </div>

      <nav class="sidebar-nav">
        <RouterLink :to="{ name: 'admin-dashboard' }" class="nav-item" :class="{ active: route.name === 'admin-dashboard' }">
          <span class="icon">📊</span> 仪表盘
        </RouterLink>

        <RouterLink :to="{ name: 'admin-courses' }" class="nav-item" :class="{ active: isActive('/admin/courses') }">
          <span class="icon">📚</span> 课程管理
        </RouterLink>

        <RouterLink :to="{ name: 'admin-users' }" class="nav-item" :class="{ active: isActive('/admin/users') }">
          <span class="icon">👥</span> 用户管理
        </RouterLink>

        <RouterLink :to="{ name: 'admin-comments' }" class="nav-item" :class="{ active: isActive('/admin/comments') }">
          <span class="icon">💬</span> 评论管理
        </RouterLink>

        <RouterLink :to="{ name: 'admin-applications' }" class="nav-item" :class="{ active: isActive('/admin/applications') }">
          <span class="icon">👨‍🏫</span> 讲师审核
        </RouterLink>

        <div class="nav-spacer"></div>

        <RouterLink :to="{ name: 'home' }" class="nav-item">
          <span class="icon">🏠</span> 返回前台
        </RouterLink>

        <a @click="handleLogout" class="nav-item danger">
          <span class="icon">🚪</span> 退出登录
        </a>
      </nav>
    </aside>

    <main class="admin-content">
      <header class="content-header">
        <div class="breadcrumb">
          当前页面: <strong>{{ route.meta.title || '后台管理' }}</strong>
        </div>
        <div class="user-info">
          管理员: {{ authStore.user?.username }}
        </div>
      </header>

      <div class="content-body">
        <RouterView />
      </div>
    </main>
  </div>
</template>

<style scoped>
.admin-layout { display: flex; min-height: 100vh; background-color: #f3f4f6; }

/* 侧边栏 */
.admin-sidebar {
  width: 240px;
  background: #1e293b; /* 深蓝灰色 */
  color: #f1f5f9;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  z-index: 1000;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #334155;
  background: #0f172a;
}
.sidebar-header h2 { margin: 0; font-size: 1.1rem; font-weight: 700; color: white; }
.sidebar-header p { margin: 5px 0 0; font-size: 0.8rem; color: #94a3b8; }

.sidebar-nav {
  flex: 1;
  padding: 15px 10px;
  display: flex;
  flex-direction: column;
  gap: 5px; /* 菜单项之间的间距 */
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 15px;
  color: #cbd5e1;
  text-decoration: none;
  border-radius: 6px;
  font-size: 0.95rem;
  transition: all 0.2s;
  cursor: pointer;
}

/* 悬停效果 */
.nav-item:hover {
  background: #334155;
  color: white;
}

/* 激活状态 */
.nav-item.active {
  background: #4f46e5; /* Indigo-600 */
  color: white;
  font-weight: 500;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.nav-item.danger:hover {
  background: #ef4444;
  color: white;
}

.icon { width: 24px; text-align: center; font-size: 1.1rem; }

.nav-spacer { flex: 1; } /* 占位符，将下方菜单推到底部 */

/* 内容区 */
.admin-content {
  flex: 1;
  margin-left: 240px;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.content-header {
  height: 60px;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 30px;
}

.content-body {
  padding: 30px;
  overflow-y: auto;
  flex: 1;
}
</style>
