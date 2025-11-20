<script setup>
// --- 1. 导入 ---
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useCourseStore } from '@/stores/courseStore'
import { useAuthStore } from '@/stores/authStore'
// 【【【修改】】】: 导入 apiClient
import apiClient from '@/api'
import { useRouter, useRoute, RouterLink } from 'vue-router'
import BackButton from '@/components/BackButton.vue'

// (API_URL 已移至 apiClient)

// --- 2. 激活仓库和路由 ---
const courseStore = useCourseStore()
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

// --- 3. 接收 URL 道具 ---
const props = defineProps({
  id: {
    type: String,
    required: true
  }
})

// --- 4. 状态 (State) ---
// (保持不变)
const newModuleTitle = ref('')
const openModuleFormId = ref(null) 
const currentLessonTitle = ref('') 
const currentVideoFile = ref(null) 
const uploadStatus = ref('')     
const editingLessonId = ref(null) 
const editLessonTitle = ref('') 
const editLessonVideoFile = ref(null) 
const editLessonOrder = ref(0) 
const isUpdatingLesson = ref(false) 
const deletingLessonId = ref(null) 
const showDeleteLessonConfirm = ref(false) 
const isDeletingLesson = ref(false) 
const lessonToDelete = ref(null) 
const lessonErrorMessage = ref('')
const lessonSuccessMessage = ref('')
const isMovingLesson = ref(false) 

// --- 5. 计算属性 (Computed) ---
// (保持不变)
const course = computed(() => {
  return courseStore.courses.find(c => c.id == props.id)
})
const isInstructorOfCourse = computed(() => {
  if (!authStore.isAuthenticated) return false
  if (authStore.user.role === 'admin') return true
  if (authStore.user.role === 'instructor' && course.value) {
    return authStore.user.id === course.value.instructor?.id
  }
  return false
})

// --- 6. 生命周期函数 ---
let videoCheckInterval = null
onMounted(() => {
  courseStore.fetchCourseDetail(props.id)
  startVideoProcessingCheck()

  // --- 【【【新增：记录观看次数】】】 ---
  // “即发即忘”，我们不需要等待它完成
  try {
    apiClient.post(`/api/courses/${props.id}/record_view/`)
    console.log(`已为课程 ${props.id} 记录一次观看`);
  } catch (error) {
    // 即便失败也不打扰用户
    console.warn(`记录课程 ${props.id} 观看次数失败:`, error);
  }
  // --- 【【【新增结束】】】 ---
})

onUnmounted(() => {
  if (videoCheckInterval) {
    clearInterval(videoCheckInterval)
  }
})

// --- 7. 视频处理检查 (不变) ---
const hasProcessingVideos = () => {
  if (!course.value || !course.value.modules) return false
  for (const module of course.value.modules) {
    if (module.lessons) {
      for (const lesson of module.lessons) {
        if (lesson.lesson_type === 'text' && lesson.video_mp4_file) {
          return true
        }
      }
    }
  }
  return false
}
const startVideoProcessingCheck = () => {
  if (videoCheckInterval) {
    clearInterval(videoCheckInterval)
  }
  videoCheckInterval = setInterval(async () => {
    if (hasProcessingVideos()) {
      await courseStore.fetchCourseDetail(props.id)
    } else {
      clearInterval(videoCheckInterval)
      videoCheckInterval = null
    }
  }, 10000)
}

// --- 8. 监听 (不变) ---
watch(course, (newCourse) => {
  if (newCourse) {
    startVideoProcessingCheck()
  }
  if (route.query.manage === 'true') {
    return;
  }
  if (newCourse && newCourse.modules && newCourse.modules.length > 0) {
    const firstModule = newCourse.modules[0];
    if (firstModule.lessons && firstModule.lessons.length > 0) {
      const firstLesson = firstModule.lessons[0];
      router.replace({
        name: 'lesson-watch',
        params: { courseId: newCourse.id, lessonId: firstLesson.id }
      });
    }
  }
}, {
  immediate: true
})

