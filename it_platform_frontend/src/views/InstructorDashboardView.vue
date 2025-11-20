<script setup>
import { ref, onMounted, computed } from 'vue' 
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
// 【【【修改】】】: 导入 apiClient
import apiClient from '@/api'
import BackButton from '@/components/BackButton.vue'

// (API_URL 已移至 apiClient)
const authStore = useAuthStore()

const courses = ref([])
const loading = ref(true)
const errorMessage = ref('')

// (不再需要手动设置 axios defaults)

const fetchInstructorCourses = async () => {
    loading.value = true
    errorMessage.value = ''
    try {
        // 【【【修改】】】: 使用 apiClient
        const response = await apiClient.get('/api/instructor/courses/')
        console.log('讲师课程API响应:', response.data)
        
        if (response.data.results) {
            courses.value = response.data.results
        } else if (Array.isArray(response.data)) {
            courses.value = response.data
        } else {
            courses.value = []
        }
        
        console.log('解析后的课程列表:', courses.value)
    } catch (error) {
        console.error('获取讲师课程失败:', error.response?.data || error.message)
        if (error.response) {
            errorMessage.value = `无法加载你的课程: ${error.response.data?.detail || error.response.statusText}`
            console.error('错误详情:', error.response.data)
        } else if (error.request) {
            errorMessage.value = '网络错误，请检查网络连接'
        } else {
            errorMessage.value = '无法加载你的课程'
        }
        courses.value = []
    } finally {
        loading.value = false
    }
}

onMounted(() => {
    fetchInstructorCourses()
})

const getFullCoverImagePath = (relativePath) => {
    if (relativePath) {
        if (relativePath.startsWith('http://') || relativePath.startsWith('https://')) {
            return relativePath
        }
        // 【【【修改】】】: 使用 apiClient 的 baseURL
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
  <div class="dashboard-container">
    <BackButton 
      :fallback-route="{ name: 'courses' }" 
      text="返回课程列表"
      small
    />
    
    <h1 class="section-title">讲师面板 - 我的课程</h1>
    
    <div v-if="loading">正在加载课程...</div>
    <div v-if="errorMessage" class="message error">{{ errorMessage }}</div>

    <section class="course-grid" v-if="courses.length > 0">
      
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
          </div>
        </RouterLink>

        <div class="card-admin-actions">
            
            <RouterLink 
                :to="{ name: 'course-detail', params: { id: course.id }, query: { manage: 'true' } }"
                class="action-button manage-button"
            >
                管理课时
            </RouterLink>
            
            <RouterLink 
                :to="{ name: 'course-edit', params: { id: course.id } }"
                class="action-button edit-button"
            >
                编辑课程
            </RouterLink>
        </div>

      </div>
      
    </section>
    
    <div v-if="!loading && courses.length === 0" class="no-results">
        <p>你还没有创建任何课程。</p>
        <RouterLink to="/create-course" class="nav-button create-course-btn">
            创建你的第一门课程
        </RouterLink>
    </div>
  </div>
</template>

<style scoped>
/* 样式部分 (完全不变) */
.dashboard-container {
    padding: 20px 40px; 
}
.dashboard-container .section-title {
    font-size: 2.2rem;
    color: #333;
    margin-bottom: 30px;
    text-align: center;
    margin-top: 0;
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
    transition: box-shadow 0.3s;
    display: flex; 
    flex-direction: column;
}
.course-card:hover {
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
    position: absolute;
    top: 8px;
    left: 8px;
}
.card-content {
    padding: 15px;
    flex-grow: 1; 
}
.card-content h3 {
    font-size: 1.1rem;
    margin: 0;
    color: #2c3e50;
}
.card-admin-actions {
    padding: 15px;
    margin-top: auto;
    display: flex;
    gap: 10px;
}
.action-button {
    display: block;
    flex: 1; 
    padding: 10px;
    color: white;
    text-align: center;
    text-decoration: none;
    border-radius: 5px;
    font-weight: bold;
    transition: background-color 0.2s;
}
.manage-button {
    background-color: #28a745; 
}
.manage-button:hover {
    background-color: #218838;
}
.edit-button {
    background-color: #007bff; 
}
.edit-button:hover {
    background-color: #0056b3;
}
.no-results {
    text-align: center;
    padding: 50px;
    font-size: 1.2rem;
    color: #777;
}
.no-results .nav-button {
    margin-top: 20px;
    font-size: 1.1rem;
    background-color: #2ecc71;
    color: white;
    text-decoration: none;
    padding: 12px 20px;
}
.message { padding: 15px; border-radius: 4px; font-size: 1.1rem; text-align: center; }
.error { background-color: #f8d7da; color: #721c24; border-color: #f5c6cb; }
</style>