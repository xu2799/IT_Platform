<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import apiClient from '@/api'
import BackButton from '@/components/BackButton.vue'

const courses = ref([])
const loading = ref(true)
const error = ref(null)

// (API_URL 已移至 apiClient)

onMounted(async () => {
  loading.value = true
  error.value = null
  try {
    // 调用我们新创建的收藏列表 API
    const response = await apiClient.get('/api/favorites/')
    if (response.data.results) {
        courses.value = response.data.results
    } else {
        courses.value = response.data
    }
  } catch (err) {
    console.error('获取收藏课程失败:', err)
    error.value = '无法加载您收藏的课程。'
  } finally {
    loading.value = false
  }
})

// --- (辅助函数) ---
const getFullCoverImagePath = (relativePath) => {
    if (relativePath) {
        if (relativePath.startsWith('http://') || relativePath.startsWith('https://')) {
            return relativePath
        }
        // 使用 apiClient 的 baseURL
        const baseUrl = apiClient.defaults.baseURL || ''
        return `${baseUrl}${relativePath}`
    }
    return 'https://via.placeholder.com/300x150.png?text=No+Cover'
}

const handleImageError = (event) => {
    event.target.src = 'https://via.placeholder.com/300x150.png?text=No+Cover'
}
</script>

<template>
  <div class="course-list-container">
    <BackButton 
      :fallback-route="{ name: 'courses' }" 
      text="返回课程列表"
      small
    />
    <h1 class="page-title">我的收藏</h1>
    
    <div v-if="loading" class="loading-container">
      <p>正在加载...</p>
    </div>

    <div v-else-if="error" class="error-container">
      <p class="error-message">{{ error }}</p>
    </div>

    <section v-else-if="courses.length > 0" class="course-grid">
      <div 
        v-for="course in courses" 
        :key="course.id" 
        class="course-card"
      >
        <RouterLink :to="`/courses/${course.id}`" class="course-link-wrapper">
          <div class="course-thumbnail">
            <img 
                :src="getFullCoverImagePath(course.cover_image)" 
                :alt="course.title + '封面'" 
                class="cover-image"
                @error="handleImageError"
            >
            <span v-if="course.category" class="category-tag">
                {{ course.category.name }}
            </span>
          </div>
          
          <div class="card-content">
            <h3>{{ course.title }}</h3>
            <div class="card-footer-stats">
              <span class="instructor-name">
                讲师: {{ course.instructor?.username || '平台认证' }}
              </span>
              <span class="like-stats">
                👍 {{ course.like_count || 0 }}
              </span>
            </div>
          </div>
        </RouterLink>
      </div>
    </section>
    
    <div v-else class="no-results">
        <p>你还没有收藏任何课程。</p>
        <RouterLink :to="{ name: 'courses' }" class="nav-button">
            去逛逛课程
        </RouterLink>
    </div>
  </div>
</template>

<style scoped>
/* (样式与 CourseListView 类似) */
.course-list-container {
    padding: 20px 40px; 
}
.page-title {
    text-align: center;
    font-size: 2rem;
    margin-bottom: 30px;
}
.course-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 30px; 
}
.course-link-wrapper {
    text-decoration: none;
    color: inherit;
    display: flex; 
    flex-direction: column;
    flex-grow: 1; 
}
.course-card {
    background-color: #ffffff;
    border-radius: 10px;
    overflow: hidden; 
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08); 
    transition: transform 0.3s, box-shadow 0.3s;
    display: flex; 
    flex-direction: column; 
}
.course-card:hover {
    transform: translateY(-8px); 
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2); 
}
.course-thumbnail {
    width: 100%;
    height: 150px;
    background-color: #3498db;
    position: relative;
    flex-shrink: 0;
}
.cover-image {
    width: 100%;
    height: 100%;
    object-fit: cover; 
}
.category-tag {
    background-color: #3498db;
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.9rem;
    font-weight: bold;
    position: absolute;
    top: 8px;
    left: 8px;
}
.card-content {
    padding: 15px;
    flex-grow: 1; 
    display: flex; 
    flex-direction: column; 
    justify-content: space-between; 
}
.card-content h3 {
    font-size: 1.1rem;
    margin-top: 0;
    margin-bottom: 8px;
    color: #2c3e50;
}
.card-footer-stats {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: auto;
}
.instructor-name {
    font-size: 0.85rem;
    color: #7f8c8d;
}
.like-stats {
    font-size: 0.9rem;
    color: #34495e;
    font-weight: 500;
}
.loading-container, .error-container, .no-results {
    text-align: center;
    padding: 50px;
    font-size: 1.2rem;
    color: #555;
}
.error-message { color: #dc3545; }
.no-results .nav-button {
    margin-top: 20px;
    font-size: 1.1rem;
    background-color: #007bff;
    color: white;
    text-decoration: none;
    padding: 12px 20px;
    border-radius: 5px;
}
</style>