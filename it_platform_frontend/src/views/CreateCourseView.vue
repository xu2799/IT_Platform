<script setup>
import { ref, onMounted } from 'vue' 
// 【【【修改】】】: 导入我们新的 apiClient
import apiClient from '@/api'
import { useRouter } from 'vue-router'
import { useCourseStore } from '@/stores/courseStore'
import BackButton from '@/components/BackButton.vue' 

const router = useRouter()
const courseStore = useCourseStore() 
    
const title = ref('')
const description = ref('')
const coverImageFile = ref(null) 
const categoryId = ref(null) 
    
const errorMessage = ref('')
const successMessage = ref('')

onMounted(() => {
  courseStore.fetchCategories()
})

const handleFileChange = (event) => {
  coverImageFile.value = event.target.files ? event.target.files[0] : null
}

const handleSubmit = async () => {
  errorMessage.value = ''
  successMessage.value = ''

  if (!categoryId.value) {
      errorMessage.value = '请选择一个课程分类。'
      return
  }

  const formData = new FormData()
  formData.append('title', title.value)
  formData.append('description', description.value)
  formData.append('category', categoryId.value) 
  
  if (coverImageFile.value) {
    formData.append('cover_image', coverImageFile.value)
  }

  try {
    console.log('正在提交课程数据 (FormData)...')
    
    // 【【【修改】】】: 使用 apiClient (它会自动附加 token)
    // 之前这个请求会因为缺少 token 而 403 失败
    const response = await apiClient.post('/api/courses/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    // 【【【关键】】】: 标记缓存为陈旧
    courseStore.markAsStale() 

    successMessage.value = `课程"${response.data.title}" 创建成功!`
    
    // 立即跳转
    router.push(`/courses/${response.data.id}`)
    
  } catch (error) {
    // 认证失败会在这里被捕获
    console.error('创建课程失败:', error.response?.data || error.message)
    if (error.response) {
      if (error.response.status === 403) {
        errorMessage.value = '权限不足! 只有讲师和管理员才能创建课程。'
      } else {
        errorMessage.value = '创建失败: ' + JSON.stringify(error.response.data)
      }
    } else {
      errorMessage.value = '网络错误或服务器连接失败。'
    }
  }
}
</script>

<template>
  <div class="create-course-page">
    <BackButton 
      :fallback-route="{ name: 'instructor-dashboard' }" 
      text="返回讲师面板"
    />
    <h1>创建新课程</h1>
    
    <p v-if="successMessage" class="message success">{{ successMessage }}</p>
    <p v-if="errorMessage" class="message error">{{ errorMessage }}</p>

    <form @submit.prevent="handleSubmit" class="course-form" enctype="multipart/form-data">
      
      <div class="form-group">
        <label for="title">课程标题:</label>
        <input type="text" id="title" v-model="title" required>
      </div>

      <div class="form-group">
        <label for="category">课程分类:</label>
        <select id="category" v-model="categoryId" required>
            <option :value="null" disabled>-- 请选择分类 --</option>
            <option 
                v-for="category in courseStore.categories" 
                :key="category.id" 
                :value="category.id"
            >
                {{ category.name }}
            </option>
        </select>
      </div>

      <div class="form-group">
        <label for="description">课程描述:</label>
        <textarea id="description" v-model="description" required rows="5"></textarea>
      </div>

      <div class="form-group">
        <label for="cover_image">课程封面图 (推荐 16:9):</label>
        <input type="file" id="cover_image" @change="handleFileChange" accept="image/*">
      </div>

      <button type="submit" class="submit-button">提交课程</button>
    </form>
  </div>
</template>

<style scoped>
/* 样式部分 (完全不变) */
.create-course-page { 
  max-width: 600px; 
  margin: 0 auto; 
  padding: 20px; 
}
.create-course-page h1 {
  margin-top: 0;
}
.course-form { display: flex; flex-direction: column; gap: 15px; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
.form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
.form-group input, .form-group textarea, .form-group select { 
    width: 100%; 
    padding: 10px; 
    box-sizing: border-box; 
    border: 1px solid #ccc; 
    border-radius: 4px; 
    font-size: 1rem;
    font-family: inherit;
}
.submit-button { padding: 12px; background-color: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 1rem; }
.submit-button:hover { background-color: #1e7e34; }
.message { padding: 10px; border-radius: 4px; margin-bottom: 15px; }
.success { background-color: #d4edda; color: #155724; border-color: #c3e6cb; }
.error { background-color: #f8d7da; color: #721c24; border-color: #f5c6cb; }
</style>