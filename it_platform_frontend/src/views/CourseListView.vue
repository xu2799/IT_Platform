<script setup>
import { watch, onMounted, computed, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useCourseStore } from '@/stores/courseStore'
import { useAuthStore } from '@/stores/authStore'
import { getFullCoverImagePath, handleImageError, formatDate } from '@/utils/common'
import BackButton from '@/components/BackButton.vue'

const courseStore = useCourseStore()
const authStore = useAuthStore()
const route = useRoute()

const pageTitle = computed(() => {
  if (route.query.search) {
    return `搜索结果: "${route.query.search}"`
  }
  if (route.query.category) {
    const category = courseStore.categories.find(c => c.slug === route.query.category)
    return category ? `${category.name}` : '分类课程'
  }
  return '全部课程'
})

onMounted(() => {
  if (courseStore.categories.length === 0) {
    courseStore.fetchCategories()
  }
  if (authStore.token && (!authStore.user || authStore.user.favorited_courses === undefined)) {
      authStore.fetchUser()
  }
})

watch(() => route.query, (newQuery) => {
  courseStore.fetchCourses(newQuery)
}, { immediate: true, deep: true })
</script>

<template>
  <div class="page-container">

    <aside class="sidebar">

      <div class="sidebar-widget">
        <h3 class="widget-title">课程分类</h3>
        <ul class="category-list">
          <li>
            <RouterLink
              :to="{ name: 'courses' }"
              class="category-link"
              :class="{ active: !route.query.category && !route.query.search }"
            >
              全部课程
            </RouterLink>
          </li>
          <li v-for="category in courseStore.categories" :key="category.id">
            <RouterLink
              :to="{ name: 'courses', query: { category: category.slug } }"
              class="category-link"
              :class="{ active: route.query.category === category.slug }"
            >
              {{ category.name }}
            </RouterLink>
          </li>
        </ul>
      </div>

      <div class="sidebar-widget promo-widget">
        <h3>成为讲师 👨‍🏫</h3>
        <p>分享知识，获得收益，加入我们的讲师团队。</p>
        <RouterLink :to="{ name: 'become-instructor' }" class="btn-sm-primary">立即申请</RouterLink>
      </div>

    </aside>

    <main class="main-content">

      <div class="content-header">
        <h1>{{ pageTitle }}</h1>
        <div class="header-actions">
           <RouterLink
            v-if="route.query.search || route.query.category"
            :to="{ name: 'courses' }"
            class="clear-filter-btn"
          >
            清除筛选 ✕
          </RouterLink>
          <span class="course-count">共 {{ courseStore.courses.length }} 门课程</span>
        </div>
      </div>

      <div v-if="courseStore.isLoading" class="state-box">
        <div class="loader"></div>
        <p>正在加载...</p>
      </div>
      <div v-else-if="courseStore.error" class="state-box error">
        <p>{{ courseStore.error }}</p>
        <button @click="courseStore.fetchCourses(route.query)" class="btn-retry">重新加载</button>
      </div>

      <section v-else class="course-grid">
        <div v-for="course in courseStore.courses" :key="course.id" class="course-card">
          <RouterLink :to="`/courses/${course.id}`" class="card-link">
            <div class="thumbnail-box">
              <img
                  :src="getFullCoverImagePath(course.cover_image)"
                  :alt="course.title"
                  class="cover-img"
                  @error="handleImageError"
              >
              <span v-if="course.category" class="category-badge">
                  {{ course.category.name }}
              </span>
            </div>

            <div class="card-body">
              <h3 class="title" :title="course.title">{{ course.title }}</h3>
              <div class="meta-row">
                <span class="instructor">👤 {{ course.instructor?.username || '讲师' }}</span>
                <span class="date">{{ formatDate(course.created_at) }}</span>
              </div>
              <div class="card-footer">
                <div class="stat">👁️ {{ course.view_count }}</div>
                <div class="stat like">❤️ {{ course.like_count }}</div>
              </div>
            </div>
          </RouterLink>
        </div>
      </section>

      <div v-if="!courseStore.isLoading && !courseStore.courses.length" class="state-box empty">
          <p>📭 暂时没有找到相关课程</p>
          <RouterLink :to="{ name: 'courses' }" class="btn-primary">返回全部</RouterLink>
      </div>

    </main>
  </div>