// --- 9. 【【【已修改】】】 核心功能函数 ---
// (所有函数保持不变)
const handleFileChange = (event) => {
  currentVideoFile.value = event.target.files ? event.target.files[0] : null
}
const showLessonForm = (moduleId) => {
  if (editingLessonId.value !== null) {
    return
  }
  if (openModuleFormId.value === moduleId) {
    openModuleFormId.value = null;
  } else {
    openModuleFormId.value = moduleId;
    currentLessonTitle.value = '';
    currentVideoFile.value = null;
    uploadStatus.value = '';
  }
}

// (C) 添加新章节
const handleAddModule = async () => {
  if (!newModuleTitle.value.trim()) return
  try {
    const moduleData = { course: props.id, title: newModuleTitle.value }
    // 【【【修改】】】: 使用 apiClient
    const response = await apiClient.post('/api/modules/', moduleData)
    if (course.value.modules) {
      course.value.modules.push(response.data)
    }
    courseStore.markAsStale()
    newModuleTitle.value = ''
  } catch (error) {
    console.error('创建章节失败:', error.response?.data || error.message)
    alert('创建章节失败！请确保你已登录且具有讲师权限。')
  }
}

// (D) 添加新课时
const handleAddLesson = async (moduleId) => {
  if (!currentLessonTitle.value.trim() || !moduleId || !currentVideoFile.value) {
    alert('请填写课时标题并上传文件。')
    return
  }
  uploadStatus.value = '视频上传中...'
  const formData = new FormData()
  formData.append('title', currentLessonTitle.value)
  formData.append('module', moduleId)
  formData.append('video_file', currentVideoFile.value)
  try {
    // 【【【修改】】】: 使用 apiClient
    const response = await apiClient.post('/api/lessons/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    const targetModule = course.value.modules.find(m => m.id == moduleId)
    if (targetModule) {
      targetModule.lessons = targetModule.lessons || []
      targetModule.lessons.push(response.data)
    }
    courseStore.markAsStale()
    uploadStatus.value = '上传成功！视频正在后台处理中...'
    await courseStore.fetchCourseDetail(props.id)
    startVideoProcessingCheck()
    setTimeout(() => {
        showLessonForm(moduleId);
    }, 1500);
  } catch (error) {
    console.error('上传课时失败:', error.response?.data || error.message)
    uploadStatus.value = '上传失败！请检查文件大小或权限。'
    if (error.response) {
      uploadStatus.value = error.response.data.detail || '上传失败！请检查文件大小或权限。'
    }
  }
}

// (E) 编辑课时
const startEditLesson = (lesson) => {
  if (openModuleFormId.value !== null) {
    openModuleFormId.value = null
  }
  editingLessonId.value = lesson.id
  editLessonTitle.value = lesson.title
  editLessonOrder.value = lesson.order || 0
  editLessonVideoFile.value = null
  lessonErrorMessage.value = ''
  lessonSuccessMessage.value = ''
}
const cancelEditLesson = () => {
  editingLessonId.value = null
  editLessonTitle.value = ''
  editLessonOrder.value = 0
  editLessonVideoFile.value = null
  lessonErrorMessage.value = ''
  lessonSuccessMessage.value = ''
}
const handleEditLessonFileChange = (event) => {
  editLessonVideoFile.value = event.target.files ? event.target.files[0] : null
}
const handleUpdateLesson = async (lessonId, moduleId) => {
  if (!editLessonTitle.value.trim()) {
    lessonErrorMessage.value = '课时标题不能为空'
    return
  }
  isUpdatingLesson.value = true
  lessonErrorMessage.value = ''
  lessonSuccessMessage.value = ''
  const formData = new FormData()
  formData.append('title', editLessonTitle.value.trim())
  formData.append('order', editLessonOrder.value)
  if (editLessonVideoFile.value) {
    formData.append('video_file', editLessonVideoFile.value)
  }
  try {
    // 【【【修改】】】: 使用 apiClient
    const response = await apiClient.patch(`/api/lessons/${lessonId}/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    const targetModule = course.value.modules.find(m => m.id == moduleId)
    if (targetModule && targetModule.lessons) {
      const lessonIndex = targetModule.lessons.findIndex(l => l.id == lessonId)
      if (lessonIndex !== -1) {
        targetModule.lessons[lessonIndex] = response.data
      }
    }
    courseStore.markAsStale()
    lessonSuccessMessage.value = '课时更新成功！'
    setTimeout(() => {
      cancelEditLesson()
    }, 1500)
  } catch (error) {
    console.error('更新课时失败:', error.response?.data || error.message)
    if (error.response) {
      if (error.response.status === 403) {
        lessonErrorMessage.value = '权限不足！只有本课程讲师和管理员才能编辑。'
      } else if (error.response.status === 400) {
        lessonErrorMessage.value = error.response.data.detail || '更新失败: 请检查输入数据'
      } else {
        lessonErrorMessage.value = '更新失败: ' + (error.response.data.detail || JSON.stringify(error.response.data))
      }
    } else if (error.request) {
      lessonErrorMessage.value = '网络错误，请检查网络连接'
    } else {
      lessonErrorMessage.value = '更新失败，请稍后重试'
    }
  } finally {
    isUpdatingLesson.value = false
  }
}

// (F) 删除课时
const startDeleteLesson = (lesson) => {
  lessonToDelete.value = lesson
  showDeleteLessonConfirm.value = true
  lessonErrorMessage.value = ''
}
const cancelDeleteLesson = () => {
  showDeleteLessonConfirm.value = false
  lessonToDelete.value = null
  deletingLessonId.value = null
}
const handleDeleteLesson = async () => {
  if (!lessonToDelete.value) return
  deletingLessonId.value = lessonToDelete.value.id
  isDeletingLesson.value = true
  lessonErrorMessage.value = ''
  try {
    // 【【【修改】】】: 使用 apiClient
    const response = await apiClient.delete(`/api/lessons/${lessonToDelete.value.id}/`)
    const targetModule = course.value.modules.find(m => 
      m.lessons && m.lessons.some(l => l.id === lessonToDelete.value.id)
    )
    if (targetModule && targetModule.lessons) {
      targetModule.lessons = targetModule.lessons.filter(l => l.id !== lessonToDelete.value.id)
    }
    courseStore.markAsStale()
    const deletedInfo = response.data?.deleted
    if (deletedInfo) {
      lessonSuccessMessage.value = `课时"${lessonToDelete.value.title}" 已成功删除! (已删除 ${deletedInfo.comments_count || 0} 条评论)`
    } else {
      lessonSuccessMessage.value = `课时"${lessonToDelete.value.title}" 已成功删除!`
    }
    cancelDeleteLesson()
    setTimeout(() => {
      lessonSuccessMessage.value = ''
    }, 3000)
  } catch (error) {
    console.error('删除课时失败:', error.response?.data || error.message)
    if (error.response) {
      if (error.response.status === 403) {
        lessonErrorMessage.value = '权限不足！只有本课程讲师和管理员才能删除。'
      } else if (error.response.status === 404) {
        lessonErrorMessage.value = '课时不存在'
      } else {
        lessonErrorMessage.value = '删除失败: ' + (error.response.data.detail || JSON.stringify(error.response.data))
      }
    } else if (error.request) {
      lessonErrorMessage.value = '网络错误，请检查网络连接'
    } else {
      lessonErrorMessage.value = '删除失败，请稍后重试'
    }
    cancelDeleteLesson()
  } finally {
    isDeletingLesson.value = false
  }
}

// 辅助函数：对课时列表进行排序
const sortedLessons = (lessons) => {
  if (!lessons || lessons.length === 0) return []
  return [...lessons].sort((a, b) => {
    const orderA = a.order !== undefined && a.order !== null ? a.order : 999
    const orderB = b.order !== undefined && b.order !== null ? b.order : 999
    return orderA - orderB
  })
}

// (G) 课时排序功能
const handleMoveLessonUp = async (lesson, moduleId) => {
  if (isMovingLesson.value) return
  const targetModule = course.value.modules.find(m => m.id == moduleId)
  if (!targetModule || !targetModule.lessons) return
  const sorted = sortedLessons(targetModule.lessons)
  const currentIndex = sorted.findIndex(l => l.id === lesson.id)
  if (currentIndex <= 0) return
  const prevLesson = sorted[currentIndex - 1]
  const currentOrder = lesson.order !== undefined && lesson.order !== null ? lesson.order : currentIndex
  const prevOrder = prevLesson.order !== undefined && prevLesson.order !== null ? prevLesson.order : (currentIndex - 1)
  await swapLessonOrder(lesson, prevLesson, currentOrder, prevOrder, targetModule)
}
const handleMoveLessonDown = async (lesson, moduleId) => {
  if (isMovingLesson.value) return
  const targetModule = course.value.modules.find(m => m.id == moduleId)
  if (!targetModule || !targetModule.lessons) return
  const sorted = sortedLessons(targetModule.lessons)
  const currentIndex = sorted.findIndex(l => l.id === lesson.id)
  if (currentIndex < 0 || currentIndex >= sorted.length - 1) return
  const nextLesson = sorted[currentIndex + 1]
  const currentOrder = lesson.order !== undefined && lesson.order !== null ? lesson.order : currentIndex
  const nextOrder = nextLesson.order !== undefined && nextLesson.order !== null ? nextLesson.order : (currentIndex + 1)
  await swapLessonOrder(lesson, nextLesson, currentOrder, nextOrder, targetModule)
}
const swapLessonOrder = async (lesson1, lesson2, order1, order2, module) => {
  isMovingLesson.value = true
  lessonErrorMessage.value = ''
  lessonSuccessMessage.value = ''
  try {
    // 【【【修改】】】: 使用 apiClient
    const [response1, response2] = await Promise.all([
      apiClient.patch(`/api/lessons/${lesson1.id}/`, { order: order2 }),
      apiClient.patch(`/api/lessons/${lesson2.id}/`, { order: order1 })
    ])
    
    const lesson1Index = module.lessons.findIndex(l => l.id === lesson1.id)
    const lesson2Index = module.lessons.findIndex(l => l.id === lesson2.id)
    
    if (lesson1Index !== -1) {
      module.lessons[lesson1Index] = { ...response1.data, order: order2 }
    }
    if (lesson2Index !== -1) {
      module.lessons[lesson2Index] = { ...response2.data, order: order1 }
    }
    
    module.lessons.sort((a, b) => {
      const orderA = a.order !== undefined && a.order !== null ? a.order : 999
      const orderB = b.order !== undefined && b.order !== null ? b.order : 999
      return orderA - orderB
    })
    
    courseStore.markAsStale()
    lessonSuccessMessage.value = '课时顺序已更新'
    setTimeout(() => {
      lessonSuccessMessage.value = ''
    }, 2000)
    
  } catch (error) {
    console.error('移动课时失败:', error.response?.data || error.message)
    if (error.response) {
      if (error.response.status === 403) {
        lessonErrorMessage.value = '权限不足！只有本课程讲师和管理员才能调整顺序。'
      } else {
        lessonErrorMessage.value = '移动失败: ' + (error.response.data.detail || '请稍后重试')
      }
    } else {
      lessonErrorMessage.value = '移动失败，请检查网络连接'
    }
  } finally {
    isMovingLesson.value = false
  }
}
</script>

<template>
  <div class="course-detail">
    <div class="course-header-actions">
      <BackButton 
        v-if="route.query.manage === 'true'"
        :fallback-route="{ name: 'instructor-dashboard' }" 
        text="返回讲师面板"
        small
        inline
      />
      <BackButton 
        v-else
        :fallback-route="{ name: 'courses' }" 
        text="返回课程列表"
        small
        inline
      />
    </div>
    
    <div v-if="!course">
      <p>正在加载课程...</p>
    </div>

    <div v-else>

      <h1>{{ course.title }}</h1>
      <p>{{ course.description }}</p>
      <p v-if="course.instructor">讲师: {{ course.instructor.username }}</p>

      <hr>

      <h2>课程内容:</h2>

      <div v-if="lessonSuccessMessage" class="lesson-message success">
        {{ lessonSuccessMessage }}
      </div>
      <div v-if="lessonErrorMessage" class="lesson-message error">
        {{ lessonErrorMessage }}
      </div>
      
      <div v-if="hasProcessingVideos()" class="video-processing-notice">
        <p>⏳ 检测到正在处理的视频，系统将自动刷新状态...</p>
        <button @click="courseStore.fetchCourseDetail(props.id)" class="btn-refresh">
          立即刷新
        </button>
      </div>

      <div class="content-management">
        <div 
          v-for="module in course.modules" 
          :key="module.id" 
          class="module-container"
        >
          <div class="module-header">
            <h3>{{ module.title }}</h3>
            <button 
              v-if="isInstructorOfCourse" 
              @click="showLessonForm(module.id)"
              class="btn-add-lesson"
              :disabled="editingLessonId !== null"
            >
              {{ openModuleFormId === module.id ? '× 关闭' : '+ 添加课时' }}
            </button>
          </div>
          
          <ul>
            <li 
              v-for="(lesson, lessonIndex) in sortedLessons(module.lessons)" 
              :key="lesson.id"
              class="lesson-item"
            >
              <div v-if="editingLessonId === lesson.id" class="lesson-edit-form">
                <form @submit.prevent="handleUpdateLesson(lesson.id, module.id)">
                  <div class="form-group">
                    <label>课时标题:</label>
                    <input type="text" v-model="editLessonTitle" required :disabled="isUpdatingLesson">
                  </div>
                  
                  <div class="form-group">
                    <label>课时顺序:</label>
                    <input type="number" v-model.number="editLessonOrder" min="0" :disabled="isUpdatingLesson">
                  </div>
                  
                  <div class="form-group">
                    <label>更新视频文件 (可选):</label>
                    <p class="small-text">(如果不选择新文件, 将保留原视频)</p>
                    <input type="file" @change="handleEditLessonFileChange" accept="video/*" :disabled="isUpdatingLesson">
                  </div>
                  
                  <div class="lesson-edit-actions">
                    <button type="submit" class="btn-save" :disabled="isUpdatingLesson">
                      {{ isUpdatingLesson ? '保存中...' : '保存' }}
                    </button>
                    <button type="button" class="btn-cancel" @click="cancelEditLesson" :disabled="isUpdatingLesson">
                      取消
                    </button>
                  </div>
                </form>
              </div>
              
              <div v-else class="lesson-display">
                <div class="lesson-main-content">
                  <div v-if="isInstructorOfCourse" class="lesson-sort-controls">
                    <button 
                      @click="handleMoveLessonUp(lesson, module.id)"
                      class="btn-sort btn-sort-up"
                      :disabled="isMovingLesson || lessonIndex === 0"
                      title="上移"
                    >
                      ▲
                    </button>
                    <button 
                      @click="handleMoveLessonDown(lesson, module.id)"
                      class="btn-sort btn-sort-down"
                      :disabled="isMovingLesson || lessonIndex === sortedLessons(module.lessons || []).length - 1"
                      title="下移"
                    >
                      ▼
                    </button>
                  </div>
                  
                  <RouterLink 
                    :to="{ name: 'lesson-watch', params: { courseId: course.id, lessonId: lesson.id } }" 
                    class="lesson-link"
                  >
                    <span class="lesson-number">{{ lessonIndex + 1 }}.</span>
                    <span class="lesson-title">{{ lesson.title }}</span>
                    <span v-if="lesson.lesson_type === 'text' && lesson.video_mp4_file" class="lesson-status processing">
                      ⏳ 视频正在处理中...
                    </span>
                    <span v-if="lesson.lesson_type === 'video'" class="lesson-status success">
                      ✅ 视频已就绪
                    </span>
                    <span v-if="!lesson.video_mp4_file && !lesson.video_m3u8_url" class="lesson-status">
                      📝 文本课时
                    </span>
                  </RouterLink>
                </div>
                
                <div v-if="isInstructorOfCourse" class="lesson-actions">
                  <button 
                    @click="startEditLesson(lesson)" 
                    class="btn-edit-lesson"
                    title="编辑课时"
                  >
                    编辑
                  </button>
                  <button 
                    @click="startDeleteLesson(lesson)" 
                    class="btn-delete-lesson"
                    title="删除课时"
                  >
                    删除
                  </button>
                </div>
              </div>
            </li>
             <li v-if="!module.lessons || sortedLessons(module.lessons).length === 0" class="lesson-empty">
                本章节暂无课时
            </li>
          </ul>
          
          <div 
            v-if="isInstructorOfCourse && openModuleFormId === module.id && editingLessonId === null" 
            class="add-lesson-form-inline"
          >
            <form @submit.prevent="handleAddLesson(module.id)">
              <div class="form-group">
                <label>新课时标题:</label>
                <input type="text" v-model="currentLessonTitle" required :disabled="uploadStatus.includes('中')">
              </div>

              <div class="form-group">
                <label>视频文件 (.mp4, .mov):</label>
                <input type="file" @change="handleFileChange" accept="video/*" required :disabled="uploadStatus.includes('中')">
              </div>
              
              <button type="submit" class="admin-button upload-button" :disabled="uploadStatus.includes('中')">
                {{ uploadStatus.includes('中') ? '上传中...' : '上传课时' }}
              </button>

              <p v-if="uploadStatus" class="status-msg">
                {{ uploadStatus }}
              </p>
            </form>
          </div>
        </div>
      </div>
      
      <div v-if="isInstructorOfCourse" class="admin-panel add-chapter-panel">
        <h3>添加新章节</h3>
        <form @submit.prevent="handleAddModule" class="add-module-form">
          <input 
            type="text" 
            v-model="newModuleTitle" 
            placeholder="输入新章节标题" 
            required
          >
          <button type="submit" class="admin-button">添加章节</button>
        </form>
      </div>

    </div>

    <div v-if="showDeleteLessonConfirm" class="delete-confirm-overlay" @click.self="cancelDeleteLesson">
      <div class="delete-confirm-dialog">
        <h3>确认删除课时</h3>
        <p>你确定要删除课时 "<strong>{{ lessonToDelete?.title }}</strong>" 吗？</p>
        <p class="warning-text">此操作不可撤销，课时及其所有评论和进度记录将被永久删除！</p>
        <div class="confirm-actions">
          <button 
            type="button" 
            class="confirm-button cancel-button" 
            @click="cancelDeleteLesson"
            :disabled="isDeletingLesson"
          >
            取消
          </button>
          <button 
            type="button" 
            class="confirm-button delete-confirm-button" 
            @click="handleDeleteLesson"
            :disabled="isDeletingLesson"
          >
            {{ isDeletingLesson ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 样式部分 (完全不变) */
.course-detail { 
  max-width: 800px; 
  margin: 0 auto; 
  padding: 20px;
}
.course-header-actions {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}
hr { margin: 25px 0; }
h1 { font-size: 2.2rem; }
h2 { margin-bottom: 15px; }
.content-management {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.module-container {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background-color: #fcfcfc;
  overflow: hidden;
}
.module-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background-color: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
}
.module-header h3 {
  font-size: 1.25rem;
  margin: 0;
}
.btn-add-lesson {
  padding: 6px 12px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: bold;
}
.btn-add-lesson:hover {
  background-color: #0056b3;
}
.module-container ul {
  list-style: none;
  padding: 10px 20px 20px 20px;
  margin: 0;
}
.add-lesson-form-inline {
  padding: 20px;
  background-color: #fdfdfd;
  border-top: 1px dashed #ccc;
}
.add-lesson-form-inline form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}
.lesson-item {
    margin-bottom: 10px;
    border-radius: 4px;
    border: 1px solid #eee;
    background-color: #fff;
    overflow: hidden;
}
.lesson-display {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 15px;
    gap: 12px;
}
.lesson-main-content {
    display: flex;
    align-items: center;
    flex: 1;
    gap: 12px;
    min-width: 0;
}
.lesson-sort-controls {
    display: flex;
    flex-direction: column;
    gap: 2px;
    flex-shrink: 0;
    margin-right: 4px;
}
.btn-sort {
    width: 32px;
    height: 20px;
    padding: 0;
    border: 1px solid #ced4da;
    background-color: #ffffff;
    color: #495057;
    border-radius: 3px;
    cursor: pointer;
    font-size: 12px;
    font-weight: bold;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
    line-height: 1;
}
.btn-sort:hover:not(:disabled) {
    background-color: #007bff;
    color: white;
    border-color: #007bff;
    transform: scale(1.05);
}
.btn-sort:active:not(:disabled) {
    transform: scale(0.95);
}
.btn-sort:disabled {
    opacity: 0.3;
    cursor: not-allowed;
    background-color: #f8f9fa;
}
.btn-sort-up {
    border-bottom-left-radius: 0;
    border-bottom-right-radius: 0;
    border-bottom: none;
}
.btn-sort-down {
    border-top-left-radius: 0;
    border-top-right-radius: 0;
    margin-top: -1px;
}
.lesson-number {
    font-weight: bold;
    color: #6c757d;
    margin-right: 6px;
    flex-shrink: 0;
    min-width: 24px;
    text-align: right;
}
.lesson-link {
  flex: 1;
  text-decoration: none;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.lesson-link:hover {
    color: #007bff;
}
.lesson-title {
    font-weight: 500;
}
.lesson-status {
    font-size: 0.85rem;
    color: #888;
    margin-left: 8px;
}
.lesson-status.success {
    color: #28a745;
    font-weight: 500;
}
.lesson-status.processing {
    color: #ffc107;
    font-weight: 500;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.6;
    }
}
.video-processing-notice {
    background-color: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.video-processing-notice p {
    margin: 0;
    color: #856404;
    font-size: 0.95rem;
}
.btn-refresh {
    padding: 6px 12px;
    background-color: #ffc107;
    color: #856404;
    border: 1px solid #ffc107;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: bold;
    transition: background-color 0.2s;
}
.btn-refresh:hover {
    background-color: #ffb300;
}
.lesson-actions {
    display: flex;
    gap: 8px;
}
.btn-edit-lesson,
.btn-delete-lesson {
    padding: 5px 12px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: bold;
    transition: background-color 0.2s;
}
.btn-edit-lesson {
    background-color: #007bff;
    color: white;
}
.btn-edit-lesson:hover {
    background-color: #0056b3;
}
.btn-delete-lesson {
    background-color: #dc3545;
    color: white;
}
.btn-delete-lesson:hover {
    background-color: #c82333;
}
.lesson-edit-form {
    padding: 15px;
    background-color: #f9f9f9;
    border-top: 2px solid #007bff;
}
.lesson-edit-form .form-group {
    margin-bottom: 12px;
}
.lesson-edit-form .form-group label {
    display: block;
    font-weight: bold;
    margin-bottom: 5px;
    font-size: 0.9rem;
}
.lesson-edit-form .form-group input {
    width: 100%;
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    box-sizing: border-box;
}
.lesson-edit-actions {
    display: flex;
    gap: 10px;
    margin-top: 15px;
}
.btn-save,
.btn-cancel {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
    transition: background-color 0.2s;
}
.btn-save {
    background-color: #28a745;
    color: white;
}
.btn-save:hover:not(:disabled) {
    background-color: #218838;
}
.btn-cancel {
    background-color: #6c757d;
    color: white;
}
.btn-cancel:hover:not(:disabled) {
    background-color: #5a6268;
}
.btn-save:disabled,
.btn-cancel:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}
.lesson-empty {
    font-style: italic;
    color: #888;
    padding: 10px 15px;
}
.lesson-message {
    padding: 12px;
    border-radius: 4px;
    margin-bottom: 15px;
    font-size: 0.95rem;
}
.lesson-message.success {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}
.lesson-message.error {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}
.add-chapter-panel {
  margin-top: 30px;
  border: 2px dashed #28a745; 
  padding: 15px;
  border-radius: 8px;
  background-color: #f0fff4;
}
.add-chapter-panel h3 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #28a745;
}
.add-module-form { 
  display: flex; 
  gap: 10px; 
}
.add-module-form input { 
  flex-grow: 1; 
  padding: 10px; 
  border: 1px solid #ccc; 
  border-radius: 4px; 
}
.form-group label { 
  display: block;
  font-weight: bold; 
  margin-bottom: 5px; 
  font-size: 0.9rem;
}
.form-group input { 
  width: 100%;
  padding: 8px; 
  border: 1px solid #ccc; 
  border-radius: 4px;
  box-sizing: border-box;
}
.admin-button { 
  padding: 10px 15px; 
  background-color: #007bff; 
  color: white; 
  border: none; 
  border-radius: 4px; 
  cursor: pointer;
  font-weight: bold;
}
.admin-button:hover { 
  background-color: #0056b3; 
}
.upload-button { 
  background-color: #28a745; 
  align-self: flex-start;
}
.upload-button:hover {
  background-color: #218838;
}
.status-msg { 
    margin-top: 10px; 
    font-weight: bold; 
}
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