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
        <router-link to="/admin/categories" class="nav-item">
          <i class="icon-list"></i> 分类管理
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
        <div class="admin-info">
          <span>管理员: {{ authStore.user?.username }}</span>
          <button @click="handleLogout">退出</button>
        </div>
      </header>
      <section class="admin-content">
        <router-view></router-view>
      </section>
    </main>
  </div>
</template>

<style scoped>
/* 核心样式建议 */
.admin-layout { display: flex; min-height: 100vh; background: #f4f7f6; }
.admin-sidebar { width: 240px; background: #2c3e50; color: white; display: flex; flex-direction: column; }
.admin-logo { padding: 20px; font-size: 1.5rem; font-weight: bold; border-bottom: 1px solid #3e4e5e; }
.nav-item { padding: 15px 20px; color: #ecf0f1; text-decoration: none; display: block; }
.nav-item.router-link-active { background: #34495e; border-left: 4px solid #42b983; }
.admin-main { flex: 1; display: flex; flex-direction: column; }
.admin-header { height: 60px; background: white; display: flex; justify-content: space-between; align-items: center; padding: 0 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
</style>
