<script setup>
import { useAuthStore } from '@/stores/authStore'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const handleLogout = () => {
  authStore.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="admin-layout">
    <aside class="admin-sidebar">
      <div class="admin-logo">管理后台</div>
      <nav class="admin-nav">
        <router-link to="/admin/dashboard" class="nav-item">
          <i class="icon-dashboard"></i> 仪表盘
        </router-link>
        <router-link to="/admin/users" class="nav-item">
          <i class="icon-user"></i> 用户管理
        </router-link>
        <router-link to="/admin/courses" class="nav-item">
          <i class="icon-book"></i> 课程管理
        </router-link>
        <router-link to="/admin/comments" class="nav-item">
          <i class="icon-comment"></i> 评论审核
        </router-link>
        <router-link to="/admin/applications" class="nav-item">
          <i class="icon-verify"></i> 讲师申请
        </router-link>
        <router-link to="/admin/assignments" class="nav-item">
          <i class="icon-task"></i> 作业监控
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <router-link to="/">返回首页</router-link>
      </div>
    </aside>

    <main class="admin-main">
      <header class="admin-header">
        <span class="page-title">{{ $route.meta.title || '系统管理' }}</span>
        <div class="header-right">
           <router-link to="/messages" class="msg-btn">💌 私信</router-link>
           <span class="admin-name">管理员: {{ authStore.user?.nickname || authStore.user?.username }}</span>
           <button @click="handleLogout" class="logout-btn">退出</button>
        </div>
      </header>
      <section class="admin-content">
        <router-view></router-view>
      </section>
    </main>
  </div>
</template>

<style scoped>
.admin-layout { display: flex; min-height: 100vh; background: #f4f7f6; }
.admin-sidebar { width: 240px; background: #2c3e50; color: white; display: flex; flex-direction: column; flex-shrink: 0; }
.admin-logo { padding: 20px; font-size: 1.5rem; font-weight: bold; border-bottom: 1px solid #3e4e5e; background: #243342; }
.admin-nav { flex: 1; padding-top: 10px; }
.nav-item { padding: 15px 20px; color: #b0c4de; text-decoration: none; display: block; transition: all 0.3s; border-left: 4px solid transparent; }
.nav-item:hover { background: #34495e; color: white; }
.nav-item.router-link-active { background: #34495e; border-left-color: #42b983; color: white; }
.sidebar-footer { padding: 20px; border-top: 1px solid #3e4e5e; }
.sidebar-footer a { color: #b0c4de; text-decoration: none; font-size: 0.9rem; }
.sidebar-footer a:hover { color: white; }

.admin-main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.admin-header { height: 60px; background: white; display: flex; justify-content: space-between; align-items: center; padding: 0 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); z-index: 10; }
.page-title { font-size: 1.2rem; font-weight: 600; color: #2c3e50; }

.header-right { display: flex; align-items: center; gap: 15px; }
.admin-name { font-size: 0.9rem; color: #666; }
.msg-btn { margin-right: 10px; text-decoration: none; color: #4f46e5; font-weight: 600; }
.msg-btn:hover { text-decoration: underline; }
.logout-btn { padding: 5px 15px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer; transition: all 0.2s; }
.logout-btn:hover { background: #f5f5f5; color: #ef4444; border-color: #ef4444; }

.admin-content { flex: 1; padding: 30px; overflow-y: auto; }
</style>
