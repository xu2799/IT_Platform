<script setup>
import { ref, onMounted } from 'vue'
import { useCourseStore } from '@/stores/courseStore.js'
import apiClient from '@/api.js'
import CategoryPopularityChart from '@/components/CategoryPopularityChart.vue'

const courseStore = useCourseStore()
const stats = ref({
  courses: 0,
  views: 0,
  likes: 0,
  pendingApps: 0
})

onMounted(async () => {
  // 1. 加载课程数据
  if (courseStore.courses.length === 0) await courseStore.fetchCourses()

  stats.value.courses = courseStore.courses.length
  stats.value.views = courseStore.courses.reduce((sum, c) => sum + (c.view_count || 0), 0)
  stats.value.likes = courseStore.courses.reduce((sum, c) => sum + (c.like_count || 0), 0)

  // 2. 加载申请数据
  try {
    const res = await apiClient.get('/api/applications/')
    const apps = res.data.results || res.data
    stats.value.pendingApps = apps.filter(a => a.status === 'pending').length
  } catch (e) { console.error(e) }
})
</script>

<template>
  <div class="dashboard-view">
    <div class="stats-row">
      <div class="stat-card bg-purple">
        <h3>总课程数</h3>
        <p class="number">{{ stats.courses }}</p>
      </div>
      <div class="stat-card bg-blue">
        <h3>全站浏览</h3>
        <p class="number">{{ stats.views }}</p>
      </div>
      <div class="stat-card bg-pink">
        <h3>总点赞</h3>
        <p class="number">{{ stats.likes }}</p>
      </div>
      <div class="stat-card bg-orange">
        <h3>待办审核</h3>
        <p class="number">{{ stats.pendingApps }}</p>
      </div>
    </div>

    <div class="charts-row">
      <div class="chart-panel">
        <CategoryPopularityChart />
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
.stat-card { padding: 25px; border-radius: 12px; color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.stat-card h3 { margin: 0 0 10px; font-size: 1rem; opacity: 0.9; }
.stat-card .number { margin: 0; font-size: 2.2rem; font-weight: 700; }

.bg-purple { background: linear-gradient(135deg, #8b5cf6, #6d28d9); }
.bg-blue { background: linear-gradient(135deg, #3b82f6, #2563eb); }
.bg-pink { background: linear-gradient(135deg, #ec4899, #db2777); }
.bg-orange { background: linear-gradient(135deg, #f59e0b, #d97706); }

.charts-row { display: flex; gap: 20px; }
.chart-panel { flex: 1; background: white; padding: 20px; border-radius: 12px; border: 1px solid #e5e7eb; }
</style>
