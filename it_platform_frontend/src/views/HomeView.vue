<script setup>
import { useRouter, RouterLink } from 'vue-router'
import { ref, onMounted } from 'vue'
import apiClient from '@/api'
import { useAuthStore } from '@/stores/authStore'
import ParticleBackground from '@/components/ParticleBackground.vue'
import { getFullCoverImagePath, handleImageError, formatDate } from '@/utils/common'

const router = useRouter()
const authStore = useAuthStore()
const hotCourses = ref([])
const newCourses = ref([])
const likedCourses = ref([])
const categories = ref([])
const loading = ref(true)

// 特色功能数据
const features = ref([
  { icon: '🎯', title: '专业课程体系', desc: '从零基础到高级进阶，完整学习路径' },
  { icon: '👨‍💻', title: '实战导向教学', desc: '真实项目案例，直接应用到工作中' },
  { icon: '💬', title: '互动答疑社区', desc: '讲师在线答疑，同学互助学习' },
  { icon: '📜', title: '学习认证证书', desc: '完成课程获得专业认证' }
])

// 获取分类图标
const getCategoryIcon = (name) => {
  const iconMap = {
    'Python': '🐍', 'JavaScript': '📜', 'Java': '☕',
    '前端开发': '🎨', '后端开发': '⚙️', '数据科学': '📊',
    '人工智能': '🤖', '移动开发': '📱', 'Web开发': '🌐',
    '数据库': '🗄️', '云计算': '☁️', '运维': '🔧'
  }
  return iconMap[name] || '💻'
}

const recordView = (courseId) => { try { apiClient.post(`/api/courses/${courseId}/record_view/`) } catch (e) {} }
const handleStartLearning = () => { router.push(authStore.isAuthenticated ? { name: 'courses' } : { name: 'login' }) }

onMounted(async () => {
  loading.value = true
  try {
    const [hotRes, newRes, likedRes, catRes] = await Promise.all([
      apiClient.get('/api/courses/popular/'),
      apiClient.get('/api/courses/newest/'),
      apiClient.get('/api/courses/top_liked/'),
      apiClient.get('/api/categories/')
    ])
    hotCourses.value = hotRes.data
    newCourses.value = newRes.data
    likedCourses.value = likedRes.data
    categories.value = catRes.data.slice(0, 6)
  } catch (error) { console.error(error) } finally { loading.value = false }
})
</script>

<template>
  <div class="home-view-wrapper">
    <ParticleBackground />
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">点亮你的 <span class="gradient-text">技术未来</span></h1>
        <p class="hero-subtitle">汇聚顶尖 IT 职业技能课程，从编程入门到架构进阶，开启你的数字化职业生涯。</p>
        <div class="hero-actions">
          <button @click="handleStartLearning" class="btn-primary-lg">开始学习 🚀</button>
          <RouterLink :to="{ name: 'about' }" class="btn-outline-lg">了解更多</RouterLink>
        </div>
      </div>
      <div class="hero-visual"><img src="/hero-banner.png" class="hero-img floating" /></div>
    </section>

    <!-- 课程排行 -->
    <div class="ranking-container">
      <div class="ranking-column">
        <div class="column-header"><h3>🔥 热门课程</h3><span class="tag">TOP 3</span></div>
        <div class="card-list">
          <RouterLink v-for="(c, i) in hotCourses" :key="c.id" :to="`/courses/${c.id}`" class="mini-card" @click="recordView(c.id)">
            <div class="rank-badge" :class="`rank-${i+1}`">{{ i + 1 }}</div>
            <div class="img-wrapper"><img :src="getFullCoverImagePath(c.cover_image)" @error="handleImageError" loading="lazy" /></div>
            <div class="info"><h4>{{ c.title }}</h4><div class="meta"><span>👁️ {{ c.view_count }}</span></div></div>
          </RouterLink>
        </div>
      </div>
      <div class="ranking-column">
        <div class="column-header"><h3>🆕 新课速递</h3></div>
        <div class="card-list">
          <RouterLink v-for="c in newCourses" :key="c.id" :to="`/courses/${c.id}`" class="mini-card" @click="recordView(c.id)">
            <div class="img-wrapper"><img :src="getFullCoverImagePath(c.cover_image)" @error="handleImageError" loading="lazy" /></div>
            <div class="info"><h4>{{ c.title }}</h4><div class="meta"><span>📅 {{ formatDate(c.created_at) }}</span></div></div>
          </RouterLink>
        </div>
      </div>
      <div class="ranking-column">
        <div class="column-header"><h3>👍 口碑好课</h3></div>
        <div class="card-list">
          <RouterLink v-for="c in likedCourses" :key="c.id" :to="`/courses/${c.id}`" class="mini-card" @click="recordView(c.id)">
            <div class="img-wrapper"><img :src="getFullCoverImagePath(c.cover_image)" @error="handleImageError" loading="lazy" /></div>
            <div class="info"><h4>{{ c.title }}</h4><div class="meta highlight"><span>❤️ {{ c.like_count }}</span></div></div>
          </RouterLink>
        </div>
      </div>
    </div>

    <!-- 特色功能展示区 -->
    <section class="features-section">
      <h2 class="section-title">为什么选择我们</h2>
      <div class="features-grid">
        <div v-for="feature in features" :key="feature.title" class="feature-card">
          <div class="feature-icon">{{ feature.icon }}</div>
          <h3>{{ feature.title }}</h3>
          <p>{{ feature.desc }}</p>
        </div>
      </div>
    </section>

    <!-- 课程分类导航 -->
    <section class="categories-section" v-if="categories.length > 0">
      <h2 class="section-title">热门课程分类</h2>
      <div class="categories-grid">
        <RouterLink
          v-for="cat in categories"
          :key="cat.id"
          :to="{ name: 'courses', query: { category: cat.slug } }"
          class="category-card"
        >
          <div class="category-icon">{{ getCategoryIcon(cat.name) }}</div>
          <h3>{{ cat.name }}</h3>
          <p>{{ cat.total_likes || 0 }} 人喜欢</p>
        </RouterLink>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-view-wrapper { width: 100%; min-height: 100vh; position: relative; }
