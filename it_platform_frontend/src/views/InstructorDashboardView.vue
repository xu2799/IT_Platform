<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import apiClient from '@/api'
import BackButton from '@/components/BackButton.vue'

// 导入新组件
import AnalyticsPanel from '@/components/instructor/AnalyticsPanel.vue'
import QAPanel from '@/components/instructor/QAPanel.vue'
import AssignmentsPanel from '@/components/instructor/AssignmentsPanel.vue'

const activeTab = ref('courses') // courses, analytics, qa, assignments
const courses = ref([])
const loading = ref(false)

const fetchInstructorCourses = async () => {
    loading.value = true
    try {
        const response = await apiClient.get('/api/instructor/courses/')
        courses.value = response.data.results || response.data
    } catch (error) {
        console.error(error)
    } finally {
        loading.value = false
    }
}

const getFullCoverImagePath = (relativePath) => {
    if (!relativePath) return 'https://via.placeholder.com/300x150.png?text=No+Cover'
    const baseUrl = apiClient.defaults.baseURL || ''
    return relativePath.startsWith('http') ? relativePath : `${baseUrl}${relativePath}`
}

onMounted(() => {
    fetchInstructorCourses()
})
</script>

<template>
  <div class="dashboard-container">
    <BackButton :fallback-route="{ name: 'courses' }" text="返回课程列表" small />

    <h1 class="section-title">👨‍🏫 讲师工作台</h1>

    <div class="dashboard-tabs">
      <button :class="{ active: activeTab === 'courses' }" @click="activeTab = 'courses'">
        📚 课程管理
      </button>
      <button :class="{ active: activeTab === 'assignments' }" @click="activeTab = 'assignments'">
        📝 作业 & 批改
      </button>
      <button :class="{ active: activeTab === 'qa' }" @click="activeTab = 'qa'">
        💬 答疑中心
      </button>
      <button :class="{ active: activeTab === 'analytics' }" @click="activeTab = 'analytics'">
        📊 数据分析
      </button>
    </div>

    <div v-if="activeTab === 'courses'" class="tab-content fade-in">
      <div v-if="loading">加载中...</div>
      <div class="header-row">
        <h3>我的课程 ({{ courses.length }})</h3>
        <RouterLink to="/create-course" class="create-btn">+ 创建新课程</RouterLink>
      </div>

      <section class="course-grid" v-if="courses.length > 0">
        <div v-for="course in courses" :key="course.id" class="course-card">
          <div class="course-thumbnail">
            <img :src="getFullCoverImagePath(course.cover_image)" class="cover-image">
            <span v-if="course.category" class="category-tag">{{ course.category.name }}</span>
          </div>
          <div class="card-content">
            <h3>{{ course.title }}</h3>
          </div>
          <div class="card-admin-actions">
            <RouterLink :to="{ name: 'course-detail', params: { id: course.id }, query: { manage: 'true' } }" class="action-button manage-button">管理内容</RouterLink>
            <RouterLink :to="{ name: 'course-edit', params: { id: course.id } }" class="action-button edit-button">编辑</RouterLink>
          </div>
        </div>
      </section>
      <div v-else-if="!loading" class="no-results">暂无课程</div>
    </div>

    <div v-if="activeTab === 'assignments'" class="tab-content fade-in">
      <AssignmentsPanel />
    </div>

    <div v-if="activeTab === 'qa'" class="tab-content fade-in">
      <QAPanel />
    </div>

    <div v-if="activeTab === 'analytics'" class="tab-content fade-in">
      <AnalyticsPanel />
    </div>

  </div>
</template>

<style scoped>
.dashboard-container { max-width: 1200px; margin: 0 auto; padding: 30px 20px; }
.section-title { text-align: center; margin-bottom: 30px; color: #1f2937; }

/* Tabs 样式 */
.dashboard-tabs { display: flex; justify-content: center; gap: 10px; margin-bottom: 30px; background: white; padding: 10px; border-radius: 50px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); width: fit-content; margin-left: auto; margin-right: auto; }
.dashboard-tabs button { padding: 10px 24px; border: none; background: transparent; border-radius: 30px; font-size: 1rem; font-weight: 600; color: #6b7280; cursor: pointer; transition: all 0.2s; }
.dashboard-tabs button:hover { color: #4f46e5; background: #f3f4f6; }
.dashboard-tabs button.active { background: #4f46e5; color: white; box-shadow: 0 2px 5px rgba(79, 70, 229, 0.3); }

.tab-content { min-height: 400px; }
.fade-in { animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }

/* 课程列表样式复用 */
.header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.create-btn { background: #10b981; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold; transition: transform 0.2s; }
.create-btn:hover { transform: translateY(-2px); }

.course-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 25px; }
.course-card { background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #f3f4f6; display: flex; flex-direction: column; }
.course-thumbnail { height: 160px; position: relative; background: #eee; }
.cover-image { width: 100%; height: 100%; object-fit: cover; }
.category-tag { position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.6); color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; }
.card-content { padding: 15px; flex: 1; }
.card-content h3 { margin: 0; font-size: 1.1rem; color: #333; }
.card-admin-actions { display: flex; border-top: 1px solid #eee; }
.action-button { flex: 1; text-align: center; padding: 12px; font-size: 0.9rem; font-weight: 600; cursor: pointer; color: #555; transition: background 0.2s; }
.action-button:hover { background: #f9fafb; color: #4f46e5; }
.manage-button { border-right: 1px solid #eee; }
.no-results { text-align: center; color: #999; margin-top: 50px; font-size: 1.2rem; }
</style>
