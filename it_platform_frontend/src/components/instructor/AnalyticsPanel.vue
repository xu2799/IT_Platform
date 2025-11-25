<script setup>
import { ref, onMounted } from 'vue'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js'
import apiClient from '@/api'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const stats = ref({ total_students: 0, total_views: 0, total_likes: 0 })
const chartData = ref(null)
const loaded = ref(false)

onMounted(async () => {
  try {
    const res = await apiClient.get('/api/instructor/analytics/')
    stats.value = res.data

    const courses = res.data.course_data
    chartData.value = {
      labels: courses.map(c => c.title.substring(0, 8) + '...'),
      datasets: [
        { label: '浏览量', backgroundColor: '#3b82f6', data: courses.map(c => c.view_count) },
        { label: '学员数', backgroundColor: '#10b981', data: courses.map(c => c.students_num) }
      ]
    }
    loaded.value = true
  } catch (e) {
    console.error(e)
  }
})

const chartOptions = { responsive: true, maintainAspectRatio: false }
</script>

<template>
  <div class="analytics-panel">
    <div class="stats-cards">
      <div class="card purple">
        <h3>累计学员</h3>
        <p>{{ stats.total_students }}</p>
      </div>
      <div class="card blue">
        <h3>总浏览量</h3>
        <p>{{ stats.total_views }}</p>
      </div>
      <div class="card pink">
        <h3>获得点赞</h3>
        <p>{{ stats.total_likes }}</p>
      </div>
    </div>

    <div class="chart-section">
      <h3>课程数据 Top 5</h3>
      <div class="chart-wrapper" v-if="loaded">
        <Bar :data="chartData" :options="chartOptions" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }
.card { padding: 20px; border-radius: 12px; color: white; text-align: center; }
.card h3 { margin: 0 0 10px; font-size: 1rem; opacity: 0.9; }
.card p { margin: 0; font-size: 2rem; font-weight: bold; }
.purple { background: linear-gradient(135deg, #8b5cf6, #6d28d9); }
.blue { background: linear-gradient(135deg, #3b82f6, #2563eb); }
.pink { background: linear-gradient(135deg, #ec4899, #db2777); }

.chart-section { background: white; padding: 20px; border-radius: 12px; border: 1px solid #e5e7eb; height: 400px; }
.chart-wrapper { height: 320px; }
</style>
