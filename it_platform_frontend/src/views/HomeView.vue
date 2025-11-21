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
const loading = ref(true)

// 【方案 H 数据】FAQ
const faqs = ref([
  { q: '课程是免费的吗？', a: '目前平台处于推广期，大部分课程均可免费学习，注册账号即可观看。', open: true },
  { q: '学习过程中遇到问题怎么办？', a: '每节课下都有评论区，您可以留言提问，讲师和同学会热心解答。', open: false },
  { q: '如何成为平台讲师？', a: '如果您有技术专长，可以在个人中心申请成为讲师，审核通过后即可发布课程。', open: false },
])

const toggleFaq = (index) => { faqs.value[index].open = !faqs.value[index].open }

const recordView = (courseId) => { try { apiClient.post(`/api/courses/${courseId}/record_view/`) } catch (e) {} }
const handleStartLearning = () => { router.push(authStore.isAuthenticated ? { name: 'courses' } : { name: 'login' }) }

onMounted(async () => {
  loading.value = true
  try {
    const [hotRes, newRes, likedRes] = await Promise.all([
      apiClient.get('/api/courses/popular/'), apiClient.get('/api/courses/newest/'), apiClient.get('/api/courses/top_liked/')
    ]);
    hotCourses.value = hotRes.data; newCourses.value = newRes.data; likedCourses.value = likedRes.data
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

    <div class="ranking-container">
      <div class="ranking-column">
        <div class="column-header"><h3>🔥 热门课程</h3><span class="tag">TOP 3</span></div>
        <div class="card-list">
          <RouterLink v-for="(c, i) in hotCourses" :key="c.id" :to="`/courses/${c.id}`" class="mini-card" @click="recordView(c.id)">
            <div class="rank-badge" :class="`rank-${i+1}`">{{ i + 1 }}</div>
            <div class="img-wrapper"><img :src="getFullCoverImagePath(c.cover_image)" @error="handleImageError" /></div>
            <div class="info"><h4>{{ c.title }}</h4><div class="meta"><span>👁️ {{ c.view_count }}</span></div></div>
          </RouterLink>
        </div>
      </div>
      <div class="ranking-column">
        <div class="column-header"><h3>🆕 新课速递</h3></div>
        <div class="card-list">
          <RouterLink v-for="c in newCourses" :key="c.id" :to="`/courses/${c.id}`" class="mini-card" @click="recordView(c.id)">
            <div class="img-wrapper"><img :src="getFullCoverImagePath(c.cover_image)" @error="handleImageError" /></div>
            <div class="info"><h4>{{ c.title }}</h4><div class="meta"><span>📅 {{ formatDate(c.created_at) }}</span></div></div>
          </RouterLink>
        </div>
      </div>
      <div class="ranking-column">
        <div class="column-header"><h3>👍 口碑好课</h3></div>
        <div class="card-list">
          <RouterLink v-for="c in likedCourses" :key="c.id" :to="`/courses/${c.id}`" class="mini-card" @click="recordView(c.id)">
            <div class="img-wrapper"><img :src="getFullCoverImagePath(c.cover_image)" @error="handleImageError" /></div>
            <div class="info"><h4>{{ c.title }}</h4><div class="meta highlight"><span>❤️ {{ c.like_count }}</span></div></div>
          </RouterLink>
        </div>
      </div>
    </div>

    <section class="faq-section">
      <div class="section-header">
        <h3>常见问题解答</h3>
      </div>
      <div class="faq-list">
        <div
          v-for="(item, index) in faqs"
          :key="index"
          class="faq-item"
          :class="{ open: item.open }"
          @click="toggleFaq(index)"
        >
          <div class="faq-question">
            <h4>{{ item.q }}</h4>
            <span class="toggle-icon">{{ item.open ? '−' : '+' }}</span>
          </div>
          <div class="faq-answer" v-show="item.open">
            <p>{{ item.a }}</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* 复用样式省略... */
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

/* 【方案 H 样式】FAQ */
.faq-section { max-width: 800px; margin: 0 auto 80px; padding: 0 20px; position: relative; z-index: 1; }
.section-header { text-align: center; margin-bottom: 40px; }
.section-header h3 { font-size: 1.8rem; font-weight: 800; color: var(--color-text-main); }

.faq-item { background: white; border-radius: 12px; border: 1px solid #f3f4f6; margin-bottom: 15px; overflow: hidden; transition: all 0.3s; cursor: pointer; }
.faq-item:hover { box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
.faq-question { padding: 20px; display: flex; justify-content: space-between; align-items: center; background: #fff; }
.faq-question h4 { margin: 0; font-size: 1.1rem; font-weight: 600; color: #333; }
.toggle-icon { font-size: 1.5rem; font-weight: 300; color: var(--color-primary); transition: transform 0.3s; }
.faq-answer { padding: 0 20px 20px; color: #6b7280; line-height: 1.6; border-top: 1px solid #f9fafb; }
.faq-item.open .toggle-icon { transform: rotate(45deg); } /* 加号变叉号 */

@media (max-width: 768px) {
  .hero-section { flex-direction: column-reverse; text-align: center; padding: 40px 20px; }
  .hero-content { max-width: 100%; }
  .hero-title { font-size: 2.5rem; }
  .hero-actions { justify-content: center; }
}
</style>