.hero-section { display: flex; align-items: center; justify-content: space-between; max-width: 1200px; margin: 0 auto; padding: 80px 20px; position: relative; z-index: 1; }
.hero-content { max-width: 50%; }
.hero-title { font-size: 3.5rem; font-weight: 800; margin-bottom: 20px; color: var(--color-text-main); }
.gradient-text { background: linear-gradient(135deg, var(--color-primary) 0%, #a855f7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.hero-subtitle { font-size: 1.1rem; color: var(--color-text-muted); margin-bottom: 40px; }
.hero-actions { display: flex; gap: 15px; }
.btn-primary-lg { background: var(--color-primary); color: white; border: none; padding: 12px 32px; border-radius: 50px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: transform 0.2s; }
.btn-primary-lg:hover { transform: translateY(-3px); }
.btn-outline-lg { background: white; border: 1px solid #e5e7eb; color: var(--color-text-main); padding: 12px 32px; border-radius: 50px; font-size: 1rem; font-weight: 600; text-decoration: none; transition: background 0.2s; }
.btn-outline-lg:hover { background: #f9fafb; }
.hero-visual img { max-width: 100%; max-height: 400px; mix-blend-mode: multiply; animation: float 6s ease-in-out infinite; }
@keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-20px); } }
.ranking-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; max-width: 1200px; margin: 0 auto 60px; padding: 0 20px; position: relative; z-index: 1; }
.ranking-column { background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); border-radius: 16px; padding: 24px; border: 1px solid rgba(255,255,255,0.5); }
.column-header { display: flex; justify-content: space-between; margin-bottom: 20px; border-bottom: 1px solid rgba(0,0,0,0.05); padding-bottom: 10px; }
.column-header h3 { font-size: 1.2rem; margin: 0; color: var(--color-text-main); }
.tag { background: #e0e7ff; color: var(--color-primary); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }
.mini-card { display: flex; align-items: center; padding: 10px; border-radius: 12px; background: white; margin-bottom: 12px; text-decoration: none; transition: transform 0.3s; }
.mini-card:hover { transform: translateX(5px); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.rank-badge { font-size: 1.5rem; font-weight: 800; color: #e5e7eb; margin-right: 15px; width: 20px; text-align: center; }
.rank-1 { color: #f59e0b; } .rank-2 { color: #94a3b8; } .rank-3 { color: #b45309; }
.img-wrapper { width: 80px; height: 50px; border-radius: 6px; overflow: hidden; margin-right: 15px; flex-shrink: 0; }
.img-wrapper img { width: 100%; height: 100%; object-fit: cover; }
.info h4 { margin: 0 0 4px; font-size: 0.95rem; color: var(--color-text-main); overflow: hidden; white-space: nowrap; text-overflow: ellipsis; max-width: 180px; }
.meta { font-size: 0.75rem; color: var(--color-text-muted); }
.meta.highlight { color: var(--color-danger); }

.section-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 50px;
  text-align: center;
  color: var(--color-text-main);
}

.features-section {
  max-width: 1200px;
  margin: 80px auto;
  padding: 0 20px;
  position: relative;
  z-index: 1;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 30px;
}

.feature-card {
  background: white;
  padding: 40px 20px;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  transition: transform 0.3s, box-shadow 0.3s;
  text-align: center;
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}

.feature-icon {
  font-size: 3rem;
  margin-bottom: 20px;
}

.feature-card h3 {
  font-size: 1.2rem;
  margin-bottom: 10px;
  color: var(--color-text-main);
}

.feature-card p {
  color: var(--color-text-muted);
  font-size: 0.95rem;
  line-height: 1.6;
}

.categories-section {
  max-width: 1200px;
  margin: 60px auto 80px;
  padding: 0 20px;
  position: relative;
  z-index: 1;
}

.categories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 20px;
}

.category-card {
  background: white;
  padding: 30px 20px;
  border-radius: 12px;
  text-align: center;
  text-decoration: none;
  border: 2px solid #f3f4f6;
  transition: all 0.3s;
}

.category-card:hover {
  border-color: var(--color-primary);
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(99, 102, 241, 0.1);
}

.category-icon {
  font-size: 2.5rem;
  margin-bottom: 15px;
}

.category-card h3 {
  font-size: 1.1rem;
  margin-bottom: 8px;
  color: var(--color-text-main);
}

.category-card p {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

@media (max-width: 768px) {
  .hero-section { flex-direction: column-reverse; text-align: center; padding: 40px 20px; }
  .hero-content { max-width: 100%; }
  .hero-title { font-size: 2.5rem; }
  .hero-actions { justify-content: center; }
  
  .features-grid { grid-template-columns: 1fr; }
  .categories-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
