<script setup>
import { ref, onMounted } from 'vue'
// 【【【修改】】】: 导入 apiClient
import apiClient from '@/api'
import { useRouter, useRoute } from 'vue-router'
import { useCourseStore } from '@/stores/courseStore'
import BackButton from '@/components/BackButton.vue' 

// (API_URL 已移至 apiClient)

const router = useRouter()
const route = useRoute() 
const courseStore = useCourseStore() 

const courseId = route.params.id 

const title = ref('')
const description = ref('')
const categoryId = ref(null) 
const coverImageFile = ref(null) 
    
const errorMessage = ref('')
const successMessage = ref('')
const loading = ref(true)
const isUpdating = ref(false)
const isDeleting = ref(false)
const showDeleteConfirm = ref(false)
const currentCourse = ref(null)

// 页面加载时, 获取课程详情和分类
onMounted(async () => {
  if (courseStore.categories.length === 0) {
    await courseStore.fetchCategories()
  }
  
  try {
    const course = await courseStore.fetchCourseDetail(courseId)
    if (course) {
      currentCourse.value = course
      title.value = course.title
      description.value = course.description
      categoryId.value = course.category?.id || null
    } else {
        errorMessage.value = "无法加载课程数据。"
    }
  } catch (error) {
     errorMessage.value = "加载课程失败。"
  } finally {
     loading.value = false
  }
})

const handleFileChange = (event) => {
  coverImageFile.value = event.target.files ? event.target.files[0] : null
}