</template>

<style scoped>
/* 使用 Grid 布局实现左右分栏 */
.page-container {
  padding: 30px 40px;
  max-width: 1600px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 250px 1fr; /* 左侧固定宽度 */
  gap: 40px;
  align-items: start;
}

/* --- 侧边栏样式 --- */
.sidebar-widget {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  border: 1px solid #f3f4f6;
}
.widget-title {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
  color: var(--color-text-main);
}

/* 分类列表 */
.category-list { list-style: none; padding: 0; margin: 0; }
.category-link {
  display: block;
  padding: 8px 12px;
  color: var(--color-text-muted);
  border-radius: 6px;
  margin-bottom: 5px;
  transition: all 0.2s;
  text-decoration: none;
}
.category-link:hover {
  background: #f3f4f6;
  color: var(--color-primary);
}
.category-link.active {
  background: #e0e7ff;
  color: var(--color-primary);
  font-weight: 600;
}

/* 推广卡片 */
.promo-widget {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-align: center;
}
.promo-widget h3 { color: white; font-size: 1.2rem; margin-bottom: 10px; }
.promo-widget p { font-size: 0.9rem; opacity: 0.9; margin-bottom: 15px; }
.btn-sm-primary {
  background: white;
  color: #764ba2;
  padding: 6px 16px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.9rem;
  text-decoration: none;
  display: inline-block;
}

/* --- 主内容区样式 --- */
.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}
.content-header h1 {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--color-text-main);
  margin: 0;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}
.course-count {
  color: var(--color-text-muted);
  font-size: 0.9rem;
}
.clear-filter-btn {
  font-size: 0.85rem;
  color: var(--color-primary);
  background: rgba(79, 70, 229, 0.1);
  padding: 5px 12px;
  border-radius: 20px;
  font-weight: 600;
  text-decoration: none;
}

/* Grid */
.course-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 30px;
}

/* 卡片样式 */
.course-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s;
  border: 1px solid #f3f4f6;
  position: relative;
}
.course-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-md);
  border-color: rgba(79, 70, 229, 0.1);
}
.card-link { text-decoration: none; color: inherit; display: flex; flex-direction: column; height: 100%; }
.thumbnail-box { position: relative; padding-top: 56.25%; overflow: hidden; }
.cover-img { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; transition: transform 0.5s; }
.course-card:hover .cover-img { transform: scale(1.08); }
.category-badge {
  position: absolute; top: 8px; left: 8px;
  background: rgba(255,255,255,0.95); color: var(--color-primary);
  padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 700;
}
.card-body { padding: 15px; flex-grow: 1; display: flex; flex-direction: column; }
.title {
  font-size: 1.1rem; font-weight: 700; color: var(--color-text-main); margin-bottom: 8px;
  line-height: 1.4; height: 2.8em; overflow: hidden;
}
.meta-row { display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--color-text-muted); margin-bottom: 12px; }
.card-footer { margin-top: auto; display: flex; justify-content: space-between; padding-top: 10px; border-top: 1px solid #f3f4f6; font-size: 0.8rem; color: var(--color-text-muted); }
.stat.like { color: var(--color-danger); }

/* 状态盒子 */
.state-box { text-align: center; padding: 60px 0; color: var(--color-text-muted); }
.btn-retry, .btn-primary {
  margin-top: 15px; padding: 8px 20px; border-radius: 6px;
  background: var(--color-primary); color: white; border: none; cursor: pointer; font-size: 0.9rem;
}

/* 响应式 */
@media (max-width: 900px) {
  .page-container { grid-template-columns: 1fr; }
  .sidebar { display: none; }
}
</style>
