<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/api'
import BackButton from '@/components/BackButton.vue'
import { getFullMediaUrl } from '@/utils/common'

const router = useRouter()

const watchHistory = ref([])
const isLoading = ref(true)

onMounted(async () => {
  try {
    const res = await apiClient.get('/api/video-progress/history/')
    watchHistory.value = res.data
  } catch (e) {
    console.error('Failed to load history', e)
  } finally {
    isLoading.value = false
  }
})

const formatDuration = (seconds) => {
  if (!seconds) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

const formatProgress = (pos, dur) => {
  if (!dur) return 0
  return Math.min(100, Math.round((pos / dur) * 100))
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const goToLesson = (item) => {
  router.push({
    name: 'lesson-watch',
    params: { courseId: item.course_id, lessonId: item.lesson },
    query: { t: Math.floor(item.last_position) }  // 传递上次观看的时间点
  })
}
</script>

<template>
  <div class="history-page">
    <BackButton :fallback-route="{ name: 'courses' }" text="返回课程" small />

    <div class="page-header">
      <h1>📺 观看历史</h1>
      <p>继续您上次的学习进度</p>
    </div>

    <div v-if="isLoading" class="loading-state">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="watchHistory.length === 0" class="empty-state">
      <div class="empty-icon">📺</div>
      <h3>暂无观看记录</h3>
      <p>开始观看课程后，这里会显示您的学习历史</p>
      <router-link :to="{ name: 'courses' }" class="btn-primary">浏览课程</router-link>
    </div>

    <div v-else class="history-grid">
      <div 
        v-for="item in watchHistory" 
        :key="item.id" 
        class="history-card"
        @click="goToLesson(item)"
      >
        <div class="card-cover">
          <img v-if="item.cover_image" :src="getFullMediaUrl(item.cover_image)" alt="Cover">
          <div v-else class="cover-placeholder">
            <span>📹</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: formatProgress(item.last_position, item.duration) + '%' }"></div>
          </div>
          <div class="play-overlay">
            <span class="play-icon">▶</span>
          </div>
        </div>
        <div class="card-info">
          <h3 class="course-title">{{ item.course_title }}</h3>
          <p class="lesson-title">{{ item.lesson_title }}</p>
          <div class="card-meta">
            <span class="time-badge">▶ {{ formatDuration(item.last_position) }} / {{ formatDuration(item.duration) }}</span>
            <span class="date">{{ formatDate(item.updated_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.history-page {
  max-width: 1200px;
  margin: 30px auto;
  padding: 0 20px;
}

.page-header {
  margin-bottom: 30px;
}

.page-header h1 {
  font-size: 1.8rem;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.page-header p {
  color: #6b7280;
  margin: 0;
}

.loading-state, .empty-state {
  text-align: center;
  padding: 80px 20px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #4f46e5;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 20px;
}

.empty-state h3 {
  font-size: 1.3rem;
  color: #374151;
  margin: 0 0 10px 0;
}

.empty-state p {
  color: #9ca3af;
  margin: 0 0 25px 0;
}

.btn-primary {
  display: inline-block;
  padding: 12px 24px;
  background: #4f46e5;
  color: white;
  border-radius: 8px;
  font-weight: 600;
  text-decoration: none;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: #4338ca;
}

.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.history-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  border: 1px solid #f3f4f6;
  cursor: pointer;
  transition: all 0.3s;
}

.history-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 30px rgba(0,0,0,0.12);
  border-color: #c7d2fe;
}

.card-cover {
  position: relative;
  aspect-ratio: 16/9;
  background: #1f2937;
  overflow: hidden;
}

.card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.history-card:hover .card-cover img {
  transform: scale(1.05);
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  font-size: 2.5rem;
}

.progress-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: rgba(0,0,0,0.4);
}

.progress-fill {
  height: 100%;
  background: #10b981;
  transition: width 0.3s;
}

.play-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.3);
  opacity: 0;
  transition: opacity 0.3s;
}

.history-card:hover .play-overlay {
  opacity: 1;
}

.play-icon {
  width: 50px;
  height: 50px;
  background: rgba(255,255,255,0.95);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  color: #4f46e5;
  box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}

.card-info {
  padding: 16px;
}

.course-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 6px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.lesson-title {
  font-size: 0.9rem;
  color: #6b7280;
  margin: 0 0 12px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.time-badge {
  font-size: 0.8rem;
  font-weight: 600;
  color: #10b981;
  background: #ecfdf5;
  padding: 4px 10px;
  border-radius: 20px;
}

.date {
  font-size: 0.8rem;
  color: #9ca3af;
}

@media (max-width: 640px) {
  .history-grid {
    grid-template-columns: 1fr;
  }
}
</style>