// 提交更新
const handleUpdate = async () => {
  errorMessage.value = ''
  successMessage.value = ''
  isUpdating.value = true

  // (验证不变)
  if (!title.value.trim()) {
      errorMessage.value = '课程标题不能为空'
      isUpdating.value = false
      return
  }
  if (!description.value.trim()) {
      errorMessage.value = '课程描述不能为空'
      isUpdating.value = false
      return
  }
  if (!categoryId.value) {
      errorMessage.value = '请选择一个课程分类'
      isUpdating.value = false
      return
  }

  const formData = new FormData()
  formData.append('title', title.value.trim())
  formData.append('description', description.value.trim())
  formData.append('category', categoryId.value)
  
  if (coverImageFile.value) {
    formData.append('cover_image', coverImageFile.value)
  }

  try {
    console.log('正在更新课程数据 (FormData)...')
    
    // 【【【修改】】】: 使用 apiClient
    const response = await apiClient.patch(`/api/courses/${courseId}/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    courseStore.markAsStale() 
    successMessage.value = `课程"${response.data.title}" 更新成功!`
    
    setTimeout(() => {
        router.push({ name: 'instructor-dashboard' })
    }, 2000)
    
  } catch (error) {
    console.error('更新课程失败:', error.response?.data || error.message)
    if (error.response) {
      if (error.response.status === 403) {
        errorMessage.value = '权限不足! 只有本课程讲师和管理员才能编辑。'
      } else if (error.response.status === 400) {
        errorMessage.value = error.response.data.detail || '更新失败: 请检查输入数据'
      } else {
        errorMessage.value = '更新失败: ' + (error.response.data.detail || JSON.stringify(error.response.data))
      }
    } else if (error.request) {
      errorMessage.value = '网络错误，请检查网络连接'
    } else {
      errorMessage.value = '更新失败，请稍后重试'
    }
  } finally {
    isUpdating.value = false
  }
}

// 删除课程
const handleDelete = async () => {
  if (!showDeleteConfirm.value) {
    showDeleteConfirm.value = true
    return
  }

  errorMessage.value = ''
  isDeleting.value = true

  try {
    console.log('正在删除课程...')
    
    // 【【【修改】】】: 使用 apiClient
    const response = await apiClient.delete(`/api/courses/${courseId}/`)
    
    courseStore.markAsStale() 
    const courseTitle = currentCourse.value?.title || '课程'
    const deletedInfo = response.data?.deleted
    
    if (deletedInfo) {
      successMessage.value = `课程"${courseTitle}" 已成功删除! (已删除 ${deletedInfo.modules_count || 0} 个模块, ${deletedInfo.lessons_count || 0} 个课时)`
    } else {
      successMessage.value = `课程"${courseTitle}" 已成功删除!`
    }
    
    setTimeout(() => {
        router.push({ name: 'instructor-dashboard' })
    }, 2000)
    
  } catch (error) {
    console.error('删除课程失败:', error.response?.data || error.message)
    showDeleteConfirm.value = false
    if (error.response) {
      if (error.response.status === 403) {
        errorMessage.value = '权限不足! 只有本课程讲师和管理员才能删除。'
      } else if (error.response.status === 404) {
        errorMessage.value = '课程不存在'
      } else {
        errorMessage.value = '删除失败: ' + (error.response.data.detail || JSON.stringify(error.response.data))
      }
    } else if (error.request) {
      errorMessage.value = '网络错误，请检查网络连接'
    } else {
      errorMessage.value = '删除失败，请稍后重试'
    }
  } finally {
    isDeleting.value = false
  }
}

// 取消删除确认
const cancelDelete = () => {
  showDeleteConfirm.value = false
}
</script>

<template>
  <div class="edit-course-page">
    <BackButton 
      :fallback-route="{ name: 'instructor-dashboard' }" 
      text="返回讲师面板"
    />
    <h1>编辑课程</h1>
    
    <div v-if="loading">正在加载课程数据...</div>
    
    <p v-if="successMessage" class="message success">{{ successMessage }}</p>
    <p v-if="errorMessage" class="message error">{{ errorMessage }}</p>

    <form @submit.prevent="handleUpdate" class="course-form" v-if="!loading && !successMessage">
      
      <div class="form-group">
        <label for="title">课程标题:</label>
        <input type="text" id="title" v-model="title" required :disabled="isUpdating">
      </div>

      <div class="form-group">
        <label for="category">课程分类:</label>
        <select id="category" v-model="categoryId" required :disabled="isUpdating">
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
        <textarea id="description" v-model="description" required rows="5" :disabled="isUpdating"></textarea>
      </div>

      <div class="form-group">
        <label for="cover_image">更新课程封面图 (推荐 16:9):</label>
        <p class="small-text">(如果不选择新文件, 将保留原封面图)</p>
        <input type="file" id="cover_image" @change="handleFileChange" accept="image/*" :disabled="isUpdating">
      </div>

      <div class="form-actions">
        <button type="submit" class="submit-button update-button" :disabled="isUpdating || isDeleting">
          {{ isUpdating ? '保存中...' : '保存更改' }}
        </button>
        
        <button 
          type="button" 
          class="submit-button delete-button" 
          @click="handleDelete"
          :disabled="isUpdating || isDeleting"
        >
          {{ isDeleting ? '删除中...' : '删除课程' }}
        </button>
      </div>
    </form>

    <div v-if="showDeleteConfirm" class="delete-confirm-overlay" @click.self="cancelDelete">
      <div class="delete-confirm-dialog">
        <h3>确认删除</h3>
        <p>你确定要删除课程 "<strong>{{ currentCourse?.title }}</strong>" 吗？</p>
        <p class="warning-text">此操作不可撤销，课程及其所有内容将被永久删除！</p>
        <div class="confirm-actions">
          <button 
            type="button" 
            class="confirm-button cancel-button" 
            @click="cancelDelete"
            :disabled="isDeleting"
          >
            取消
          </button>
          <button 
            type="button" 
            class="confirm-button delete-confirm-button" 
            @click="handleDelete"
            :disabled="isDeleting"
          >
            {{ isDeleting ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 样式部分 (完全不变) */
.edit-course-page { 
  max-width: 600px; 
  margin: 20px auto; 
  padding: 20px; 
}
.edit-course-page h1 {
  margin-top: 0;
}
.course-form { display: flex; flex-direction: column; gap: 15px; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
.form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
.form-group .small-text { font-size: 0.9rem; color: #777; margin: -5px 0 5px 0; }
.form-group input, .form-group textarea, .form-group select { 
    width: 100%; 
    padding: 10px; 
    box-sizing: border-box; 
    border: 1px solid #ccc; 
    border-radius: 4px; 
    font-size: 1rem;
    font-family: inherit;
}
.form-actions {
    display: flex;
    gap: 15px;
    margin-top: 10px;
}
.submit-button { 
    flex: 1;
    padding: 12px; 
    color: white; 
    border: none; 
    border-radius: 4px; 
    cursor: pointer; 
    font-size: 1rem;
    font-weight: bold;
    transition: background-color 0.2s;
}
.submit-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}
.update-button {
    background-color: #007bff;
}
.update-button:hover:not(:disabled) {
    background-color: #0056b3;
}
.delete-button {
    background-color: #dc3545;
}
.delete-button:hover:not(:disabled) {
    background-color: #c82333;
}
.message { padding: 10px; border-radius: 4px; margin-bottom: 15px; }
.success { background-color: #d4edda; color: #155724; border-color: #c3e6cb; }
.error { background-color: #f8d7da; color: #721c24; border-color: #f5c6cb; }
.delete-confirm-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}
.delete-confirm-dialog {
    background-color: white;
    padding: 30px;
    border-radius: 8px;
    max-width: 500px;
    width: 90%;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.delete-confirm-dialog h3 {
    margin-top: 0;
    color: #dc3545;
    font-size: 1.5rem;
}
.delete-confirm-dialog p {
    margin: 15px 0;
    line-height: 1.6;
}
.warning-text {
    color: #dc3545;
    font-weight: bold;
    font-size: 0.95rem;
}
.confirm-actions {
    display: flex;
    gap: 10px;
    margin-top: 25px;
    justify-content: flex-end;
}
.confirm-button {
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    font-weight: bold;
    transition: background-color 0.2s;
}
.confirm-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}
.cancel-button {
    background-color: #6c757d;
    color: white;
}
.cancel-button:hover:not(:disabled) {
    background-color: #5a6268;
}
.delete-confirm-button {
    background-color: #dc3545;
    color: white;
}
.delete-confirm-button:hover:not(:disabled) {
    background-color: #c82333;
}
</style>