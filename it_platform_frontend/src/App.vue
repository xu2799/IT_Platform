<script setup>
import { RouterLink, RouterView, useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { useCourseStore } from '@/stores/courseStore'
import { computed, ref, onMounted } from 'vue'

const authStore = useAuthStore()
const courseStore = useCourseStore()
const router = useRouter()
const route = useRoute()

const searchQuery = ref('')

const shouldShowHeader = computed(() => !route.meta.hideHeader)
const shouldShowSimpleHeader = computed(() => !!route.meta.simpleHeader)
const shouldShowFullHeader = computed(() => shouldShowHeader.value && !shouldShowSimpleHeader.value)

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const getAvatarUrl = (user) => {
  if (!user) return ''
  if (user.avatar) {
      if (user.avatar.startsWith('http')) return user.avatar
      const cleanPath = user.avatar.startsWith('/') ? user.avatar : `/${user.avatar}`
      const cleanBase = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL
      return `${cleanBase}${cleanPath}`
  }
  return `https://ui-avatars.com/api/?name=${user.username}&background=4f46e5&color=fff`
}

onMounted(() => {
  courseStore.fetchCategories()
})

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const handleSearchSubmit = () => {
  if (searchQuery.value.trim()) {
    router.push({ name: 'courses', query: { search: searchQuery.value.trim() } })
    searchQuery.value = ''
  }
}
</script>

<template>
  <div id="app">
    <header v-if="shouldShowSimpleHeader" class="app-header simple">
      <div class="navbar-brand">
        <RouterLink :to="{ name: 'home' }"><span class="logo-text">IT 职业技能在线培训平台</span></RouterLink>
      </div>
      <nav class="navbar-user">
        <RouterLink to="/login" class="nav-link">登录</RouterLink>
        <RouterLink to="/register" class="nav-btn primary">注册</RouterLink>
      </nav>
    </header>

    <header v-if="shouldShowFullHeader" class="app-header glass">
      <div class="navbar-left">
        <div class="navbar-brand">
          <RouterLink :to="{ name: 'home' }"><span class="logo-text">IT 职业技能在线培训平台</span></RouterLink>
        </div>
        <nav class="navbar-main">
          <RouterLink :to="{ name: 'about' }" class="nav-link">关于我们</RouterLink>
        </nav>
      </div>

      <div class="navbar-center">
        <form @submit.prevent="handleSearchSubmit" class="search-form">
          <input type="text" v-model="searchQuery" placeholder="搜索感兴趣的课程..." class="search-input">
          <button type="submit" class="search-btn">🔍</button>
        </form>
      </div>

      <div class="navbar-right">
        <nav class="navbar-user">
          <template v-if="!authStore.isAuthenticated">
            <RouterLink to="/login" class="nav-link">登录</RouterLink>
            <RouterLink to="/register" class="nav-btn primary">注册</RouterLink>
          </template>

          <template v-else>
            <RouterLink v-if="['instructor', 'admin'].includes(authStore.user?.role)" to="/create-course" class="nav-btn success">+ 创建课程</RouterLink>

            <div class="dropdown-wrapper">
              <a class="nav-link user-trigger">
                <img :src="getAvatarUrl(authStore.user)" class="nav-avatar" alt="avatar">
                <span class="username">{{ authStore.user?.nickname || authStore.user?.username }}</span>
              </a>

              <div class="dropdown-menu right">
                <RouterLink :to="{ name: 'profile' }" class="dropdown-item">个人资料</RouterLink>
                <RouterLink :to="{ name: 'favorites' }" class="dropdown-item">我的收藏</RouterLink>
                <div class="divider"></div>

                <RouterLink v-if="['instructor', 'admin'].includes(authStore.user?.role)" :to="{ name: 'instructor-dashboard' }" class="dropdown-item">讲师面板</RouterLink>
                <RouterLink v-if="authStore.user?.role === 'student'" :to="{ name: 'become-instructor' }" class="dropdown-item">成为讲师</RouterLink>

                <RouterLink v-if="authStore.user?.role === 'admin'" :to="{ name: 'admin-dashboard' }" class="dropdown-item">后台管理</RouterLink>

                <div class="divider"></div>
                <a @click="handleLogout" class="dropdown-item danger">退出登录</a>
              </div>
            </div>
          </template>
        </nav>
      </div>
    </header>

    <main class="app-main" :class="{ 'no-header': !shouldShowHeader }">
      <RouterView :key="route.fullPath" />
    </main>
  </div>
</template>

<style scoped>
.app-header { height: 70px; padding: 0 30px; display: flex; justify-content: space-between; align-items: center; position: relative; z-index: 100; transition: all 0.3s; }
.app-header.glass { background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(12px); border-bottom: 1px solid rgba(0,0,0,0.05); box-shadow: var(--shadow-sm); }

.navbar-left, .navbar-right { display: flex; align-items: center; gap: 20px; flex: 1; }
.navbar-right { justify-content: flex-end; }
.navbar-user { display: flex; align-items: center; gap: 15px; }
.navbar-center { flex: 2; display: flex; justify-content: center; max-width: 600px; margin: 0 20px; }
.navbar-main { display: flex; align-items: center; gap: 20px; }

.logo-text { font-size: 1.2rem; font-weight: 800; background: linear-gradient(135deg, var(--color-primary) 0%, #8b5cf6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; white-space: nowrap; }

.nav-link { color: var(--color-text-main); font-weight: 500; font-size: 0.95rem; cursor: pointer; padding: 8px 12px; border-radius: 6px; white-space: nowrap; }
.nav-link:hover { color: var(--color-primary); background: rgba(79, 70, 229, 0.05); }
.nav-btn { padding: 8px 20px; border-radius: 20px; font-weight: 600; font-size: 0.9rem; transition: all 0.2s; white-space: nowrap; display: inline-block; }
.nav-btn.primary { background: var(--color-primary); color: white; box-shadow: 0 2px 5px rgba(79, 70, 229, 0.3); }
.nav-btn.primary:hover { background: var(--color-primary-hover); transform: translateY(-1px); }
.nav-btn.success { background: var(--color-success); color: white; }

.search-form { position: relative; width: 100%; }
.search-input { width: 100%; padding: 10px 20px; border-radius: 30px; border: 1px solid #e5e7eb; background: #f9fafb; outline: none; transition: all 0.2s; }
.search-input:focus { border-color: var(--color-primary); background: white; box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1); }
.search-btn { position: absolute; right: 12px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; opacity: 0.6; font-size: 1.1rem; }

.dropdown-wrapper { position: relative; height: 100%; display: flex; align-items: center; }
.dropdown-wrapper:hover .dropdown-menu { opacity: 1; visibility: visible; transform: translateY(0); }
.dropdown-menu { position: absolute; top: 100%; left: 0; width: 180px; background: white; border-radius: 8px; box-shadow: var(--shadow-lg); border: 1px solid #f3f4f6; padding: 8px; opacity: 0; visibility: hidden; transform: translateY(10px); transition: all 0.2s ease; z-index: 200; }
.dropdown-menu.right { left: auto; right: 0; }
.dropdown-item { display: block; padding: 8px 12px; color: var(--color-text-main); font-size: 0.9rem; border-radius: 4px; }
.dropdown-item:hover { background: #f3f4f6; color: var(--color-primary); }
.dropdown-item.danger { color: var(--color-danger); }
.dropdown-item.danger:hover { background: #fef2f2; }
.divider { height: 1px; background: #e5e7eb; margin: 6px 0; }

.user-trigger { display: flex; align-items: center; gap: 8px; }
.nav-avatar { width: 32px; height: 32px; border-radius: 50%; object-fit: cover; border: 2px solid #e0e7ff; }
.username { font-weight: 600; max-width: 100px; overflow: hidden; text-overflow: ellipsis; }
</style>
