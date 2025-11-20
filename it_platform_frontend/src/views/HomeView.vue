<script setup>
import { useRouter, RouterLink } from 'vue-router'
import { ref, onMounted } from 'vue'
import apiClient from '@/api'
import { useAuthStore } from '@/stores/authStore'
import ParticleBackground from '@/components/ParticleBackground.vue'
import CategoryPopularityChart from '@/components/CategoryPopularityChart.vue'
import { getFullCoverImagePath, handleImageError, formatDate } from '@/utils/common'

const router = useRouter()
const authStore = useAuthStore()

const hotCourses = ref([])
const newCourses = ref([])
const likedCourses = ref([])
const loading = ref(true)

const recordView = (courseId) => {
  try { apiClient.post(`/api/courses/${courseId}/record_view/`) } catch (e) {}
}

const handleStartLearning = () => {
  if (authStore.isAuthenticated) {
    router.push({ name: 'courses' })
  } else {
    router.push({ name: 'login' })
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const [hotRes, newRes, likedRes] = await Promise.all([
      apiClient.get('/api/courses/popular/'),
      apiClient.get('/api/courses/newest/'),
      apiClient.get('/api/courses/top_liked/')
    ]);
    hotCourses.value = hotRes.data
    newCourses.value = newRes.data
    likedCourses.value = likedRes.data
  } catch (error) {
    console.error("加载首页数据失败:", error)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="home-view-wrapper">
    <ParticleBackground />

    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">
          点亮你的 <span class="gradient-text">技术未来</span>
        </h1>
        <p class="hero-subtitle">
          汇聚顶尖 IT 职业技能课程，从编程入门到架构进阶，开启你的数字化职业生涯。
        </p>
        <div class="hero-actions">
          <button @click="handleStartLearning" class="btn-primary-lg">开始学习 🚀</button>
          <RouterLink :to="{ name: 'about' }" class="btn-outline-lg">了解更多</RouterLink>
        </div>
      </div>
      <div class="hero-visual">
        <img src="/hero-banner.png" alt="Online Learning" class="hero-img floating" />
      </div>
    </section>

    <div class="ranking-container">
      
      <div class="ranking-column">
        <div class="column-header">
          <h3>🔥 热门课程</h3>
          <span class="tag">TOP 3</span>
        </div>
        <div class="card-list">
          <RouterLink 
            v-for="(course, index) in hotCourses" :key="course.id"
            :to="`/courses/${course.id}`" 
            class="mini-card"
            @click="recordView(course.id)"
          >
            <div class="rank-badge" :class="`rank-${index+1}`">{{ index + 1 }}</div>
            <div class="img-wrapper">
              <img :src="getFullCoverImagePath(course.cover_image)" @error="handleImageError" />
            </div>
            <div class="info">
              <h4>{{ course.title }}</h4>
              <div class="meta">
                <span>👁️ {{ course.view_count }} 观看</span>
                <span>👤 {{ course.instructor?.username }}</span>
              </div>
            </div>
          </RouterLink>
        </div>
      </div>

      <div class="ranking-column">
        <div class="column-header">
          <h3>🆕 新课速递</h3>
        </div>
        <div class="card-list">
          <RouterLink 
            v-for="(course, index) in newCourses" :key="course.id"
            :to="`/courses/${course.id}`" 
            class="mini-card"
            @click="recordView(course.id)"
          >
            <div class="img-wrapper">
              <img :src="getFullCoverImagePath(course.cover_image)" @error="handleImageError" />
            </div>
            <div class="info">
              <h4>{{ course.title }}</h4>
              <div class="meta">
                <span>📅 {{ formatDate(course.created_at) }}</span>
              </div>
            </div>
          </RouterLink>
        </div>
      </div>

      <div class="ranking-column">
        <div class="column-header">
          <h3>👍 口碑好课</h3>
        </div>
        <div class="card-list">
          <RouterLink 
            v-for="(course, index) in likedCourses" :key="course.id"
            :to="`/courses/${course.id}`" 
            class="mini-card"
            @click="recordView(course.id)"
          >
            <div class="img-wrapper">
              <img :src="getFullCoverImagePath(course.cover_image)" @error="handleImageError" />
            </div>
            <div class="info">
              <h4>{{ course.title }}</h4>
              <div class="meta highlight">
                <span>❤️ {{ course.like_count }} 点赞</span>
              </div>
            </div>
          </RouterLink>
        </div>
      </div>

    </div>

    <section class="chart-section">
      <CategoryPopularityChart />
    </section>

  </div>
</template>

<style scoped>
.home-view-wrapper {
  width: 100%;
  min-height: 100vh;
  background-color: transparent;
  position: relative;
}

/* Hero Section */
.hero-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto;
  padding: 80px 20px;
  position: relative;
  z-index: 1;
}
.hero-content { max-width: 50%; }
.hero-title {
  font-size: 3.5rem;
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 20px;
  color: var(--color-text-main);
}
.gradient-text {
  background: linear-gradient(135deg, var(--color-primary) 0%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.hero-subtitle {
  font-size: 1.1rem;
  color: var(--color-text-muted);
  margin-bottom: 40px;
  line-height: 1.6;
}
.hero-actions { display: flex; gap: 15px; }
.btn-primary-lg, .btn-outline-lg {
  padding: 12px 32px;
  border-radius: 50px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}
.btn-primary-lg {
  background: var(--color-primary);
  color: white;
  border: none;
  box-shadow: 0 10px 20px rgba(79, 70, 229, 0.3);
}
.btn-primary-lg:hover { transform: translateY(-3px); background: var(--color-primary-hover); }
.btn-outline-lg {
  background: white;
  border: 1px solid #e5e7eb;
  color: var(--color-text-main);
}
.btn-outline-lg:hover { background: #f9fafb; }

.hero-visual img { max-width: 100%; height: auto; max-height: 400px; }
.floating { animation: float 6s ease-in-out infinite; }
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
}

/* Ranking Grid */
.ranking-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 30px;
  max-width: 1200px;
  margin: 0 auto 60px;
  padding: 0 20px;
  position: relative;
  z-index: 1;
}
.ranking-column {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 24px;
  box-shadow: var(--shadow-md);
  border: 1px solid rgba(255,255,255,0.5);
}
.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(0,0,0,0.05);
}
.column-header h3 { font-size: 1.2rem; font-weight: 700; color: var(--color-text-main); margin: 0; }
.tag { background: #e0e7ff; color: var(--color-primary); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }

.mini-card {
  display: flex;
  align-items: center;
  padding: 10px;
  border-radius: 12px;
  background: white;
  margin-bottom: 12px;
  transition: all 0.3s ease;
  text-decoration: none;
  border: 1px solid transparent;
}
.mini-card:hover {
  transform: translateX(5px);
  box-shadow: var(--shadow-md);
  border-color: rgba(79, 70, 229, 0.2);
}
.rank-badge {
  font-size: 1.5rem; font-weight: 800; color: #e5e7eb; margin-right: 15px; width: 20px; text-align: center;
}
.rank-1 { color: #f59e0b; } .rank-2 { color: #94a3b8; } .rank-3 { color: #b45309; }

.img-wrapper {
  width: 80px; height: 50px; border-radius: 6px; overflow: hidden; margin-right: 15px; flex-shrink: 0;
}
.img-wrapper img { width: 100%; height: 100%; object-fit: cover; }
.info h4 {
  margin: 0 0 4px; font-size: 0.95rem; color: var(--color-text-main); font-weight: 600;
  display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden;
}
.meta { font-size: 0.75rem; color: var(--color-text-muted); display: flex; gap: 10px; }
.meta.highlight { color: var(--color-danger); font-weight: 500; }

/* Chart Section */
.chart-section {
  max-width: 1200px;
  margin: 0 auto 60px;
  padding: 20px;
  position: relative;
  z-index: 1;
}

@media (max-width: 768px) {
  .hero-section { flex-direction: column-reverse; text-align: center; padding: 40px 20px; }
  .hero-content { max-width: 100%; }
  .hero-title { font-size: 2.5rem; }
  .hero-actions { justify-content: center; }
}
</style>